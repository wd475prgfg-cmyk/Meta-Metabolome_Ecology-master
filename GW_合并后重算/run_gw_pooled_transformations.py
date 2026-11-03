#!/usr/bin/env python3
"""Pool six GW samples by formula, select N>0 and H/C<1.5, then build one network.

The primary count is degree in the selected-formula network. It does not count
connections to formulas excluded by the N/H:C selection. No Lake data are used.
"""

import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZipFile, ZIP_DEFLATED

import numpy as np
import pandas as pd
from openpyxl import load_workbook

import run_molecular_transformations as core


ELEMENTS = ["C", "H", "O", "N", "P", "S"]
SAMPLES = ["Groundwater-2", "Groundwater-8", "Groundwater-10",
           "Groundwater-Yt", "Groundwater-Yz", "Groundwater-Zh"]
TITLE = "地下水六样合并_N大于0_HC小于1.5_转化次数"
MASS_SCALE = 1_000_000_000  # exact nanodaltons; database has at most 9 decimals
TOLERANCE_NDA = 10_000


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mass_to_integer(value):
    scaled = Decimal(str(value)) * MASS_SCALE
    if scaled != scaled.to_integral_value():
        raise ValueError(f"Mass exceeds 9 decimal places: {value}")
    return int(scaled)


def input_mass_integer(value, decimal_places):
    original = Decimal(str(value))
    normalized = original.quantize(Decimal(10) ** -decimal_places)
    if abs(original - normalized) > Decimal("0.0000000001"):
        raise ValueError(f"Unexpected input precision: {value}")
    return mass_to_integer(normalized)


def match_integer_masses(masses, transformations):
    """Inclusive tolerance unaffected by floating-point roundoff.

    One undirected pair; retain the last database hit, as in the original code.
    """
    db_masses = np.array([mass for _, mass in transformations], dtype=np.int64)
    matched = {}
    for start in range(0, len(masses), 512):
        target = masses[start:start + 512, None] + db_masses[None, :]
        left = np.searchsorted(masses, target - TOLERANCE_NDA, side="left")
        right = np.searchsorted(masses, target + TOLERANCE_NDA, side="right")
        for y_local, trans_index in np.argwhere(left < right):
            y = start + int(y_local)
            for x in range(int(left[y_local, trans_index]), int(right[y_local, trans_index])):
                if x > y:
                    matched[(x, y)] = int(trans_index)
    return sorted(matched.items())


def read_groundwater(path):
    wb = load_workbook(path, read_only=True, data_only=True)
    if set(wb.sheetnames) - {"ALL_6_GW"} != set(SAMPLES):
        raise ValueError("Expected the six named groundwater sheets")
    records = []
    for sample in SAMPLES:
        rows = wb[sample].iter_rows(values_only=True)
        headers = list(next(rows))
        required = {"meas.m/z", "theor.m/z", "formula", "intens", *ELEMENTS}
        if required - set(headers):
            raise ValueError(f"{sample}: missing columns")
        for row_number, values in enumerate(rows, start=2):
            record = dict(zip(headers, values))
            if record["meas.m/z"] is None:
                continue
            record.update(sample=sample, Excel_Row=row_number)
            records.append(record)
    wb.close()
    raw = pd.DataFrame(records)
    if raw["formula"].isna().any():
        raise ValueError("Missing molecular formula")
    raw["formula"] = raw["formula"].str.strip()
    if raw["formula"].eq("").any() or raw.duplicated(["sample", "formula"]).any():
        raise ValueError("Blank or repeated formula within a sample")
    for column in ["meas.m/z", "theor.m/z", "intens", *ELEMENTS]:
        raw[column] = pd.to_numeric(raw[column], errors="raise")
        if not np.isfinite(raw[column]).all():
            raise ValueError(f"Nonfinite {column}")
    if ((raw[ELEMENTS] < 0) | (raw[ELEMENTS] != np.floor(raw[ELEMENTS]))).any().any():
        raise ValueError("Invalid elemental composition")
    raw[ELEMENTS] = raw[ELEMENTS].astype(int)
    raw["Measured_Mass_nDa"] = raw["meas.m/z"].map(lambda v: input_mass_integer(v, 6))
    raw["Theoretical_Mass_nDa"] = raw["theor.m/z"].map(lambda v: input_mass_integer(v, 9))
    for column in [*ELEMENTS, "theor.m/z"]:
        if raw.groupby("formula")[column].nunique().max() != 1:
            raise ValueError(f"Inconsistent {column} for the same formula")
    raw["Included_200_900_positive"] = raw["meas.m/z"].between(200, 900) & raw["intens"].gt(0)
    raw["H_C_calculated"] = raw["H"] / raw["C"].replace(0, np.nan)
    raw["Eligible_N_HC"] = raw["N"].gt(0) & raw["C"].gt(0) & (2 * raw["H"] < 3 * raw["C"])
    return raw


