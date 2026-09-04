#!/usr/bin/env python3
"""Build the research-lead result figures from pinned, tracked CSV evidence."""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "evidence" / "canonical-audit" / "figures" / "data"
SELECTED = ROOT / "evidence" / "source-results"
PARAMETERS = ROOT / "evidence" / "model-parameter-sources.csv"
DATA = ROOT / "data" / "results"
FIGURES = ROOT / "assets" / "results"

SOURCE_HEAD = "b3a348684692f615d789392692ce34a1359192d3"
COMMON_MODELS = [
    "claude-haiku-4-5",
    "claude-opus-4-8",
    "gpt-5.4",
    "gpt-5.4-mini",
    "qwen3-8b",
]
MODEL_LABELS = {
    "claude-haiku-4-5": "Claude Haiku 4.5",
    "claude-opus-4-8": "Claude Opus 4.8",
    "gpt-5.4": "GPT-5.4",
    "gpt-5.4-mini": "GPT-5.4 mini",
    "qwen3-8b": "Qwen3 8B",
}
MODEL_COLORS = {
    "claude-haiku-4-5": "#3A86C8",
    "claude-opus-4-8": "#6A54A3",
    "gpt-5.4": "#D65F35",
    "gpt-5.4-mini": "#E0A11B",
    "qwen3-8b": "#16866B",
}
MODEL_MARKERS = {
    "claude-haiku-4-5": "o",
    "claude-opus-4-8": "s",
    "gpt-5.4": "^",
    "gpt-5.4-mini": "D",
    "qwen3-8b": "P",
}
MODEL_SHORT_LABELS = ["Haiku", "Opus", "GPT-5.4", "Mini", "Qwen"]
FAMILY_COLORS = {"Qwen": "#16866B", "Gemma": "#D65F35", "Llama": "#3A86C8", "DeepSeek": "#6A54A3"}
FAMILY_MARKERS = {"Qwen": "o", "Gemma": "s", "Llama": "^", "DeepSeek": "D"}
FAMILY_LINESTYLES = {"Qwen": "-", "Gemma": "--", "Llama": "-.", "DeepSeek": ":"}
INK = "#17212B"
MUTED = "#66717C"
GRID = "#D9DEE3"
PAPER = "#FFFFFF"
GREEN = "#16866B"
AMBER = "#D89210"
RED = "#C44A3A"
BLUE = "#2676B8"
PURPLE = "#7651A8"

TASKS = {
    "moralbench_mfq_agreement": ("MFQ agreement", "Normalized preference", (0.50, 1.01), 20),
    "moralbench_vignette_agreement": ("Vignette agreement", "Normalized preference", (0.50, 1.01), 24),
    "moralbench_mfq_compare": ("MFQ compare", "Accuracy", (0.10, 1.00), 20),
    "moralbench_vignette_compare": ("Vignette compare", "Accuracy", (0.10, 1.00), 24),
    "unimoral_action_prediction": ("UniMoral action", "Accuracy", (0.52, 0.71), 8784),
    "unimoral_moral_typology": ("UniMoral typology", "Accuracy", (0.52, 0.71), 3492),
    "unimoral_factor_attribution": ("UniMoral factor", "Accuracy", (0.52, 0.71), 3492),
    "unimoral_consequence_generation": ("UniMoral consequence", "METEOR", (0.05, 0.18), 1782),
    "value_prism_relevance": ("ValuePrism relevance", "Accuracy", (0.40, 0.78), None),
    "value_prism_valence": ("ValuePrism valence", "Accuracy", (0.30, 0.80), None),
}
SIX_TASKS = [
    "unimoral_action_prediction",
    "unimoral_moral_typology",
    "unimoral_factor_attribution",
    "unimoral_consequence_generation",
    "value_prism_relevance",
    "value_prism_valence",
]
SCALING_LIMITS = {
    "unimoral_action_prediction": (0.30, 0.80),
    "unimoral_moral_typology": (0.30, 0.80),
    "unimoral_factor_attribution": (0.30, 0.80),
    "unimoral_consequence_generation": (0.05, 0.18),
    "value_prism_relevance": (0.30, 0.80),
    "value_prism_valence": (0.30, 0.80),
}


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 11.5,
            "axes.labelsize": 9.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "cei-moral-psychology-results-2026-09-03",
        }
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        FIGURES / f"{stem}.png",
        dpi=220,
        bbox_inches="tight",
        facecolor=PAPER,
        metadata={"Software": "CEI result visual builder", "Creation Time": "2026-09-03"},
    )
    fig.savefig(
        FIGURES / f"{stem}.svg",
        bbox_inches="tight",
        facecolor=PAPER,
        metadata={"Creator": "CEI result visual builder", "Date": "2026-09-03"},
    )
    plt.close(fig)


