#!/usr/bin/env python3
"""Run the per-sample mass-difference analysis in Transformation_Analysis_by_Sample.R.

The supplied archive already contains the processed Data and Mol CSV files. This
runner names those inputs explicitly, avoids the example paths in the R script,
and writes only the molecular transformation comparison stage.
"""

import argparse
import csv
import math
from pathlib import Path

import numpy as np


TOLERANCE = 0.000010  # Da; inclusive, as in the R script
SEARCH_MARGIN = 1e-9  # Cover floating-point rounding; the exact R predicate runs below.
BASE = Path(__file__).resolve().parent
REPORTS = BASE / "Manuscript Specifc Files" / "FTICR Reports"
DEFAULT_DATA = REPORTS / "Processed_Shoreline_FTICR_Data_clean.csv"
DEFAULT_MOL = REPORTS / "Processed_Shoreline_FTICR_Mol_clean.csv"
DEFAULT_DB = BASE / "Transformation_Database_07-2020.csv"
DEFAULT_OUTPUT = BASE / "Molecular_Transformation_Results"

COMPARISON_FIELDS = [
    "sample", "Dist", "peak.x", "peak.y", "Dist.plus", "Dist.minus", "Trans.name"
]
ANNOTATED_FIELDS = [
    "sample", "peak.x", "C_x", "H_x", "O_x", "N_x", "P_x", "S_x",
    "formula_x", "class_x", "peak.y", "C_y", "H_y", "O_y", "N_y",
    "P_y", "S_y", "formula_y", "class_y", "Dist", "Dist.plus",
    "Dist.minus", "Trans.name",
]


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 2:
        raise ValueError(f"Empty input: {path}")
    return rows[0], rows[1:]


def load_inputs(data_path, mol_path, db_path):
    data_header, data_rows = read_csv(data_path)
    mol_header, mol_rows = read_csv(mol_path)
    db_header, db_rows = read_csv(db_path)

    if not data_header[1:] or len(set(data_header[1:])) != len(data_header[1:]):
        raise ValueError("Data must have distinct sample columns")
    if len(data_rows) != len(mol_rows) or [r[0] for r in data_rows] != [r[0] for r in mol_rows]:
        raise ValueError("Data and Mol Mass rows do not match in order")
    if any(len(r) != len(data_header) for r in data_rows):
        raise ValueError("Data has a row with the wrong number of columns")
    if any(len(r) != len(mol_header) for r in mol_rows):
        raise ValueError("Mol has a row with the wrong number of columns")
    needed = {"C", "H", "O", "N", "P", "S", "C13", "MolForm", "Class"}
    if not needed.issubset(mol_header):
        raise ValueError(f"Mol is missing columns: {sorted(needed - set(mol_header))}")
    if not {"Name", "Mass"}.issubset(db_header):
        raise ValueError("Transformation database must contain Name and Mass")

    mass_text = [r[0] for r in data_rows]
    masses = np.array([float(v) for v in mass_text], dtype=np.float64)
    if not np.isfinite(masses).all() or not np.all(np.diff(masses) > 0):
        raise ValueError("Mass values must be finite, distinct, and increasing")
    molecular = [dict(zip(mol_header, row)) for row in mol_rows]
    if any(float(row["C13"] or 0) == 1 for row in molecular):
        raise ValueError("C13 isotope peaks are present; process the FTMS report first")

    abundance = np.array([[float(v) for v in row[1:]] for row in data_rows], dtype=np.float64)
    if not np.isfinite(abundance).all():
        raise ValueError("Data contains a non-finite intensity")
    transformations = [(row[db_header.index("Name")], float(row[db_header.index("Mass")])) for row in db_rows]
    if not transformations or any(not math.isfinite(m) or m <= 0 for _, m in transformations):
        raise ValueError("Transformation masses must be finite and positive")
    return data_header[1:], mass_text, masses, molecular, abundance, transformations