def pooled_formulas(raw, method):
    retained = raw.loc[raw["Included_200_900_positive"]].copy()
    group = retained.groupby("formula", sort=True)
    pooled = group[ELEMENTS].first()
    pooled["H_C"] = pooled["H"] / pooled["C"].replace(0, np.nan)
    pooled["GW_Sample_Count"] = group["sample"].nunique()
    pooled["GW_Samples"] = group["sample"].agg(lambda x: ";".join(x))
    median_integer = group["Measured_Mass_nDa"].median()
    if not (median_integer == np.floor(median_integer)).all():
        raise ValueError("Median needs finer than 1e-9 Da precision")
    pooled["Measured_mz_median"] = median_integer.astype(np.int64) / MASS_SCALE
    pooled["Measured_mz_min"] = group["meas.m/z"].min()
    pooled["Measured_mz_max"] = group["meas.m/z"].max()
    pooled["Measured_mz_span"] = pooled["Measured_mz_max"] - pooled["Measured_mz_min"]
    pooled["Theoretical_neutral_mass"] = group["theor.m/z"].first()
    pooled["Representative_Mass_nDa"] = (median_integer.astype(np.int64) if method == "median"
                                             else group["Theoretical_Mass_nDa"].first())
    pooled["Representative_Mass"] = pooled["Representative_Mass_nDa"] / MASS_SCALE
    pooled["Mass_Method"] = method
    pooled["Eligible_N_HC"] = pooled["N"].gt(0) & pooled["C"].gt(0) & (2 * pooled["H"] < 3 * pooled["C"])
    for source, prefix in [("meas.m/z", "Measured_mz"), ("intens", "Raw_intensity")]:
        wide = retained.pivot(index="formula", columns="sample", values=source).reindex(columns=SAMPLES)
        wide.columns = [f"{prefix}_{sample}" for sample in wide.columns]
        pooled = pooled.join(wide)
    return pooled.reset_index()


def write_workbook(path, sheets):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
            sheet = writer.sheets[name]
            sheet.freeze_panes = "B2"
            sheet.auto_filter.ref = sheet.dimensions
            for column in sheet.iter_cols(min_row=1, max_row=1):
                cell = column[0]
                sheet.column_dimensions[cell.column_letter].width = min(42, max(14, len(str(cell.value)) + 2))