def save_csv(frame: pd.DataFrame, name: str) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    frame.to_csv(DATA / name, index=False, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")


def validate_selected_sources() -> None:
    manifest = pd.read_csv(SELECTED / "SOURCE_MANIFEST.csv", keep_default_na=False)
    assert len(manifest) == 2
    assert set(manifest["source_repository_head"]) == {SOURCE_HEAD}
    for row in manifest.itertuples(index=False):
        path = SELECTED / row.path
        assert path.is_file(), f"missing selected-grid source: {path}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row.sha256, f"source hash drift: {row.path}"
        frame = pd.read_csv(path)
        assert frame.shape == (int(row.rows), int(row.columns)), f"source shape drift: {row.path}"


def load_verified_results() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    primary = pd.read_csv(CANONICAL / "primary_confidence_intervals.csv")
    precision = pd.read_csv(CANONICAL / "task_diagnostic_spread.csv")
    partition = pd.read_csv(CANONICAL / "audit_partition.csv")
    assert primary.shape[0] == 78
    assert set(primary["repo_commit_sha"]) == {SOURCE_HEAD}
    assert precision.shape[0] == 8
    assert partition.set_index("inclusion_class")["cells"].to_dict() == {
        "primary": 78,
        "sensitivity_only": 26,
        "multimodal_extension": 9,
        "excluded": 30,
    }
    common = primary[primary["model"].isin(COMMON_MODELS)].copy()
    assert common.shape[0] == 40
    assert common.groupby("model")["task"].nunique().to_dict() == {model: 8 for model in COMMON_MODELS}
    common["model_label"] = common["model"].map(MODEL_LABELS)
    common["task_label"] = common["task"].map(lambda task: TASKS[task][0])
    return common, precision, partition


def plot_common_roster(common: pd.DataFrame) -> None:
    order = [
        "moralbench_mfq_agreement",
        "moralbench_vignette_agreement",
        "moralbench_mfq_compare",
        "moralbench_vignette_compare",
        "unimoral_action_prediction",
        "unimoral_moral_typology",
        "unimoral_factor_attribution",
        "unimoral_consequence_generation",
    ]
    fig, axes = plt.subplots(2, 4, figsize=(16, 9.6))
    fig.suptitle("No model is the point-estimate leader on every task", x=0.055, y=0.985, ha="left", fontsize=22, fontweight="bold")
    fig.text(0.055, 0.942, "Current primary aggregates · tracked-artifact audit · 5-model common roster · metrics remain separate", color=MUTED, fontsize=11.5)

    for ax, task in zip(axes.flat, order):
        subset = common[common["task"] == task].set_index("model").loc[COMMON_MODELS].reset_index()
        for x, row in enumerate(subset.itertuples(index=False)):
            lower = row.score - row.ci_lower
            upper = row.ci_upper - row.score
            ax.errorbar(
                x,
                row.score,
                yerr=np.array([[lower], [upper]]),
                fmt=MODEL_MARKERS[row.model],
                markersize=7,
                capsize=3,
                color=MODEL_COLORS[row.model],
                ecolor=MODEL_COLORS[row.model],
                elinewidth=2,
                zorder=3,
            )
        label, metric, ylim, n_value = TASKS[task]
        ax.set_title(f"{label}\nn = {n_value:,} per model", loc="left", fontweight="bold", pad=8)
        ax.set_ylim(*ylim)
        ax.set_ylabel(metric)
        ax.set_xticks(range(len(COMMON_MODELS)))
        ax.set_xticklabels(MODEL_SHORT_LABELS, rotation=28, ha="right", fontsize=7.5)
        ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
        if "compare" in task:
            ax.axhline(0.5, color=MUTED, linestyle="--", linewidth=1, alpha=0.65)

    handles = [
        plt.Line2D([0], [0], marker=MODEL_MARKERS[m], color="none", markerfacecolor=MODEL_COLORS[m], markeredgecolor=MODEL_COLORS[m], markersize=8, label=MODEL_LABELS[m])
        for m in COMMON_MODELS
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.53, 0.91), ncol=5, frameon=False, fontsize=10)
    fig.text(0.055, 0.035, "Result: point-estimate leaders change by task. Compare-task intervals overlap pairwise, so those panels do not establish a model order.", fontsize=10.2, fontweight="bold")
    fig.text(0.055, 0.012, "Panel scales differ: compare models within a task, not vertical distance across tasks. Intervals omit route drift, contamination, construct error, and human validity.", fontsize=9.1, color=MUTED)
    fig.tight_layout(rect=(0.04, 0.07, 0.99, 0.89), w_pad=1.2, h_pad=2.0)
    save_figure(fig, "01_common_roster_task_results")


