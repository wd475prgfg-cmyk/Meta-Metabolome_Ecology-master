#!/usr/bin/env python3
"""Run the PPT molecular-transformation step for the Miyun GW and Lake workbooks.

Use the six individual Groundwater sheets (the ALL_6_GW sheet duplicates them)
and each Lake/*_result.xlsx workbook as a separate sample. Input workbooks
already provide measured m/z, intensity, elemental composition, and formula.
"""

import argparse
import csv
from io import BytesIO
from pathlib import Path, PurePosixPath
import re
from zipfile import ZipFile

import numpy as np
from openpyxl import load_workbook

import run_molecular_transformations as core


NEEDED = ("meas.m/z", "formula", "intens", "C", "H", "N", "O", "P", "S")
MASS_MIN, MASS_MAX = 200, 900  # The FTMS_Analysis.R mass filter used in the PPT.


def read_sample(sheet):
    rows = sheet.iter_rows(values_only=True)
    header = next(rows)
    positions = {name: i for i, name in enumerate(header)}
    if missing := set(NEEDED) - set(positions):
        raise ValueError(f"{sheet.title}: missing columns {sorted(missing)}")

    records = []
    counts = {"source_peaks": 0, "outside_200_900": 0, "nonpositive_intensity": 0}
    for row in rows:
        if row[positions["meas.m/z"]] is None:
            continue
        counts["source_peaks"] += 1
        raw_mass = float(row[positions["meas.m/z"]])
        mass = round(raw_mass, 6)
        if not np.isfinite(raw_mass) or abs(raw_mass - mass) > 1e-8:
            raise ValueError(f"{sheet.title}: mass has unexpected precision: {raw_mass}")
        if not MASS_MIN <= mass <= MASS_MAX:
            counts["outside_200_900"] += 1
            continue
        intensity = float(row[positions["intens"]] or 0)
        if not np.isfinite(intensity):
            raise ValueError(f"{sheet.title}: intensity is not finite at mass {mass}")
        if intensity <= 0:
            counts["nonpositive_intensity"] += 1
            continue
        formula = row[positions["formula"]]
        if formula is None or str(formula).strip() == "":
            formula = "NA"
        elements = {}
        for symbol in ("C", "H", "O", "N", "P", "S"):
            value = row[positions[symbol]]
            number = float(value or 0)
            if not np.isfinite(number) or number < 0 or number != int(number):
                raise ValueError(f"{sheet.title}: invalid {symbol} count at mass {mass}")
            elements[symbol] = str(int(number))
        records.append((mass, f"{mass:.6f}", {**elements, "MolForm": str(formula), "Class": "None"}))

    records.sort(key=lambda item: item[0])
    if len({item[0] for item in records}) != len(records):
        raise ValueError(f"{sheet.title}: repeated Mass after six-decimal normalization")
    counts["retained_peaks"] = len(records)
    return records, counts


