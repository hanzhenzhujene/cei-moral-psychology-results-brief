#!/usr/bin/env python3
"""Independently validate the CEI research-lead results brief."""

from __future__ import annotations

import argparse
import hashlib
import io
import itertools
import json
import posixpath
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "evidence" / "canonical-audit"
SELECTED = ROOT / "evidence" / "source-results"
RESULT_DATA = ROOT / "data" / "results"
PARAMETERS = ROOT / "evidence" / "model-parameter-sources.csv"
RELEASE_PERIODS = ROOT / "data" / "model_release_periods.csv"
SLIDE_DECK = ROOT / "slides" / "cei-moral-psychology-results-deck.pptx"
SLIDE_PDF = ROOT / "slides" / "cei-moral-psychology-results-deck.pdf"
SLIDE_RENDER_DIR = ROOT / "slides" / "rendered"
SLIDE_EXPORT_MANIFEST = ROOT / "slides" / "RENDER_MANIFEST.csv"

SOURCE_HEAD = "b3a348684692f615d789392692ce34a1359192d3"
CANONICAL_SHA = "276acecd603761e6ff61bd6e2685fbb87f0eaa47"
UPSTREAM_BAD_SHA = CANONICAL_SHA + "d"
RUN_IDENTITY_SCOPE = "named-model specification only; served provider endpoint, quantization, and checkpoint revision not retained"
RELEASE_PERIOD_SOURCE_PATH = "data/model_release_periods.csv"
COMMON_MODELS = {
    "claude-haiku-4-5",
    "claude-opus-4-8",
    "gpt-5.4",
    "gpt-5.4-mini",
    "qwen3-8b",
}
COMPARE_TASKS = {"moralbench_mfq_compare", "moralbench_vignette_compare"}
SCORE_METRICS = {
    "moralbench_mfq_agreement": "normalized_preference",
    "moralbench_vignette_agreement": "normalized_preference",
    "moralbench_mfq_compare": "accuracy",
    "moralbench_vignette_compare": "accuracy",
    "unimoral_action_prediction": "accuracy",
    "unimoral_moral_typology": "accuracy",
    "unimoral_factor_attribution": "accuracy",
    "unimoral_consequence_generation": "meteor",
}
SLIDE_TASK_EXPLANATIONS = {
    "moralbench_mfq_agreement": "Track benchmark human ratings of value statements",
    "moralbench_vignette_agreement": "Track benchmark human ratings of moral stories",
    "moralbench_mfq_compare": "Pick the higher-rated value statement",
    "moralbench_vignette_compare": "Pick the higher-rated moral story",
    "unimoral_action_prediction": "Match one recorded human choice",
    "unimoral_moral_typology": "Classify the recorded choice into one of four types",
    "unimoral_factor_attribution": "Pick a top-rated factor for the recorded choice",
    "unimoral_consequence_generation": "Write what could happen next",
}
SCALING_TASK_LABELS = {
    "unimoral_action_prediction": ("UniMoral action", "Accuracy"),
    "unimoral_moral_typology": ("UniMoral typology", "Accuracy"),
    "unimoral_factor_attribution": ("UniMoral factor", "Accuracy"),
    "unimoral_consequence_generation": ("UniMoral consequence", "METEOR"),
    "value_prism_relevance": ("ValuePrism relevance", "Accuracy"),
    "value_prism_valence": ("ValuePrism valence", "Accuracy"),
}
EXPECTED_PARAMETER_FACTS = {
    "qwen/qwen3-8b": ("Qwen3-8B", 8.2, None, "8.2B total", "dense", "https://huggingface.co/Qwen/Qwen3-8B"),
    "qwen/qwen3-32b": ("Qwen3-32B", 32.8, None, "32.8B total", "dense", "https://huggingface.co/Qwen/Qwen3-32B"),
    "qwen/qwen3-235b-a22b-2507": ("Qwen3-235B-A22B (2507)", 235.0, 22.0, "235B total / 22B active", "MoE", "https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507"),
    "google/gemma-3-4b-it": ("Gemma 3-4B-IT", 4.0, None, "4B total", "dense", "https://huggingface.co/google/gemma-3-4b-it"),
    "google/gemma-3-12b-it": ("Gemma 3-12B-IT", 12.0, None, "12B total", "dense", "https://huggingface.co/google/gemma-3-12b-it"),
    "google/gemma-3-27b-it": ("Gemma 3-27B-IT", 27.0, None, "27B total", "dense", "https://huggingface.co/google/gemma-3-27b-it"),
    "meta-llama/llama-3.2-3b-instruct": ("Llama 3.2-3B Instruct", 3.0, None, "3B total", "dense", "https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct"),
    "meta-llama/llama-3.1-8b-instruct": ("Llama 3.1-8B Instruct", 8.0, None, "8B total", "dense", "https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct"),
    "meta-llama/llama-3.3-70b-instruct": ("Llama 3.3-70B Instruct", 70.0, None, "70B total", "dense", "https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct"),
    "qwen/qwen-2.5-7b-instruct": ("Qwen2.5-7B Instruct", 7.61, None, "7.61B total", "dense", "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct"),
    "qwen/qwen3.5-9b": ("Qwen3.5-9B", 9.0, None, "9B total", "dense", "https://huggingface.co/Qwen/Qwen3.5-9B"),
    "deepseek/deepseek-chat-v3-0324": ("DeepSeek V3-0324", 671.0, 37.0, "671B main model / 37B active", "MoE", "https://huggingface.co/deepseek-ai/DeepSeek-V3-0324"),
    "deepseek/deepseek-chat-v3.1": ("DeepSeek V3.1", 671.0, 37.0, "671B main model / 37B active", "MoE", "https://huggingface.co/deepseek-ai/DeepSeek-V3.1"),
    "deepseek/deepseek-v3.2": ("DeepSeek V3.2", 671.0, 37.0, "671B main model / 37B active", "MoE", "https://huggingface.co/deepseek-ai/DeepSeek-V3.2"),
    "deepseek/deepseek-v4-flash": ("DeepSeek V4 Flash", 284.0, 13.0, "284B main model / 13B active", "MoE", "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash"),
}
EXPECTED_SOURCE_REVISIONS = {
    "qwen/qwen3-8b": "b968826d9c46dd6066d109eabc6255188de91218",
    "qwen/qwen3-32b": "9216db5781bf21249d130ec9da846c4624c16137",
    "qwen/qwen3-235b-a22b-2507": "ac9c66cc9b46af7306746a9250f23d47083d689e",
    "google/gemma-3-4b-it": "093f9f388b31de276ce2de164bdc2081324b9767",
    "google/gemma-3-12b-it": "96b6f1eccf38110c56df3a15bffe176da04bfd80",
    "google/gemma-3-27b-it": "005ad3404e59d6023443cb575daa05336842228a",
    "meta-llama/llama-3.2-3b-instruct": "0cb88a4f764b7a12671c53f0838cd831a0843b95",
    "meta-llama/llama-3.1-8b-instruct": "0e9e39f249a16976918f6564b8830bc894c89659",
    "meta-llama/llama-3.3-70b-instruct": "6f6073b423013f6a7d4d9f39144961bfbfbc386b",
    "qwen/qwen-2.5-7b-instruct": "a09a35458c702b33eeacc393d103063234e8bc28",
    "qwen/qwen3.5-9b": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
    "deepseek/deepseek-chat-v3-0324": "e9b33add76883f293d6bf61f6bd89b497e80e335",
    "deepseek/deepseek-chat-v3.1": "c0781d039fb7a1ba2abc4add0bdc293e92d2b8db",
    "deepseek/deepseek-v3.2": "a7e62ac04ecb2c0a54d736dc46601c5606cf10a6",
    "deepseek/deepseek-v4-flash": "60d8d70770c6776ff598c94bb586a859a38244f1",
}
EXPECTED_RELEASE_PERIODS = {
    "qwen/qwen-2.5-7b-instruct": ("2024-Q4", "2024-09-19", "2024-Q3", "https://qwenlm.github.io/blog/qwen2.5/"),
    "qwen/qwen3.5-9b": ("2026-Q1", "2026-02-27", "2026-Q1", "https://huggingface.co/Qwen/Qwen3.5-9B"),
    "deepseek/deepseek-chat-v3-0324": ("2025-Q1", "2025-03-24", "2025-Q1", "https://huggingface.co/deepseek-ai/DeepSeek-V3-0324"),
    "deepseek/deepseek-chat-v3.1": ("2025-Q3", "2025-08-21", "2025-Q3", "https://huggingface.co/deepseek-ai/DeepSeek-V3.1"),
    "deepseek/deepseek-v3.2": ("2025-Q4", "2025-12-01", "2025-Q4", "https://huggingface.co/deepseek-ai/DeepSeek-V3.2"),
    "deepseek/deepseek-v4-flash": ("2026-Q2", "2026-04-22", "2026-Q2", "https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash"),
}


class ValidationError(RuntimeError):
    """Raised when an evidence or release contract fails."""


CHECKS: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def passed(message: str) -> None:
    CHECKS.append(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def within_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def validate_canonical_bundle() -> pd.DataFrame:
    manifest_path = CANONICAL / "ARTIFACT_MANIFEST.csv"
    manifest = pd.read_csv(manifest_path, keep_default_na=False)
    check(list(manifest.columns) == ["path", "bytes", "sha256"], "canonical manifest schema drift")
    check(len(manifest) == 31, f"canonical manifest must contain 31 rows, found {len(manifest)}")
    check(manifest["path"].is_unique, "canonical manifest contains duplicate paths")

    expected_files = {"ARTIFACT_MANIFEST.csv"}
    for row in manifest.itertuples(index=False):
        relative = Path(row.path)
        check(not relative.is_absolute() and ".." not in relative.parts, f"unsafe canonical path: {row.path}")
        path = CANONICAL / relative
        expected_files.add(relative.as_posix())
        check(path.is_file(), f"missing canonical artifact: {row.path}")
        check(path.stat().st_size == int(row.bytes), f"canonical byte drift: {row.path}")
        check(sha256(path) == row.sha256, f"canonical SHA-256 drift: {row.path}")
    actual_files = {path.relative_to(CANONICAL).as_posix() for path in CANONICAL.rglob("*") if path.is_file()}
    check(actual_files == expected_files, "canonical bundle file set differs from its manifest")

    provenance = json.loads((CANONICAL / "BUILD_PROVENANCE.json").read_text())
    check(provenance.get("source_repository_head") == SOURCE_HEAD, "canonical source HEAD drift")
    check(provenance.get("canonical_evidence_source_sha") == CANONICAL_SHA, "canonical evidence SHA drift")
    check(re.fullmatch(r"[0-9a-f]{40}", CANONICAL_SHA) is not None, "canonical evidence SHA is not 40 lowercase hex")
    check(provenance.get("upstream_recorded_source_sha") == UPSTREAM_BAD_SHA, "upstream malformed SHA record drift")
    check(len(UPSTREAM_BAD_SHA) == 41, "upstream malformed SHA must remain a 41-character provenance record")
    for key in ("generator_sha256", "validator_sha256"):
        check(re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(key, ""))) is not None, f"invalid {key}")

    partition = pd.read_csv(CANONICAL / "figures" / "data" / "audit_partition.csv")
    observed_partition = partition.set_index("inclusion_class")["cells"].astype(int).to_dict()
    check(
        observed_partition == {"primary": 78, "sensitivity_only": 26, "multimodal_extension": 9, "excluded": 30},
        f"canonical partition drift: {observed_partition}",
    )
    check(sum(observed_partition.values()) == 143, "canonical partition no longer sums to 143")

    primary = pd.read_csv(CANONICAL / "figures" / "data" / "primary_confidence_intervals.csv")
    check(len(primary) == 78, f"primary table must contain 78 rows, found {len(primary)}")
    check(not primary.duplicated(["model", "task"]).any(), "primary table has duplicate model-task cells")
    check(set(primary["repo_commit_sha"]) == {SOURCE_HEAD}, "primary rows point to an unexpected repository HEAD")
    widths = primary["ci_upper"] - primary["ci_lower"]
    check(np.allclose(widths, primary["ci_width"], rtol=0, atol=1e-12), "primary CI width arithmetic drift")
    check(((primary["ci_lower"] <= primary["score"]) & (primary["score"] <= primary["ci_upper"])).all(), "score outside saved interval")
    wide = primary[primary["ci_width"] > 0.30]
    check(len(wide) == 18 and set(wide["task"]) == COMPARE_TASKS, "the 18 wide intervals are no longer confined to compare tasks")

    ledger = pd.read_csv(CANONICAL / "PAPER_REPO_EVIDENCE_LEDGER.csv")
    status = ledger["comparability_status"].value_counts().to_dict()
    check(len(ledger) == 37, f"canonical paper ledger must have 37 rows, found {len(ledger)}")
    check(status == {"approximate": 17, "unavailable": 16, "proxy-only": 4}, f"canonical paper crosswalk drift: {status}")
    passed("canonical bundle: 31 manifested artifacts; partition 78/26/9/30; 18 wide intervals; paper ledger 17/4/16/0")
    return primary


