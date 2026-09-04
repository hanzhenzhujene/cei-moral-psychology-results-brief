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
RELEASE_PERIODS = ROOT / "data" / "model_release_periods.csv"
DATA = ROOT / "data" / "results"
FIGURES = ROOT / "assets" / "results"

SOURCE_HEAD = "b3a348684692f615d789392692ce34a1359192d3"
RELEASE_PERIOD_SOURCE_PATH = "data/model_release_periods.csv"
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
SOFT_GREEN = "#E8F4F0"
SOFT_AMBER = "#FFF4DF"
SOFT_RED = "#FBEAE7"
SOFT_GRAY = "#F1F3F5"

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


def save_figure(fig: plt.Figure, stem: str, *, tight: bool = True) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    bbox_inches = "tight" if tight else None
    fig.savefig(
        FIGURES / f"{stem}.png",
        dpi=220,
        bbox_inches=bbox_inches,
        facecolor=PAPER,
        metadata={"Software": "CEI result visual builder", "Creation Time": "2026-09-03"},
    )
    fig.savefig(
        FIGURES / f"{stem}.svg",
        bbox_inches=bbox_inches,
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
    ax.text(0.20, 0.99, ".20 internal planning target", transform=ax.get_xaxis_transform(), ha="right", va="top", color=MUTED, fontsize=8.5)
    ax.text(0.30, 0.91, ".30 internal audit warning", transform=ax.get_xaxis_transform(), ha="left", va="top", color=RED, fontsize=8.5)
    ax.set_yticks(ypos)
    ax.set_yticklabels(ordered["task_label"])
    ax.set_xlim(0, 0.45)
    ax.set_xlabel("Median full width of the saved 95% interval")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_title("Saved ranges overlap for every model pair on both comparison tests", loc="left", fontsize=20, fontweight="bold", pad=28)
    ax.text(0, 1.025, "Each dot = one task median. Full panels: 8 MFQ and 10 vignette models. Saved ranges overlap for all 28 MFQ and 45 vignette model pairs.", transform=ax.transAxes, color=MUTED, fontsize=10.5)
    fig.text(0.055, 0.065, "Decision: recover per-question outcomes, check scoring, compare models directly, and run human review.\nAdd independent items only if the order is still unclear.", fontsize=9.7, fontweight="bold")
    fig.text(0.055, 0.018, "Narrow UniMoral intervals are nominal row-level precision; they do not establish construct validity or cluster-aware uncertainty.", fontsize=9.1, color=MUTED)
    fig.tight_layout(rect=(0.03, 0.14, 0.99, 0.95))
    save_figure(fig, "02_precision_by_task")


def load_verified_release_periods() -> pd.DataFrame:
    periods = pd.read_csv(RELEASE_PERIODS, keep_default_na=False)
    expected_columns = {
        "model",
        "snapshot_release_period",
        "source_event_date",
        "verified_release_period",
        "source_url",
        "source_revision",
        "source_basis",
        "checked_on",
    }
    assert set(periods.columns) == expected_columns
    assert len(periods) == 6 and periods["model"].is_unique
    assert set(periods["model"]) == {
        "qwen/qwen-2.5-7b-instruct",
        "qwen/qwen3.5-9b",
        "deepseek/deepseek-chat-v3-0324",
        "deepseek/deepseek-chat-v3.1",
        "deepseek/deepseek-v3.2",
        "deepseek/deepseek-v4-flash",
    }
    assert periods["snapshot_release_period"].str.fullmatch(r"\d{4}-Q[1-4]").all()
    assert periods["verified_release_period"].str.fullmatch(r"\d{4}-Q[1-4]").all()
    dates = pd.to_datetime(periods["source_event_date"], format="%Y-%m-%d", errors="raise")
    derived_periods = dates.map(lambda value: f"{value.year}-Q{(value.month - 1) // 3 + 1}")
    assert derived_periods.equals(periods["verified_release_period"])
    assert periods["source_url"].str.startswith("https://").all()
    revisions = periods["source_revision"]
    assert revisions.eq("").sum() == 1
    assert revisions[revisions.ne("")].str.fullmatch(r"[0-9a-f]{40}").all()
    changed = periods[periods["snapshot_release_period"] != periods["verified_release_period"]]
    assert changed[["model", "verified_release_period"]].to_records(index=False).tolist() == [
        ("qwen/qwen-2.5-7b-instruct", "2024-Q3")
    ]
    return periods


def apply_verified_release_periods(frame: pd.DataFrame, periods: pd.DataFrame) -> pd.DataFrame:
    corrected = frame.copy()
    for row in periods.itertuples(index=False):
        mask = corrected["model"] == row.model
        assert mask.any()
        assert set(corrected.loc[mask, "release_period"]) == {row.snapshot_release_period}
        corrected.loc[mask, "release_period"] = row.verified_release_period
    return corrected


def load_selected_grid() -> tuple[pd.DataFrame, pd.DataFrame]:
    validate_selected_sources()
    grid = pd.read_csv(SELECTED / "model_grid.csv")
    results = pd.read_csv(SELECTED / "result_summary.csv")
    assert grid.shape == (17, 13)
    assert results["run_status"].value_counts().to_dict() == {"success": 102, "error": 13, "cancelled": 4}
    periods = load_verified_release_periods()
    grid = apply_verified_release_periods(grid, periods)
    results = apply_verified_release_periods(results, periods)
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


def compact_score(value: float) -> str:
    return f"{value:.3f}".removeprefix("0")


def compact_parameter_label(value: str) -> str:
    return value.replace(" main model", " main").replace(" total", "")


def plot_size_answer(points: pd.DataFrame, summary: pd.DataFrame) -> None:
    """Answer the UniMoral size question with one overview and one concrete path."""
    unimoral_tasks = SIX_TASKS[:4]
    unimoral = summary[summary["task"].isin(unimoral_tasks)].copy()
    counts = unimoral["direction"].value_counts().to_dict()
    assert len(unimoral) == 12
    assert counts == {"mixed": 7, "rising": 4, "falling": 1}

    fig = plt.figure(figsize=(14, 10))
    grid = fig.add_gridspec(2, 1, height_ratios=[0.72, 1.45], hspace=0.48)
    count_ax = fig.add_subplot(grid[0])
    path_ax = fig.add_subplot(grid[1])
    fig.suptitle(
        "Bigger models do not score higher consistently on UniMoral",
        x=0.055,
        y=0.982,
        ha="left",
        fontsize=22,
        fontweight="bold",
    )
    fig.text(
        0.055,
        0.944,
        "Question: within a named family, do saved task scores rise at both size steps?  Answer: only 4 of 12 complete UniMoral paths do.",
        color=MUTED,
        fontsize=11.5,
    )

    direction_order = ["rising", "mixed", "falling"]
    direction_labels = ["Rises at both steps", "Changes direction", "Falls at both steps"]
    direction_colors = [BLUE, AMBER, PURPLE]
    values = [counts[key] for key in direction_order]
    bars = count_ax.barh(direction_labels, values, color=direction_colors, height=0.55)
    count_ax.invert_yaxis()
    count_ax.set_xlim(0, 12)
    count_ax.set_xticks([0, 3, 6, 9, 12])
    count_ax.set_xlabel("Complete family × task paths (n = 12)")
    count_ax.set_title("Across Qwen, Gemma, and Llama on the four UniMoral tasks", loc="left", fontweight="bold", pad=10)
    count_ax.grid(axis="x", color=GRID, linewidth=0.8)
    count_ax.spines["left"].set_visible(False)
    count_ax.spines["bottom"].set_color(GRID)
    count_ax.tick_params(axis="y", length=0)
    for bar, value in zip(bars, values):
        count_ax.text(
            value + 0.18,
            bar.get_y() + bar.get_height() / 2,
            f"{value} of 12",
            va="center",
            ha="left",
            fontsize=12,
            fontweight="bold",
        )

    gemma = points[
        (points["family"] == "Gemma")
        & (points["task"].isin(["unimoral_factor_attribution", "unimoral_moral_typology"]))
    ].copy()
    gemma["tier_order"] = gemma["tier"].map({"S": 0, "M": 1, "L": 2})
    task_styles = {
        "unimoral_factor_attribution": ("Factor attribution", BLUE, "o", "-"),
        "unimoral_moral_typology": ("Moral typology", PURPLE, "s", "--"),
    }
    for task, (label, color, marker, linestyle) in task_styles.items():
        ordered = gemma[gemma["task"] == task].sort_values("tier_order")
        assert len(ordered) == 3
        path_ax.plot(
            ordered["tier_order"],
            ordered["score"],
            color=color,
            marker=marker,
            linestyle=linestyle,
            linewidth=2.8,
            markersize=8.5,
            label=label,
            zorder=3,
        )
        for row in ordered.itertuples(index=False):
            label_offset = (
                {0: -18, 1: 12, 2: 12}[int(row.tier_order)]
                if task == "unimoral_factor_attribution"
                else {0: 12, 1: -18, 2: -18}[int(row.tier_order)]
            )
            value_label = path_ax.annotate(
                f"{float(row.score):.3f}".removeprefix("0"),
                (float(row.tier_order), float(row.score)),
                xytext=(0, label_offset),
                textcoords="offset points",
                ha="center",
                va="bottom" if label_offset > 0 else "top",
                fontsize=11.5,
                fontweight="bold",
                color=color,
                annotation_clip=False,
            )
            value_label.set_gid(point_label_gid("size-answer", task, row.model))

    model_ticks = (
        gemma[gemma["task"] == "unimoral_factor_attribution"]
        .sort_values("tier_order")
        .drop_duplicates("tier_order")
    )
    path_ax.set_xticks(
        model_ticks["tier_order"],
        [f"{row.model_display}\n{row.parameter_label}" for row in model_ticks.itertuples(index=False)],
    )
    path_ax.set_xlim(-0.12, 2.42)
    path_ax.set_ylim(0.50, 0.65)
    path_ax.set_ylabel("Accuracy")
    path_ax.set_xlabel("Published model size within the same Gemma 3 generation")
    path_ax.set_title("Concrete counterexample: the same three Gemma models move two tasks in opposite directions", loc="left", fontweight="bold", pad=10)
    path_ax.grid(axis="y", color=GRID, linewidth=0.8)
    path_ax.spines["left"].set_color(GRID)
    path_ax.spines["bottom"].set_color(GRID)
    path_ax.legend(loc="upper left", frameon=False, ncol=2)
    path_ax.text(2.08, 0.617, "Factor  +.034", color=BLUE, fontsize=11.5, fontweight="bold", ha="left")
    path_ax.text(2.08, 0.566, "Typology  −.027", color=PURPLE, fontsize=11.5, fontweight="bold", ha="left")

    fig.text(
        0.055,
        0.018,
        "Each dot is one saved aggregate accuracy for one named model on one task; lines only join the selected variants. Exploratory: no saved intervals or raw-log replay, and B is not a controlled intervention.",
        fontsize=9.6,
        color=MUTED,
    )
    fig.subplots_adjust(left=0.16, right=0.965, top=0.89, bottom=0.09)
    save_figure(fig, "03_size_paths")


def plot_size_answer_mobile(points: pd.DataFrame, summary: pd.DataFrame) -> None:
    """Render the same size answer with mobile-readable type and stacking."""
    unimoral = summary[summary["task"].isin(SIX_TASKS[:4])].copy()
    counts = unimoral["direction"].value_counts().to_dict()
    assert counts == {"mixed": 7, "rising": 4, "falling": 1}

    fig = plt.figure(figsize=(6, 10.8))
    grid = fig.add_gridspec(2, 1, height_ratios=[0.72, 1.4], hspace=0.5)
    count_ax = fig.add_subplot(grid[0])
    path_ax = fig.add_subplot(grid[1])
    fig.suptitle(
        "Bigger models do not score\nhigher consistently",
        x=0.07,
        y=0.995,
        ha="left",
        fontsize=20,
        fontweight="bold",
    )
    fig.text(
        0.07,
        0.885,
        "UniMoral-only local follow-up · 4 of 12 complete paths rise at both size steps",
        color=MUTED,
        fontsize=16,
        wrap=True,
    )

    labels = ["Rises twice", "Changes\ndirection", "Falls twice"]
    values = [counts["rising"], counts["mixed"], counts["falling"]]
    bars = count_ax.barh(labels, values, color=[BLUE, AMBER, PURPLE], height=0.56)
    count_ax.invert_yaxis()
    count_ax.set_xlim(0, 12)
    count_ax.set_xticks([0, 4, 8, 12])
    count_ax.tick_params(axis="both", labelsize=16)
    count_ax.set_xlabel("Complete family × task paths", fontsize=16)
    count_ax.set_title("What happens across\nall 12 paths?", loc="left", fontweight="bold", fontsize=18, pad=10)
    count_ax.grid(axis="x", color=GRID, linewidth=0.8)
    count_ax.spines["left"].set_visible(False)
    count_ax.spines["bottom"].set_color(GRID)
    count_ax.tick_params(axis="y", length=0)
    for bar, value in zip(bars, values):
        count_ax.text(
            value + 0.2,
            bar.get_y() + bar.get_height() / 2,
            f"{value} of 12",
            va="center",
            fontsize=17,
            fontweight="bold",
        )

    gemma = points[
        (points["family"] == "Gemma")
        & (points["task"].isin(["unimoral_factor_attribution", "unimoral_moral_typology"]))
    ].copy()
    gemma["tier_order"] = gemma["tier"].map({"S": 0, "M": 1, "L": 2})
    styles = {
        "unimoral_factor_attribution": ("Factor", BLUE, "o", "-"),
        "unimoral_moral_typology": ("Typology", PURPLE, "s", "--"),
    }
    for task, (label, color, marker, linestyle) in styles.items():
        ordered = gemma[gemma["task"] == task].sort_values("tier_order")
        path_ax.plot(
            ordered["tier_order"],
            ordered["score"],
            color=color,
            marker=marker,
            linestyle=linestyle,
            linewidth=3.0,
            markersize=9,
            label=label,
            zorder=3,
        )
        for row in ordered.itertuples(index=False):
            offset = (
                {0: -20, 1: 13, 2: 13}[int(row.tier_order)]
                if task == "unimoral_factor_attribution"
                else {0: 13, 1: -20, 2: -20}[int(row.tier_order)]
            )
            annotation = path_ax.annotate(
                f"{float(row.score):.3f}".removeprefix("0"),
                (float(row.tier_order), float(row.score)),
                xytext=(0, offset),
                textcoords="offset points",
                ha="center",
                va="bottom" if offset > 0 else "top",
                fontsize=17,
                fontweight="bold",
                color=color,
                annotation_clip=False,
            )
            annotation.set_gid(point_label_gid("size-mobile-answer", task, row.model))

    ticks = gemma[gemma["task"] == "unimoral_factor_attribution"].sort_values("tier_order")
    path_ax.set_xticks(
        ticks["tier_order"],
        [f"Gemma 3\n{row.model_display.removeprefix('Gemma 3-')}\n{row.parameter_label}" for row in ticks.itertuples(index=False)],
    )
    edge_tick_labels = path_ax.get_xticklabels()
    edge_tick_labels[0].set_ha("left")
    edge_tick_labels[-1].set_ha("right")
    path_ax.tick_params(axis="both", labelsize=16)
    path_ax.set_xlim(-0.12, 2.12)
    path_ax.set_ylim(0.50, 0.65)
    path_ax.set_ylabel("Accuracy", fontsize=16)
    path_ax.set_title("Same models,\nopposite task paths", loc="left", fontweight="bold", fontsize=18, pad=10)
    path_ax.grid(axis="y", color=GRID, linewidth=0.8)
    path_ax.spines["left"].set_color(GRID)
    path_ax.spines["bottom"].set_color(GRID)
    path_ax.legend(loc="upper center", frameon=False, ncol=2, fontsize=16)

    fig.text(
        0.07,
        0.018,
        "Each dot = one saved aggregate\nfor one named model + task.\nExploratory: no saved intervals.\nB is not a controlled intervention.",
        fontsize=15.5,
        color=MUTED,
        linespacing=1.35,
    )
    fig.subplots_adjust(left=0.24, right=0.95, top=0.79, bottom=0.21)
    save_figure(fig, "03_size_paths_mobile", tight=False)


def plot_size_detail(points: pd.DataFrame, tasks: list[str], stem: str, title: str) -> None:
    fig, axes = plt.subplots(len(tasks), 1, figsize=(16, 13), sharex=True)
    axes = np.atleast_1d(axes)
    fig.suptitle(title, x=0.055, y=0.985, ha="left", fontsize=21, fontweight="bold")
    fig.text(
        0.055,
        0.956,
        "Each point is one saved task score for a named model; each line joins that family's small, medium, and large variants. Published-B spacing is ordinal, not proportional.",
        color=MUTED,
        fontsize=11.2,
    )
    annotations: list[mpl.text.Annotation] = []
    label_lanes = {0: 0.84, 1: 0.16, 2: 0.66, 3: 0.34, 4: 0.88, 5: 0.12, 6: 0.68, 7: 0.32, 8: 0.84}
    for ax, task in zip(axes, tasks):
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
        axis_models = points[["model", "size_plot_position", "total_parameters_b"]].drop_duplicates().sort_values("size_plot_position")
        axis_labels = [f"{value:g}B" for value in axis_models["total_parameters_b"]]
        ax.set_xlim(-0.7, 8.7)
        ax.set_xticks(axis_models["size_plot_position"], axis_labels)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
        incomplete = [family for family in ["Qwen", "Gemma", "Llama"] if set(task_rows.loc[task_rows["family"] == family, "tier"]) != {"S", "M", "L"}]
        if incomplete:
            ax.text(0.02, 0.03, "Incomplete: " + ", ".join(incomplete), transform=ax.transAxes, color=MUTED, fontsize=8)
    for ax in axes[:-1]:
        ax.tick_params(axis="x", labelbottom=False)
    axes[-1].set_xlabel("Published total B categories — ordered only; horizontal gaps are not to scale")
    handles = [
        plt.Line2D([0], [0], color=FAMILY_COLORS[f], marker=FAMILY_MARKERS[f], linestyle=FAMILY_LINESTYLES[f], linewidth=2.4, label=f)
        for f in ["Qwen", "Gemma", "Llama"]
    ]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.96, 0.985), ncol=3, frameon=False)
    fig.text(
        0.055,
        0.018,
        "Named-model specifications only; no saved intervals or raw-log replay. METEOR remains separate from accuracy.",
        fontsize=9.1,
        color=MUTED,
    )
    fig.tight_layout(rect=(0.04, 0.045, 0.99, 0.925), h_pad=1.8)
    assert_point_label_layout(fig, annotations, expected=len(points[points["task"].isin(tasks)]))
    save_figure(fig, stem)


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
    points["release_period_source_path"] = RELEASE_PERIOD_SOURCE_PATH
    return points