def plot_precision(precision: pd.DataFrame) -> None:
    ordered = precision.sort_values("median_ci_width", ascending=True).copy()
    colors = []
    for task in ordered["task"]:
        if "compare" in task:
            colors.append(RED)
        elif "agreement" in task:
            colors.append(AMBER)
        else:
            colors.append(GREEN)
    fig, ax = plt.subplots(figsize=(13.5, 7.5))
    ypos = np.arange(len(ordered))
    ax.hlines(ypos, 0, ordered["median_ci_width"], color=colors, linewidth=5, alpha=0.9)
    ax.scatter(ordered["median_ci_width"], ypos, s=95, color=colors, edgecolor="white", linewidth=1.3, zorder=3)
    for y, value in zip(ypos, ordered["median_ci_width"]):
        ax.text(value + 0.012, y, f"{value:.3f}", va="center", fontsize=10, fontweight="bold")
    ax.axvline(0.20, color=MUTED, linestyle="--", linewidth=1.3)
    ax.axvline(0.30, color=RED, linestyle=":", linewidth=1.5)
    ax.text(0.20, 0.99, ".20 planning target", transform=ax.get_xaxis_transform(), ha="right", va="top", color=MUTED, fontsize=8.5)
    ax.text(0.30, 0.91, ".30 audit warning", transform=ax.get_xaxis_transform(), ha="left", va="top", color=RED, fontsize=8.5)
    ax.set_yticks(ypos)
    ax.set_yticklabels(ordered["task_label"])
    ax.set_xlim(0, 0.45)
    ax.set_xlabel("Median full width of the saved 95% interval")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_title("Available marginal intervals do not resolve a comparison-task model order", loc="left", fontsize=20, fontweight="bold", pad=28)
    ax.text(0, 1.025, "All 18 intervals wider than .30 occur in MoralBench compare; every within-task pair overlaps marginally.", transform=ax.transAxes, color=MUTED, fontsize=11)
    ax.text(0, -0.13, "Decision: recover paired item outcomes first; if the order remains unresolved, expand the independent item banks.", transform=ax.transAxes, fontsize=10.2, fontweight="bold")
    ax.text(0, -0.18, "Narrow UniMoral intervals are nominal row-level precision; they do not establish construct validity or cluster-aware uncertainty.", transform=ax.transAxes, fontsize=9.3, color=MUTED)
    fig.tight_layout(rect=(0.03, 0.08, 0.99, 0.95))
    save_figure(fig, "02_precision_by_task")