def apply_verified_release_periods(results: pd.DataFrame) -> pd.DataFrame:
    periods = pd.read_csv(RELEASE_PERIODS, keep_default_na=False)
    expected_columns = [
        "model",
        "snapshot_release_period",
        "source_event_date",
        "verified_release_period",
        "source_url",
        "source_revision",
        "source_basis",
        "checked_on",
    ]
    check(list(periods.columns) == expected_columns, "release-period source schema drift")
    check(len(periods) == 6 and periods["model"].is_unique, "release-period source must contain six unique release-path models")
    check(set(periods["model"]) == set(EXPECTED_RELEASE_PERIODS), "release-period source model set drift")
    check(periods["snapshot_release_period"].str.fullmatch(r"\d{4}-Q[1-4]").all(), "snapshot release-period format drift")
    check(periods["verified_release_period"].str.fullmatch(r"\d{4}-Q[1-4]").all(), "verified release-period format drift")
    dates = pd.to_datetime(periods["source_event_date"], format="%Y-%m-%d", errors="coerce")
    check(dates.notna().all(), "release-period source event date is not ISO formatted")
    derived = dates.map(lambda value: f"{value.year}-Q{(value.month - 1) // 3 + 1}")
    check(derived.equals(periods["verified_release_period"]), "verified release date and quarter disagree")
    check(periods["checked_on"].eq("2026-09-04").all(), "release-period source check date drift")

    corrected = results.copy()
    for row in periods.itertuples(index=False):
        snapshot_period, event_date, verified_period, source_url = EXPECTED_RELEASE_PERIODS[row.model]
        check(row.snapshot_release_period == snapshot_period, f"snapshot period drift for {row.model}")
        check(row.source_event_date == event_date, f"release-period source event date drift for {row.model}")
        check(row.verified_release_period == verified_period, f"verified release period drift for {row.model}")
        check(row.source_url == source_url, f"release source URL drift for {row.model}")
        if row.model == "qwen/qwen-2.5-7b-instruct":
            check(row.source_revision == "" and row.source_basis == "official Qwen launch post", "Qwen2.5 release source boundary drift")
        else:
            check(row.source_revision == EXPECTED_SOURCE_REVISIONS[row.model], f"release source revision drift for {row.model}")
            check(row.source_basis == "official model repository creation date", f"release source basis drift for {row.model}")
        mask = corrected["model"] == row.model
        check(mask.any(), f"release-period model absent from selected snapshot: {row.model}")
        check(set(corrected.loc[mask, "release_period"]) == {snapshot_period}, f"selected snapshot period drift for {row.model}")
        corrected.loc[mask, "release_period"] = verified_period

    changed = periods[periods["snapshot_release_period"] != periods["verified_release_period"]]
    check(
        changed[["model", "verified_release_period"]].to_records(index=False).tolist()
        == [("qwen/qwen-2.5-7b-instruct", "2024-Q3")],
        "documented release-period corrections drift",
    )
    passed("release metadata: six release-path models sourced; Qwen2.5 corrected from snapshot Q4 to official 2024-Q3")
    return corrected


def validate_selected_sources(source_repo: Path | None) -> pd.DataFrame:
    manifest = pd.read_csv(SELECTED / "SOURCE_MANIFEST.csv", keep_default_na=False)
    check(len(manifest) == 2 and manifest["path"].is_unique, "selected source manifest must contain two unique rows")
    check(set(manifest["path"]) == {"model_grid.csv", "result_summary.csv"}, "selected source manifest file set drift")
    check(set(manifest["source_repository_head"]) == {SOURCE_HEAD}, "selected source HEAD drift")
    check(set(manifest["evidence_class"]) == {"exploratory aggregate"}, "selected source evidence class drift")
    for row in manifest.itertuples(index=False):
        path = SELECTED / row.path
        check(path.is_file(), f"missing selected source: {row.path}")
        check(sha256(path) == row.sha256, f"selected source hash drift: {row.path}")
        frame = pd.read_csv(path)
        check(frame.shape == (int(row.rows), int(row.columns)), f"selected source shape drift: {row.path}")
        if source_repo is not None:
            original = source_repo / row.source_repository_path
            check(original.is_file(), f"source-repo file missing: {row.source_repository_path}")
            check(sha256(original) == row.sha256, f"selected snapshot differs from source repo: {row.path}")

    results = pd.read_csv(SELECTED / "result_summary.csv")
    status = results["run_status"].value_counts().to_dict()
    check(status == {"success": 102, "error": 13, "cancelled": 4}, f"selected run status drift: {status}")
    success = results[results["run_status"] == "success"]
    check(success["score"].notna().all(), "a successful selected-grid row has no score")
    check(success["score"].between(0, 1).all(), "a successful selected-grid score lies outside [0, 1]")
    resolved_logs = sum((ROOT / str(path)).is_file() for path in success["log_path"])
    check(resolved_logs == 0, f"expected zero bundled selected-grid raw logs, found {resolved_logs}")

    qwen_tokens = int(results.loc[results["model"] == "qwen/qwen3-32b", "reasoning_tokens_actual"].fillna(0).sum())
    deepseek_tokens = int(results.loc[results["model"] == "deepseek/deepseek-v4-flash", "reasoning_tokens_actual"].fillna(0).sum())
    check(qwen_tokens == 107375, f"Qwen3-32B reasoning-token total drift: {qwen_tokens}")
    check(deepseek_tokens == 1171189, f"DeepSeek V4 reasoning-token total drift: {deepseek_tokens}")
    passed("selected grid: 17-model metadata, 119 result rows, statuses 102/13/4, 0 bundled raw logs, token-drift totals confirmed")
    return apply_verified_release_periods(results)


def intervals_all_overlap(frame: pd.DataFrame) -> tuple[int, int]:
    overlapping = 0
    pairs = 0
    for left, right in itertools.combinations(frame.itertuples(index=False), 2):
        pairs += 1
        if max(left.ci_lower, right.ci_lower) <= min(left.ci_upper, right.ci_upper):
            overlapping += 1
    return overlapping, pairs


def validate_parameter_metadata() -> pd.DataFrame:
    parameters = pd.read_csv(PARAMETERS, keep_default_na=False)
    expected_columns = [
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
    ]
    check(list(parameters.columns) == expected_columns, "model-parameter source schema drift")
    check(len(parameters) == 15 and parameters["model"].is_unique, "model-parameter source must contain 15 unique models")
    check(set(parameters["model"]) == set(EXPECTED_PARAMETER_FACTS), "model-parameter source model set drift")
    check(parameters["source_url"].is_unique, "model-parameter source URLs must be unique")
    check(parameters["source_revision"].str.fullmatch(r"[0-9a-f]{40}").all(), "model-card revision is not a 40-character commit SHA")
    check(parameters["run_identity_scope"].eq(RUN_IDENTITY_SCOPE).all(), "served-model identity boundary drift")
    check(parameters["checked_on"].str.fullmatch(r"\d{4}-\d{2}-\d{2}").all(), "parameter source check date is not ISO formatted")

    for row in parameters.itertuples(index=False):
        display, total, active, label, architecture, source_url = EXPECTED_PARAMETER_FACTS[row.model]
        observed_active = None if row.activated_parameters_b == "" else float(row.activated_parameters_b)
        check(row.model_display == display, f"model display drift for {row.model}")
        check(np.isclose(float(row.total_parameters_b), total, rtol=0, atol=1e-12), f"total parameter count drift for {row.model}")
        check(
            (active is None and observed_active is None)
            or (active is not None and observed_active is not None and np.isclose(observed_active, active, rtol=0, atol=1e-12)),
            f"active parameter count drift for {row.model}",
        )
        check(row.parameter_label == label, f"parameter label drift for {row.model}")
        check(row.architecture == architecture, f"architecture label drift for {row.model}")
        check(row.source_url == source_url, f"official model-card URL drift for {row.model}")
        check(row.source_revision == EXPECTED_SOURCE_REVISIONS[row.model], f"official model-card revision drift for {row.model}")
        expected_basis = (
            "vendor-published main-model count; auxiliary/MTP weights excluded"
            if row.model.startswith("deepseek/")
            else "published named-model count"
        )
        check(row.parameter_basis == expected_basis, f"parameter-count basis drift for {row.model}")
        recomputed_label = (
            f"{float(row.total_parameters_b):g}B main model / {observed_active:g}B active"
            if row.model.startswith("deepseek/")
            else f"{float(row.total_parameters_b):g}B total / {observed_active:g}B active"
            if architecture == "MoE"
            else f"{float(row.total_parameters_b):g}B total"
        )
        check(row.parameter_label == recomputed_label, f"parameter label does not recompute from numeric fields for {row.model}")

    numeric = parameters.copy()
    numeric["total_parameters_b"] = pd.to_numeric(numeric["total_parameters_b"], errors="raise")
    numeric["activated_parameters_b"] = pd.to_numeric(
        numeric["activated_parameters_b"].replace("", np.nan), errors="raise"
    )
    moe = numeric["architecture"] == "MoE"
    check(numeric.loc[moe, "activated_parameters_b"].notna().all(), "a MoE model lacks its published active-parameter count")
    check((numeric.loc[moe, "activated_parameters_b"] <= numeric.loc[moe, "total_parameters_b"]).all(), "a MoE active-parameter count exceeds its total count")
    check(numeric.loc[~moe, "activated_parameters_b"].isna().all(), "a dense model unexpectedly has an active-parameter count")
    passed("model parameters: 15 official model-card revisions pinned; published count basis and served-identity boundary retained")
    return numeric