def build_release_summary(points: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (family, task), group in points.groupby(["family", "task"], sort=True):
        ordered = group.sort_values("release_period", key=lambda values: values.map(quarter_key))
        first = ordered.iloc[0]
        last = ordered.iloc[-1]
        values = ordered["score"].to_numpy(dtype=float)
        deltas = np.diff(values)
        endpoint_delta = float(last.score - first.score)
        endpoint_direction = "higher" if endpoint_delta > 0 else "lower" if endpoint_delta < 0 else "unchanged"
        monotonic = bool(np.all(deltas > 0) or np.all(deltas < 0))
        rows.append(
            {
                "family": family,
                "task": task,
                "task_label": TASKS[task][0],
                "metric": TASKS[task][1],
                "first_period": first.release_period,
                "first_score": float(first.score),
                "first_model": first.model,
                "first_model_display": first.model_display,
                "first_parameter_label": first.parameter_label,
                "last_period": last.release_period,
                "last_score": float(last.score),
                "last_model": last.model,
                "last_model_display": last.model_display,
                "last_parameter_label": last.parameter_label,
                "endpoint_delta": endpoint_delta,
                "endpoint_direction": endpoint_direction,
                "internal_reversal": len(values) > 2 and not monotonic,
                "observed_points": len(ordered),
                "evidence_status": "exploratory aggregate; no CI or raw-log replay",
                "source_repository_head": SOURCE_HEAD,
                "source_path": "evidence/source-results/result_summary.csv",
                "release_period_source_path": RELEASE_PERIOD_SOURCE_PATH,
            }
        )
    summary = pd.DataFrame(rows)
    assert len(summary) == 12
    assert summary.groupby(["family", "endpoint_direction"]).size().to_dict() == {
        ("DeepSeek", "higher"): 3,
        ("DeepSeek", "lower"): 3,
        ("Qwen", "higher"): 5,
        ("Qwen", "lower"): 1,
    }
    return summary


def quarter_key(value: str) -> int:
    year, quarter = value.split("-Q")
    return int(year) * 4 + int(quarter)


def quarter_label(value: int) -> str:
    year = (value - 1) // 4
    quarter = value - year * 4
    return f"{year}\nQ{quarter}"


def plot_release_answer(summary: pd.DataFrame) -> None:
    """Show UniMoral endpoint changes without treating release quarter as evaluation time."""
    unimoral = summary[summary["task"].isin(SIX_TASKS[:4])].copy()
    counts = unimoral.groupby(["family", "endpoint_direction"]).size().to_dict()
    assert len(unimoral) == 8
    assert counts == {
        ("DeepSeek", "higher"): 2,
        ("DeepSeek", "lower"): 2,
        ("Qwen", "higher"): 3,
        ("Qwen", "lower"): 1,
    }

    fig = plt.figure(figsize=(14, 10))
    grid = fig.add_gridspec(2, 1, height_ratios=[1.55, 0.72], hspace=0.55)
    accuracy_ax = fig.add_subplot(grid[0])
    meteor_ax = fig.add_subplot(grid[1])
    fig.suptitle(
        "Newer named releases do not move every UniMoral task up",
        x=0.055,
        y=0.982,
        ha="left",
        fontsize=22,
        fontweight="bold",
    )
    fig.text(
        0.055,
        0.944,
        "Qwen endpoints: 3 higher, 1 lower.  DeepSeek endpoints: 2 higher, 2 lower.  All scores were evaluated May 28–29, 2026.",
        color=MUTED,
        fontsize=11.5,
    )
    fig.text(
        0.055,
        0.902,
        "Qwen  ●  Qwen2.5-7B Instruct (7.61B total)  →  Qwen3.5-9B (9B total)",
        color=FAMILY_COLORS["Qwen"],
        fontsize=10.5,
        fontweight="bold",
    )
    fig.text(
        0.055,
        0.875,
        "DeepSeek  ◆  V3-0324 (671B main / 37B active)  →  V4 Flash (284B main / 13B active)",
        color=FAMILY_COLORS["DeepSeek"],
        fontsize=10.5,
        fontweight="bold",
    )

    family_offsets = {"Qwen": 0.13, "DeepSeek": -0.13}
    family_markers = {"Qwen": "o", "DeepSeek": "D"}

    def draw_delta_panel(ax: plt.Axes, rows: pd.DataFrame, tasks: list[str], limit: float, metric: str) -> None:
        y_positions = {task: len(tasks) - index - 1 for index, task in enumerate(tasks)}
        ax.axvline(0, color=INK, linewidth=1.2, zorder=1)
        for row in rows.itertuples(index=False):
            y = y_positions[row.task] + family_offsets[row.family]
            delta = float(row.endpoint_delta)
            point = ax.scatter(
                delta,
                y,
                s=78,
                marker=family_markers[row.family],
                color=FAMILY_COLORS[row.family],
                zorder=3,
            )
            reversal = "  †" if bool(row.internal_reversal) else ""
            delta_text = f"{delta:+.3f}".replace("-", "−")
            point_label = ax.annotate(
                f"{row.family} {delta_text}{reversal}",
                (delta, y),
                xytext=(8 if delta >= 0 else -8, 0),
                textcoords="offset points",
                ha="left" if delta >= 0 else "right",
                va="center",
                fontsize=10.5,
                fontweight="bold",
                color=FAMILY_COLORS[row.family],
                annotation_clip=False,
            )
            point_label.set_gid(point_label_gid("release-answer", row.task, row.family))
        ax.set_xlim(-limit, limit)
        ax.set_yticks([y_positions[task] for task in tasks], [TASKS[task][0] for task in tasks])
        ax.set_ylim(-0.55, len(tasks) - 0.45)
        ax.set_xlabel(f"Endpoint change in {metric}  (later named model − earlier named model)")
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(axis="y", length=0)

    accuracy_tasks = SIX_TASKS[:3]
    draw_delta_panel(
        accuracy_ax,
        unimoral[unimoral["task"].isin(accuracy_tasks)],
        accuracy_tasks,
        0.22,
        "accuracy",
    )
    accuracy_ax.set_title("Classification tasks — zero means no endpoint change", loc="left", fontweight="bold", pad=10)
    draw_delta_panel(
        meteor_ax,
        unimoral[unimoral["task"] == "unimoral_consequence_generation"],
        ["unimoral_consequence_generation"],
        0.035,
        "METEOR",
    )
    meteor_ax.set_title("Consequence generation — separate metric and scale", loc="left", fontweight="bold", pad=10)

    fig.text(
        0.055,
        0.052,
        "Each point is one later-minus-earlier aggregate for the named model path above. † The saved intermediate DeepSeek path changes direction; see the full path figures for every checkpoint.",
        fontsize=9.6,
        color=MUTED,
    )
    fig.text(
        0.055,
        0.026,
        "Exploratory: no saved intervals or raw-log replay. Release quarter is model metadata, not evaluation time; generation, route, architecture, and parameter count change together.",
        fontsize=9.6,
        color=MUTED,
    )
    fig.subplots_adjust(left=0.19, right=0.965, top=0.82, bottom=0.11)
    save_figure(fig, "04_release_period_paths")


def plot_release_answer_mobile(summary: pd.DataFrame) -> None:
    """Render the release answer as a mobile-readable pair of delta panels."""
    unimoral = summary[summary["task"].isin(SIX_TASKS[:4])].copy()
    counts = unimoral.groupby(["family", "endpoint_direction"]).size().to_dict()
    assert counts == {
        ("DeepSeek", "higher"): 2,
        ("DeepSeek", "lower"): 2,
        ("Qwen", "higher"): 3,
        ("Qwen", "lower"): 1,
    }

    fig = plt.figure(figsize=(6, 13.8))
    grid = fig.add_gridspec(2, 1, height_ratios=[1.45, 0.68], hspace=0.62)
    accuracy_ax = fig.add_subplot(grid[0])
    meteor_ax = fig.add_subplot(grid[1])
    fig.suptitle(
        "Newer named releases do not\nmove every UniMoral task up",
        x=0.07,
        y=0.99,
        ha="left",
        fontsize=19.5,
        fontweight="bold",
    )
    fig.text(
        0.07,
        0.920,
        "Qwen: 3 higher, 1 lower\nDeepSeek: 2 higher, 2 lower",
        color=MUTED,
        fontsize=16,
    )
    fig.text(
        0.07,
        0.855,
        "Qwen ●  Qwen2.5-7B Instruct\n7.61B total\n→ Qwen3.5-9B · 9B total",
        color=FAMILY_COLORS["Qwen"],
        fontsize=15.5,
        fontweight="bold",
        linespacing=1.25,
    )
    fig.text(
        0.07,
        0.770,
        "DeepSeek ◆  V3-0324\n671B main / 37B active\n→ V4 Flash\n284B main / 13B active",
        color=FAMILY_COLORS["DeepSeek"],
        fontsize=15.5,
        fontweight="bold",
        linespacing=1.25,
    )

    offsets = {"Qwen": 0.22, "DeepSeek": -0.22}
    markers = {"Qwen": "o", "DeepSeek": "D"}

    def draw_panel(ax: plt.Axes, rows: pd.DataFrame, tasks: list[str], limit: float, metric: str) -> None:
        positions = {task: len(tasks) - index - 1 for index, task in enumerate(tasks)}
        ax.axvline(0, color=INK, linewidth=1.3, zorder=1)
        for row in rows.itertuples(index=False):
            delta = float(row.endpoint_delta)
            y = positions[row.task] + offsets[row.family]
            ax.scatter(
                delta,
                y,
                s=92,
                marker=markers[row.family],
                color=FAMILY_COLORS[row.family],
                zorder=3,
            )
            reversal = "†" if bool(row.internal_reversal) else ""
            value = f"{delta:+.3f}".replace("-", "−")
            point_text = f"{row.family} {value}{reversal}"
            if row.family == "DeepSeek" and delta < 0:
                x_offset, align = 10, "left"
                point_text = f"{row.family}\n{value}{reversal}"
            elif delta > limit * 0.45:
                x_offset, align = -10, "right"
            elif delta < -limit * 0.45:
                x_offset, align = 10, "left"
            elif delta >= 0:
                x_offset, align = 9, "left"
            else:
                x_offset, align = -9, "right"
            label = ax.annotate(
                point_text,
                (delta, y),
                xytext=(x_offset, 0),
                textcoords="offset points",
                ha=align,
                va="center",
                fontsize=17,
                fontweight="bold",
                color=FAMILY_COLORS[row.family],
                annotation_clip=False,
            )
            label.set_gid(point_label_gid("release-mobile-answer", row.task, row.family))
        ax.set_xlim(-limit, limit)
        ax.set_yticks([positions[task] for task in tasks], [TASKS[task][0].replace("UniMoral ", "") for task in tasks])
        ax.set_ylim(-0.55, len(tasks) - 0.45)
        ax.tick_params(axis="both", labelsize=16)
        ax.set_xlabel(f"Later − earlier {metric}", fontsize=17)
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(axis="y", length=0)

    accuracy_tasks = SIX_TASKS[:3]
    draw_panel(
        accuracy_ax,
        unimoral[unimoral["task"].isin(accuracy_tasks)],
        accuracy_tasks,
        0.22,
        "accuracy",
    )
    accuracy_ax.set_title("Classification tasks\nZero = no endpoint change", loc="left", fontsize=18, fontweight="bold", pad=10)
    draw_panel(
        meteor_ax,
        unimoral[unimoral["task"] == "unimoral_consequence_generation"],
        ["unimoral_consequence_generation"],
        0.035,
        "METEOR",
    )
    meteor_ax.set_title("Consequence\nSeparate METEOR scale", loc="left", fontsize=18, fontweight="bold", pad=10)

    fig.text(
        0.07,
        0.033,
        "Each point = one later-minus-earlier aggregate\nfor the named path above.\n† Intermediate DeepSeek checkpoints\nchange direction.\nAll scores ran May 28–29, 2026.",
        fontsize=15.5,
        color=MUTED,
        linespacing=1.35,
    )
    fig.subplots_adjust(left=0.27, right=0.95, top=0.62, bottom=0.19)
    save_figure(fig, "04_release_period_paths_mobile", tight=False)


def plot_release_detail(points: pd.DataFrame, tasks: list[str], stem: str, title: str) -> None:
    period_keys = points["release_period"].map(quarter_key)
    first_period = int(period_keys.min())
    last_period = int(period_keys.max())
    quarter_ticks = list(range(first_period, last_period + 1))
    xpos = {period: quarter_key(period) - first_period for period in points["release_period"].unique()}
    fig, axes = plt.subplots(len(tasks), 1, figsize=(16, 13), sharex=True)
    axes = np.atleast_1d(axes)
    fig.suptitle(title, x=0.055, y=0.985, ha="left", fontsize=21, fontweight="bold")
    fig.text(
        0.055,
        0.956,
        "Each point is one saved task score for a different named model; lines join models within a family. All scores were evaluated May 28–29, 2026.",
        color=MUTED,
        fontsize=11.2,
    )
    annotations: list[mpl.text.Annotation] = []
    release_offsets = {
        "qwen/qwen-2.5-7b-instruct": (9, 25),
        "deepseek/deepseek-chat-v3-0324": (9, -28),
        "deepseek/deepseek-chat-v3.1": (9, 34),
        "deepseek/deepseek-v3.2": (-9, -36),
        "qwen/qwen3.5-9b": (-9, 55),
        "deepseek/deepseek-v4-flash": (-9, -45),
    }
    for ax, task in zip(axes, tasks):
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
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
    for ax in axes[:-1]:
        ax.tick_params(axis="x", labelbottom=False)
    axes[-1].set_xlabel("Named model release quarter — metadata, not evaluation time")
    handles = [
        plt.Line2D([0], [0], color=FAMILY_COLORS[f], marker=FAMILY_MARKERS[f], linestyle="--" if f == "Qwen" else ":", linewidth=2.4, label=f)
        for f in ["Qwen", "DeepSeek"]
    ]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.96, 0.985), ncol=2, frameon=False)
    fig.text(
        0.055,
        0.018,
        "Release quarter is model metadata, not evaluation time. DeepSeek counts exclude auxiliary/MTP weights; no saved intervals or raw-log replay.",
        fontsize=9.1,
        color=MUTED,
    )
    fig.tight_layout(rect=(0.04, 0.045, 0.99, 0.925), h_pad=1.8)
    assert_point_label_layout(fig, annotations, expected=len(points[points["task"].isin(tasks)]))
    save_figure(fig, stem)