def load_selected_grid() -> tuple[pd.DataFrame, pd.DataFrame]:
    validate_selected_sources()
    grid = pd.read_csv(SELECTED / "model_grid.csv")
    results = pd.read_csv(SELECTED / "result_summary.csv")
    assert grid.shape == (17, 13)
    assert results["run_status"].value_counts().to_dict() == {"success": 102, "error": 13, "cancelled": 4}
    results["score"] = pd.to_numeric(results["score"], errors="coerce")
    return grid, results


def load_model_parameters() -> pd.DataFrame:
    parameters = pd.read_csv(PARAMETERS, keep_default_na=False)
    required = {
        "model",
        "model_display",
        "total_parameters_b",
        "activated_parameters_b",
        "parameter_label",
        "architecture",
        "source_url",
        "source_revision",
        "parameter_basis",
        "run_identity_scope",
        "checked_on",
    }
    assert set(parameters.columns) == required
    assert len(parameters) == 15
    assert parameters["model"].is_unique
    assert parameters["model_display"].ne("").all()
    assert parameters["parameter_label"].str.contains("B").all()
    assert parameters["source_url"].str.startswith("https://").all()
    assert parameters["source_revision"].str.fullmatch(r"[0-9a-f]{40}").all()
    assert parameters["parameter_basis"].ne("").all()
    assert (
        parameters["run_identity_scope"]
        == "named-model specification only; served provider endpoint, quantization, and checkpoint revision not retained"
    ).all()
    parameters["total_parameters_b"] = pd.to_numeric(parameters["total_parameters_b"], errors="raise")
    parameters["activated_parameters_b"] = pd.to_numeric(
        parameters["activated_parameters_b"].replace("", np.nan), errors="raise"
    )
    moe = parameters["architecture"] == "MoE"
    assert parameters.loc[moe, "activated_parameters_b"].notna().all()
    assert parameters.loc[~moe, "activated_parameters_b"].isna().all()
    assert (
        parameters.loc[parameters["model"] == "qwen/qwen3-235b-a22b-2507", "parameter_label"].iloc[0]
        == "235B total / 22B active"
    )
    return parameters


def attach_model_parameters(points: pd.DataFrame, parameters: pd.DataFrame) -> pd.DataFrame:
    merged = points.merge(parameters, on="model", how="left", validate="many_to_one")
    assert merged["model_display"].notna().all()
    assert merged["total_parameters_b"].notna().all()
    assert merged["parameter_label"].notna().all()
    merged["point_label"] = merged["model_display"] + "\n" + merged["parameter_label"]
    return merged


def add_size_plot_positions(points: pd.DataFrame) -> pd.DataFrame:
    model_order = (
        points[["model", "total_parameters_b"]]
        .drop_duplicates()
        .sort_values(["total_parameters_b", "model"], kind="stable")
        .reset_index(drop=True)
    )
    assert len(model_order) == 9
    positions = {model: index for index, model in enumerate(model_order["model"])}
    ordered = points.copy()
    ordered["size_plot_position"] = ordered["model"].map(positions)
    assert ordered["size_plot_position"].notna().all()
    return ordered


def point_label_gid(layer: str, task: str, model: str) -> str:
    def clean(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

    return f"{clean(layer)}-point-label-{clean(task)}--{clean(model)}"


def add_point_annotation(
    ax: plt.Axes,
    x: float,
    y: float,
    label: str,
    offset: tuple[float, float],
    gid: str,
) -> mpl.text.Annotation:
    horizontal = "left" if offset[0] >= 0 else "right"
    annotation = ax.annotate(
        label,
        xy=(x, y),
        xytext=offset,
        textcoords="offset points",
        ha=horizontal,
        va="center",
        fontsize=10.5,
        linespacing=1.08,
        color=INK,
        bbox={"boxstyle": "round,pad=0.18", "facecolor": PAPER, "edgecolor": GRID, "linewidth": 0.55, "alpha": 0.94},
        arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.65, "shrinkA": 2, "shrinkB": 3},
        annotation_clip=False,
        zorder=6,
    )
    annotation.set_gid(gid)
    return annotation