def validate_derived_results(primary: pd.DataFrame, selected: pd.DataFrame, parameters: pd.DataFrame) -> None:
    common = pd.read_csv(RESULT_DATA / "common_roster_primary.csv")
    check(len(common) == 40 and not common.duplicated(["model", "task"]).any(), "common roster must be 40 unique cells")
    check(set(common["model"]) == COMMON_MODELS, "common roster model set drift")
    check(common.groupby("model")["task"].nunique().eq(8).all(), "a common-roster model lacks an expected task")
    expected_common = primary[primary["model"].isin(COMMON_MODELS)].copy()
    key = ["model", "task"]
    merged = common.merge(expected_common, on=key, suffixes=("_derived", "_canonical"), validate="one_to_one")
    for column in ("score", "ci_lower", "ci_upper", "ci_width", "n_scored"):
        check(
            np.allclose(merged[f"{column}_derived"], merged[f"{column}_canonical"], rtol=0, atol=1e-12),
            f"common-roster {column} differs from canonical source",
        )
    observed_metrics = common.groupby("task")["metric_semantics"].first().to_dict()
    check(observed_metrics == SCORE_METRICS, f"task metric mapping drift: {observed_metrics}")
    leader_sets = []
    for _, group in common.groupby("task"):
        leader_sets.append(set(group.loc[np.isclose(group["score"], group["score"].max()), "model"]))
    check(not set.intersection(*leader_sets), "one model is unexpectedly the point-estimate leader on all tasks")
    for task, expected_pairs in (("moralbench_mfq_compare", 28), ("moralbench_vignette_compare", 45)):
        overlap, pairs = intervals_all_overlap(primary[primary["task"] == task])
        check((overlap, pairs) == (expected_pairs, expected_pairs), f"{task} marginal overlap count drift: {overlap}/{pairs}")

    precision = pd.read_csv(RESULT_DATA / "task_precision.csv")
    canonical_precision = pd.read_csv(CANONICAL / "figures" / "data" / "task_diagnostic_spread.csv")
    check(list(precision.columns) == list(canonical_precision.columns), "task precision schema drift")
    left = precision.sort_values("task").reset_index(drop=True)
    right = canonical_precision.sort_values("task").reset_index(drop=True)
    check(left.equals(right), "task precision table differs from canonical source table")

    size_points = pd.read_csv(RESULT_DATA / "size_task_points.csv")
    size_summary = pd.read_csv(RESULT_DATA / "size_path_summary.csv")
    check(len(size_points) == 45 and len(size_summary) == 15, "size layer must contain 45 points and 15 complete paths")
    check((size_points["run_status"] == "success").all() and size_points["score"].notna().all(), "size plot contains a failed or missing score")
    check(set(size_points["evidence_status"]) == {"exploratory aggregate; no CI or raw-log replay"}, "size evidence label drift")
    check(set(size_summary["source_repository_head"]) == {SOURCE_HEAD}, "size provenance HEAD drift")
    directions: list[str] = []
    for row in size_summary.itertuples(index=False):
        values = np.array([row.small, row.medium, row.large], dtype=float)
        direction = "rising" if np.all(np.diff(values) > 0) else "falling" if np.all(np.diff(values) < 0) else "mixed"
        check(direction == row.direction, f"size direction drift for {row.family}/{row.task}")
        directions.append(direction)
    check(pd.Series(directions).value_counts().to_dict() == {"mixed": 9, "rising": 5, "falling": 1}, "size direction totals drift")

    release = pd.read_csv(RESULT_DATA / "release_period_task_points.csv")
    release_summary = pd.read_csv(RESULT_DATA / "release_path_summary.csv")
    check(len(release) == 35, f"release layer must contain 35 points, found {len(release)}")
    check(len(release_summary) == 12, f"release summary must contain 12 paths, found {len(release_summary)}")
    check(release.groupby(["family", "task"]).ngroups == 12, "release layer must contain 12 family-task paths")
    check(set(release["family"]) == {"Qwen", "DeepSeek"}, "release family set drift")
    check(not release.duplicated(["family", "task", "release_period"]).any(), "duplicate family-task-quarter in release layer")
    check((release["run_status"] == "success").all() and release["score"].notna().all(), "release plot contains a failed or missing score")
    check(set(release["evidence_status"]) == {"exploratory aggregate; no CI or raw-log replay"}, "release evidence label drift")
    check(set(release["source_path"]) == {"evidence/source-results/result_summary.csv"}, "release score source path drift")
    check(
        set(release["release_period_source_path"]) == {RELEASE_PERIOD_SOURCE_PATH},
        "release-period source path omits the verified metadata overlay",
    )
    run_dates = release["log_path"].str.extract(r"/(2026-05-(?:28|29))T", expand=False)
    check(run_dates.notna().all() and set(run_dates) == {"2026-05-28", "2026-05-29"}, "release rows are not confined to the recorded two-day evaluation window")

    expected_size_candidates = selected[
        (selected["grid"] == "within-family scaling")
        & (selected["run_status"] == "success")
        & (selected["benchmark"] != "CCD-Bench")
    ].copy()
    expected_size_candidates["_tier"] = expected_size_candidates["size_tier"].str.extract(r"^([SML])", expand=False)
    expected_size_groups = []
    for _, group in expected_size_candidates.groupby(["family", "task"], sort=True):
        if len(group) == 3 and set(group["_tier"]) == {"S", "M", "L"}:
            expected_size_groups.append(group.drop(columns="_tier"))
    expected_size_source = pd.concat(expected_size_groups, ignore_index=True)

    expected_release_candidates = selected[
        (selected["grid"] == "time scaling")
        & (selected["run_status"] == "success")
        & (selected["benchmark"] != "CCD-Bench")
    ].copy()
    expected_release_groups = [
        group
        for _, group in expected_release_candidates.groupby(["family", "task"], sort=True)
        if group["release_period"].nunique() >= 2
    ]
    expected_release_source = pd.concat(expected_release_groups, ignore_index=True)

    point_frames = {
        "size": (size_points, expected_size_source, 45),
        "release": (release, expected_release_source, 35),
    }
    lineage_keys = ["model", "task", "grid", "benchmark"]
    metadata_columns = [
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
    ]
    for name, (frame, independently_selected, expected_rows) in point_frames.items():
        check(not frame.duplicated(lineage_keys).any(), f"{name} points contain a duplicate source key")
        observed_source = frame[selected.columns].sort_values(lineage_keys).reset_index(drop=True).convert_dtypes()
        expected_source = independently_selected[selected.columns].sort_values(lineage_keys).reset_index(drop=True).convert_dtypes()
        check(len(expected_source) == expected_rows and observed_source.equals(expected_source), f"{name} points differ from selected source rows")

        joined = frame.merge(parameters, on="model", how="left", suffixes=("_point", "_source"), validate="many_to_one")
        check(len(joined) == expected_rows, f"{name} parameter join changed the point count")
        for column in metadata_columns:
            point_column = joined[f"{column}_point"]
            source_column = joined[f"{column}_source"]
            if column in {"total_parameters_b", "activated_parameters_b"}:
                check(
                    np.allclose(
                        pd.to_numeric(point_column, errors="coerce"),
                        pd.to_numeric(source_column, errors="coerce"),
                        rtol=0,
                        atol=1e-12,
                        equal_nan=True,
                    ),
                    f"{name} {column} differs from model-parameter source",
                )
            else:
                check(
                    point_column.astype("string").fillna("").equals(source_column.astype("string").fillna("")),
                    f"{name} {column} differs from model-parameter source",
                )
        expected_labels = frame["model_display"] + "\n" + frame["parameter_label"]
        check(frame["point_label"].equals(expected_labels), f"{name} compound point labels drift from model plus parameter count")

    expected_release_with_parameters = expected_release_source.merge(parameters, on="model", how="left", validate="many_to_one")
    expected_summary_rows: list[dict[str, object]] = []
    for (family, task), group in expected_release_with_parameters.groupby(["family", "task"], sort=True):
        ordered = group.sort_values("release_period")
        first = ordered.iloc[0]
        last = ordered.iloc[-1]
        values = ordered["score"].to_numpy(dtype=float)
        deltas = np.diff(values)
        endpoint_delta = float(last.score - first.score)
        expected_summary_rows.append(
            {
                "family": family,
                "task": task,
                "task_label": SCALING_TASK_LABELS[task][0],
                "metric": SCALING_TASK_LABELS[task][1],
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
                "endpoint_direction": "higher" if endpoint_delta > 0 else "lower" if endpoint_delta < 0 else "unchanged",
                "internal_reversal": len(values) > 2 and not (np.all(deltas > 0) or np.all(deltas < 0)),
                "observed_points": len(ordered),
                "evidence_status": "exploratory aggregate; no CI or raw-log replay",
                "source_repository_head": SOURCE_HEAD,
                "source_path": "evidence/source-results/result_summary.csv",
                "release_period_source_path": RELEASE_PERIOD_SOURCE_PATH,
            }
        )
    expected_release_summary = pd.DataFrame(expected_summary_rows)
    check(list(release_summary.columns) == list(expected_release_summary.columns), "release summary schema drift")
    observed_summary = release_summary.sort_values(["family", "task"]).reset_index(drop=True)
    expected_release_summary = expected_release_summary.sort_values(["family", "task"]).reset_index(drop=True)
    for column in ("first_score", "last_score", "endpoint_delta", "observed_points"):
        check(
            np.allclose(observed_summary[column], expected_release_summary[column], rtol=0, atol=1e-12),
            f"release summary {column} differs from independently selected source rows",
        )
    for column in [name for name in release_summary.columns if name not in {"first_score", "last_score", "endpoint_delta", "observed_points"}]:
        check(
            observed_summary[column].astype("string").equals(expected_release_summary[column].astype("string")),
            f"release summary {column} differs from independently selected source rows",
        )
    direction_counts = release_summary.groupby(["family", "endpoint_direction"]).size().to_dict()
    check(
        direction_counts == {("DeepSeek", "higher"): 3, ("DeepSeek", "lower"): 3, ("Qwen", "higher"): 5, ("Qwen", "lower"): 1},
        f"release endpoint-direction totals drift: {direction_counts}",
    )
    check(int(release_summary["internal_reversal"].sum()) == 5, "release internal-reversal count drift")

    expected_size_counts = {model: count for model, count in [
        ("qwen/qwen3-8b", 4),
        ("qwen/qwen3-32b", 4),
        ("qwen/qwen3-235b-a22b-2507", 4),
        ("google/gemma-3-4b-it", 5),
        ("google/gemma-3-12b-it", 5),
        ("google/gemma-3-27b-it", 5),
        ("meta-llama/llama-3.2-3b-instruct", 6),
        ("meta-llama/llama-3.1-8b-instruct", 6),
        ("meta-llama/llama-3.3-70b-instruct", 6),
    ]}
    expected_release_counts = {
        "qwen/qwen-2.5-7b-instruct": 6,
        "qwen/qwen3.5-9b": 6,
        "deepseek/deepseek-chat-v3-0324": 6,
        "deepseek/deepseek-chat-v3.1": 6,
        "deepseek/deepseek-v3.2": 6,
        "deepseek/deepseek-v4-flash": 5,
    }
    check(set(size_points["model"]) | set(release["model"]) == set(parameters["model"]), "plotted model union differs from parameter ledger")
    check(size_points["model"].value_counts().to_dict() == expected_size_counts, "size point-label multiplicities drift")
    check(release["model"].value_counts().to_dict() == expected_release_counts, "release point-label multiplicities drift")
    complete_tiers = size_points.groupby(["family", "task"])["tier"].agg(lambda values: (len(values), set(values)))
    check(all(length == 3 and tiers == {"S", "M", "L"} for length, tiers in complete_tiers), "a size path is not an exact S/M/L triplet")
    size_order = (
        parameters[parameters["model"].isin(expected_size_counts)][["model", "total_parameters_b"]]
        .sort_values(["total_parameters_b", "model"], kind="stable")
        .reset_index(drop=True)
    )
    expected_positions = dict(zip(size_order["model"], range(len(size_order))))
    expected_row_positions = size_points["model"].map(expected_positions)
    check(
        np.array_equal(size_points["size_plot_position"].astype(int).to_numpy(), expected_row_positions.astype(int).to_numpy()),
        "a size point is assigned to the wrong parameter-ordered x position",
    )
    check(size_points.groupby("model")["size_plot_position"].nunique().eq(1).all(), "one size model appears at multiple x positions")
    check(set(size_points["size_plot_position"].astype(int)) == set(range(9)), "size x positions must be contiguous 0 through 8")
    for _, group in size_points.groupby(["family", "task"]):
        tier_order = group.set_index("tier").loc[["S", "M", "L"], "total_parameters_b"].to_numpy(dtype=float)
        check(np.all(np.diff(tier_order) > 0), "a size S/M/L tier does not increase in published total parameters")

    takeaways = pd.read_csv(RESULT_DATA / "research_question_takeaways.csv", keep_default_na=False)
    check(len(takeaways) == 5, "research-question table must contain five rows")
    check(not takeaways["evidence_status"].str.contains(r"^verified", case=False, regex=True).any(), "takeaway overclaims verification")
    for source in takeaways["source"]:
        check((ROOT / source).is_file(), f"takeaway source does not resolve: {source}")
    precision_takeaway = takeaways.loc[
        takeaways["research_question"] == "Can the two comparison tests tell us which model leads?"
    ]
    check(len(precision_takeaway) == 1, "precision takeaway row is missing or duplicated")
    check(
        precision_takeaway.iloc[0]["source"]
        == "evidence/canonical-audit/figures/data/primary_confidence_intervals.csv",
        "wide-interval claim must cite the cell-level primary interval table",
    )
    joined_answers = " ".join(takeaways["answer"])
    for phrase in (
        "18 intervals",
        "4 of 12",
        "7 change direction",
        "5 of 15 rising",
        "9 changing direction",
        "Qwen has 3 higher and 1 lower",
        "DeepSeek has 2 higher and 2 lower",
        "full selected-grid counts are 5/1 and 3/3",
        "May 28–29, 2026",
    ):
        check(phrase in joined_answers, f"takeaway table is missing expected result: {phrase}")
    passed("derived results: 40 common cells; 28/28 and 45/45 compare overlaps; all 80 plotted rows and 12 release summaries match source and parameter metadata")


REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
P_NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
C_NS = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
S_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def check_text_hygiene(text: str, label: str) -> None:
    mac_user_root = "/" + "Users/"
    file_scheme = "file" + "://"
    check(
        mac_user_root not in text
        and file_scheme not in text
        and not re.search(r"[A-Za-z]:\\Users\\", text),
        f"private absolute path in {label}",
    )
    for secret_label, pattern in SECRET_PATTERNS.items():
        check(pattern.search(text) is None, f"possible {secret_label} in {label}")