def save_takeaways(partition: pd.DataFrame, size_summary: pd.DataFrame, release_summary: pd.DataFrame) -> None:
    table = pd.DataFrame(
        [
            {
                "research_question": "Do the five consistently covered models have one stable order?",
                "answer": "No. In the five-model primary common roster, the highest saved score belongs to different models on different tasks.",
                "evidence_status": "main audited aggregate",
                "decision": "Report task-specific results and keep metrics separate.",
                "source": "evidence/canonical-audit/figures/data/primary_confidence_intervals.csv",
            },
            {
                "research_question": "Can the two comparison tests tell us which model leads?",
                "answer": "No. Marginal score ranges overlap for all 28 MFQ and all 45 vignette model pairs; all 18 intervals wider than .30 occur in these two tasks.",
                "evidence_status": "main audited aggregate; not a paired model-difference test",
                "decision": "Restore every model's answer and score for each question; check scoring and labels; then compare models directly.",
                "source": "evidence/canonical-audit/figures/data/primary_confidence_intervals.csv",
            },
            {
                "research_question": "Do task scores keep rising across two size increases?",
                "answer": "Only 4 of 12 UniMoral family-task paths rise at both steps; 7 change direction and 1 falls. Including ValuePrism, the full selected-grid count is 5 of 15 rising, 9 changing direction, and 1 falling.",
                "evidence_status": "exploratory aggregate; no saved uncertainty or original run files",
                "decision": "Bigger is not always better; treat size as an exploratory clue.",
                "source": "evidence/source-results/result_summary.csv",
            },
            {
                "research_question": "Do later Qwen and DeepSeek versions score higher on every UniMoral task?",
                "answer": "No. On UniMoral, Qwen has 3 higher and 1 lower endpoint; DeepSeek has 2 higher and 2 lower. Including ValuePrism, the full selected-grid counts are 5/1 and 3/3. All plotted evaluations ran May 28–29, 2026.",
                "evidence_status": "exploratory aggregate; no saved uncertainty or original run files",
                "decision": "Newer is not always better; release period is model metadata, not a progress trend.",
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
    assert release_summary.groupby(["family", "endpoint_direction"]).size().to_dict() == {
        ("DeepSeek", "higher"): 3,
        ("DeepSeek", "lower"): 3,
        ("Qwen", "higher"): 5,
        ("Qwen", "lower"): 1,
    }
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
    release_summary = build_release_summary(release_points)

    save_csv(common, "common_roster_primary.csv")
    save_csv(precision, "task_precision.csv")
    save_csv(size_points, "size_task_points.csv")
    save_csv(size_summary, "size_path_summary.csv")
    save_csv(release_points, "release_period_task_points.csv")
    save_csv(release_summary, "release_path_summary.csv")
    save_takeaways(partition, size_summary, release_summary)

    plot_common_roster(common)
    plot_precision(precision)
    plot_size_answer(size_points, size_summary)
    plot_size_answer_mobile(size_points, size_summary)
    plot_size_detail(
        size_points,
        SIX_TASKS[:3],
        "03_size_paths_detail_a",
        "How model size relates to UniMoral classification scores",
    )
    plot_size_detail(
        size_points,
        SIX_TASKS[3:],
        "03_size_paths_detail_b",
        "How model size relates to consequence and ValuePrism scores",
    )
    plot_release_answer(release_summary)
    plot_release_answer_mobile(release_summary)
    plot_release_detail(
        release_points,
        SIX_TASKS[:3],
        "04_release_period_paths_detail_a",
        "How named model releases move across UniMoral classification tasks",
    )
    plot_release_detail(
        release_points,
        SIX_TASKS[3:],
        "04_release_period_paths_detail_b",
        "How named model releases move on consequence and ValuePrism",
    )
    print("Built 10 result figures and 7 machine-readable result tables.")


if __name__ == "__main__":
    main()