def run(args):
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    raw = read_groundwater(args.groundwater)
    pooled = pooled_formulas(raw, args.mass_method)
    selected = pooled.loc[pooled["Eligible_N_HC"]].sort_values(
        ["Representative_Mass", "formula"], kind="stable").reset_index(drop=True)
    masses = selected["Representative_Mass"].to_numpy(dtype=np.float64)
    integer_masses = selected["Representative_Mass_nDa"].to_numpy(dtype=np.int64)
    if not np.all(np.diff(integer_masses) > 0):
        raise ValueError("Selected formulas must have distinct representative masses")
    with args.database.open(encoding="utf-8-sig", newline="") as handle:
        transformations = [(row["Name"], mass_to_integer(row["Mass"])) for row in csv.DictReader(handle)]
    if not transformations or any(m <= 0 for _, m in transformations):
        raise ValueError("Invalid transformation database")
    matches = match_integer_masses(integer_masses, transformations)
    degrees = np.zeros(len(selected), dtype=np.int64)
    molecular = [dict(**{e: str(row[e]) for e in ELEMENTS}, MolForm=row["formula"], Class="None")
                 for row in selected.to_dict("records")]
    # Retain the possible 7th decimal of medians of six-decimal measured values.
    mass_text = [core.formatted_difference(x) for x in masses]
    annotated_rows = []
    for (x, y), transformation in matches:
        degrees[x] += 1
        degrees[y] += 1
        annotated_rows.append(core.annotated_row(
            "GW_6_Pooled_N_HC", mass_text, molecular, x, y,
            int(integer_masses[x] - integer_masses[y]) / MASS_SCALE, transformations[transformation][0]))
    annotated = pd.DataFrame(annotated_rows, columns=core.ANNOTATED_FIELDS)
    selected.insert(1, "Transformation_Count", degrees)
    selected.insert(2, "RI_le1_in_selected_network", degrees <= 1)
    selected.insert(3, "Zero_in_selected_network", degrees == 0)
    if int(degrees.sum()) != 2 * len(matches):
        raise AssertionError("Degree sum must be twice the number of pairs")
    if len({pair for pair, _ in matches}) != len(matches):
        raise AssertionError("Duplicate pairs")
    ri = selected.loc[selected["Transformation_Count"] <= 1].copy()
    zero = selected.loc[selected["Transformation_Count"] == 0].copy()
    one = selected.loc[selected["Transformation_Count"] == 1].copy()
    retained = raw.loc[raw["Included_200_900_positive"]]
    counts = {
        "原始样本数": len(SAMPLES), "原始峰记录": len(raw),
        "原始合并去重分子式": raw["formula"].nunique(),
        "200–900且正峰强记录": len(retained),
        "200–900合并分子式": len(pooled),
        "合并后N大于0分子式": int(pooled["N"].gt(0).sum()),
        "N大于0且HC小于1.5分子式": len(selected),
        "筛后集合匹配峰对": len(matches),
        "转化次数等于0": len(zero), "转化次数等于1": len(one),
        "转化次数小于等于1": len(ri), "转化次数大于1": int((degrees > 1).sum()),
    }
    summary = pd.DataFrame(counts.items(), columns=["步骤", "数量"])
    mass_description = ("同一分子式六样本已检出实测 meas.m/z 的中位数，保留第7位小数，不按6位再舍入"
                        if args.mass_method == "median" else "同一分子式的 theor.m/z；原表该列为理论中性质量")
    notes = [
        ("计算顺序", "六个GW样本按分子式合并 → N>0且H/C<1.5 → 对筛后分子建一个网络 → 统计每式连接数"),
        ("质量预处理", "沿用此前200–900 Da（含端点），intens>0；仅读六张独立样本表，ALL_6_GW不重复加入"),
        ("合并质量", mass_description),
        ("精确条件", "N>0且C>0且2H<3C；H/C从元素计数计算，不用四舍五入后的展示值"),
        ("转化次数含义", "每个分子与筛后集合中其他分子匹配的不同峰对数；一次无向连接给两端各计1次"),
        ("零次的范围", "仅表示筛后网络内0次；N=0或H/C>=1.5等被排除分子与其连边不计入"),
        ("RI主要阈值", "转化次数≤1；零次和恰好一次分别列出。该RI计数限定于本次筛后网络"),
        ("匹配规则", "沿用1255条数据库和峰对规则，±0.000010 Da含端点；多条库命中同一峰对时保留库最后一条"),
        ("数值实现", "以1e-9 Da整数运算执行闭区间匹配，修正旧浮点代码在恰好容差边界的漏匹配；不是旧浮点算法逐位复刻"),
        ("输入质量精度", "实测质量规范化到原始6位，理论质量9位，仅移除不超过1e-10 Da的Excel二进制表示误差；中位数保留第7位"),
        ("可复算质量", "Representative_Mass_nDa为精确整数代表质量，除以10^9得到Da；中位数从原始整数质量求得"),
        ("算法解释", "基于质量差的潜在转化匹配，不是实测反应速率或反应发生次数"),
        ("marker状态", "地下水筛后网络RI候选；未比较其他来源端元，尚非端元独有marker"),
        ("湖水", "本轮只重算地下水；Lake是受体，不作为排除参照，也不参与本轮网络"),
        ("注释字段", "23列分子转化表延续原表字段；Class输入缺失，以字符串None占位"),
        ("质量与峰强溯源", "合并表含各样本原实测m/z及intens；缺失留空。强度未归一化、未求和"),
        ("原表RI列", "原始峰记录中的RI为输入原值，未用作本轮Transformation_Count或筛选依据"),
        ("同位素处理", "原输入无C13指示列，本轮未额外执行同位素过滤"),
        ("输入SHA256", sha256(args.groundwater)),
        ("转化数据库SHA256", sha256(args.database)),
    ]
    sheets = {
        "计算说明": pd.DataFrame(notes, columns=["项目", "说明"]),
        "筛选汇总": summary,
        "合并后全部分子式": pooled,
        "筛后分子_转化次数": selected,
        "转化次数≤1": ri,
        "转化次数=0": zero,
        "转化次数=1": one,
        "分子转化23列": annotated,
        "六样原始峰记录": raw,
    }
    workbook = output / f"{TITLE}.xlsx"
    write_workbook(workbook, sheets)
    for filename, frame in [("合并分子式.csv", pooled), ("筛后分子_转化次数.csv", selected),
                            ("转化次数≤1.csv", ri), ("转化次数=0.csv", zero),
                            ("分子转化23列.csv", annotated), ("筛选汇总.csv", summary)]:
        frame.to_csv(output / filename, index=False, encoding="utf-8-sig", float_format="%.12g")
    metadata = {"input_filename": args.groundwater.name, "input_sha256": sha256(args.groundwater),
                "mass_method": args.mass_method, "mass_range": [200, 900],
                "network_scope": "pooled unique formulas with N>0 and H/C<1.5",
                "tolerance_Da": core.TOLERANCE, "database_rows": len(transformations),
                "matching_arithmetic": "integer nanodaltons, inclusive tolerance 10000 nDa",
                "database_sha256": sha256(args.database), "counts": counts,
                "software": {"numpy": np.__version__, "pandas": pd.__version__},
                "core_sha256": sha256(core.__file__)}
    (output / "计算参数.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    readme = "# 地下水六样合并后重算：N > 0，H/C < 1.5\n\n"
    readme += "\n\n".join(f"**{key}**：{value}" for key, value in notes) + "\n\n"
    readme += "|步骤|数量|\n|---|---:|\n" + "".join(f"|{key}|{value:,}|\n" for key, value in counts.items())
    readme += '\n复算（输入为用户原始工作簿）：\n\n```bash\npython -m pip install -r requirements.txt\n'
    readme += f'python run_gw_pooled_transformations.py --groundwater "九月密云_GW_6样合并.xlsx" --output-dir output --mass-method {args.mass_method}\n```\n'
    readme += "\n工作簿同时提供≤1、=0和=1子表，标题覆盖全部转化次数；零次候选尚未完成其他来源端元排重。\n"
    (output / "README.md").write_text(readme, encoding="utf-8")
    (output / "requirements.txt").write_text("numpy\npandas\nopenpyxl\n", encoding="utf-8")
    for path in [Path(__file__), Path(core.__file__), args.database]:
        destination = output / path.name
        if path.resolve() != destination.resolve():
            shutil.copy2(path, destination)
    hashes = [f"{sha256(path)}  {path.name}" for path in sorted(output.iterdir())
              if path.is_file() and path.name != "SHA256SUMS.txt"]
    (output / "SHA256SUMS.txt").write_text("\n".join(hashes) + "\n", encoding="utf-8")
    archive_path = output.parent / f"{TITLE}_结果与代码.zip"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(output.iterdir()):
            if path.is_file():
                archive.write(path, f"{output.name}/{path.name}")
    with ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise AssertionError("ZIP integrity check failed")
    print(json.dumps({"counts": counts, "workbook": str(workbook), "zip": str(archive_path),
                      "zip_bytes": archive_path.stat().st_size}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groundwater", type=Path, required=True)
    parser.add_argument("--database", type=Path,
                        default=Path(__file__).resolve().parent / "Transformation_Database_07-2020.csv")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mass-method", choices=["median", "theoretical"], default="median")
    run(parser.parse_args())