def resolve_package_target(source_part: str, target: str) -> str:
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    return posixpath.normpath(posixpath.join(posixpath.dirname(source_part), target))


def relationship_part(source_part: str) -> str:
    parent, name = posixpath.split(source_part)
    return posixpath.join(parent, "_rels", f"{name}.rels")


def relationship_source_part(rels_part: str) -> str:
    if rels_part == "_rels/.rels":
        return ""
    part = PurePosixPath(rels_part)
    check(part.parent.name == "_rels" and part.name.endswith(".rels"), f"invalid relationship part path: {rels_part}")
    return (part.parent.parent / part.name.removesuffix(".rels")).as_posix()


def validate_package_graph(archive: ZipFile, label: str) -> None:
    members = archive.namelist()
    check(len(members) == len(set(members)), f"{label} contains duplicate ZIP part names")
    names = set(members)
    for rels_name in sorted(name for name in names if name.endswith(".rels")):
        source_part = relationship_source_part(rels_name)
        check(not source_part or source_part in names, f"{label} relationship source is missing: {source_part}")
        root = ET.fromstring(archive.read(rels_name))
        relationships = root.findall(f"{REL_NS}Relationship")
        relationship_ids = [rel.attrib.get("Id", "") for rel in relationships]
        check(all(relationship_ids) and len(relationship_ids) == len(set(relationship_ids)), f"{label} has missing or duplicate relationship IDs in {rels_name}")
        for rel in relationships:
            target = rel.attrib.get("Target", "")
            check(rel.attrib.get("Type", "") and target, f"{label} has an incomplete relationship in {rels_name}")
            parsed = urllib.parse.urlsplit(target)
            check(
                not parsed.scheme
                and not parsed.netloc
                and not parsed.query
                and not parsed.fragment
                and "\\" not in target
                and "\x00" not in target,
                f"{label} has an unsafe relationship target in {rels_name}",
            )
            check(rel.attrib.get("TargetMode", "").lower() != "external", f"{label} contains an external relationship in {rels_name}")
            resolved = resolve_package_target(source_part, urllib.parse.unquote(parsed.path))
            check(
                resolved not in {"", ".", ".."}
                and not resolved.startswith("../")
                and not posixpath.isabs(resolved),
                f"{label} relationship escapes the package in {rels_name}: {target}",
            )
            check(resolved in names, f"{label} relationship target is missing: {resolved}")


def package_xml_text(archive: ZipFile) -> str:
    text: list[str] = []
    for name in sorted(member for member in archive.namelist() if member.endswith((".xml", ".rels"))):
        root = ET.fromstring(archive.read(name))
        for node in root.iter():
            if node.text:
                text.append(node.text)
            text.extend(node.attrib.values())
    return "\n".join(text)


def package_relationships(archive: ZipFile, source_part: str) -> list[dict[str, str]]:
    rels_name = relationship_part(source_part)
    check(rels_name in archive.namelist(), f"slide deck relationship part is missing: {rels_name}")
    root = ET.fromstring(archive.read(rels_name))
    relationships = []
    for rel in root.findall(f"{REL_NS}Relationship"):
        relationships.append({
            "id": rel.attrib.get("Id", ""),
            "type": rel.attrib.get("Type", ""),
            "target": rel.attrib.get("Target", ""),
            "target_mode": rel.attrib.get("TargetMode", ""),
            "resolved": resolve_package_target(source_part, rel.attrib.get("Target", "")),
        })
    return relationships


def cell_text(cell: ET.Element) -> str:
    paragraphs = [
        "".join(node.text or "" for node in paragraph.iter(f"{A_NS}t"))
        for paragraph in cell.iter(f"{A_NS}p")
    ]
    if paragraphs:
        return "\n".join(paragraphs)
    return "".join(node.text or "" for node in cell.iter(f"{A_NS}t"))


def slide_tables(root: ET.Element) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    for table in root.iter(f"{A_NS}tbl"):
        rows: list[list[str]] = []
        for row in table.findall(f"{A_NS}tr"):
            rows.append([cell_text(cell) for cell in row.findall(f"{A_NS}tc")])
        tables.append(rows)
    return tables


def chart_cache(archive: ZipFile, chart_part: str) -> list[dict[str, object]]:
    root = ET.fromstring(archive.read(chart_part))
    series: list[dict[str, object]] = []
    for item in root.iter(f"{C_NS}ser"):
        tx = item.find(f"{C_NS}tx")
        name_node = next(tx.iter(f"{C_NS}v"), None) if tx is not None else None
        category_parent = item.find(f"{C_NS}cat")
        value_parent = item.find(f"{C_NS}val")
        check(name_node is not None and category_parent is not None and value_parent is not None, f"incomplete chart series in {chart_part}")

        categories = sorted(
            (
                int(point.attrib["idx"]),
                next(point.iter(f"{C_NS}v")).text or "",
            )
            for point in category_parent.iter(f"{C_NS}pt")
        )
        values = sorted(
            (
                int(point.attrib["idx"]),
                float(next(point.iter(f"{C_NS}v")).text or "nan"),
            )
            for point in value_parent.iter(f"{C_NS}pt")
        )
        check([idx for idx, _ in categories] == list(range(len(categories))), f"non-contiguous chart categories in {chart_part}")
        check([idx for idx, _ in values] == list(range(len(values))), f"non-contiguous chart values in {chart_part}")
        check(len(categories) == len(values), f"chart category/value length mismatch in {chart_part}")
        series.append({
            "name": name_node.text or "",
            "categories": [value for _, value in categories],
            "values": [value for _, value in values],
        })
    check(series, f"no cached native chart series found in {chart_part}")
    return series


def xlsx_column_name(index: int) -> str:
    check(index >= 0, "worksheet column index cannot be negative")
    name = ""
    value = index + 1
    while value:
        value, remainder = divmod(value - 1, 26)
        name = chr(ord("A") + remainder) + name
    return name


def validate_chart_formula_ranges(
    chart_root: ET.Element,
    series: list[dict[str, object]],
    chart_part: str,
) -> None:
    xml_series = list(chart_root.iter(f"{C_NS}ser"))
    check(len(xml_series) == len(series), f"chart series/formula count drift in {chart_part}")
    for series_index, (item, cached) in enumerate(zip(xml_series, series)):
        row_count = len(cached["categories"])
        category_parent = item.find(f"{C_NS}cat")
        value_parent = item.find(f"{C_NS}val")
        check(category_parent is not None and value_parent is not None, f"chart series lacks category or value formula in {chart_part}")
        category_formulas = [node.text or "" for node in category_parent.iter(f"{C_NS}f")]
        value_formulas = [node.text or "" for node in value_parent.iter(f"{C_NS}f")]
        category_column = xlsx_column_name(series_index * 2)
        value_column = xlsx_column_name(series_index * 2 + 1)
        expected_category = f"'Chart Data'!${category_column}$2:${category_column}${row_count + 1}"
        expected_values = f"'Chart Data'!${value_column}$2:${value_column}${row_count + 1}"
        check(category_formulas == [expected_category], f"chart category formula does not point to its cached workbook cells in {chart_part}")
        check(value_formulas == [expected_values], f"chart value formula does not point to its cached workbook cells in {chart_part}")


def xlsx_matrix(blob: bytes) -> list[list[str | float]]:
    with ZipFile(io.BytesIO(blob)) as workbook:
        validate_package_graph(workbook, "embedded chart workbook")
        check_text_hygiene(package_xml_text(workbook), "embedded chart workbook")
        workbook_part = "xl/workbook.xml"
        workbook_root = ET.fromstring(workbook.read(workbook_part))
        sheets = workbook_root.findall(f".//{S_NS}sheet")
        check(len(sheets) == 1, f"embedded chart workbook must contain exactly one worksheet, found {len(sheets)}")
        first_sheet = sheets[0]
        check(first_sheet.attrib.get("name") == "Chart Data", "embedded chart workbook worksheet must be named 'Chart Data'")
        relationship_id = first_sheet.attrib.get(R_ID, "")
        sheet_rel = next(
            (rel for rel in package_relationships(workbook, workbook_part) if rel["id"] == relationship_id),
            None,
        )
        check(
            sheet_rel is not None
            and sheet_rel["type"].endswith("/worksheet")
            and sheet_rel["resolved"] in workbook.namelist(),
            "embedded chart worksheet relationship is broken",
        )

        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            shared_root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
            shared_strings = ["".join(node.text or "" for node in item.iter(f"{S_NS}t")) for item in shared_root.findall(f"{S_NS}si")]

        sheet_root = ET.fromstring(workbook.read(sheet_rel["resolved"]))
        matrix: list[list[str | float]] = []
        for row in sheet_root.iter(f"{S_NS}row"):
            observed: dict[int, str | float] = {}
            for cell in row.findall(f"{S_NS}c"):
                reference = cell.attrib.get("r", "")
                letters = re.match(r"[A-Z]+", reference)
                check(letters is not None, f"invalid worksheet cell reference: {reference}")
                column = 0
                for character in letters.group(0):
                    column = column * 26 + ord(character) - ord("A") + 1
                column -= 1
                cell_type = cell.attrib.get("t", "")
                value_node = cell.find(f"{S_NS}v")
                if cell_type == "inlineStr":
                    value: str | float = "".join(node.text or "" for node in cell.iter(f"{S_NS}t"))
                elif cell_type == "s":
                    check(value_node is not None, f"shared-string cell has no value: {reference}")
                    value = shared_strings[int(value_node.text or "0")]
                elif value_node is None or value_node.text is None:
                    value = ""
                else:
                    value = float(value_node.text)
                observed[column] = value
            width = max(observed, default=-1) + 1
            matrix.append([observed.get(column, "") for column in range(width)])
        return matrix


def workbook_matrix_from_chart(series: list[dict[str, object]]) -> list[list[str | float]]:
    width = len(series) * 2
    rows: list[list[str | float]] = [[] for _ in range(len(series[0]["categories"]) + 1)]
    for item in series:
        categories = item["categories"]
        values = item["values"]
        check(len(categories) + 1 == len(rows), "native chart series use different category counts")
        rows[0].extend(["Category", str(item["name"])])
        for index, (category, value) in enumerate(zip(categories, values), start=1):
            rows[index].extend([str(category), float(value)])
    check(all(len(row) == width for row in rows), "embedded chart workbook matrix is ragged")
    return rows


def check_matrix_equal(observed: list[list[str | float]], expected: list[list[str | float]], label: str) -> None:
    check(len(observed) == len(expected), f"{label} row count drift")
    for row_index, (left, right) in enumerate(zip(observed, expected), start=1):
        check(len(left) == len(right), f"{label} column count drift on row {row_index}")
        for column_index, (left_value, right_value) in enumerate(zip(left, right), start=1):
            if isinstance(right_value, float):
                check(isinstance(left_value, float) and np.isclose(left_value, right_value, rtol=0, atol=1e-12), f"{label} numeric drift at row {row_index}, column {column_index}")
            else:
                check(str(left_value) == str(right_value), f"{label} text drift at row {row_index}, column {column_index}")


def check_chart_equal(
    observed: list[dict[str, object]],
    expected: list[dict[str, object]],
    label: str,
) -> None:
    check(len(observed) == len(expected), f"{label} series count drift")
    for observed_series, expected_series in zip(observed, expected):
        check(observed_series["name"] == expected_series["name"], f"{label} series-name drift")
        check(observed_series["categories"] == expected_series["categories"], f"{label} category drift")
        left = np.asarray(observed_series["values"], dtype=float)
        right = np.asarray(expected_series["values"], dtype=float)
        check(left.shape == right.shape and np.allclose(left, right, rtol=0, atol=1e-12), f"{label} value drift")