def add_laned_point_annotation(
    ax: plt.Axes,
    x: float,
    y: float,
    label: str,
    lane: float,
    gid: str,
) -> mpl.text.Annotation:
    annotation = ax.annotate(
        label,
        xy=(x, y),
        xytext=(x, lane),
        textcoords=ax.get_xaxis_transform(),
        ha="center",
        va="center",
        fontsize=10.5,
        linespacing=1.08,
        color=INK,
        bbox={"boxstyle": "round,pad=0.18", "facecolor": PAPER, "edgecolor": GRID, "linewidth": 0.55, "alpha": 0.94},
        arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.65, "shrinkA": 2, "shrinkB": 3},
        annotation_clip=False,
        zorder=6,
    )
    annotation.set_gid(gid)
    return annotation


def assert_point_label_layout(fig: plt.Figure, annotations: list[mpl.text.Annotation], expected: int) -> None:
    assert len(annotations) == expected
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    figure_box = fig.bbox
    by_axes: dict[plt.Axes, list[tuple[mpl.text.Annotation, object]]] = {}
    for annotation in annotations:
        patch = annotation.get_bbox_patch()
        assert patch is not None
        box = patch.get_window_extent(renderer=renderer)
        assert box.x0 >= figure_box.x0 and box.y0 >= figure_box.y0
        assert box.x1 <= figure_box.x1 and box.y1 <= figure_box.y1
        by_axes.setdefault(annotation.axes, []).append((annotation, box.expanded(1.01, 1.06)))
    for labels in by_axes.values():
        for index, (left_label, left) in enumerate(labels):
            for right_label, right in labels[index + 1 :]:
                assert not left.overlaps(right), (
                    f"direct point labels overlap: {left_label.get_gid()} {tuple(round(v, 1) for v in left.bounds)} "
                    f"and {right_label.get_gid()} {tuple(round(v, 1) for v in right.bounds)}"
                )


