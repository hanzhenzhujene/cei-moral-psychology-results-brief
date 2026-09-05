#!/usr/bin/env python3
"""Validate the separate 33-slide full-results release.

This validator checks the published PowerPoint, PDF, rendered PNGs, native
chart caches, the paper-result CSV, the bubble encoding, and both slide
manifests. Pass ``--write-manifest`` after a deliberate rebuild to refresh the
full-deck manifest before running the normal read-only validation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "slides"
PPTX = SLIDES / "cei-moral-psychology-results-full-deck.pptx"
PDF = SLIDES / "cei-moral-psychology-results-full-deck.pdf"
RENDERS = SLIDES / "full-rendered"
MANIFEST = SLIDES / "FULL_RENDER_MANIFEST.csv"
CORE_MANIFEST = SLIDES / "RENDER_MANIFEST.csv"
PAPER_DATA = ROOT / "data" / "paper_visual_results.csv"
SPEAKER_NOTES = ROOT / "data" / "full_slide_speaker_notes.json"
RELEASE_POINTS = ROOT / "data" / "results" / "release_period_task_points.csv"
RELEASE_DATES = ROOT / "data" / "model_release_periods.csv"

EMU_PER_POINT = 12_700
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
C_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
NS = {"a": A_NS, "p": P_NS, "c": C_NS}

EXPECTED_PAPER_VALUES = {
    ("MoralBench", "MFQ binary"): [54.2, 58.5, 49.9, 54.7, 56.6],
    ("MoralBench", "Vignette binary"): [48.1, 52.6, 44.4, 50.3, 52.8],
    ("MoralBench", "MFQ comparison"): [8.2, 8.0, 9.6, 12.4, 9.8],
    ("MoralBench", "Vignette comparison"): [10.4, 13.2, 10.8, 14.2, 13.8],
    ("UniMoral", "RQ1 AP weighted F1 range"): [0.5057, 0.6617],
    ("UniMoral", "RQ2 MTC weighted F1 range"): [0.1742, 0.5701],
    ("UniMoral", "RQ3 FAA weighted F1 range"): [0.0630, 0.3859],
    ("UniMoral", "RQ4 consequence derived mean"): [0.0138, 0.0968, 0.7193],
    ("UniMoral", "RQ1 contextual-cue AP means"): [0.5518, 0.5700],
    ("MoReBench", "Table 2 displayed average"): [52.7, 53.6, 47.9, 50.1, 81.1],
    ("MoralLens", "Reasoning order"): [0.230, 0.052, 0.641, 0.792],
    ("Value Kaleidoscope", "Relevance accuracy"): [0.660, 0.835, 0.872, 0.884, 0.891],
    ("Value Kaleidoscope", "Valence accuracy"): [0.597, 0.745, 0.792, 0.808, 0.819],
    ("Value Kaleidoscope", "Generation perplexity"): [2.86, 2.53, 2.34, 2.23, 2.22],
    ("Value Kaleidoscope", "Explanation perplexity"): [5.70, 4.23, 3.52, 3.14, 2.99],
}

EXPECTED_CHARTS = {
    1: (["Primary text", "Sensitivity-only", "Multimodal extension", "Excluded"], [78, 26, 9, 30]),
    2: (["Zephyr", "LLaMA-2", "Gemma-1.1", "GPT-3.5", "GPT-4"], EXPECTED_PAPER_VALUES[("MoralBench", "MFQ binary")]),
    3: (["Zephyr", "LLaMA-2", "Gemma-1.1", "GPT-3.5", "GPT-4"], EXPECTED_PAPER_VALUES[("MoralBench", "Vignette binary")]),
    4: (["Zephyr", "LLaMA-2", "Gemma-1.1", "GPT-3.5", "GPT-4"], EXPECTED_PAPER_VALUES[("MoralBench", "MFQ comparison")]),
    5: (["Zephyr", "LLaMA-2", "Gemma-1.1", "GPT-3.5", "GPT-4"], EXPECTED_PAPER_VALUES[("MoralBench", "Vignette comparison")]),
    6: (["Identify / recall", "Process clear", "Process logical", "Outcome helpful", "Outcome harmless"], EXPECTED_PAPER_VALUES[("MoReBench", "Table 2 displayed average")]),
    7: (["60M", "220M", "770M", "3B", "11B"], EXPECTED_PAPER_VALUES[("Value Kaleidoscope", "Relevance accuracy")]),
    8: (["60M", "220M", "770M", "3B", "11B"], EXPECTED_PAPER_VALUES[("Value Kaleidoscope", "Valence accuracy")]),
    9: (["60M", "220M", "770M", "3B", "11B"], EXPECTED_PAPER_VALUES[("Value Kaleidoscope", "Generation perplexity")]),
    10: (["60M", "220M", "770M", "3B", "11B"], EXPECTED_PAPER_VALUES[("Value Kaleidoscope", "Explanation perplexity")]),
}

BUBBLE_POINTS = [
    ("Qwen2.5-7B Instruct", "2024-09-19", 0.634904, 7.61, "7.61B total"),
    ("DeepSeek V3-0324", "2025-03-24", 0.452755, 671.0, "671B main / 37B active"),
    ("DeepSeek V3.1", "2025-08-21", 0.660064, 671.0, "671B main / 37B active"),
    ("DeepSeek V3.2", "2025-12-01", 0.645606, 671.0, "671B main / 37B active"),
    ("Qwen3.5-9B", "2026-02-27", 0.652778, 9.0, "9B total"),
    ("DeepSeek V4 Flash", "2026-04-22", 0.639344, 284.0, "284B main / 13B active"),
]


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def approx_list(actual: list[float], expected: list[float], *, tol: float = 1e-9) -> bool:
    return len(actual) == len(expected) and all(math.isclose(a, e, abs_tol=tol) for a, e in zip(actual, expected))


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def validate_speaker_notes_data() -> list[dict[str, object]]:
    require(SPEAKER_NOTES.exists(), f"missing {SPEAKER_NOTES.relative_to(ROOT)}")
    rows = json.loads(SPEAKER_NOTES.read_text(encoding="utf-8"))
    require(isinstance(rows, list) and len(rows) == 33, "speaker-note data must contain 33 slide records")
    require([row.get("slide") for row in rows] == list(range(1, 34)), "speaker-note slide numbers must be unique and ordered from 1 to 33")
    required_fields = ("context", "read", "meaning", "limit", "sources")
    banned_punctuation = ("—", ";", "•", "→", "|")
    for row in rows:
        slide_number = row["slide"]
        for field in required_fields:
            value = row.get(field)
            require(isinstance(value, str) and value.strip(), f"slide {slide_number} speaker notes are missing {field}")
        spoken_fields = [str(row[field]) for field in required_fields[:-1]]
        spoken_text = " ".join(spoken_fields)
        word_count = len(re.findall(r"[A-Za-z0-9%.-]+", spoken_text))
        require(45 <= word_count <= 100, f"slide {slide_number} speaker notes must stay concise, found {word_count} spoken words")
        require(all(len(value) <= 220 for value in spoken_fields), f"slide {slide_number} has an overlong speaker-note section")
        require(not any(mark in spoken_text for mark in banned_punctuation), f"slide {slide_number} uses dense punctuation in speaker notes")
    return rows


def slide_text(archive: ZipFile, slide_number: int) -> str:
    root = ET.fromstring(archive.read(f"ppt/slides/slide{slide_number}.xml"))
    return "\n".join(node.text or "" for node in root.iter(f"{{{A_NS}}}t"))


def chart_cache(archive: ZipFile, chart_number: int) -> tuple[list[str], list[float]]:
    root = ET.fromstring(archive.read(f"ppt/slides/charts/chart{chart_number}.xml"))
    labels = [node.text or "" for node in root.findall(".//c:strCache/c:pt/c:v", NS)]
    values = [float(node.text or "nan") for node in root.findall(".//c:numCache/c:pt/c:v", NS)]
    return labels, values


def chart_value_axis_scale(archive: ZipFile, chart_number: int) -> tuple[float | None, float | None, str]:
    root = ET.fromstring(archive.read(f"ppt/slides/charts/chart{chart_number}.xml"))
    value_axis = root.find(".//c:valAx", NS)
    require(value_axis is not None, f"chart {chart_number} has no value axis")
    minimum = value_axis.find("./c:scaling/c:min", NS)
    maximum = value_axis.find("./c:scaling/c:max", NS)
    title = " ".join(node.text or "" for node in value_axis.findall(".//a:t", NS))
    return (
        float(minimum.get("val")) if minimum is not None else None,
        float(maximum.get("val")) if maximum is not None else None,
        title,
    )


def validate_paper_csv() -> None:
    with PAPER_DATA.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 60, f"paper result CSV must contain 60 data rows, found {len(rows)}")
    grouped: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        grouped.setdefault((row["paper"], row["panel"]), []).append(float(row["value"]))
    for key, expected in EXPECTED_PAPER_VALUES.items():
        require(key in grouped, f"missing paper result group: {key}")
        require(approx_list(grouped[key], expected), f"paper result values changed for {key}: {grouped[key]}")
    more_boundaries = " ".join(row["interpretation_boundary"] for row in rows if row["paper"] == "MoReBench")
    require("conflicting" in more_boundaries, "MoReBench paper/prose conflict must remain disclosed")
    lens_boundaries = " ".join(row["interpretation_boundary"] for row in rows if row["paper"] == "MoralLens")
    require("not moral quality" in lens_boundaries, "MoralLens Utility boundary is missing")
    gemma_vignette = next(row for row in rows if row["paper"] == "MoralBench" and row["panel"] == "Vignette binary" and row["item"] == "Gemma-1.1")
    require("51.8" in gemma_vignette["interpretation_boundary"], "MoralBench Gemma vignette internal mismatch is not disclosed")
    value_boundaries = " ".join(row["interpretation_boundary"] for row in rows if row["paper"] == "Value Kaleidoscope" and row["panel"] in {"Relevance accuracy", "Valence accuracy"})
    require("Contrastive synthetic target" in value_boundaries and "Supports/Opposes/Either" in value_boundaries and "not human or normative accuracy" in value_boundaries, "Value Kaleidoscope synthetic-target boundary is missing")


def validate_bubble_sources() -> None:
    with RELEASE_DATES.open(newline="", encoding="utf-8") as handle:
        date_rows = {row["model"]: row for row in csv.DictReader(handle)}
    with RELEASE_POINTS.open(newline="", encoding="utf-8") as handle:
        rows = [
            row for row in csv.DictReader(handle)
            if row["task"] == "unimoral_action_prediction" and row["model_display"] in {point[0] for point in BUBBLE_POINTS}
        ]
    by_display = {row["model_display"]: row for row in rows}
    require(len(by_display) == 6, f"expected six bubble-source rows, found {len(by_display)}")
    for model, event_date, score, total_b, label in BUBBLE_POINTS:
        row = by_display.get(model)
        require(row is not None, f"missing bubble source row for {model}")
        require(math.isclose(float(row["score"]), score, abs_tol=5e-7), f"bubble score changed for {model}")
        require(math.isclose(float(row["total_parameters_b"]), total_b, abs_tol=1e-9), f"bubble size changed for {model}")
        compact_label = row["parameter_label"].replace(" model", "")
        require(label == compact_label, f"bubble parameter label changed for {model}: {row['parameter_label']}")
        model_key = row["model"]
        require(model_key in date_rows, f"missing release metadata for {model}")
        require(date_rows[model_key]["source_event_date"] == event_date, f"bubble date changed for {model}")


def validate_bubble_shapes(archive: ZipFile) -> None:
    text = slide_text(archive, 20)
    for model, event_date, score, _b, label in BUBBLE_POINTS:
        require(model in text and event_date in text and label in text and f"accuracy {score:.3f}" in text, f"slide 20 is missing a direct label for {model}")
    for phrase in [
        "Model release date",
        "UniMoral action accuracy",
        "Bubble area shows published total or main-model B",
        "Some served-model details were not saved",
    ]:
        require(phrase in text, f"slide 20 is missing axis or boundary text: {phrase}")

    root = ET.fromstring(archive.read("ppt/slides/slide20.xml"))
    ellipses: list[tuple[float, float, float, float]] = []
    for shape in root.findall(".//p:sp", NS):
        geometry = shape.find("./p:spPr/a:prstGeom", NS)
        if geometry is None or geometry.get("prst") != "ellipse":
            continue
        offset = shape.find("./p:spPr/a:xfrm/a:off", NS)
        extent = shape.find("./p:spPr/a:xfrm/a:ext", NS)
        require(offset is not None and extent is not None, "bubble ellipse lacks geometry")
        ellipses.append(tuple(float(value) / EMU_PER_POINT for value in (
            offset.get("x"), offset.get("y"), extent.get("cx"), extent.get("cy")
        )))
    require(len(ellipses) == 6, f"slide 20 must contain six bubble marks, found {len(ellipses)}")

    x_min = date(2024, 9, 1).toordinal()
    x_max = date(2026, 5, 15).toordinal()
    expected_shapes = []
    for _model, event_date, score, total_b, _label in BUBBLE_POINTS:
        event_ordinal = date.fromisoformat(event_date).toordinal()
        x = 110 + ((event_ordinal - x_min) / (x_max - x_min)) * 810
        y = 190 + 390 - ((score - 0.40) / (0.72 - 0.40)) * 390
        radius = 6 * math.sqrt(total_b / 7.61)
        expected_shapes.append(tuple(value * 0.75 for value in (x - radius, y - radius, radius * 2, radius * 2)))
    for actual, expected in zip(sorted(ellipses), sorted(expected_shapes)):
        require(approx_list(list(actual), list(expected), tol=0.05), f"bubble geometry changed: {actual} != {expected}")


def validate_pptx(expected_speaker_notes: list[dict[str, object]]) -> str:
    require(PPTX.exists(), f"missing {PPTX.relative_to(ROOT)}")
    try:
        with ZipFile(PPTX) as archive:
            require(archive.testzip() is None, "PPTX zip contains a corrupt member")
            names = archive.namelist()
            slides = [name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)]
            notes = [name for name in names if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)]
            charts = [name for name in names if re.fullmatch(r"ppt/slides/charts/chart\d+\.xml", name)]
            workbooks = [name for name in names if name.startswith("ppt/embeddings/") and name.endswith(".xlsx")]
            require(len(slides) == 33, f"expected 33 slides, found {len(slides)}")
            require(len(notes) == 33, f"expected 33 notes parts, found {len(notes)}")
            require(len(charts) == 10, f"expected 10 native charts, found {len(charts)}")
            require(len(workbooks) == 10, f"expected 10 embedded chart workbooks, found {len(workbooks)}")
            table_count = 0
            fonts: set[str] = set()
            for name in slides:
                root = ET.fromstring(archive.read(name))
                table_count += len(root.findall(".//a:tbl", NS))
                fonts.update(node.get("typeface", "") for node in root.findall(".//a:latin", NS))
            require(table_count == 2, f"expected two native tables, found {table_count}")
            require(fonts <= {"", "Aptos"}, f"unexpected slide fonts: {sorted(fonts)}")

            for number, (expected_labels, expected_values) in EXPECTED_CHARTS.items():
                labels, values = chart_cache(archive, number)
                require(labels == expected_labels, f"chart {number} categories changed: {labels}")
                require(approx_list(values, [float(value) for value in expected_values]), f"chart {number} values changed: {values}")
            expected_bar_axes = {
                2: (0.0, 65.0, "Paper summed score (raw)"),
                3: (0.0, 60.0, "Paper summed score (raw)"),
                4: (0.0, 20.0, "Mean correct choices (retained N=20)"),
                5: (0.0, 24.0, "Mean correct choices (retained N=24)"),
                6: (0.0, 100.0, "Expert criteria satisfied (%)"),
            }
            for number, expected in expected_bar_axes.items():
                actual = chart_value_axis_scale(archive, number)
                require(actual == expected, f"chart {number} value axis changed: {actual}")
            expected_accuracy_axes = {
                7: (0.0, 1.0, "Test accuracy (fraction)"),
                8: (0.0, 1.0, "Test accuracy (fraction)"),
            }
            for number, expected in expected_accuracy_axes.items():
                actual = chart_value_axis_scale(archive, number)
                require(actual == expected, f"chart {number} value axis changed: {actual}")

            required_slide_text = {
                7: ["Five papers ask different questions", "MoralBench", "UniMoral", "MoReBench", "MoralLens", "Value Kaleidoscope", "Keep paper scores and CEI scores separate"],
                21: ["MoralBench paper: the top model differs across 4 tests", "align with human ratings", "saved task files contain 20 MFQ and 24 vignette pairs", "does not report confidence ranges or the maximum binary score", "51.8", "not a CEI result"],
                22: ["UniMoral paper: CEI does not test all paper questions", "No matching CEI test for cues, languages, or story sources", "CEI measure", ".5057 to .6617", ".1742 to .5701", ".0630 to .3859", "Derived from 6 paper-table language cells", "BLEU .0138", "METEOR .0968", "BERTScore .7193", "No-persona accuracy on annotator labels", "offline BERTScore", "no BLEU", "Higher with cues", "psychological rather than Reddit stories", "Not tested", "not directly comparable"],
                23: ["MoReBench paper: harmlessness 81.1%, logical process 47.9%", "thinking traces", "written reasoning before the final answer", "not final-answer results", "CEI keyword check is not the same review"],
                24: ["MoralLens paper: reasoning first shifts reasons and choices", "Reason score: .230 to .052", "Larger-group choices: .641 to .792", "toward duty-based reasons", "larger-group rate is not moral quality", "CEI keyword check cannot repeat this test"],
                25: ["Value Kaleidoscope paper: most gains occur before 3B", "Paper question:", "CEI ValuePrism uses different models and tests", "Relevance compares a GPT-4 example for this situation with one from another", "Supports / Opposes / Either", "Not human judgments", "Size labels are evenly spaced, not numeric distance", "3B to 11B"],
                26: ["CEI has 0 exact repeats of UniMoral or Value Kaleidoscope", "Across 37 paper-to-CEI comparison rows", "17 are related but different", "4 are indirect", "16 cannot be compared", "13 UniMoral rows + 24 ValuePrism rows"],
                27: ["UniMoral: different models have the highest saved score", "x = model", "dot = score", "saved 95% range"],
                28: ["UniMoral factor size: Gemma rises", "Qwen and Llama reverse", "published size category, ordered only", "labels = model + B"],
                29: ["ValuePrism valence size: Llama falls, then rises", "published size category, ordered only", "labels = model + B", "available files"],
                30: ["UniMoral factor releases: DeepSeek falls .038", "Qwen changes .002", "model release quarter", "metadata, not test time", "labels = model + B"],
                31: ["ValuePrism valence releases: Qwen +.187", "DeepSeek -.062", "model release quarter", "metadata, not test time", "labels = model + B", "available files"],
                32: ["Next: check the current evidence before buying more model runs", "Review 12 cases", "Run human validation", "Run paid models only after these checks"],
            }
            for slide_number, phrases in required_slide_text.items():
                combined = slide_text(archive, slide_number) + "\n" + slide_text_from_notes(archive, slide_number)
                for phrase in phrases:
                    require(phrase in combined, f"slide {slide_number} is missing evidence text: {phrase}")
            for entry in expected_speaker_notes:
                slide_number = int(entry["slide"])
                expected_lines = [
                    f"Context: {entry['context']}",
                    f"How to read: {entry['read']}",
                    f"Meaning: {entry['meaning']}",
                    f"Limit: {entry['limit']}",
                    "Reference only:",
                    f"Sources: {entry['sources']}",
                ]
                actual = normalize_text(slide_text_from_notes(archive, slide_number))
                cursor = -1
                for line in expected_lines:
                    position = actual.find(normalize_text(line), cursor + 1)
                    require(position > cursor, f"slide {slide_number} speaker notes are missing or out of order: {line}")
                    cursor = position
                require("approved core page is preserved" not in actual.lower(), f"slide {slide_number} still has build-process notes instead of a talk track")
            validate_bubble_shapes(archive)
    except BadZipFile as exc:
        raise ValidationError(f"invalid PPTX: {exc}") from exc
    return sha256(PPTX)


def slide_text_from_notes(archive: ZipFile, slide_number: int) -> str:
    root = ET.fromstring(archive.read(f"ppt/notesSlides/notesSlide{slide_number}.xml"))
    return "\n".join(node.text or "" for node in root.iter(f"{{{A_NS}}}t"))


def validate_pdf_and_pngs() -> None:
    require(PDF.exists(), f"missing {PDF.relative_to(ROOT)}")
    pdf_pages = PdfReader(str(PDF)).pages
    require(len(pdf_pages) == 33, "full-deck PDF must contain 33 pages")
    for index, page in enumerate(pdf_pages, start=1):
        media_box = tuple(float(value) for value in page.mediabox)
        require(media_box == (0.0, 0.0, 960.0, 540.0), f"PDF page {index} must be 960 x 540 points")
        resources = page.get("/Resources")
        resources = resources.get_object() if hasattr(resources, "get_object") else resources
        require(resources is not None and "/Font" not in resources, f"PDF page {index} must be image-only to preserve the reviewed slide rendering")
        xobjects = resources.get("/XObject")
        xobjects = xobjects.get_object() if hasattr(xobjects, "get_object") else xobjects
        require(xobjects is not None and len(xobjects) == 1, f"PDF page {index} must contain exactly one full-slide image")
        image_object = next(iter(xobjects.values()))
        image_object = image_object.get_object() if hasattr(image_object, "get_object") else image_object
        require(image_object.get("/Subtype") == "/Image", f"PDF page {index} XObject must be an image")
        require((int(image_object.get("/Width")), int(image_object.get("/Height"))) == (1600, 900), f"PDF page {index} image must be 1600 x 900")
    pngs = sorted(RENDERS.glob("slide-*.png"))
    require(len(pngs) == 33, f"expected 33 rendered PNGs, found {len(pngs)}")
    require([path.name for path in pngs] == [f"slide-{index:02d}.png" for index in range(1, 34)], "rendered PNG names are incomplete")
    for path in pngs:
        with Image.open(path) as image:
            require(image.size == (1600, 900), f"{path.name} must be 1600 x 900, found {image.size}")


def manifest_rows(pptx_hash: str) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    rows.append({
        "path": str(PPTX.relative_to(ROOT)), "kind": "pptx", "bytes": PPTX.stat().st_size,
        "sha256": pptx_hash, "width_px": "", "height_px": "", "pages": 33,
        "source_pptx_sha256": pptx_hash,
    })
    rows.append({
        "path": str(PDF.relative_to(ROOT)), "kind": "pdf", "bytes": PDF.stat().st_size,
        "sha256": sha256(PDF), "width_px": "", "height_px": "", "pages": 33,
        "source_pptx_sha256": pptx_hash,
    })
    for path in sorted(RENDERS.glob("slide-*.png")):
        with Image.open(path) as image:
            width, height = image.size
        rows.append({
            "path": str(path.relative_to(ROOT)), "kind": "png", "bytes": path.stat().st_size,
            "sha256": sha256(path), "width_px": width, "height_px": height, "pages": 1,
            "source_pptx_sha256": pptx_hash,
        })
    return rows


def write_manifest(pptx_hash: str) -> None:
    fieldnames = ["path", "kind", "bytes", "sha256", "width_px", "height_px", "pages", "source_pptx_sha256"]
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(manifest_rows(pptx_hash))


def validate_manifest(pptx_hash: str) -> None:
    require(MANIFEST.exists(), f"missing {MANIFEST.relative_to(ROOT)}")
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        recorded = list(csv.DictReader(handle))
    actual = [{key: str(value) for key, value in row.items()} for row in manifest_rows(pptx_hash)]
    require(recorded == actual, "FULL_RENDER_MANIFEST.csv does not match the published full-deck files")


def validate_core_release_unchanged() -> None:
    require(CORE_MANIFEST.exists(), "missing core slide manifest")
    with CORE_MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    require(len(rows) == 9, f"core slide manifest must retain 9 rows, found {len(rows)}")
    expected_pptx_hashes = {row["source_pptx_sha256"] for row in rows}
    require(len(expected_pptx_hashes) == 1, "core manifest has multiple source PPTX hashes")
    core_pptx = SLIDES / "cei-moral-psychology-results-deck.pptx"
    require(sha256(core_pptx) == expected_pptx_hashes.pop(), "the approved eight-slide core PPTX changed")
    for row in rows:
        path = ROOT / row["path"]
        require(path.exists(), f"missing core slide release file: {row['path']}")
        require(path.stat().st_size == int(row["bytes"]), f"core slide release size changed: {row['path']}")
        require(sha256(path) == row["sha256"], f"core slide release hash changed: {row['path']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-manifest", action="store_true", help="refresh the full-deck manifest before validation")
    args = parser.parse_args()
    try:
        expected_speaker_notes = validate_speaker_notes_data()
        validate_paper_csv()
        validate_bubble_sources()
        pptx_hash = validate_pptx(expected_speaker_notes)
        validate_pdf_and_pngs()
        if args.write_manifest:
            write_manifest(pptx_hash)
        validate_manifest(pptx_hash)
        validate_core_release_unchanged()
    except (ValidationError, OSError, ET.ParseError, KeyError, ValueError) as exc:
        print(f"FULL SLIDE VALIDATION FAILED: {exc}", file=sys.stderr)
        return 1
    print("FULL SLIDE VALIDATION PASSED")
    print("33 slides · 10 native charts · 2 native tables · 33 rendered PNGs · 35 manifested release files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