def validate_slide_deck(slide_deck: Path = SLIDE_DECK) -> None:
    check(slide_deck.is_file(), f"research-lead slide deck is missing: {slide_deck}")
    with ZipFile(slide_deck) as archive:
        validate_package_graph(archive, "slide deck")
        check_text_hygiene(package_xml_text(archive), "slide deck package text")
        names = set(archive.namelist())
        presentation_root = ET.fromstring(archive.read("ppt/presentation.xml"))
        slide_size = presentation_root.find(f"{P_NS}sldSz")
        check(slide_size is not None, "slide deck has no declared page size")
        check(
            (slide_size.attrib.get("cx"), slide_size.attrib.get("cy")) == ("12192000", "6858000"),
            "slide deck is not the intended 16:9 1280 x 720 canvas",
        )
        presentation_relationships = {
            rel["id"]: rel for rel in package_relationships(archive, "ppt/presentation.xml")
        }
        slide_parts: list[str] = []
        for slide_id in presentation_root.findall(f".//{P_NS}sldId"):
            relationship_id = slide_id.attrib.get(R_ID, "")
            relationship = presentation_relationships.get(relationship_id)
            check(relationship is not None and relationship["type"].endswith("/slide"), "presentation slide order contains a broken relationship")
            slide_parts.append(relationship["resolved"])
        check(len(slide_parts) == len(set(slide_parts)) == 8, "slide deck must contain exactly 8 uniquely related slides")

        chart_parts_by_slide: dict[int, str] = {}
        workbook_parts: set[str] = set()
        notes_parts: list[str] = []
        slide_roots: dict[int, ET.Element] = {}
        for slide_number, slide_part in enumerate(slide_parts, start=1):
            check(slide_part in names, f"slide {slide_number} package part is missing")
            root = ET.fromstring(archive.read(slide_part))
            slide_roots[slide_number] = root
            relationships = package_relationships(archive, slide_part)
            relationships_by_id = {rel["id"]: rel for rel in relationships}
            chart_rels = []
            for chart_reference in root.iter(f"{C_NS}chart"):
                relationship = relationships_by_id.get(chart_reference.attrib.get(R_ID, ""))
                check(relationship is not None and relationship["type"].endswith("/chart"), f"slide {slide_number} has a broken native-chart relationship")
                chart_rels.append(relationship)
            note_rels = [rel for rel in relationships if rel["type"].endswith("/notesSlide")]
            check(len(note_rels) == 1 and note_rels[0]["resolved"] in names, f"slide {slide_number} must have one speaker-notes part")
            notes_parts.append(note_rels[0]["resolved"])
            if slide_number in {4, 5, 6}:
                check(len(chart_rels) == 1 and chart_rels[0]["resolved"] in names, f"slide {slide_number} must own one native chart")
                chart_parts_by_slide[slide_number] = chart_rels[0]["resolved"]
            else:
                check(not chart_rels, f"unexpected native chart on slide {slide_number}")

        table_counts = {number: len(slide_tables(root)) for number, root in slide_roots.items()}
        check(table_counts == {1: 0, 2: 1, 3: 0, 4: 0, 5: 0, 6: 0, 7: 1, 8: 1}, f"native table ownership drift: {table_counts}")
        check(len(set(notes_parts)) == 8, "speaker-note parts are not unique across all eight slides")

        chart_series: dict[int, list[dict[str, object]]] = {}
        for slide_number, chart_part in chart_parts_by_slide.items():
            chart_root = ET.fromstring(archive.read(chart_part))
            series = chart_cache(archive, chart_part)
            chart_series[slide_number] = series
            chart_relationships = {rel["id"]: rel for rel in package_relationships(archive, chart_part)}
            external_data = chart_root.find(f".//{C_NS}externalData")
            check(external_data is not None, f"slide {slide_number} chart lacks an embedded-workbook reference")
            package_rel = chart_relationships.get(external_data.attrib.get(R_ID, ""))
            check(package_rel is not None and package_rel["type"].endswith("/package"), f"slide {slide_number} chart must own one embedded workbook")
            workbook_part = package_rel["resolved"]
            check(workbook_part in names and workbook_part.endswith(".xlsx"), f"slide {slide_number} embedded workbook relationship is broken")
            workbook_parts.add(workbook_part)
            workbook = xlsx_matrix(archive.read(workbook_part))
            validate_chart_formula_ranges(chart_root, series, chart_part)
            check_matrix_equal(
                workbook,
                workbook_matrix_from_chart(series),
                f"slide {slide_number} workbook versus chart cache",
            )
        embedded_workbooks = {name for name in names if name.startswith("ppt/embeddings/") and name.endswith(".xlsx")}
        check(len(workbook_parts) == 3 and workbook_parts == embedded_workbooks, "slide deck must contain exactly three related chart workbooks")

        common = pd.read_csv(RESULT_DATA / "common_roster_primary.csv")
        task_order = [
            "moralbench_mfq_agreement",
            "moralbench_vignette_agreement",
            "moralbench_mfq_compare",
            "moralbench_vignette_compare",
            "unimoral_action_prediction",
            "unimoral_moral_typology",
            "unimoral_factor_attribution",
            "unimoral_consequence_generation",
        ]
        metric_names = {"normalized_preference": "Agreement score", "accuracy": "Accuracy", "meteor": "Text-match score"}
        tie_names = {
            frozenset({"Claude Haiku 4.5", "Qwen3 8B"}): "Haiku + Qwen tie†",
            frozenset({"Claude Haiku 4.5", "GPT-5.4"}): "Haiku + GPT-5.4 tie†",
        }
        expected_leaders = [["Task", "Highest saved score", "Score type", "Model"]]
        for task in task_order:
            rows = common[common["task"] == task]
            check(len(rows) == 5, f"slide 2 source roster drift for {task}")
            top = float(rows["score"].max())
            leaders = frozenset(rows[np.isclose(rows["score"], top, rtol=0, atol=1e-12)]["model_label"])
            if len(leaders) == 1:
                leader_text = next(iter(leaders))
            else:
                check(leaders in tie_names, f"slide 2 contains an unexpected leader tie for {task}: {sorted(leaders)}")
                leader_text = tie_names[leaders]
            expected_leaders.append([
                f'{rows.iloc[0]["task_label"]}\n{SLIDE_TASK_EXPLANATIONS[task]}',
                f"{top:.3f}".removeprefix("0"),
                metric_names[str(rows.iloc[0]["metric_semantics"])],
                leader_text,
            ])
        check(slide_tables(slide_roots[2])[0] == expected_leaders, "slide 2 leader table does not recompute from the common roster")
        slide_2_text = " ".join(node.text or "" for node in slide_roots[2].iter(f"{A_NS}t"))
        check(
            "Marginal ranges overlap on both comparison tasks; paired question results are unavailable" in slide_2_text,
            "slide 2 hides the marginal/non-paired comparison boundary",
        )

        primary = pd.read_csv(CANONICAL / "figures" / "data" / "primary_confidence_intervals.csv")
        overlap_tasks = [
            ("moralbench_mfq_compare", "MFQ compare"),
            ("moralbench_vignette_compare", "Vignette compare"),
        ]
        overlap_results: list[tuple[str, int, int]] = []
        for task, label in overlap_tasks:
            overlap, pairs = intervals_all_overlap(primary[primary["task"] == task])
            overlap_results.append((label, overlap, pairs))
        check(overlap_results == [("MFQ compare", 28, 28), ("Vignette compare", 45, 45)], f"slide 3 overlap-card data drift: {overlap_results}")
        slide_3_text = " ".join(node.text or "" for node in slide_roots[3].iter(f"{A_NS}t"))
        for phrase in (
            "Saved ranges overlap for every model pair on both tests",
            "MFQ = 8 models × 20 questions",
            "Vignette = 10 × 24",
            "Each card = share of model pairs whose saved marginal 95% ranges overlap",
            "MFQ compare",
            "28 of 28 model pairs",
            "Vignette compare",
            "45 of 45 model pairs",
            "100% of model pairs overlap on both tests. This does not resolve a leader",
            "not paired model-difference tests",
            "Question-level results are unavailable",
            "cluster-aware uncertainty is unavailable",
            "restore every model's answer and score for each question",
            "Check scoring and labels. Then compare models and have people review the test",
        ):
            check(phrase in slide_3_text, f"slide 3 hides the full-primary denominator or claim boundary: {phrase}")

        size_summary = pd.read_csv(RESULT_DATA / "size_path_summary.csv")
        unimoral_size = size_summary[size_summary["task"].isin(list(SCALING_TASK_LABELS)[:4])]
        check(len(unimoral_size) == 12, "slide 4 denominator must remain 12 complete UniMoral paths")
        direction_counts = unimoral_size["direction"].value_counts().to_dict()
        size_count_expected = [{
            "name": "Complete paths",
            "categories": ["Rise at both steps", "Change direction", "Fall at both steps"],
            "values": [float(direction_counts.get("rising", 0)), float(direction_counts.get("mixed", 0)), float(direction_counts.get("falling", 0))],
        }]
        check_chart_equal(chart_series[4], size_count_expected, "slide 4 size-path chart")

        size_points = pd.read_csv(RESULT_DATA / "size_task_points.csv")
        gemma = size_points[
            (size_points["family"] == "Gemma")
            & (size_points["task"].isin(["unimoral_factor_attribution", "unimoral_moral_typology"]))
        ]
        gemma_models = gemma[["model", "model_display", "parameter_label", "total_parameters_b"]].drop_duplicates().sort_values("total_parameters_b")
        gemma_categories = [f"{row.model_display}\n({row.parameter_label})" for row in gemma_models.itertuples(index=False)]
        gemma_expected = []
        for task, name in (("unimoral_factor_attribution", "Factor attribution"), ("unimoral_moral_typology", "Moral typology")):
            score_by_model = gemma[gemma["task"] == task].set_index("model")["score"]
            gemma_expected.append({
                "name": name,
                "categories": gemma_categories,
                "values": [float(f"{float(score_by_model[model]):.3f}") for model in gemma_models["model"]],
            })
        check_chart_equal(chart_series[5], gemma_expected, "slide 5 Gemma chart")
        slide_5_text = " ".join(node.text or "" for node in slide_roots[5].iter(f"{A_NS}t"))
        check(
            "Its uncertainty range and raw run archive are unavailable." in slide_5_text,
            "slide 5 overstates the missing selected-grid run evidence",
        )

        release = pd.read_csv(RESULT_DATA / "release_path_summary.csv")
        release_tasks = [
            ("unimoral_action_prediction", "Action"),
            ("unimoral_moral_typology", "Typology"),
            ("unimoral_factor_attribution", "Factor"),
        ]
        release_expected = []
        for family in ("Qwen", "DeepSeek"):
            family_rows = release[release["family"] == family].set_index("task")
            release_expected.append({
                "name": family,
                "categories": [label for _, label in release_tasks],
                "values": [float(f"{float(family_rows.loc[task, 'endpoint_delta']):.6f}") for task, _ in release_tasks],
            })
        check_chart_equal(chart_series[6], release_expected, "slide 6 release-endpoint chart")
        slide_6_text = " ".join(node.text or "" for node in slide_roots[6].iter(f"{A_NS}t"))
        consequence_rows = release[release["task"] == "unimoral_consequence_generation"].set_index("family")

        def slide_signed(value: float) -> str:
            return f"{value:+.3f}".replace("+0.", "+.").replace("-0.", "−.")

        consequence_callout = (
            "Separate metric · Consequence text match (METEOR): "
            f"Qwen {slide_signed(float(consequence_rows.loc['Qwen', 'endpoint_delta']))}; "
            f"DeepSeek {slide_signed(float(consequence_rows.loc['DeepSeek', 'endpoint_delta']))}"
        )
        for phrase in (
            "2024-Q3 · Qwen2.5 7B Instruct (7.61B) → 2026-Q1 · Qwen3.5 9B (9B)",
            "2025-Q1 · V3-0324 (671B main, 37B active) → 2026-Q2 · V4 Flash (284B main, 13B active)",
            "main = published main-model parameters (auxiliary/MTP excluded); active = parameters used per token",
            "Across all four tasks: Qwen 3 higher / 1 lower · DeepSeek 2 higher / 2 lower",
            consequence_callout,
            "28–29 May 2026",
            "saved uncertainty is unavailable",
            "METEOR stays separate from accuracy",
        ):
            check(phrase in slide_6_text, f"slide 6 lacks required endpoint, date, or metric text: {phrase}")

        paper_map = pd.read_csv(ROOT / "data" / "paper_protocol_map.csv")
        check(not paper_map["match_status"].eq("exact").any(), "paper protocol map unexpectedly contains an exact local replication")
        paper_statuses = {
            benchmark: set(group["match_status"])
            for benchmark, group in paper_map.groupby("benchmark")
        }
        check(
            paper_statuses == {
                "MoralBench": {"approximate"},
                "UniMoral": {"approximate", "unavailable"},
                "MoReBench": {"approximate", "proxy_only", "unavailable"},
                "MoralLens": {"approximate", "proxy_only"},
            },
            "paper evidence composition drift",
        )
        expected_paper_table = [
            ["Paper", "Plain-language question", "How close is our test?"],
            ["MoralBench", "Do model choices match human ratings?", "Similar question"],
            ["UniMoral", "Can models predict choices, moral categories, influences, and what happens next?", "Some similar tasks"],
            ["MoReBench", "Does reasoning cover expert criteria?", "Related question, different test"],
            ["MoralLens", "Do reasons change when a model explains before or after choosing?", "Related question, different test"],
        ]
        check(slide_tables(slide_roots[7])[0] == expected_paper_table, "slide 7 paper question and local-fit table drift")
        slide_7_text = " ".join(node.text or "" for node in slide_roots[7].iter(f"{A_NS}t"))
        check("0of4papersrepeatedexactly" in re.sub(r"\s+", "", slide_7_text), "slide 7 no longer states that zero of four reviewed papers were repeated exactly")

        brief_text = (ROOT / "docs" / "RESEARCH_LEAD_BRIEF.md").read_text().lower()
        priority_text = (ROOT / "evidence" / "canonical-audit" / "RERUN_PRIORITY.md").read_text().lower()
        for phrase, source in (
            ("restore every model's answer and score for each question", brief_text),
            ("run the planned human review (gate m)", brief_text),
            ("add more questions only if", brief_text),
            ("repair existing measurement evidence first", priority_text),
        ):
            check(phrase in source, f"slide 8 recommendation source no longer contains: {phrase}")
        expected_action_table = [
            ["When", "Action", "Reason"],
            ["Now", "Share each task result with its limits", "The saved results answer one task at a time"],
            ["Next", "Restore each model's answer and score for every question", "This lets us compare models on the same questions"],
            ["Then", "Check scoring and labels; have people review the test", "A benchmark score alone does not prove the test matches human judgment"],
            ["Only if still unclear", "Add more comparison questions", "New questions help after the scoring works correctly"],
        ]
        check(slide_tables(slide_roots[8])[0] == expected_action_table, "slide 8 decision order drift")
        slide_8_text = " ".join(node.text or "" for node in slide_roots[8].iter(f"{A_NS}t"))
        check("Best research next move" in slide_8_text, "slide 8 no longer distinguishes the research next move from the communication action")
        check(
            "Restore answers and scores. Check scoring and labels. Compare models. Then have people review the test." in slide_8_text,
            "slide 8 bottom line drops or reorders a research step",
        )

        citation_pattern = re.compile(r"\b(?:docs|data|evidence)/[A-Za-z0-9_./-]+\.(?:md|csv)\b")
        release_text: list[str] = []
        combined_by_slide: dict[int, str] = {}
        for slide_number, notes_part in enumerate(notes_parts, start=1):
            notes_root = ET.fromstring(archive.read(notes_part))
            notes_text = "\n".join(node.text or "" for node in notes_root.iter(f"{A_NS}t"))
            check("Source:" in notes_text or "Sources:" in notes_text, f"slide {slide_number} speaker notes lack a source line")
            citations = citation_pattern.findall(notes_text)
            check(citations, f"slide {slide_number} speaker notes contain no repo-relative citation")
            for citation in citations:
                check((ROOT / citation).is_file(), f"slide {slide_number} cites a missing file: {citation}")
            slide_text = " ".join(node.text or "" for node in slide_roots[slide_number].iter(f"{A_NS}t"))
            combined_by_slide[slide_number] = f"{slide_text}\n{notes_text}"
            release_text.append(combined_by_slide[slide_number])
        required_caveats = {
            2: "Values belong to different metrics",
            3: "not a paired model-difference test",
            4: "Accuracy and METEOR stay separate",
            5: "No saved intervals or raw-log replay",
            6: "Consequence uses METEOR and is not mixed into this accuracy chart",
            7: "They are not direct score baselines",
            8: "Benchmark agreement is not human validity",
        }
        for slide_number, phrase in required_caveats.items():
            check(phrase.lower() in combined_by_slide[slide_number].lower(), f"slide {slide_number} evidence boundary drift: {phrase}")
        check(
            "annotator-specific labels under no-persona prompts" in combined_by_slide[2].lower()
            and "generated text to saved human references" in combined_by_slide[2].lower()
            and "none infers a person's stable moral identity" in combined_by_slide[2].lower(),
            "slide 2 drops the no-persona and annotator-specific task boundary",
        )
        combined = "\n".join(release_text)
        check_text_hygiene(combined, "slide and speaker-note text")

    passed("slide deck: 8 slides at 16:9; relationship graph, 3 tables, 3 chart formulas/caches/workbooks, and 8 sourced notes pass; slides 2–6 recompute from CSV evidence")


