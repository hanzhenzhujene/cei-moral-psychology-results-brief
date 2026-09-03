#!/usr/bin/env python3
"""Build the research-lead result figures from pinned, tracked CSV evidence."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "evidence" / "canonical-audit" / "figures" / "data"
SELECTED = ROOT / "evidence" / "source-results"
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
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 9.2))
    fig.suptitle("Bigger is not reliably better", x=0.055, y=0.985, ha="left", fontsize=22, fontweight="bold")
    fig.text(0.055, 0.944, "Exploratory selected grid · 15 complete family × task paths: 5 rise · 9 mixed · 1 falls", color=MUTED, fontsize=11.5)
    for ax, task in zip(axes.flat, SIX_TASKS):
        task_rows = points[points["task"] == task]
        for family, family_rows in task_rows.groupby("family"):
            if set(family_rows["tier"]) != {"S", "M", "L"}:
                continue
            ordered = family_rows.set_index("tier").loc[["S", "M", "L"]]
            ax.plot(
                [0, 1, 2],
                ordered["score"],
                marker=FAMILY_MARKERS[family],
                linestyle=FAMILY_LINESTYLES[family],
                linewidth=2.4,
                markersize=6.5,
                color=FAMILY_COLORS[family],
                label=family,
            )
        label, metric, _, _ = TASKS[task]
        ax.set_title(label, loc="left", fontweight="bold")
        ax.set_ylabel(metric)
        ax.set_ylim(*SCALING_LIMITS[task])
        ax.set_xticks([0, 1, 2], ["Small", "Medium", "Large"])
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
        incomplete = [family for family in ["Qwen", "Gemma", "Llama"] if set(task_rows.loc[task_rows["family"] == family, "tier"]) != {"S", "M", "L"}]
        if incomplete:
            ax.text(0.02, 0.03, "Incomplete: " + ", ".join(incomplete), transform=ax.transAxes, color=MUTED, fontsize=8)
    handles = [
        plt.Line2D([0], [0], color=FAMILY_COLORS[f], marker=FAMILY_MARKERS[f], linestyle=FAMILY_LINESTYLES[f], linewidth=2.4, label=f)
        for f in ["Qwen", "Gemma", "Llama"]
    ]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.96, 0.965), ncol=3, frameon=False)
    fig.text(0.055, 0.035, "Result: point-estimate direction changes by task and family. A larger tier can move upward on one task and downward on another.", fontsize=10.2, fontweight="bold")
    fig.text(0.055, 0.013, "Accuracy panels share one scale; METEOR is separate. No intervals are saved; Qwen/Llama tiers also differ in period. ValuePrism predicts synthetic/GPT-4 labels.", fontsize=8.9, color=MUTED)
    fig.tight_layout(rect=(0.04, 0.07, 0.99, 0.90), w_pad=1.4, h_pad=2.0)
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
    fig, axes = plt.subplots(2, 3, figsize=(15.5, 9.2))
    fig.suptitle("Newer-route point estimates move in both directions", x=0.055, y=0.985, ha="left", fontsize=22, fontweight="bold")
    fig.text(0.055, 0.944, "Exploratory release-period view · markers are observed points; lines only connect them · route, architecture, and size can change", color=MUTED, fontsize=11.0)
    for ax, task in zip(axes.flat, SIX_TASKS):
        task_rows = points[points["task"] == task]
        for family, family_rows in task_rows.groupby("family"):
            ordered = family_rows.sort_values("release_period", key=lambda s: s.map(quarter_key))
            ax.plot(
                ordered["release_period"].map(xpos),
                ordered["score"],
                marker=FAMILY_MARKERS[family],
                linestyle="--" if family == "Qwen" else ":",
                linewidth=2.4,
                markersize=6.5,
                color=FAMILY_COLORS[family],
                label=family,
            )
        label, metric, _, _ = TASKS[task]
        ax.set_title(label, loc="left", fontweight="bold")
        ax.set_ylabel(metric)
        ax.set_ylim(*SCALING_LIMITS[task])
        ax.set_xticks([value - first_period for value in quarter_ticks], [quarter_label(value) for value in quarter_ticks])
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.spines["left"].set_color(GRID)
        ax.spines["bottom"].set_color(GRID)
    handles = [
        plt.Line2D([0], [0], color=FAMILY_COLORS[f], marker=FAMILY_MARKERS[f], linestyle="--" if f == "Qwen" else ":", linewidth=2.4, label=f)
        for f in ["Qwen", "DeepSeek"]
    ]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.96, 0.965), ncol=2, frameon=False)
    fig.text(0.055, 0.035, "Result: Qwen point estimates rise on five endpoints and fall on consequence METEOR; DeepSeek endpoint movement is also mixed.", fontsize=10.2, fontweight="bold")
    fig.text(0.055, 0.013, "Accuracy panels share one scale; METEOR is separate. Gemma is blocked; DeepSeek relevance ends 2025 Q4. No intervals; ValuePrism predicts synthetic/GPT-4 labels.", fontsize=8.8, color=MUTED)
    fig.tight_layout(rect=(0.04, 0.07, 0.99, 0.90), w_pad=1.4, h_pad=2.0)
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
    size_points, size_summary = build_size_paths(results)
    release_points = build_release_paths(results)

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
