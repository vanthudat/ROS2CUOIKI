#!/usr/bin/env python3
import argparse
import math
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage


FREE = 0
OCCUPIED = 1
UNKNOWN = 2


def load_map(yaml_path):
    yaml_path = Path(yaml_path)
    meta = yaml.safe_load(yaml_path.read_text())
    image_path = yaml_path.parent / meta["image"]
    image = Image.open(image_path).convert("L")
    return {
        "name": yaml_path.stem,
        "image": image,
        "resolution": float(meta["resolution"]),
        "origin": tuple(float(v) for v in meta["origin"][:2]),
    }


def bounds(map_data):
    width, height = map_data["image"].size
    origin_x, origin_y = map_data["origin"]
    resolution = map_data["resolution"]
    return (
        origin_x,
        origin_y,
        origin_x + width * resolution,
        origin_y + height * resolution,
    )


def pixel_class(value):
    if value < 65:
        return OCCUPIED
    if value > 250:
        return FREE
    return UNKNOWN


def sample_map(map_data, x, y):
    image = map_data["image"]
    width, height = image.size
    origin_x, origin_y = map_data["origin"]
    resolution = map_data["resolution"]
    ix = int(math.floor((x - origin_x) / resolution))
    iy = int(math.floor((y - origin_y) / resolution))
    if ix < 0 or ix >= width or iy < 0 or iy >= height:
        return UNKNOWN
    return pixel_class(image.getpixel((ix, height - 1 - iy)))


def rasterize(map_data, extent, resolution):
    min_x, min_y, max_x, max_y = extent
    width = int(math.ceil((max_x - min_x) / resolution))
    height = int(math.ceil((max_y - min_y) / resolution))
    grid = np.full((height, width), UNKNOWN, dtype=np.uint8)

    for row in range(height):
        y = min_y + (row + 0.5) * resolution
        for col in range(width):
            x = min_x + (col + 0.5) * resolution
            grid[height - 1 - row, col] = sample_map(map_data, x, y)
    return grid


def boundary(occupied_mask):
    if not occupied_mask.any():
        return occupied_mask
    eroded = ndimage.binary_erosion(occupied_mask, structure=np.ones((3, 3), dtype=bool))
    return occupied_mask & ~eroded


def rmse_mm(reference_boundary, test_boundary, resolution):
    if not reference_boundary.any() or not test_boundary.any():
        return float("nan")

    # Symmetric nearest-boundary RMSE, equivalent to a bidirectional Chamfer RMSE.
    dist_to_reference = ndimage.distance_transform_edt(~reference_boundary) * resolution * 1000.0
    dist_to_test = ndimage.distance_transform_edt(~test_boundary) * resolution * 1000.0
    test_to_ref = dist_to_reference[test_boundary]
    ref_to_test = dist_to_test[reference_boundary]
    distances = np.concatenate([test_to_ref, ref_to_test])
    return float(np.sqrt(np.mean(distances * distances)))


def draw_overlay(reference_grid, test_grid, title, rmse, output_path, scale=3):
    ref_boundary = boundary(reference_grid == OCCUPIED)
    test_boundary = boundary(test_grid == OCCUPIED)
    height, width = reference_grid.shape

    canvas = Image.new("RGB", (width, height), "white")
    pixels = canvas.load()
    ref_rows, ref_cols = np.where(ref_boundary)
    test_rows, test_cols = np.where(test_boundary)

    for row, col in zip(ref_rows, ref_cols):
        pixels[col, row] = (180, 40, 40)
    for row, col in zip(test_rows, test_cols):
        pixels[col, row] = (0, 0, 0)

    nearest = getattr(getattr(Image, "Resampling", Image), "NEAREST")
    canvas = canvas.resize((width * scale, height * scale), nearest)
    footer_height = 96
    composed = Image.new("RGB", (canvas.width, canvas.height + footer_height), "white")
    composed.paste(canvas, (0, 0))
    draw = ImageDraw.Draw(composed)
    title_font = load_font(30)
    rmse_font = load_font(34)
    draw.text((16, canvas.height + 10), title, fill=(0, 0, 0), font=title_font)
    draw.text((16, canvas.height + 48), f"RMSE = {rmse:.2f} mm", fill=(0, 0, 0), font=rmse_font)
    composed.save(output_path)


def make_panel(image_paths, output_path, columns=2):
    images = [Image.open(path).convert("RGB") for path in image_paths]
    cell_width = max(image.width for image in images)
    cell_height = max(image.height for image in images)
    rows = math.ceil(len(images) / columns)
    footer_height = 58
    panel = Image.new("RGB", (cell_width * columns, cell_height * rows + footer_height), "white")
    draw = ImageDraw.Draw(panel)
    note_font = load_font(26)

    for index, image in enumerate(images):
        x = (index % columns) * cell_width
        y = (index // columns) * cell_height
        panel.paste(image, (x, y))
        draw.rectangle([x, y, x + cell_width - 1, y + cell_height - 1], outline=(0, 0, 0))

    note = "Red: reference map; black: SLAM map. RMSE unit: mm."
    draw.text((16, cell_height * rows + 14), note, fill=(0, 0, 0), font=note_font)
    panel.save(output_path)


def load_font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def main():
    parser = argparse.ArgumentParser(description="Create paper-style map comparison overlays.")
    parser.add_argument("--reference", default="maps/house_scan_ground_truth.yaml")
    parser.add_argument("--output-dir", default="maps")
    parser.add_argument("--panel-name", default="house_mtd_paper_comparison_panel.png")
    parser.add_argument("maps", nargs="*", help="Map yaml files to compare against the reference")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    reference = load_map(args.reference)
    map_paths = args.maps or [
        "maps/house_mtd_005.yaml",
        "maps/house_mtd_010.yaml",
        "maps/house_mtd_030.yaml",
        "maps/house_mtd_060.yaml",
    ]
    tests = [load_map(path) for path in map_paths]

    all_bounds = [bounds(reference)] + [bounds(test) for test in tests]
    extent = (
        min(item[0] for item in all_bounds),
        min(item[1] for item in all_bounds),
        max(item[2] for item in all_bounds),
        max(item[3] for item in all_bounds),
    )
    resolution = min([reference["resolution"]] + [test["resolution"] for test in tests])

    reference_grid = rasterize(reference, extent, resolution)
    reference_boundary = boundary(reference_grid == OCCUPIED)

    output_paths = []
    for test in tests:
        test_grid = rasterize(test, extent, resolution)
        test_boundary = boundary(test_grid == OCCUPIED)
        score = rmse_mm(reference_boundary, test_boundary, resolution)
        output_path = output_dir / f"{test['name']}_paper_compare.png"
        draw_overlay(reference_grid, test_grid, test["name"], score, output_path)
        output_paths.append(output_path)
        print(f"{test['name']}: RMSE = {score:.2f} mm -> {output_path}")

    panel_path = output_dir / args.panel_name
    make_panel(output_paths, panel_path)
    print(f"panel -> {panel_path}")


if __name__ == "__main__":
    main()