def match_all_masses(masses, transformations):
    """Find positive differences, assigning the last database hit per peak pair."""
    db_masses = np.array([mass for _, mass in transformations], dtype=np.float64)
    matched = {}
    for start in range(0, len(masses), 512):
        target = masses[start:start + 512, None] + db_masses[None, :]
        left = np.searchsorted(masses, target - TOLERANCE - SEARCH_MARGIN, side="left")
        right = np.searchsorted(masses, target + TOLERANCE + SEARCH_MARGIN, side="right")
        for y_local, trans_index in np.argwhere(left < right):
            y_index = start + int(y_local)
            for x_index in range(int(left[y_local, trans_index]), int(right[y_local, trans_index])):
                difference = masses[x_index] - masses[y_index]
                db_mass = db_masses[trans_index]
                if x_index > y_index and difference + TOLERANCE >= db_mass and difference - TOLERANCE <= db_mass:
                    matched[(x_index, y_index)] = int(trans_index)
    return sorted(matched.items())


def formatted_difference(value):
    """Avoid floating-point display artifacts in the mass-difference CSVs."""
    return f"{value:.10f}".rstrip("0").rstrip(".")


def annotated_row(sample, mass_text, molecular, x_index, y_index, difference, name):
    x, y = molecular[x_index], molecular[y_index]
    return [
        sample, mass_text[x_index], *[x[k] for k in ("C", "H", "O", "N", "P", "S")],
        x["MolForm"], x["Class"], mass_text[y_index],
        *[y[k] for k in ("C", "H", "O", "N", "P", "S")],
        y["MolForm"], y["Class"], formatted_difference(difference),
        formatted_difference(difference + TOLERANCE),
        formatted_difference(difference - TOLERANCE), name,
    ]


def run(data_path, mol_path, db_path, output_dir, dataset_name):
    samples, mass_text, masses, molecular, abundance, transformations = load_inputs(
        data_path, mol_path, db_path
    )
    matched = match_all_masses(masses, transformations)
    plain_dir = output_dir / "Transformation Peak Comparisons" / dataset_name
    annotated_dir = output_dir / "Annotated Peak Comparisons" / dataset_name
    plain_dir.mkdir(parents=True, exist_ok=True)
    annotated_dir.mkdir(parents=True, exist_ok=True)

    summary = []
    for sample_index, original_name in enumerate(samples):
        sample = f"Sample_{original_name}"
        present = abundance[:, sample_index] > 0
        selected = [(x, y, t) for (x, y), t in matched if present[x] and present[y]]
        filename = f"Peak.2.Peak_{sample}.csv"
        with (plain_dir / filename).open("w", newline="", encoding="utf-8") as handle, \
                (annotated_dir / filename).open("w", newline="", encoding="utf-8") as annotated_handle:
            writer = csv.writer(handle)
            annotated_writer = csv.writer(annotated_handle)
            writer.writerow(COMPARISON_FIELDS)
            annotated_writer.writerow(ANNOTATED_FIELDS)
            for x_index, y_index, trans_index in selected:
                difference = float(masses[x_index] - masses[y_index])
                name = transformations[trans_index][0]
                writer.writerow([
                    sample, formatted_difference(difference), mass_text[x_index], mass_text[y_index],
                    formatted_difference(difference + TOLERANCE),
                    formatted_difference(difference - TOLERANCE), name,
                ])
                annotated_writer.writerow(annotated_row(
                    sample, mass_text, molecular, x_index, y_index, difference, name
                ))
        summary.append((sample, int(np.count_nonzero(present)), len(selected),
                        sum(molecular[x]["MolForm"] not in ("", "NA") and
                            molecular[y]["MolForm"] not in ("", "NA")
                            for x, y, _ in selected)))
        print(f"{sample}: {len(selected)} matched peak pairs")

    with (output_dir / "sample_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sample", "present_peaks", "matched_peak_pairs", "both_formulas_known"])
        writer.writerows(summary)
    print(f"Total: {sum(row[2] for row in summary)} sample-specific peak pairs")
    print(f"Saved results in {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--mol", type=Path, default=DEFAULT_MOL)
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dataset-name", default="Shoreline")
    arguments = parser.parse_args()
    run(arguments.data, arguments.mol, arguments.database, arguments.output_dir, arguments.dataset_name)