def build_size_paths(results: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = results[
        (results["grid"] == "within-family scaling")
        & (results["run_status"] == "success")
        & (results["benchmark"] != "CCD-Bench")
    ].copy()
    rows["tier"] = rows["size_tier"].str.extract(r"^([SML])", expand=False)
    complete = []
    keep_indices = []
    for (family, task), group in rows.groupby(["family", "task"], sort=True):
        if set(group["tier"]) != {"S", "M", "L"} or len(group) != 3:
            continue
        ordered = group.set_index("tier").loc[["S", "M", "L"]]
        values = ordered["score"].to_numpy(dtype=float)
        direction = "rising" if np.all(np.diff(values) > 0) else "falling" if np.all(np.diff(values) < 0) else "mixed"
        complete.append(
            {
                "family": family,
                "task": task,
                "task_label": TASKS[task][0],
                "metric": TASKS[task][1],
                "small": values[0],
                "medium": values[1],
                "large": values[2],
                "direction": direction,
            }
        )
        keep_indices.extend(ordered.index.map(lambda tier: group[group["tier"] == tier].index[0]).tolist())
    summary = pd.DataFrame(complete)
    assert len(summary) == 15
    assert summary["direction"].value_counts().to_dict() == {"mixed": 9, "rising": 5, "falling": 1}
    summary["evidence_status"] = "exploratory aggregate; no CI or raw-log replay"
    summary["source_repository_head"] = SOURCE_HEAD
    summary["source_path"] = "evidence/source-results/result_summary.csv"
    points = rows.loc[sorted(set(keep_indices))].copy()
    points["task_label"] = points["task"].map(lambda task: TASKS[task][0])
    points["evidence_status"] = "exploratory aggregate; no CI or raw-log replay"
    points["source_repository_head"] = SOURCE_HEAD
    points["source_path"] = "evidence/source-results/result_summary.csv"
    return points, summary


def plot_size_paths(points: pd.DataFrame, summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(6, 1, figsize=(16, 21), sharex=True)
    fig.suptitle("Bigger is not reliably better", x=0.055, y=0.985, ha="left", fontsize=22, fontweight="bold")
    fig.text(
        0.055,
        0.964,
        "Models ordered by published total parameters (categorical spacing) · every observed point names the model and B count · MoE labels also show active B",
        color=MUTED,
        fontsize=11.5,
    )
    annotations: list[mpl.text.Annotation] = []
    label_lanes = {0: 0.84, 1: 0.16, 2: 0.66, 3: 0.34, 4: 0.88, 5: 0.12, 6: 0.68, 7: 0.32, 8: 0.84}
    for ax, task in zip(axes, SIX_TASKS):
        task_rows = points[points["task"] == task]
        for family, family_rows in task_rows.groupby("family"):
            if set(family_rows["tier"]) != {"S", "M", "L"}:
                continue
            ordered = family_rows.sort_values("size_plot_position")
            ax.plot(
                ordered["size_plot_position"],
                ordered["score"],
                marker=FAMILY_MARKERS[family],
                linestyle=FAMILY_LINESTYLES[family],
                linewidth=2.4,
                markersize=7.5,
                color=FAMILY_COLORS[family],
                label=family,
                zorder=3,
            )
            for row in ordered.itertuples(index=False):
                annotations.append(
                    add_laned_point_annotation(
                        ax,
                        float(row.size_plot_position),
                        float(row.score),
                        row.point_label,
                        label_lanes[int(row.size_plot_position)],
                        point_label_gid("size", task, row.model),
                    )
                )
        label, metric, _, _ = TASKS[task]
        ax.set_title(label, loc="left", fontweight="bold")
        ax.set_ylabel(metric)
        ax.set_ylim(*SCALING_LIMITS[task])
        axis_models = (
            points[["model", "size_plot_position", "total_parameters_b"]]
            .drop_duplicates()
            .sort_values("size_plot_position")
        )
        axis_labels = [f"{value:g}B" for value in axis_models["total_parameters_b"]]
        ax.set_xlim(-0.7, 8.7)
        ax.set_xticks(axis_models["size_plot_position"], axis_labels)
        ax.tick_params(axis="x", which="both", labelbottom=True)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
        incomplete = [family for family in ["Qwen", "Gemma", "Llama"] if set(task_rows.loc[task_rows["family"] == family, "tier"]) != {"S", "M", "L"}]
        if incomplete:
            ax.text(0.02, 0.03, "Incomplete: " + ", ".join(incomplete), transform=ax.transAxes, color=MUTED, fontsize=8)
    axes[-1].set_xlabel("Published total B, ordered categories — horizontal gaps are not to scale")
    handles = [
        plt.Line2D([0], [0], color=FAMILY_COLORS[f], marker=FAMILY_MARKERS[f], linestyle=FAMILY_LINESTYLES[f], linewidth=2.4, label=f)
        for f in ["Qwen", "Gemma", "Llama"]
    ]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.96, 0.985), ncol=3, frameon=False)
    fig.text(0.055, 0.027, "Result: point-estimate direction changes by task and family. More total parameters do not produce one shared direction.", fontsize=10.2, fontweight="bold")
    fig.text(
        0.055,
        0.011,
        "Published named-model specs only; served provider, quantization, and checkpoint revision are not retained. Total-B order is not inference compute. No intervals; METEOR is separate.",
        fontsize=8.9,
        color=MUTED,
    )
    fig.tight_layout(rect=(0.04, 0.045, 0.99, 0.945), h_pad=1.45)
    assert_point_label_layout(fig, annotations, expected=45)
    save_figure(fig, "03_size_paths")


