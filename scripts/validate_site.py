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

SOURCE_HEAD = "b3a348684692f615d789392692ce34a1359192d3"
CANONICAL_SHA = "276acecd603761e6ff61bd6e2685fbb87f0eaa47"
UPSTREAM_BAD_SHA = CANONICAL_SHA + "d"
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


def validate_derived_results(primary: pd.DataFrame, selected: pd.DataFrame) -> None:
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
    check(len(release) == 35, f"release layer must contain 35 points, found {len(release)}")
    check(release.groupby(["family", "task"]).ngroups == 12, "release layer must contain 12 family-task paths")
    check(set(release["family"]) == {"Qwen", "DeepSeek"}, "release family set drift")
    check(not release.duplicated(["family", "task", "release_period"]).any(), "duplicate family-task-quarter in release layer")
    check((release["run_status"] == "success").all() and release["score"].notna().all(), "release plot contains a failed or missing score")
    check(set(release["evidence_status"]) == {"exploratory aggregate; no CI or raw-log replay"}, "release evidence label drift")

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
    for phrase in ("18 intervals", "5 of 15", "9 are mixed", "1 falls"):
        check(phrase in joined_answers, f"takeaway table is missing expected result: {phrase}")
    passed("derived results: 40 common cells; 28/28 and 45/45 compare overlaps; 45 size points; 35 release points; no failed row plotted")


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
    check(len(images) == 8, f"expected 8 site images, found {len(images)}")
    for index, image in enumerate(images):
        check(str(image.get("alt", "")).strip() != "", f"image {index + 1} has no alt text")
        check(image.has_attr("width") and image.has_attr("height"), f"image {index + 1} lacks intrinsic dimensions")
        source = ROOT / str(image["src"])
        with Image.open(source) as decoded:
            check(int(image["width"]) == decoded.width and int(image["height"]) == decoded.height, f"HTML dimensions drift for {image['src']}")
        if index > 0:
            check(image.get("loading") == "lazy", f"below-fold image is not lazy loaded: {image['src']}")
    check(len(soup.select("figure.wide-chart")) == 4, "all four result charts must use the mobile scroll container")
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
    passed(f"site structure: {local_refs} local HTML references, {markdown_links} local Markdown references, 8 dimensioned images, anchors resolved")


def validate_visuals() -> None:
    expected = {
        "01_common_roster_task_results": ("No model is the point-estimate leader on every task", {"Haiku", "Opus", "GPT-5.4", "Mini", "Qwen"}),
        "02_precision_by_task": ("Available marginal intervals do not resolve a comparison-task model order", {".20 planning target", ".30 audit warning"}),
        "03_size_paths": ("Bigger is not reliably better", {"Qwen", "Gemma", "Llama"}),
        "04_release_period_paths": ("Newer-route point estimates move in both directions", {"2025", "Q2", "DeepSeek"}),
    }
    for stem, (title, labels) in expected.items():
        png = ROOT / "assets" / "results" / f"{stem}.png"
        svg = ROOT / "assets" / "results" / f"{stem}.svg"
        check(png.is_file() and svg.is_file(), f"missing visual pair: {stem}")
        with Image.open(png) as image:
            image.verify()
        with Image.open(png) as image:
            check(image.width >= 2500 and image.height >= 1200, f"result PNG is unexpectedly small: {stem}")
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

    builder = (ROOT / "scripts" / "build_result_visuals.py").read_text()
    check("MODEL_MARKERS" in builder and "FAMILY_LINESTYLES" in builder, "multi-series visuals lack non-color encodings")
    check("quarter_key(period) - first_period" in builder, "release plot is not using actual quarter spacing")
    css = (ROOT / "assets" / "styles.css").read_text()
    check(".wide-chart" in css and "overflow-x: auto" in css and "width: 820px" in css, "mobile chart readability contract missing")

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
    passed("visuals: 4 PNG/SVG pairs decode, contain expected titles/labels, use non-color encodings, actual quarter spacing, and non-clipping shared scales")


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
        validate_derived_results(primary, selected)
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
