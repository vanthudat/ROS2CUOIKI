#!/usr/bin/env python3
import csv
import math
from pathlib import Path

import numpy as np

from evaluate_maps import OCCUPIED, FREE, UNKNOWN, boundary, bounds, load_map, rasterize, rmse_mm


REFERENCE = "maps/house_scan_ground_truth.yaml"
OUTPUT_DIR = Path("reports")

STUDIES = [
    (
        "minimum_travel_distance",
        [
            ("0.05", "maps/house_mtd_005.yaml"),
            ("0.10", "maps/house_mtd_010.yaml"),
            ("0.30", "maps/house_mtd_030.yaml"),
            ("0.60", "maps/house_mtd_060.yaml"),
        ],
    ),
    (
        "minimum_travel_heading",
        [
            ("0.05", "maps/house_mth_005.yaml"),
            ("0.10", "maps/house_mth_010.yaml"),
            ("0.30", "maps/house_mth_030.yaml"),
            ("0.60", "maps/house_mth_060.yaml"),
        ],
    ),
    (
        "resolution",
        [
            ("0.02", "maps/house_res_002.yaml"),
            ("0.05", "maps/house_res_005.yaml"),
            ("0.10", "maps/house_res_010.yaml"),
            ("0.15", "maps/house_res_015.yaml"),
        ],
    ),
    (
        "do_loop_closing",
        [
            ("true", "maps/house_loop_on.yaml"),
            ("false", "maps/house_loop_off.yaml"),
        ],
    ),
]


def common_extent(reference, tests):
    all_bounds = [bounds(reference)] + [bounds(test) for test in tests]
    return (
        min(item[0] for item in all_bounds),
        min(item[1] for item in all_bounds),
        max(item[2] for item in all_bounds),
        max(item[3] for item in all_bounds),
    )


def calculate_metrics(reference_grid, test_grid, resolution):
    reference_occupied = reference_grid == OCCUPIED
    test_occupied = test_grid == OCCUPIED
    reference_free = reference_grid == FREE
    test_free = test_grid == FREE
    reference_unknown = reference_grid == UNKNOWN
    test_unknown = test_grid == UNKNOWN

    total = reference_grid.size
    different = np.count_nonzero(reference_grid != test_grid)

    occupied_intersection = np.count_nonzero(reference_occupied & test_occupied)
    occupied_union = np.count_nonzero(reference_occupied | test_occupied)
    free_intersection = np.count_nonzero(reference_free & test_free)
    free_union = np.count_nonzero(reference_free | test_free)
    unknown_intersection = np.count_nonzero(reference_unknown & test_unknown)
    unknown_union = np.count_nonzero(reference_unknown | test_unknown)

    false_occupied = np.count_nonzero(test_occupied & ~reference_occupied)
    missed_occupied = np.count_nonzero(reference_occupied & ~test_occupied)
    extra_free = np.count_nonzero(test_free & ~reference_free)
    missed_free = np.count_nonzero(reference_free & ~test_free)

    reference_boundary = boundary(reference_occupied)
    test_boundary = boundary(test_occupied)
    rmse = rmse_mm(reference_boundary, test_boundary, resolution)

    return {
        "rmse_mm": rmse,
        "error_rate_pct": different / total * 100.0,
        "occupied_iou": occupied_intersection / occupied_union if occupied_union else 0.0,
        "free_iou": free_intersection / free_union if free_union else 0.0,
        "unknown_iou": unknown_intersection / unknown_union if unknown_union else 0.0,
        "false_occupied_pixels": int(false_occupied),
        "missed_occupied_pixels": int(missed_occupied),
        "extra_free_pixels": int(extra_free),
        "missed_free_pixels": int(missed_free),
    }


def evaluate():
    reference = load_map(REFERENCE)
    rows = []

    for study_name, cases in STUDIES:
        available_cases = [(value, path) for value, path in cases if Path(path).exists()]
        tests = [load_map(path) for _, path in available_cases]
        if not tests:
            continue
        extent = common_extent(reference, tests)
        resolution = min([reference["resolution"]] + [test["resolution"] for test in tests])
        reference_grid = rasterize(reference, extent, resolution)

        for (value, path), test in zip(available_cases, tests):
            test_grid = rasterize(test, extent, resolution)
            metrics = calculate_metrics(reference_grid, test_grid, resolution)
            rows.append(
                {
                    "study": study_name,
                    "value": value,
                    "map": Path(path).stem,
                    **metrics,
                }
            )
    return rows


def write_csv(rows, path):
    fieldnames = [
        "study",
        "value",
        "map",
        "rmse_mm",
        "error_rate_pct",
        "occupied_iou",
        "free_iou",
        "unknown_iou",
        "false_occupied_pixels",
        "missed_occupied_pixels",
        "extra_free_pixels",
        "missed_free_pixels",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fmt(value, digits=3):
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.{digits}f}"
    return str(value)


def write_markdown(rows, path):
    lines = [
        "# SLAM Toolbox Map Evaluation",
        "",
        "Reference map: `maps/house_scan_ground_truth.yaml`",
        "",
        "| Study | Value | Map | RMSE (mm) | Error (%) | Occupied IoU | Free IoU | False occupied | Missed occupied |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["study"],
                    row["value"],
                    f"`{row['map']}`",
                    fmt(row["rmse_mm"], 2),
                    fmt(row["error_rate_pct"], 2),
                    fmt(row["occupied_iou"], 3),
                    fmt(row["free_iou"], 3),
                    str(row["false_occupied_pixels"]),
                    str(row["missed_occupied_pixels"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Notes:",
            "- `RMSE` is computed from the symmetric nearest occupied-boundary distance.",
            "- `Occupied IoU` measures obstacle overlap with the reference map.",
            "- `Free IoU` measures free-space overlap with the reference map.",
            "- `False occupied` means the SLAM map adds obstacle pixels not present in the reference.",
            "- `Missed occupied` means obstacle pixels in the reference are missing from the SLAM map.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = evaluate()
    csv_path = OUTPUT_DIR / "slam_map_metrics.csv"
    markdown_path = OUTPUT_DIR / "slam_map_metrics.md"
    write_csv(rows, csv_path)
    write_markdown(rows, markdown_path)
    print(f"wrote {csv_path}")
    print(f"wrote {markdown_path}")


if __name__ == "__main__":
    main()