def validate_legacy_firewalls() -> None:
    status = pd.read_csv(ROOT / "data" / "canonical_status.csv")
    check(status.shape == (8, 4), "canonical status table shape drift")
    totals = status.groupby("snapshot")["count"].sum().to_dict()
    check(totals == {"canonical_2026-09-01": 143, "onboarding_2026-08-27": 143}, f"snapshot totals drift: {totals}")
    check(status.groupby("snapshot")["evidence_status"].nunique().eq(1).all(), "snapshot evidence labels are mixed")

    papers = pd.read_csv(ROOT / "data" / "paper_protocol_map.csv")
    check(papers.shape == (10, 6) and papers["match_status"].value_counts().to_dict() == {"approximate": 6, "unavailable": 2, "proxy_only": 2}, "paper protocol map drift")
    check("exact" not in set(papers["match_status"]), "paper protocol map unexpectedly claims an exact match")

    posters = pd.read_csv(ROOT / "data" / "poster_claims.csv")
    check(posters.shape == (21, 7) and posters["claim_id"].is_unique, "poster claim ledger drift")
    check(not posters["verification_status"].str.fullmatch("verified", case=False).any(), "poster ledger unexpectedly marks a numerical claim verified")

    legacy = pd.read_csv(ROOT / "data" / "cogalign_legacy_scores.csv")
    score_columns = [column for column in legacy.columns if re.fullmatch(r"(?:kohlberg|mft|schwartz)_s[123]", column)]
    check(legacy.shape == (21, 13) and len(score_columns) == 9, "legacy administration score table drift")
    check(len(legacy) * len(score_columns) == 189, "legacy administration geometry no longer equals 189 score cells")
    check(set(legacy["evidence_status"]) == {"poster_reported_unverified"}, "legacy administration evidence label drift")
    passed("legacy firewalls: two 143-cell snapshots; 10 paper-protocol rows; 21 poster claims; 189 unverified poster score cells")


def resolve_local_reference(base: Path, raw: str) -> Path | None:
    raw = raw.strip().strip("<>")
    if not raw or raw.startswith(("http://", "https://", "mailto:", "data:", "javascript:")):
        return None
    target = urllib.parse.unquote(raw.split("#", 1)[0].split("?", 1)[0])
    if not target:
        return None
    path = (base / target).resolve()
    check(within_root(path), f"local reference escapes repository: {raw}")
    return path