def build_release_paths(results: pd.DataFrame) -> pd.DataFrame:
    rows = results[
        (results["grid"] == "time scaling")
        & (results["run_status"] == "success")
        & (results["benchmark"] != "CCD-Bench")
    ].copy()
    valid_groups = []
    for (family, task), group in rows.groupby(["family", "task"], sort=True):
        if group["release_period"].nunique() >= 2:
            valid_groups.append(group)
    points = pd.concat(valid_groups, ignore_index=True)
    assert points.groupby(["family", "task"]).ngroups == 12
    assert set(points["family"]) == {"Qwen", "DeepSeek"}
    points["task_label"] = points["task"].map(lambda task: TASKS[task][0])
    points["evidence_status"] = "exploratory aggregate; no CI or raw-log replay"
    points["source_repository_head"] = SOURCE_HEAD
    points["source_path"] = "evidence/source-results/result_summary.csv"
    return points


def quarter_key(value: str) -> int:
    year, quarter = value.split("-Q")
    return int(year) * 4 + int(quarter)


def quarter_label(value: int) -> str:
    year = (value - 1) // 4
    quarter = value - year * 4
    return f"{year}\nQ{quarter}"


def plot_release_paths(points: pd.DataFrame) -> None:
    period_keys = points["release_period"].map(quarter_key)
    first_period = int(period_keys.min())
    last_period = int(period_keys.max())
    quarter_ticks = list(range(first_period, last_period + 1))
    xpos = {period: quarter_key(period) - first_period for period in points["release_period"].unique()}
    fig, axes = plt.subplots(6, 1, figsize=(16, 21), sharex=True)
    fig.suptitle("Newer-route point estimates move in both directions", x=0.055, y=0.985, ha="left", fontsize=22, fontweight="bold")
    fig.text(
        0.055,
        0.964,
        "Saved release period on the x-axis · every observed point names the model and published B count · lines only connect observations",
        color=MUTED,
        fontsize=11.0,
    )
    annotations: list[mpl.text.Annotation] = []
    release_offsets = {
        "qwen/qwen-2.5-7b-instruct": (9, 25),
        "deepseek/deepseek-chat-v3-0324": (9, -28),
        "deepseek/deepseek-chat-v3.1": (9, 25),
        "deepseek/deepseek-v3.2": (-9, -28),
        "qwen/qwen3.5-9b": (-9, 55),
        "deepseek/deepseek-v4-flash": (-9, -45),
    }
    for ax, task in zip(axes, SIX_TASKS):
        task_rows = points[points["task"] == task]
        for family, family_rows in task_rows.groupby("family"):
            ordered = family_rows.sort_values("release_period", key=lambda s: s.map(quarter_key))
            ax.plot(
                ordered["release_period"].map(xpos),
                ordered["score"],
                marker=FAMILY_MARKERS[family],
                linestyle="--" if family == "Qwen" else ":",
                linewidth=2.4,
                markersize=7.5,
                color=FAMILY_COLORS[family],
                label=family,
                zorder=3,
            )
            for row in ordered.itertuples(index=False):
                annotations.append(
                    add_point_annotation(
                        ax,
                        float(xpos[row.release_period]),
                        float(row.score),
                        row.point_label,
                        release_offsets[row.model],
                        point_label_gid("release", task, row.model),
                    )
                )
        label, metric, _, _ = TASKS[task]
        ax.set_title(label, loc="left", fontweight="bold")
        ax.set_ylabel(metric)
        ax.set_ylim(*SCALING_LIMITS[task])
        ax.set_xticks([value - first_period for value in quarter_ticks], [quarter_label(value) for value in quarter_ticks])
        ax.set_xlim(-0.35, last_period - first_period + 0.35)
        ax.tick_params(axis="x", labelbottom=True)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
    axes[-1].set_xlabel("Saved release period")
    handles = [
        plt.Line2D([0], [0], color=FAMILY_COLORS[f], marker=FAMILY_MARKERS[f], linestyle="--" if f == "Qwen" else ":", linewidth=2.4, label=f)
        for f in ["Qwen", "DeepSeek"]
    ]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.96, 0.985), ncol=2, frameon=False)
    fig.text(0.055, 0.027, "Result: Qwen and DeepSeek endpoints move in both directions; release period does not isolate a model-size or architecture effect.", fontsize=10.2, fontweight="bold")
    fig.text(
        0.055,
        0.011,
        "DeepSeek B values are vendor-published main-model counts; auxiliary/MTP weights are excluded. Served provider, quantization, and checkpoint revision are not retained. No intervals.",
        fontsize=8.8,
        color=MUTED,
    )
    fig.tight_layout(rect=(0.04, 0.045, 0.99, 0.945), h_pad=1.45)
    assert_point_label_layout(fig, annotations, expected=35)
    save_figure(fig, "04_release_period_paths")


