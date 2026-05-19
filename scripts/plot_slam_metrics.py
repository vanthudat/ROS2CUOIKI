#!/usr/bin/env python3
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


METRICS_CSV = Path("reports/slam_map_metrics.csv")
CPU_CSV = Path("reports/slam_cpu_metrics.csv")
FIGURE_DIR = Path("reports/figures")


STUDY_TITLES = {
    "minimum_travel_distance": "Minimum Travel Distance",
    "minimum_travel_heading": "Minimum Travel Heading",
    "resolution": "Map Resolution",
    "do_loop_closing": "Loop Closure",
}


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def as_float(row, key):
    return float(row[key])


def save_bar_chart(path, title, labels, values, ylabel, color="#3b6ea8", ylim=None):
    width = max(7.5, 1.35 * len(labels))
    fig, ax = plt.subplots(figsize=(width, 4.6), dpi=180)
    bars = ax.bar(labels, values, color=color, edgecolor="#222222", linewidth=0.7)
    ax.set_title(title, fontsize=14, pad=12)
    ax.set_xlabel("Parameter value", fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    if ylim:
        ax.set_ylim(*ylim)
    else:
        apply_headroom(ax, values)
    for bar, value in zip(bars, values):
        ax.annotate(
            f"{value:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def save_group_summary(path, study, rows):
    labels = [row["value"] for row in rows]
    rmse = [as_float(row, "rmse_mm") for row in rows]
    error = [as_float(row, "error_rate_pct") for row in rows]
    occupied_iou = [as_float(row, "occupied_iou") for row in rows]
    free_iou = [as_float(row, "free_iou") for row in rows]

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8), dpi=180)
    fig.suptitle(STUDY_TITLES.get(study, study), fontsize=16)
    plots = [
        (axes[0, 0], rmse, "RMSE (mm)", "#b64b4b"),
        (axes[0, 1], error, "Error rate (%)", "#d08a2e"),
        (axes[1, 0], occupied_iou, "Occupied IoU", "#4b7f52"),
        (axes[1, 1], free_iou, "Free IoU", "#3b6ea8"),
    ]
    for ax, values, ylabel, color in plots:
        bars = ax.bar(labels, values, color=color, edgecolor="#222222", linewidth=0.6)
        ax.set_xlabel("Parameter value")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        if "IoU" in ylabel:
            ax.set_ylim(0, 1.12)
        else:
            apply_headroom(ax, values)
        for bar, value in zip(bars, values):
            fmt = f"{value:.3f}" if "IoU" in ylabel else f"{value:.2f}"
            ax.annotate(
                fmt,
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(path)
    plt.close(fig)


def apply_headroom(ax, values):
    if not values:
        return
    max_value = max(values)
    if max_value <= 0:
        ax.set_ylim(0, 1)
        return
    ax.set_ylim(0, max_value * 1.22)


def plot_metrics():
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_rows(METRICS_CSV)
    studies = {}
    for row in rows:
        studies.setdefault(row["study"], []).append(row)

    for study, study_rows in studies.items():
        safe_name = study.replace("/", "_")
        title = STUDY_TITLES.get(study, study)
        labels = [row["value"] for row in study_rows]
        save_group_summary(FIGURE_DIR / f"{safe_name}_summary.png", study, study_rows)
        save_bar_chart(
            FIGURE_DIR / f"{safe_name}_rmse.png",
            f"{title}: RMSE",
            labels,
            [as_float(row, "rmse_mm") for row in study_rows],
            "RMSE (mm)",
            "#b64b4b",
        )
        save_bar_chart(
            FIGURE_DIR / f"{safe_name}_error_rate.png",
            f"{title}: Error Rate",
            labels,
            [as_float(row, "error_rate_pct") for row in study_rows],
            "Error rate (%)",
            "#d08a2e",
        )
        save_bar_chart(
            FIGURE_DIR / f"{safe_name}_occupied_iou.png",
            f"{title}: Occupied IoU",
            labels,
            [as_float(row, "occupied_iou") for row in study_rows],
            "Occupied IoU",
            "#4b7f52",
            (0, 1),
        )
        save_bar_chart(
            FIGURE_DIR / f"{safe_name}_free_iou.png",
            f"{title}: Free IoU",
            labels,
            [as_float(row, "free_iou") for row in study_rows],
            "Free IoU",
            "#3b6ea8",
            (0, 1),
        )


def write_cpu_template():
    if CPU_CSV.exists():
        return
    metric_rows = read_rows(METRICS_CSV)
    with CPU_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["study", "value", "map", "cpu_avg_pct", "cpu_max_pct", "ram_avg_mb"])
        for row in metric_rows:
            writer.writerow([row["study"], row["value"], row["map"], "", "", ""])


def plot_cpu_if_available():
    if not CPU_CSV.exists():
        return
    rows = [row for row in read_rows(CPU_CSV) if row["cpu_avg_pct"] and row["cpu_max_pct"]]
    if not rows:
        return
    studies = {}
    for row in rows:
        studies.setdefault(row["study"], []).append(row)
    for study, study_rows in studies.items():
        labels = [row["value"] for row in study_rows]
        avg = [float(row["cpu_avg_pct"]) for row in study_rows]
        max_values = [float(row["cpu_max_pct"]) for row in study_rows]
        x = range(len(labels))
        fig, ax = plt.subplots(figsize=(8, 4.8), dpi=180)
        ax.bar([i - 0.18 for i in x], avg, width=0.36, label="CPU average", color="#5876a8")
        ax.bar([i + 0.18 for i in x], max_values, width=0.36, label="CPU max", color="#b85c5c")
        ax.set_xticks(list(x), labels)
        ax.set_xlabel("Parameter value")
        ax.set_ylabel("CPU (%)")
        ax.set_title(f"{STUDY_TITLES.get(study, study)}: CPU usage")
        ax.grid(axis="y", linestyle="--", alpha=0.35)
        ax.legend()
        fig.tight_layout()
        fig.savefig(FIGURE_DIR / f"{study}_cpu.png")
        plt.close(fig)


def main():
    plot_metrics()
    write_cpu_template()
    plot_cpu_if_available()
    print(f"wrote figures to {FIGURE_DIR}")
    print(f"cpu template: {CPU_CSV}")


if __name__ == "__main__":
    main()
