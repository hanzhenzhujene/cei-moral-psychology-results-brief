#!/usr/bin/env python3
"""Independently validate the CEI research-lead results brief."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "evidence" / "canonical-audit"
SELECTED = ROOT / "evidence" / "source-results"
RESULT_DATA = ROOT / "data" / "results"
PARAMETERS = ROOT / "evidence" / "model-parameter-sources.csv"

SOURCE_HEAD = "b3a348684692f615d789392692ce34a1359192d3"
CANONICAL_SHA = "276acecd603761e6ff61bd6e2685fbb87f0eaa47"
UPSTREAM_BAD_SHA = CANONICAL_SHA + "d"
RUN_IDENTITY_SCOPE = "named-model specification only; served provider endpoint, quantization, and checkpoint revision not retained"
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
    return results


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
        takeaways["research_question"] == "Where does sampling uncertainty block a model order?"
    ]
    check(len(precision_takeaway) == 1, "precision takeaway row is missing or duplicated")
    check(
        precision_takeaway.iloc[0]["source"]
        == "evidence/canonical-audit/figures/data/primary_confidence_intervals.csv",
        "wide-interval claim must cite the cell-level primary interval table",
    )
    joined_answers = " ".join(takeaways["answer"])
    for phrase in ("18 intervals", "5 of 15", "9 are mixed", "1 falls", "5 higher and 1 lower", "3 higher and 3 lower", "May 28–29, 2026"):
        check(phrase in joined_answers, f"takeaway table is missing expected result: {phrase}")
    passed("derived results: 40 common cells; 28/28 and 45/45 compare overlaps; all 80 plotted rows and 12 release summaries match source and parameter metadata")


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
    check(local_refs >= 40, f"unexpectedly few local HTML references: {local_refs}")

    images = soup.find_all("img")
    check(len(images) == 6, f"expected 6 site images, found {len(images)}")
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
    check(len(soup.select("figure.insight-matrix")) == 2, "size and release must use compact insight matrices")
    check(not soup.select("figure.insight-matrix img"), "primary insight matrices must reflow as HTML instead of shrinking a fixed image")
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
    check(len(soup.select("details.audit-details")) == 2, "size and release audit detail must be collapsed by default")
    detail_links = [link for link in soup.select("details.audit-details a") if "_detail_" in str(link.get("href", ""))]
    check(len(detail_links) == 4, "expected four split landscape audit-detail links")
    check("labeled-point-chart" not in html, "dense point-label composites must not remain inline")
    check(html.index('id="decisions"') < html.index('id="posters"'), "decision surface must precede poster appendix")
    check('href="#evidence-summary"' in html, "navigation must target the release-boundary evidence section")

    markdown_links = 0
    markdown_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for md_path in [ROOT / "README.md", ROOT / "AGENTS.md", *sorted((ROOT / "docs").glob("*.md")), *sorted((ROOT / "evidence").rglob("*.md"))]:
        for match in markdown_pattern.finditer(md_path.read_text(errors="replace")):
            path = resolve_local_reference(md_path.parent, match.group(1))
            if path is not None:
                markdown_links += 1
                check(path.exists(), f"missing Markdown target in {md_path.relative_to(ROOT)}: {match.group(1)}")
    passed(f"site structure: {local_refs} local HTML references, {markdown_links} local Markdown references, 6 dimensioned images, responsive matrices and collapsed detail links resolved")


def validate_visuals() -> None:
    expected = {
        "01_common_roster_task_results": ("No model is the point-estimate leader on every task", {"Haiku", "Opus", "GPT-5.4", "Mini", "Qwen"}),
        "02_precision_by_task": ("Available marginal intervals do not resolve a comparison-task model order", {".20 planning target", ".30 audit warning"}),
        "03_size_paths": ("Model size is not a reliable shortcut", {"15 complete paths", "5 rising", "9 mixed", "1 falling", "235B / 22B active"}),
        "03_size_paths_detail_a": ("Size detail · UniMoral classification", {"Qwen3-8B", "32.8B total", "235B total / 22B active", "Gemma", "Llama"}),
        "03_size_paths_detail_b": ("Size detail · consequence and ValuePrism", {"Qwen3-8B", "235B total / 22B active", "ValuePrism relevance", "ValuePrism valence"}),
        "04_release_period_paths": ("Model release quarter is not a progress curve", {"May 28–29, 2026", "Qwen 5 higher / 1 lower", "DeepSeek 3 higher / 3 lower", "671B main / 37B active"}),
        "04_release_period_paths_detail_a": ("Release-quarter detail · UniMoral classification", {"Qwen3.5-9B", "671B main model / 37B active", "284B main model / 13B active"}),
        "04_release_period_paths_detail_b": ("Release-quarter detail · consequence and ValuePrism", {"Qwen3.5-9B", "671B main model / 37B active", "284B main model / 13B active"}),
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

    size_summary = pd.read_csv(RESULT_DATA / "size_path_summary.csv")
    observed_size_matrix: dict[str, str] = {}
    size_root = ET.parse(ROOT / "assets" / "results" / "03_size_paths.svg").getroot()
    for element in size_root.iter():
        if element.attrib.get("id", "").startswith("size-matrix-point-label-"):
            observed_size_matrix[element.attrib["id"]] = " ".join("".join(element.itertext()).split())
            font_sizes = [
                float(match.group(1))
                for child in element.iter()
                if (match := re.search(r"font:\s+(?:\d+\s+)?([0-9.]+)px", str(child.attrib.get("style", ""))))
            ]
            check(font_sizes and min(font_sizes) >= 14.0, "static size matrix score text fell below the readability floor")
    expected_size_matrix: dict[str, str] = {}
    for task in SCALING_TASK_LABELS:
        for family in ("Qwen", "Gemma", "Llama"):
            key = point_label_gid("size-matrix", task, family)
            match = size_summary[(size_summary["family"] == family) & (size_summary["task"] == task)]
            expected_size_matrix[key] = (
                "Not complete"
                if match.empty
                else " → ".join(f"{float(value):.3f}".removeprefix("0") for value in match.iloc[0][["small", "medium", "large"]])
            )
    check(len(observed_size_matrix) == 18 and observed_size_matrix == expected_size_matrix, "size matrix cell values or identities drift from the 15-path summary")

    release_summary = pd.read_csv(RESULT_DATA / "release_path_summary.csv")
    release_root = ET.parse(ROOT / "assets" / "results" / "04_release_period_paths.svg").getroot()
    observed_release_matrix = {
        element.attrib["id"]: " ".join("".join(element.itertext()).split())
        for element in release_root.iter()
        if element.attrib.get("id", "").startswith("release-matrix-point-label-")
    }
    for element in release_root.iter():
        if element.attrib.get("id", "").startswith("release-matrix-point-label-"):
            font_sizes = [
                float(match.group(1))
                for child in element.iter()
                if (match := re.search(r"font:\s+(?:\d+\s+)?([0-9.]+)px", str(child.attrib.get("style", ""))))
            ]
            check(font_sizes and min(font_sizes) >= 14.0, "static release matrix score text fell below the readability floor")
    expected_release_matrix = {
        point_label_gid("release-matrix", row.task, row.family): (
            f"{float(row.first_score):.3f}".removeprefix("0")
            + " → "
            + f"{float(row.last_score):.3f}".removeprefix("0")
            + f" ({float(row.endpoint_delta):+.3f})"
        )
        for row in release_summary.itertuples(index=False)
    }
    check(len(observed_release_matrix) == 12 and observed_release_matrix == expected_release_matrix, "release matrix cell values or identities drift from the 12-path summary")

    builder = (ROOT / "scripts" / "build_result_visuals.py").read_text()
    check("MODEL_MARKERS" in builder and "FAMILY_LINESTYLES" in builder, "multi-series visuals lack non-color encodings")
    check("quarter_key(period) - first_period" in builder, "release plot is not using actual quarter spacing")
    check("size_plot_position" in builder and "horizontal gaps are not to scale" in builder, "size detail does not disclose its parameter-ordered categorical axis")
    check("assert_point_label_layout" in builder, "direct point labels lack build-time overlap and clipping checks")
    css = (ROOT / "assets" / "styles.css").read_text()
    check(".wide-chart" in css and "overflow-x: auto" in css, "dense primary charts lack contained mobile overflow")
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
    passed("visuals: 8 landscape PNG/SVG pairs decode; 18/12 matrix cells and all 45/35 detail labels bind to exact evidence identities")


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
    authored = [ROOT / "README.md", ROOT / "index.html", ROOT / "docs" / "RESULTS_READOUT.md", ROOT / "docs" / "RESEARCH_LEAD_BRIEF.md"]
    combined = "\n".join(path.read_text(errors="replace") for path in authored)
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

    text_suffixes = {".md", ".html", ".css", ".py", ".csv", ".json", ".svg", ".txt"}
    secret_patterns = {
        "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
        "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
        "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    }
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in text_suffixes:
            continue
        text = path.read_text(errors="replace")
        mac_user_root = "/" + "Users/"
        file_scheme = "file" + "://"
        check(mac_user_root not in text and file_scheme not in text and not re.search(r"[A-Za-z]:\\Users\\", text), f"private absolute path in {path.relative_to(ROOT)}")
        for label, pattern in secret_patterns.items():
            check(pattern.search(text) is None, f"possible {label} in {path.relative_to(ROOT)}")
    passed("language and hygiene: no power overclaim, raw-replay overclaim, private path, or common credential pattern")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-repo",
        type=Path,
        help="Optional pinned moral-psychology-benchmark checkout; verifies selected snapshots byte-for-byte.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.source_repo is not None:
            check(args.source_repo.is_dir(), f"source repo does not exist: {args.source_repo}")
        primary = validate_canonical_bundle()
        selected = validate_selected_sources(args.source_repo)
        parameters = validate_parameter_metadata()
        validate_derived_results(primary, selected, parameters)
        validate_legacy_firewalls()
        validate_site_and_links()
        validate_visuals()
        validate_pdf_hashes()
        validate_language_and_hygiene()
    except (ValidationError, KeyError, ValueError, OSError, ET.ParseError) as error:
        print(f"VALIDATION FAILED: {error}", file=sys.stderr)
        return 1

    print("VALIDATION PASSED")
    for item in CHECKS:
        print(f"- {item}")
    print("- scope limit: canonical generator/validator hashes are recorded provenance; their source files are not bundled here")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