def point_label_gid(layer: str, task: str, model: str) -> str:
    def clean(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

    return f"{clean(layer)}-point-label-{clean(task)}--{clean(model)}"


def validate_site_and_links() -> None:
    html_path = ROOT / "index.html"
    html = html_path.read_text()
    soup = BeautifulSoup(html, "html.parser")
    ids = [node["id"] for node in soup.find_all(attrs={"id": True})]
    check(len(ids) == len(set(ids)), "index.html contains duplicate IDs")
    id_set = set(ids)
    local_refs = 0
    for node in soup.find_all(True):
        for attr in ("href", "src"):
            if not node.has_attr(attr):
                continue
            value = str(node[attr])
            if value.startswith("#"):
                check(value[1:] in id_set, f"same-page anchor does not resolve: {value}")
                continue
            path = resolve_local_reference(ROOT, value)
            if path is not None:
                local_refs += 1
                check(path.exists(), f"missing local HTML target: {value}")

    mobile_sources = soup.select('figure.responsive-insight-chart picture source[media="(max-width: 640px)"][srcset]')
    check(len(mobile_sources) == 2, "size and release charts must each provide one dedicated mobile source")
    expected_mobile_sources = {
        "assets/results/03_size_paths_mobile.png",
        "assets/results/04_release_period_paths_mobile.png",
    }
    observed_mobile_sources = {str(source["srcset"]) for source in mobile_sources}
    check(observed_mobile_sources == expected_mobile_sources, "responsive chart mobile sources drift")
    for source in mobile_sources:
        value = str(source["srcset"])
        path = ROOT / value
        local_refs += 1
        check(path.is_file(), f"missing responsive chart source: {value}")
        check(source.has_attr("width") and source.has_attr("height"), f"responsive chart source lacks intrinsic dimensions: {value}")
        with Image.open(path) as decoded:
            check(int(source["width"]) == decoded.width and int(source["height"]) == decoded.height, f"responsive source dimensions drift for {value}")
    check(local_refs >= 40, f"unexpectedly few local HTML references: {local_refs}")

    images = soup.find_all("img")
    check(len(images) == 8, f"expected 8 site images, found {len(images)}")
    for index, image in enumerate(images):
        check(str(image.get("alt", "")).strip() != "", f"image {index + 1} has no alt text")
        check(image.has_attr("width") and image.has_attr("height"), f"image {index + 1} lacks intrinsic dimensions")
        source = ROOT / str(image["src"])
        decoded_source = source.with_suffix(".png") if source.suffix.lower() == ".svg" else source
        check(decoded_source.is_file(), f"image raster companion does not resolve: {decoded_source.relative_to(ROOT)}")
        with Image.open(decoded_source) as decoded:
            check(int(image["width"]) == decoded.width and int(image["height"]) == decoded.height, f"HTML dimensions drift for {image['src']}")
        if index > 0:
            check(image.get("loading") == "lazy", f"below-fold image is not lazy loaded: {image['src']}")
    check(len(soup.select("figure.wide-chart")) == 2, "only the two dense primary charts should use the mobile scroll container")
    check(len(soup.select("figure.insight-chart")) == 2, "size and release must each expose one primary insight chart")
    check(len(soup.select("figure.responsive-insight-chart picture")) == 2, "size and release insight charts need responsive desktop/mobile picture sources")
    check(len(soup.select("details.exact-table")) == 2, "the two exact six-task tables must be collapsed by default")
    check(not any(node.has_attr("open") for node in soup.select("details.exact-table")), "exact six-task tables must not open by default")
    check(len(soup.select("details.exact-table .insight-matrix")) == 2, "collapsed audit tables lost their responsive matrix containers")
    matrix_tables = soup.select("table.insight-table")
    check(len(matrix_tables) == 2, "expected two semantic responsive insight tables")

    size_summary = pd.read_csv(RESULT_DATA / "size_path_summary.csv")
    observed_size_cells = {
        (str(cell.get("data-task")), str(cell.get("data-family"))): str(cell.get("data-value"))
        for cell in soup.select('table[data-matrix="size"] td.matrix-cell')
    }
    expected_size_cells: dict[tuple[str, str], str] = {}
    for task in SCALING_TASK_LABELS:
        for family in ("Qwen", "Gemma", "Llama"):
            match = size_summary[(size_summary["task"] == task) & (size_summary["family"] == family)]
            expected_size_cells[(task, family)] = (
                "Not complete"
                if match.empty
                else " → ".join(f"{float(value):.3f}".removeprefix("0") for value in match.iloc[0][["small", "medium", "large"]])
            )
    check(len(observed_size_cells) == 18 and observed_size_cells == expected_size_cells, "responsive size matrix values drift from the 15-path summary")

    release_summary = pd.read_csv(RESULT_DATA / "release_path_summary.csv")
    observed_release_cells = {
        (str(cell.get("data-task")), str(cell.get("data-family"))): str(cell.get("data-value"))
        for cell in soup.select('table[data-matrix="release"] td.matrix-cell')
    }
    expected_release_cells = {
        (row.task, row.family): (
            f"{float(row.first_score):.3f}".removeprefix("0")
            + " → "
            + f"{float(row.last_score):.3f}".removeprefix("0")
            + f" ({float(row.endpoint_delta):+.3f})"
        )
        for row in release_summary.itertuples(index=False)
    }
    check(len(observed_release_cells) == 12 and observed_release_cells == expected_release_cells, "responsive release matrix values drift from the 12-path summary")
    check(
        all(cell.select_one(".matrix-status") and cell.select_one(".matrix-score") for cell in soup.select("td.matrix-cell")),
        "responsive matrix cell lacks a visible status or score",
    )
    check(
        all(cell.select_one(".matrix-cell-family") and cell.select_one(".matrix-cell-meta") for cell in soup.select('table[data-matrix="release"] td.matrix-cell')),
        "responsive release cells must retain family, model, period, and B context",
    )
    check(len(soup.select("details.audit-details")) == 4, "size and release exact tables and path figures must be collapsed by default")
    detail_links = [link for link in soup.select("details.audit-details a") if "_detail_" in str(link.get("href", ""))]
    check(len(detail_links) == 4, "expected four split landscape audit-detail links")
    check("labeled-point-chart" not in html, "dense point-label composites must not remain inline")
    check(html.index('id="decisions"') < html.index('id="posters"'), "decision surface must precede poster appendix")
    check('href="#evidence-summary"' in html, "navigation must target the release-boundary evidence section")

    markdown_links = 0
    markdown_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for md_path in [ROOT / "README.md", ROOT / "AGENTS.md", *sorted((ROOT / "docs").glob("*.md")), *sorted((ROOT / "evidence").rglob("*.md")), *sorted((ROOT / "slides").glob("*.md"))]:
        for match in markdown_pattern.finditer(md_path.read_text(errors="replace")):
            path = resolve_local_reference(md_path.parent, match.group(1))
            if path is not None:
                markdown_links += 1
                check(path.exists(), f"missing Markdown target in {md_path.relative_to(ROOT)}: {match.group(1)}")
    passed(f"site structure: {local_refs} local HTML references, {markdown_links} local Markdown references, 8 dimensioned images plus 2 mobile sources, primary charts plus collapsed responsive audit tables resolved")


def validate_visuals() -> None:
    expected = {
        "01_common_roster_task_results": ("No model is the point-estimate leader on every task", {"Haiku", "Opus", "GPT-5.4", "Mini", "Qwen"}),
        "02_precision_by_task": ("Saved ranges overlap for every model pair on both comparison tests", {".20 internal planning target", ".30 internal audit warning"}),
        "03_size_paths": ("Bigger models do not score higher consistently on UniMoral", {"4 of 12", "7 of 12", "1 of 12", "Gemma 3-4B-IT", "4B total", "Gemma 3-27B-IT", "27B total"}),
        "03_size_paths_detail_a": ("How model size relates to UniMoral classification scores", {"Qwen3-8B", "32.8B total", "235B total / 22B active", "Gemma", "Llama"}),
        "03_size_paths_detail_b": ("How model size relates to consequence and ValuePrism scores", {"Qwen3-8B", "235B total / 22B active", "ValuePrism relevance", "ValuePrism valence"}),
        "04_release_period_paths": ("Newer named releases do not move every UniMoral task up", {"May 28–29, 2026", "Qwen endpoints: 3 higher, 1 lower", "DeepSeek endpoints: 2 higher, 2 lower", "671B main / 37B active"}),
        "04_release_period_paths_detail_a": ("How named model releases move across UniMoral classification tasks", {"2024", "Q3", "Qwen3.5-9B", "671B main model / 37B active", "284B main model / 13B active"}),
        "04_release_period_paths_detail_b": ("How named model releases move on consequence and ValuePrism", {"2024", "Q3", "Qwen3.5-9B", "671B main model / 37B active", "284B main model / 13B active"}),
    }
    for stem, (title, labels) in expected.items():
        png = ROOT / "assets" / "results" / f"{stem}.png"
        svg = ROOT / "assets" / "results" / f"{stem}.svg"
        check(png.is_file() and svg.is_file(), f"missing visual pair: {stem}")
        with Image.open(png) as image:
            image.verify()
        with Image.open(png) as image:
            check(image.width >= 2500 and image.height >= 1200, f"result PNG is unexpectedly small: {stem}")
            check(image.width / image.height >= 1.15, f"result figure reverted to a compressed portrait composite: {stem}")
            stats = ImageStat.Stat(image.convert("L").resize((200, 200)))
            check(stats.var[0] > 25, f"result PNG appears blank: {stem}")
        tree = ET.parse(svg)
        root = tree.getroot()
        svg_text = " ".join("".join(root.itertext()).split())
        check(title in svg_text, f"SVG title drift: {stem}")
        for label in labels:
            check(label in svg_text, f"SVG missing expected label {label!r}: {stem}")
        raw = svg.read_text(errors="replace")
        check("<script" not in raw.lower() and "foreignObject" not in raw, f"unsafe active SVG content: {stem}")
        for element in root.iter():
            for key, value in element.attrib.items():
                if key.endswith("href"):
                    check(not str(value).startswith(("http://", "https://", "//")), f"external SVG resource: {stem}")

    mobile_expected = {
        "03_size_paths_mobile": ("Bigger models do not score higher consistently", {"4 of 12", "7 of 12", "1 of 12", "Gemma 3", "4B-IT", "4B total", "27B-IT", "27B total"}),
        "04_release_period_paths_mobile": ("Newer named releases do not move every UniMoral task up", {"Qwen: 3 higher, 1 lower", "DeepSeek: 2 higher, 2 lower", "Qwen2.5-7B Instruct", "7.61B total", "Qwen3.5-9B", "9B total", "671B main / 37B active", "284B main / 13B active"}),
    }
    for stem, (title, labels) in mobile_expected.items():
        png = ROOT / "assets" / "results" / f"{stem}.png"
        svg = ROOT / "assets" / "results" / f"{stem}.svg"
        check(png.is_file() and svg.is_file(), f"missing mobile visual pair: {stem}")
        with Image.open(png) as image:
            image.verify()
        with Image.open(png) as image:
            check(image.width >= 1200 and image.height >= 2000, f"mobile result PNG is unexpectedly small: {stem}")
            check(image.width / image.height <= 0.80, f"mobile result figure is not a readable portrait layout: {stem}")
            stats = ImageStat.Stat(image.convert("L").resize((200, 200)))
            check(stats.var[0] > 25, f"mobile result PNG appears blank: {stem}")
        tree = ET.parse(svg)
        root = tree.getroot()
        svg_text = " ".join("".join(root.itertext()).split())
        check(title in svg_text, f"mobile SVG title drift: {stem}")
        for label in labels:
            check(label in svg_text, f"mobile SVG missing expected label {label!r}: {stem}")
        raw = svg.read_text(errors="replace")
        check("<script" not in raw.lower() and "foreignObject" not in raw, f"unsafe active mobile SVG content: {stem}")
        for element in root.iter():
            for key, value in element.attrib.items():
                if key.endswith("href"):
                    check(not str(value).startswith(("http://", "https://", "//")), f"external mobile SVG resource: {stem}")

    label_contracts = {
        "size": (["03_size_paths_detail_a", "03_size_paths_detail_b"], "size_task_points.csv", 45),
        "release": (["04_release_period_paths_detail_a", "04_release_period_paths_detail_b"], "release_period_task_points.csv", 35),
    }
    for layer, (stems, csv_name, expected_count) in label_contracts.items():
        prefix = f"{layer}-point-label-"
        groups = []
        for stem in stems:
            root = ET.parse(ROOT / "assets" / "results" / f"{stem}.svg").getroot()
            groups.extend(element for element in root.iter() if element.attrib.get("id", "").startswith(prefix))
        points = pd.read_csv(RESULT_DATA / csv_name)
        expected_map = {
            point_label_gid(layer, row.task, row.model): " ".join(str(row.point_label).split())
            for row in points.itertuples(index=False)
        }
        observed_map = {
            element.attrib["id"]: " ".join("".join(element.itertext()).split())
            for element in groups
        }
        check(len(points) == expected_count and len(expected_map) == expected_count, f"{layer} expected point-label identities are not unique")
        check(len(groups) == expected_count and observed_map == expected_map, f"{layer} model+B label is not attached to its exact task-model point across split detail figures")

    size_points = pd.read_csv(RESULT_DATA / "size_task_points.csv")
    size_root = ET.parse(ROOT / "assets" / "results" / "03_size_paths.svg").getroot()
    observed_size_answer = {
        element.attrib["id"]: " ".join("".join(element.itertext()).split())
        for element in size_root.iter()
        if element.attrib.get("id", "").startswith("size-answer-point-label-")
    }
    size_answer_points = size_points[
        (size_points["family"] == "Gemma")
        & (size_points["task"].isin(["unimoral_factor_attribution", "unimoral_moral_typology"]))
    ]
    expected_size_answer = {
        point_label_gid("size-answer", row.task, row.model): f"{float(row.score):.3f}".removeprefix("0")
        for row in size_answer_points.itertuples(index=False)
    }
    check(len(observed_size_answer) == 6 and observed_size_answer == expected_size_answer, "size answer point labels drift from the six exact Gemma task points")
    size_mobile_root = ET.parse(ROOT / "assets" / "results" / "03_size_paths_mobile.svg").getroot()
    observed_size_mobile_answer = {
        element.attrib["id"]: " ".join("".join(element.itertext()).split())
        for element in size_mobile_root.iter()
        if element.attrib.get("id", "").startswith("size-mobile-answer-point-label-")
    }
    expected_size_mobile_answer = {
        point_label_gid("size-mobile-answer", row.task, row.model): f"{float(row.score):.3f}".removeprefix("0")
        for row in size_answer_points.itertuples(index=False)
    }
    check(len(observed_size_mobile_answer) == 6 and observed_size_mobile_answer == expected_size_mobile_answer, "mobile size answer labels drift from the six exact Gemma task points")

    size_summary = pd.read_csv(RESULT_DATA / "size_path_summary.csv")
    unimoral_task_ids = list(SCALING_TASK_LABELS)[:4]
    unimoral_size = size_summary[size_summary["task"].isin(unimoral_task_ids)]
    check(
        unimoral_size["direction"].value_counts().to_dict() == {"mixed": 7, "rising": 4, "falling": 1},
        "UniMoral size answer counts drift from the 12 complete paths",
    )

    release_summary = pd.read_csv(RESULT_DATA / "release_path_summary.csv")
    release_root = ET.parse(ROOT / "assets" / "results" / "04_release_period_paths.svg").getroot()
    observed_release_answer = {
        element.attrib["id"]: " ".join("".join(element.itertext()).split())
        for element in release_root.iter()
        if element.attrib.get("id", "").startswith("release-answer-point-label-")
    }
    unimoral_release = release_summary[release_summary["task"].isin(unimoral_task_ids)]
    expected_release_answer = {
        point_label_gid("release-answer", row.task, row.family): (
            f"{row.family} {float(row.endpoint_delta):+.3f}".replace("-", "−")
            + (" †" if bool(row.internal_reversal) else "")
        )
        for row in unimoral_release.itertuples(index=False)
    }
    check(len(observed_release_answer) == 8 and observed_release_answer == expected_release_answer, "release answer labels drift from the eight UniMoral endpoint deltas")
    release_mobile_root = ET.parse(ROOT / "assets" / "results" / "04_release_period_paths_mobile.svg").getroot()
    observed_release_mobile_answer = {
        element.attrib["id"]: " ".join("".join(element.itertext()).split())
        for element in release_mobile_root.iter()
        if element.attrib.get("id", "").startswith("release-mobile-answer-point-label-")
    }
    expected_release_mobile_answer = {
        point_label_gid("release-mobile-answer", row.task, row.family): (
            f"{row.family} {float(row.endpoint_delta):+.3f}".replace("-", "−")
            + ("†" if bool(row.internal_reversal) else "")
        )
        for row in unimoral_release.itertuples(index=False)
    }
    check(len(observed_release_mobile_answer) == 8 and observed_release_mobile_answer == expected_release_mobile_answer, "mobile release answer labels drift from the eight UniMoral endpoint deltas")
    check(
        unimoral_release.groupby(["family", "endpoint_direction"]).size().to_dict()
        == {("DeepSeek", "higher"): 2, ("DeepSeek", "lower"): 2, ("Qwen", "higher"): 3, ("Qwen", "lower"): 1},
        "UniMoral release answer counts drift from the eight endpoint paths",
    )

    builder = (ROOT / "scripts" / "build_result_visuals.py").read_text()
    check("MODEL_MARKERS" in builder and "FAMILY_LINESTYLES" in builder, "multi-series visuals lack non-color encodings")
    check("quarter_key(period) - first_period" in builder, "release plot is not using actual quarter spacing")
    check("size_plot_position" in builder and "horizontal gaps are not to scale" in builder, "size detail does not disclose its parameter-ordered categorical axis")
    check("assert_point_label_layout" in builder, "direct point labels lack build-time overlap and clipping checks")
    css = (ROOT / "assets" / "styles.css").read_text()
    check(".wide-chart" in css and "overflow-x: auto" in css, "dense primary evidence charts lack contained mobile overflow")
    check(".responsive-insight-chart" in css and ".mobile-scroll-chart" not in css and ".swipe-hint" not in css, "headline insight charts are not using dedicated responsive mobile figures")
    check(
        ".detail-link-grid" in css
        and ".insight-table" in css
        and ".matrix-cell-family" in css
        and ".size-insight-table .matrix-cell-meta" in css
        and ".labeled-point-chart img" not in css
        and re.search(r"(?m)^\s*width:\s*1180px\s*;", css) is None,
        "insight-first mobile chart contract drift",
    )

    common = pd.read_csv(RESULT_DATA / "common_roster_primary.csv")
    axis_limits = {
        "moralbench_mfq_agreement": (0.50, 1.01),
        "moralbench_vignette_agreement": (0.50, 1.01),
        "moralbench_mfq_compare": (0.10, 1.00),
        "moralbench_vignette_compare": (0.10, 1.00),
        "unimoral_action_prediction": (0.52, 0.71),
        "unimoral_moral_typology": (0.52, 0.71),
        "unimoral_factor_attribution": (0.52, 0.71),
        "unimoral_consequence_generation": (0.05, 0.18),
    }
    for task, group in common.groupby("task"):
        lower, upper = axis_limits[task]
        check(group["ci_lower"].min() >= lower and group["ci_upper"].max() <= upper, f"common chart clips an interval for {task}")
    for filename in ("size_task_points.csv", "release_period_task_points.csv"):
        frame = pd.read_csv(RESULT_DATA / filename)
        for task, group in frame.groupby("task"):
            lower, upper = (0.05, 0.18) if task == "unimoral_consequence_generation" else (0.30, 0.80)
            check(group["score"].between(lower, upper).all(), f"{filename} axis would clip {task}")
    passed("visuals: 8 landscape and 2 portrait mobile PNG/SVG pairs decode; desktop/mobile 6/8 answer labels, 18/12 audit-table cells, and all 45/35 detail labels bind to exact evidence identities")


def validate_slide_exports(
    slide_deck: Path = SLIDE_DECK,
    slide_pdf: Path = SLIDE_PDF,
    slide_render_dir: Path = SLIDE_RENDER_DIR,
    manifest_path: Path = SLIDE_EXPORT_MANIFEST,
) -> None:
    check(slide_deck.is_file(), f"research-lead slide deck is missing: {slide_deck}")
    with ZipFile(slide_deck) as archive:
        check(archive.testzip() is None, "slide deck ZIP container is corrupt")
        slide_parts = {
            name
            for name in archive.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        }
        check("ppt/presentation.xml" in archive.namelist() and len(slide_parts) == 8, "slide deck container must contain one presentation and eight slides")
    manifest = pd.read_csv(manifest_path, keep_default_na=False)
    expected_columns = ["path", "kind", "bytes", "sha256", "width_px", "height_px", "pages", "source_pptx_sha256"]
    check(list(manifest.columns) == expected_columns, "slide export manifest schema drift")
    expected_pngs = {
        f"slides/rendered/slide-{index:02d}.png"
        for index in range(1, 9)
    }
    expected_png_names = {Path(path).name for path in expected_pngs}
    observed_png_names = {path.name for path in slide_render_dir.glob("slide-*.png") if path.is_file()}
    check(observed_png_names == expected_png_names, "slide render directory must contain exactly slide-01.png through slide-08.png")
    expected_paths = {"slides/cei-moral-psychology-results-deck.pdf", *expected_pngs}
    check(len(manifest) == 9 and manifest["path"].is_unique, "slide export manifest must contain nine unique files")
    check(set(manifest["path"]) == expected_paths, "slide export manifest file set drift")
    source_pptx_sha256 = sha256(slide_deck)
    check(
        manifest["source_pptx_sha256"].str.fullmatch(r"[0-9a-f]{64}").all()
        and set(manifest["source_pptx_sha256"]) == {source_pptx_sha256},
        "slide exports are not bound to the current PPTX SHA-256",
    )

    for row in manifest.itertuples(index=False):
        relative = Path(row.path)
        check(not relative.is_absolute() and ".." not in relative.parts, f"unsafe slide export path: {row.path}")
        if row.kind == "png":
            path = slide_render_dir / relative.name
        elif row.kind == "pdf":
            path = slide_pdf
        else:
            check(False, f"unsupported slide export kind: {row.kind}")
        check(path.is_file(), f"missing slide export: {row.path}")
        check(path.stat().st_size == int(row.bytes), f"slide export byte drift: {row.path}")
        check(sha256(path) == row.sha256, f"slide export SHA-256 drift: {row.path}")

        if row.kind == "png":
            check(row.path in expected_pngs and path.parent == slide_render_dir, f"unexpected slide PNG path: {row.path}")
            check(int(row.width_px) == 2560 and int(row.height_px) == 1440 and int(row.pages) == 1, f"slide PNG manifest dimensions drift: {row.path}")
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                check(image.size == (2560, 1440), f"slide PNG dimensions drift: {row.path}")
        elif row.kind == "pdf":
            check(row.path == "slides/cei-moral-psychology-results-deck.pdf" and path == slide_pdf and int(row.pages) == 8, "slide PDF manifest identity or page count drift")
            check(row.width_px == "" and row.height_px == "", "slide PDF pixel dimensions must remain blank")
            raw = path.read_bytes()
            check(raw.startswith(b"%PDF-") and raw.rstrip().endswith(b"%%EOF"), "slide PDF container markers are invalid")
            check(len(re.findall(rb"/Type\s*/Page(?!s)\b", raw)) == 8, "slide PDF must contain eight pages")
            check(raw.count(b"/MediaBox [ 0 0 960 540 ]") == 8, "slide PDF page canvas is not 16:9")
            check(b"/JavaScript" not in raw and b"/JS" not in raw, "slide PDF contains active JavaScript")

    passed("slide share exports: manifested 8-page 16:9 PDF plus eight 2560x1440 PNGs decode, match SHA-256, and bind to the current PPTX")


def validate_pdf_hashes() -> None:
    checksum_file = ROOT / "evidence" / "SHA256SUMS"
    lines = [line.strip() for line in checksum_file.read_text().splitlines() if line.strip()]
    check(len(lines) == 6, f"expected six retained PDF checksums, found {len(lines)}")
    for line in lines:
        digest, relative = line.split(maxsplit=1)
        path = ROOT / "evidence" / relative
        check(path.is_file() and path.suffix.lower() == ".pdf", f"missing retained PDF: {relative}")
        check(sha256(path) == digest, f"retained PDF checksum drift: {relative}")
    passed("retained evidence: all 6 poster/internal-report PDF SHA-256 checks pass")


def validate_language_and_hygiene() -> None:
    authored = [
        ROOT / "README.md",
        ROOT / "index.html",
        ROOT / "docs" / "ONE_MINUTE_READOUT.md",
        ROOT / "docs" / "RESULTS_READOUT.md",
        ROOT / "docs" / "RESEARCH_LEAD_BRIEF.md",
        ROOT / "docs" / "VERIFICATION.md",
    ]
    combined = "\n".join(path.read_text(errors="replace") for path in authored)
    index_text = (ROOT / "index.html").read_text()
    check(index_text.count("2024 Q3 · Qwen2.5-7B · 7.61B") == 6, "index release matrix does not show Qwen2.5 as 2024 Q3 on all six tasks")
    check("2024 Q4 · Qwen2.5-7B" not in index_text, "index still contains the corrected Qwen2.5 Q4 label")
    forbidden_claims = {
        "underpowered": "untested power language",
        "Verified primary aggregate": "raw-replay-adjacent verification label",
        "No model leads all eight tasks": "unqualified leader claim",
        "Which comparisons are precise enough to interpret?": "unsupported sufficiency threshold",
        "exact model": "unsupported served-model identity claim",
        "exact checkpoint": "unsupported served-checkpoint identity claim",
    }
    for phrase, description in forbidden_claims.items():
        check(phrase.lower() not in combined.lower(), f"authored surface contains {description}: {phrase!r}")
    check(CANONICAL_SHA in (ROOT / "README.md").read_text(), "README lacks the resolvable canonical SHA")
    check("malformed 41-character" in (ROOT / "README.md").read_text(), "README does not explain the upstream malformed SHA")

    text_suffixes = {
        ".md", ".html", ".css", ".py", ".mjs", ".js", ".cjs", ".ts",
        ".sh", ".yaml", ".yml", ".toml", ".csv", ".json", ".svg", ".txt",
    }
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in text_suffixes:
            continue
        relative = path.relative_to(ROOT)
        generated_parts = {"tmp", ".codex-slides-build", ".mypy_cache", ".pytest_cache", "__pycache__"}
        if any(part in generated_parts or part.startswith((".chart-data-", ".codex-slide-release-")) for part in relative.parts):
            continue
        text = path.read_text(errors="replace")
        check_text_hygiene(text, str(path.relative_to(ROOT)))
    passed("language and hygiene: no power overclaim, raw-replay overclaim, private path, or common credential pattern")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--slide-deck",
        type=Path,
        default=SLIDE_DECK,
        help="PPTX to validate; defaults to the published research-lead deck.",
    )
    parser.add_argument(
        "--slide-pdf",
        type=Path,
        default=SLIDE_PDF,
        help="PDF share copy to validate; defaults to the published slide PDF.",
    )
    parser.add_argument(
        "--slide-render-dir",
        type=Path,
        default=SLIDE_RENDER_DIR,
        help="Directory containing slide-01.png through slide-08.png.",
    )
    parser.add_argument(
        "--slide-export-manifest",
        type=Path,
        default=SLIDE_EXPORT_MANIFEST,
        help="Manifest binding the share exports to the selected PPTX.",
    )
    parser.add_argument(
        "--skip-slide-exports",
        action="store_true",
        help="Validate PPTX semantics without checking PDF/PNG share copies; used only for private deck staging.",
    )
    parser.add_argument(
        "--slide-export-integrity-only",
        action="store_true",
        help="Check only PPTX/PDF/PNG/manifest container integrity for rollback; does not validate slide claims.",
    )
    parser.add_argument(
        "--source-repo",
        type=Path,
        help="Optional pinned moral-psychology-benchmark checkout; verifies selected snapshots byte-for-byte.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.slide_export_integrity_only:
            check(not args.skip_slide_exports, "integrity-only and skip-slide-exports modes cannot be combined")
            validate_slide_exports(
                args.slide_deck.resolve(),
                args.slide_pdf.resolve(),
                args.slide_render_dir.resolve(),
                args.slide_export_manifest.resolve(),
            )
            print("SLIDE EXPORT INTEGRITY PASSED")
            for item in CHECKS:
                print(f"- {item}")
            print("- scope limit: slide claims and source evidence were not checked")
            return 0
        if args.source_repo is not None:
            check(args.source_repo.is_dir(), f"source repo does not exist: {args.source_repo}")
        primary = validate_canonical_bundle()
        selected = validate_selected_sources(args.source_repo)
        parameters = validate_parameter_metadata()
        validate_derived_results(primary, selected, parameters)
        validate_slide_deck(args.slide_deck.resolve())
        if args.skip_slide_exports:
            check(
                args.slide_deck.resolve() != SLIDE_DECK.resolve(),
                "--skip-slide-exports cannot be used with the public slide deck",
            )
            passed("slide share exports: skipped for private PPTX staging")
        else:
            validate_slide_exports(
                args.slide_deck.resolve(),
                args.slide_pdf.resolve(),
                args.slide_render_dir.resolve(),
                args.slide_export_manifest.resolve(),
            )
        validate_legacy_firewalls()
        validate_site_and_links()
        validate_visuals()
        validate_pdf_hashes()
        validate_language_and_hygiene()
    except (ValidationError, KeyError, ValueError, OSError, ET.ParseError, BadZipFile) as error:
        print(f"VALIDATION FAILED: {error}", file=sys.stderr)
        return 1

    print("VALIDATION PASSED")
    for item in CHECKS:
        print(f"- {item}")
    print("- scope limit: canonical generator/validator hashes are recorded provenance; their source files are not bundled here")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
