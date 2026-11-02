#!/usr/bin/env python3
"""Count per-sample molecular transformation degree, including zero-degree peaks.

Inputs must be the same GW workbook, Lake ZIP, and transformation results used by
run_miyun_transformations.py. The two RI flags are alternative thresholds; this
script does not choose markers or perform source apportionment.
"""

import argparse
from collections import defaultdict
import csv
from io import BytesIO
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from openpyxl import load_workbook

from run_miyun_transformations import natural_key, read_sample


PEAK_FIELDS = [
    "endpoint", "sample", "Mass", "formula", "C", "H", "O", "N", "P", "S",
    "transformation_count", "RI_eq0", "RI_le1",
]
SUMMARY_FIELDS = [
    "endpoint", "sample", "retained_peaks", "matched_peak_pairs", "count_eq0",
    "count_eq1", "count_le1", "percent_eq0", "percent_le1", "mean_count",
    "max_count",
]


def analyze_sample(endpoint, name, records, results_root, writer, formulas):
    sample = f"Sample_{endpoint}_{name}"
    masses = {record[1] for record in records}
    if len(masses) != len(records):
        raise ValueError(f"{sample}: duplicate masses")
    counts = defaultdict(int)
    seen = set()
    path = results_root / endpoint / "Transformation Peak Comparisons" / f"Peak.2.Peak_{sample}.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        pairs = 0
        for row in reader:
            x, y = row["peak.x"], row["peak.y"]
            if row["sample"] != sample or x not in masses or y not in masses or float(x) <= float(y):
                raise ValueError(f"{sample}: invalid transformation pair")
            if (x, y) in seen:
                raise ValueError(f"{sample}: duplicate transformation pair")
            seen.add((x, y))
            counts[x] += 1
            counts[y] += 1
            pairs += 1
    if sum(counts.values()) != 2 * pairs:
        raise ValueError(f"{sample}: transformation degree sum disagrees with pair count")

    count0 = count1 = max_count = 0
    for _, mass_text, molecule in records:
        degree = counts[mass_text]
        count0 += degree == 0
        count1 += degree == 1
        max_count = max(max_count, degree)
        formula = molecule["MolForm"]
        writer.writerow([
            endpoint, sample, mass_text, formula,
            *[molecule[symbol] for symbol in ("C", "H", "O", "N", "P", "S")],
            degree, int(degree == 0), int(degree <= 1),
        ])
        record = formulas[(endpoint, formula)]
        record[0] += 1
        record[1] += degree == 0
        record[2] += degree <= 1
    n = len(records)
    print(f"{sample}: {n} peaks; {pairs} pairs; degree 0={count0}; degree 1={count1}", flush=True)
    return [endpoint, sample, n, pairs, count0, count1, count0 + count1,
            round(100 * count0 / n, 4), round(100 * (count0 + count1) / n, 4),
            round(2 * pairs / n, 4), max_count]


def run(gw_path, lake_path, results_root, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    formulas = defaultdict(lambda: [0, 0, 0])
    with (output_dir / "per_peak_degree.csv").open("w", newline="", encoding="utf-8") as peak_file:
        writer = csv.writer(peak_file)
        writer.writerow(PEAK_FIELDS)

        gw = load_workbook(gw_path, read_only=True, data_only=True)
        sheets = [sheet for sheet in gw if sheet.title != "ALL_6_GW"]
        if len(sheets) != 6:
            raise ValueError("Expected six individual groundwater sheets")
        for sheet in sheets:
            records, _ = read_sample(sheet)
            summaries.append(analyze_sample("GW", sheet.title, records, results_root, writer, formulas))
        gw.close()

        with ZipFile(lake_path) as archive:
            names = [name for name in archive.namelist() if
                     PurePosixPath(name).parts[:1] == ("Lake",) and
                     name.endswith("_result.xlsx") and len(PurePosixPath(name).parts) == 2]
            if len(names) != 50:
                raise ValueError("Expected 50 Lake workbooks")
            names.sort(key=lambda name: natural_key(PurePosixPath(name).stem))
            for member in names:
                name = PurePosixPath(member).stem.removesuffix("_result")
                workbook = load_workbook(BytesIO(archive.read(member)), read_only=True, data_only=True)
                records, _ = read_sample(workbook.active)
                summaries.append(analyze_sample("Lake", name, records, results_root, writer, formulas))
                workbook.close()

    with (output_dir / "sample_threshold_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(SUMMARY_FIELDS)
        writer.writerows(summaries)
    with (output_dir / "formula_threshold_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["endpoint", "formula", "samples_detected", "samples_RI_eq0",
                         "samples_RI_le1", "always_RI_eq0", "always_RI_le1"])
        for (endpoint, formula), (detected, zero, le1) in sorted(formulas.items()):
            writer.writerow([endpoint, formula, detected, zero, le1,
                             int(zero == detected), int(le1 == detected)])
    for endpoint in ("GW", "Lake"):
        rows = [row for row in summaries if row[0] == endpoint]
        print(endpoint, "peaks", sum(r[2] for r in rows), "degree 0", sum(r[4] for r in rows),
              "degree 1", sum(r[5] for r in rows), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groundwater", type=Path, required=True)
    parser.add_argument("--lake-zip", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.groundwater, args.lake_zip, args.results_root, args.output_dir)