def transformation_database(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not {"Name", "Mass"}.issubset(reader.fieldnames or []):
            raise ValueError("Database is missing Name or Mass")
        records = [(row["Name"], float(row["Mass"])) for row in reader]
    if not records:
        raise ValueError("Empty transformation database")
    return records


def write_sample(output_dir, endpoint, name, records, transformations):
    sample = f"Sample_{endpoint}_{name}"
    masses = np.array([r[0] for r in records], dtype=np.float64)
    mass_text = [r[1] for r in records]
    molecular = [r[2] for r in records]
    matches = core.match_all_masses(masses, transformations)
    comparison_dir = output_dir / endpoint / "Transformation Peak Comparisons"
    annotated_dir = output_dir / endpoint / "Annotated Peak Comparisons"
    comparison_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir.mkdir(parents=True, exist_ok=True)
    filename = f"Peak.2.Peak_{sample}.csv"
    with (comparison_dir / filename).open("w", newline="", encoding="utf-8") as plain_file, \
            (annotated_dir / filename).open("w", newline="", encoding="utf-8") as annotated_file:
        plain = csv.writer(plain_file)
        annotated = csv.writer(annotated_file)
        plain.writerow(core.COMPARISON_FIELDS)
        annotated.writerow(core.ANNOTATED_FIELDS)
        for (x_index, y_index), trans_index in matches:
            difference = float(masses[x_index] - masses[y_index])
            trans_name = transformations[trans_index][0]
            plain.writerow([
                sample, core.formatted_difference(difference), mass_text[x_index],
                mass_text[y_index], core.formatted_difference(difference + core.TOLERANCE),
                core.formatted_difference(difference - core.TOLERANCE), trans_name,
            ])
            annotated.writerow(core.annotated_row(
                sample, mass_text, molecular, x_index, y_index, difference, trans_name
            ))
    print(f"{sample}: {len(records)} peaks; {len(matches)} matched pairs", flush=True)
    return sample, len(matches), sum(
        molecular[x]["MolForm"] != "NA" and molecular[y]["MolForm"] != "NA"
        for (x, y), _ in matches
    )


def natural_key(text):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text)]


def run(groundwater_path, lake_zip_path, database_path, output_dir):
    transformations = transformation_database(database_path)
    summary = []

    gw = load_workbook(groundwater_path, read_only=True, data_only=True)
    gw_sheets = [sheet for sheet in gw if sheet.title != "ALL_6_GW"]
    if len(gw_sheets) != 6:
        raise ValueError("Expected six individual groundwater sheets")
    for sheet in gw_sheets:
        records, counts = read_sample(sheet)
        sample, pair_count, known_formulas = write_sample(
            output_dir, "GW", sheet.title, records, transformations
        )
        summary.append(("GW", sample, sheet.title, *counts.values(), pair_count, known_formulas))
    gw.close()

    with ZipFile(lake_zip_path) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise ValueError(f"Lake ZIP has a damaged entry: {bad}")
        members = [name for name in archive.namelist() if
                   PurePosixPath(name).parts[:1] == ("Lake",) and
                   name.endswith("_result.xlsx") and len(PurePosixPath(name).parts) == 2]
        if len(members) != 50:
            raise ValueError(f"Expected 50 Lake sample workbooks; found {len(members)}")
        members.sort(key=lambda name: natural_key(PurePosixPath(name).stem))
        for member in members:
            name = PurePosixPath(member).stem.removesuffix("_result")
            if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
                raise ValueError(f"Unexpected Lake sample name: {member}")
            workbook = load_workbook(BytesIO(archive.read(member)), read_only=True, data_only=True)
            if workbook.sheetnames != ["result"]:
                raise ValueError(f"Unexpected sheets in {member}: {workbook.sheetnames}")
            records, counts = read_sample(workbook.active)
            sample, pair_count, known_formulas = write_sample(
                output_dir, "Lake", name, records, transformations
            )
            summary.append(("Lake", sample, member, *counts.values(), pair_count, known_formulas))
            workbook.close()

    header = ["endpoint", "sample", "source", "source_peaks", "outside_200_900",
              "nonpositive_intensity", "retained_peaks", "matched_peak_pairs",
              "both_formulas_known"]
    with (output_dir / "sample_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(summary)
    for endpoint in ("GW", "Lake"):
        rows = [row for row in summary if row[0] == endpoint]
        with (output_dir / endpoint / "sample_summary.csv").open(
                "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)
        print(f"{endpoint}: {len(rows)} samples; {sum(row[-2] for row in rows)} matched pairs", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groundwater", type=Path, required=True)
    parser.add_argument("--lake-zip", type=Path, required=True)
    parser.add_argument("--database", type=Path,
                        default=Path(__file__).resolve().parent / "Transformation_Database_07-2020.csv")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    run(args.groundwater, args.lake_zip, args.database, args.output_dir)