def save_takeaways(partition: pd.DataFrame, size_summary: pd.DataFrame) -> None:
    table = pd.DataFrame(
        [
            {
                "research_question": "Do the consistently covered models form one stable order?",
                "answer": "No model is the point-estimate leader on all eight tasks; compare-task ranks are unresolved by the available aggregate intervals.",
                "evidence_status": "current primary aggregate; tracked-artifact audit",
                "decision": "Report task-specific results and keep metrics separate.",
                "source": "evidence/canonical-audit/figures/data/primary_confidence_intervals.csv",
            },
            {
                "research_question": "Where does sampling uncertainty block a model order?",
                "answer": "All 18 intervals wider than .30 occur in the two MoralBench compare tasks.",
                "evidence_status": "current primary aggregate; tracked-artifact audit",
                "decision": "Recover paired outcomes first; expand the item banks if the order remains unresolved.",
                "source": "evidence/canonical-audit/figures/data/primary_confidence_intervals.csv",
            },
            {
                "research_question": "Does bigger reliably score better?",
                "answer": f"Only {(size_summary['direction'] == 'rising').sum()} of {len(size_summary)} complete paths rise monotonically; 9 are mixed and 1 falls.",
                "evidence_status": "exploratory aggregate; no CI or raw-log replay",
                "decision": "Treat size effects as family- and task-specific hypotheses.",
                "source": "evidence/source-results/result_summary.csv",
            },
            {
                "research_question": "Do newer-route point estimates all rise?",
                "answer": "Qwen and DeepSeek point estimates rise on some task endpoints and fall on others; Gemma has no valid newer endpoint.",
                "evidence_status": "exploratory aggregate; no CI or raw-log replay",
                "decision": "Do not claim a causal year trend.",
                "source": "evidence/source-results/result_summary.csv",
            },
            {
                "research_question": "How much of the 143-cell audit is headline evidence?",
                "answer": f"{int(partition.loc[partition['inclusion_class'] == 'primary', 'cells'].iloc[0])} cells are primary; the other classes serve different analytical roles.",
                "evidence_status": "tracked-artifact accounting",
                "decision": "Keep primary, sensitivity, extension, and exclusion separate.",
                "source": "evidence/canonical-audit/figures/data/audit_partition.csv",
            },
        ]
    )
    save_csv(table, "research_question_takeaways.csv")


def main() -> None:
    configure_style()
    common, precision, partition = load_verified_results()
    _, results = load_selected_grid()
    parameters = load_model_parameters()
    size_points, size_summary = build_size_paths(results)
    release_points = build_release_paths(results)
    plotted_models = set(size_points["model"]) | set(release_points["model"])
    assert plotted_models == set(parameters["model"])
    size_points = attach_model_parameters(size_points, parameters)
    size_points = add_size_plot_positions(size_points)
    release_points = attach_model_parameters(release_points, parameters)

    save_csv(common, "common_roster_primary.csv")
    save_csv(precision, "task_precision.csv")
    save_csv(size_points, "size_task_points.csv")
    save_csv(size_summary, "size_path_summary.csv")
    save_csv(release_points, "release_period_task_points.csv")
    save_takeaways(partition, size_summary)

    plot_common_roster(common)
    plot_precision(precision)
    plot_size_paths(size_points, size_summary)
    plot_release_paths(release_points)
    print("Built 4 result figures and 6 machine-readable result tables.")


if __name__ == "__main__":
    main()
