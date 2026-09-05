import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const workspaceDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SKILL_DIR = process.env.PRESENTATIONS_SKILL_DIR;
const RUNTIME_PYTHON = process.env.WORKSPACE_PYTHON;
const ARTIFACT_TOOL_DIR = process.env.ARTIFACT_TOOL_DIR;
const RUNTIME_NODE_MODULES = process.env.RUNTIME_NODE_MODULES;
const OUTPUT_PPTX = process.env.FULL_SLIDE_DECK_OUTPUT;

for (const [name, value] of Object.entries({
  PRESENTATIONS_SKILL_DIR: SKILL_DIR,
  WORKSPACE_PYTHON: RUNTIME_PYTHON,
  ARTIFACT_TOOL_DIR,
  RUNTIME_NODE_MODULES,
  FULL_SLIDE_DECK_OUTPUT: OUTPUT_PPTX,
})) {
  if (!value || !path.isAbsolute(value)) throw new Error(`${name} must be an absolute path.`);
}

const { Presentation, PresentationFile } = await import(pathToFileURL(
  path.join(ARTIFACT_TOOL_DIR, "dist/artifact_tool.mjs"),
).href);
const {
  resolvePresentationFont,
  applyPresentationChartFont,
  finalizePresentation,
} = await import(pathToFileURL(
  path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs"),
).href);

const expectedOutputPath = path.join(workspaceDir, "slides", "cei-moral-psychology-results-full-deck.pptx");
if (path.resolve(OUTPUT_PPTX) !== expectedOutputPath) {
  throw new Error("FULL_SLIDE_DECK_OUTPUT must point to slides/cei-moral-psychology-results-full-deck.pptx.");
}

const family = resolvePresentationFont({ fontFamily: "Aptos" });
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const runtimeRequire = createRequire(path.join(RUNTIME_NODE_MODULES, "sharp", "package.json"));
const sharp = runtimeRequire("sharp");

const C = {
  bg: "#F7F5EF",
  ink: "#17212B",
  muted: "#66727E",
  grid: "#D8D9D5",
  teal: "#14856D",
  tealSoft: "#E3F0EB",
  coral: "#CF5D4A",
  coralSoft: "#F6E5E0",
  gold: "#D3971E",
  goldSoft: "#F5EACF",
  purple: "#6E5AA8",
  purpleSoft: "#EBE6F4",
  blue: "#2B78B8",
  blueSoft: "#E4EEF7",
  white: "#FFFFFF",
};

function addText(slide, text, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name: options.name,
    position,
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: family,
    fontSize: options.fontSize ?? 22,
    bold: options.bold ?? false,
    color: options.color ?? C.ink,
    alignment: options.alignment ?? "left",
    autoFit: options.autoFit ?? "shrinkText",
  };
  return shape;
}

function addRule(slide, left, top, width, color = C.grid, weight = 1) {
  return slide.shapes.add({
    geometry: "line",
    position: { left, top, width, height: 0 },
    fill: "none",
    line: { style: "solid", fill: color, width: weight },
  });
}

function addTag(slide, label, fill, color) {
  const tag = slide.shapes.add({
    geometry: "roundRect",
    position: { left: 1018, top: 40, width: 190, height: 34 },
    fill,
    line: { fill: "none", width: 0 },
    borderRadius: 17,
  });
  tag.text = label;
  tag.text.style = {
    typeface: family,
    fontSize: 13,
    bold: true,
    color,
    alignment: "center",
    autoFit: "shrinkText",
  };
  return tag;
}

function addSlideFrame(slide, title, subtitle, tag) {
  slide.background.fill = C.bg;
  addText(slide, title, { left: 72, top: 36, width: 1136, height: 62 }, {
    name: "slide-title",
    fontSize: 34,
    bold: true,
    autoFit: "shrinkText",
  });
  if (subtitle) {
    addText(slide, subtitle, { left: 82, top: 100, width: 1080, height: 34 }, {
      name: "slide-subtitle",
      fontSize: 17,
      color: C.muted,
    });
  }
  addRule(slide, 72, 142, 1136, C.grid, 1);
}

function addCard(slide, position, options = {}) {
  return slide.shapes.add({
    geometry: "roundRect",
    position,
    fill: options.fill ?? C.white,
    line: { style: "solid", fill: options.line ?? C.grid, width: options.width ?? 1 },
    borderRadius: options.radius ?? 18,
  });
}

function addPill(slide, text, position, fill, color) {
  const shape = slide.shapes.add({
    geometry: "roundRect",
    position,
    fill,
    line: { fill: "none", width: 0 },
    borderRadius: 14,
  });
  shape.text = text;
  shape.text.style = {
    typeface: family,
    fontSize: 12,
    bold: true,
    color,
    alignment: "center",
    autoFit: "shrinkText",
  };
  return shape;
}

function styleTable(table, rows, columns, options = {}) {
  table.borders.assign({ style: "solid", fill: C.grid, width: 1 });
  table.cells.block({ row: 0, column: 0, rowCount: rows, columnCount: columns }).assign({
    fill: C.white,
    textStyle: { typeface: family, fontSize: options.bodySize ?? 15, color: C.ink },
    margins: { left: 10, right: 10, top: 6, bottom: 6 },
  });
  table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount: columns }).assign({
    fill: options.headerFill ?? C.ink,
    textStyle: { typeface: family, fontSize: options.headerSize ?? 14, color: C.white, bold: true },
  });
}

function setNotes(slide, lines) {
  slide.speakerNotes.textFrame.setText(lines);
  slide.speakerNotes.setVisible(true);
}

async function addImage(slide, sourcePath, position, alt, options = {}) {
  const input = await fs.readFile(path.join(workspaceDir, sourcePath));
  let output = input;
  if (options.crop) {
    const metadata = await sharp(input).metadata();
    if (!metadata.width || !metadata.height) throw new Error(`Cannot read image size: ${sourcePath}`);
    const left = Math.round(metadata.width * (options.crop.left ?? 0));
    const top = Math.round(metadata.height * (options.crop.top ?? 0));
    const right = Math.round(metadata.width * (options.crop.right ?? 0));
    const bottom = Math.round(metadata.height * (options.crop.bottom ?? 0));
    output = await sharp(input).extract({
      left,
      top,
      width: metadata.width - left - right,
      height: metadata.height - top - bottom,
    }).png().toBuffer();
  }
  const bytes = new Uint8Array(output);
  if (options.frame !== false) {
    addCard(slide, {
      left: position.left - 4,
      top: position.top - 4,
      width: position.width + 8,
      height: position.height + 8,
    }, { fill: C.white, line: C.grid, width: 1, radius: 14 });
  }
  return slide.images.add({
    blob: bytes,
    contentType: "image/png",
    alt,
    fit: "contain",
    position,
  });
}

async function containedImageBounds(sourcePath, position, crop = {}) {
  const metadata = await sharp(await fs.readFile(path.join(workspaceDir, sourcePath))).metadata();
  if (!metadata.width || !metadata.height) throw new Error(`Cannot read image size: ${sourcePath}`);
  const croppedWidth = metadata.width * (1 - (crop.left ?? 0) - (crop.right ?? 0));
  const croppedHeight = metadata.height * (1 - (crop.top ?? 0) - (crop.bottom ?? 0));
  const scale = Math.min(position.width / croppedWidth, position.height / croppedHeight);
  const width = croppedWidth * scale;
  const height = croppedHeight * scale;
  return {
    left: position.left + (position.width - width) / 2,
    top: position.top + (position.height - height) / 2,
    width,
    height,
  };
}

async function addCoreSlide(slideNumber, alt) {
  const slide = presentation.slides.add();
  slide.background.fill = C.bg;
  const sourcePath = `slides/rendered/slide-${String(slideNumber).padStart(2, "0")}.png`;
  const bytes = new Uint8Array(await fs.readFile(path.join(workspaceDir, sourcePath)));
  slide.images.add({
    blob: bytes,
    contentType: "image/png",
    alt,
    fit: "contain",
    position: { left: 0, top: 0, width: 1280, height: 720 },
  });
  setNotes(slide, [
    `Source: ${sourcePath}; exact 2560 × 1440 render from slides/cei-moral-psychology-results-deck.pptx.`,
    "This approved core page is preserved as a full-slide image in the expanded deck. The separate 8-slide PowerPoint remains the editable source.",
  ]);
  return slide;
}

async function addEvidenceImageSlide({
  title,
  subtitle,
  sourcePath,
  alt,
  claim,
  howToRead,
  boundary,
  tag,
  portrait = false,
  cropTop = 0.10,
  cropBottom = 0.045,
  maskSourceTop = 0,
}) {
  const slide = presentation.slides.add();
  addSlideFrame(slide, title, subtitle, tag);
  const imagePosition = { left: 72, top: 152, width: 1136, height: 505 };
  const crop = { top: cropTop, bottom: cropBottom };
  await addImage(slide, sourcePath, imagePosition, alt, {
    crop,
    frame: false,
  });
  if (maskSourceTop > 0) {
    const bounds = await containedImageBounds(sourcePath, imagePosition, crop);
    slide.shapes.add({
      geometry: "rect",
      position: { left: bounds.left, top: bounds.top, width: bounds.width, height: maskSourceTop },
      fill: C.white,
      line: { fill: "none", width: 0 },
    });
  }
  addText(slide, boundary, { left: 82, top: 665, width: 1116, height: 30 }, {
    fontSize: 14,
    color: C.muted,
    alignment: "center",
  });
  setNotes(slide, [
    `Source image: ${sourcePath}.`,
    `Claim: ${claim}`,
    `How to read: ${howToRead}`,
    `Boundary: ${boundary}`,
    "The source figure keeps its original aspect ratio. Only the section named on this slide is shown.",
  ]);
  return slide;
}

function chartBase() {
  return {
    hasLegend: false,
    chartFill: C.bg,
    chartLine: { fill: "none", width: 0 },
    plotAreaFill: C.bg,
    plotAreaLine: { fill: "none", width: 0 },
  };
}

await addCoreSlide(1, "MoralBench and UniMoral results for a research lead.");
await addCoreSlide(2, "MoralBench and UniMoral task leaders for the same five models.");
await addCoreSlide(3, "For every MoralBench model pair, the two 95% score ranges overlap.");
await addCoreSlide(4, "Four of twelve UniMoral family and task comparisons rise at both size steps.");
await addCoreSlide(5, "UniMoral Gemma factor accuracy rises while typology accuracy falls.");
await addCoreSlide(6, "Later Qwen and DeepSeek releases move UniMoral tasks in different directions.");

// Slide 7: five-paper map. The eight-slide core deck remains unchanged.
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "Five papers ask different questions. None is exactly repeated here.",
    "Paper results and CEI results use different models, data, prompts, or scores.",
    { label: "PAPER MAP", fill: C.coralSoft, color: C.coral },
  );
  const values = [
    ["Paper", "What it asks", "Headline paper result", "Closest CEI evidence"],
    ["MoralBench", "Do model choices track human ratings?", "Different models lead its four assessments", "Related tasks, different setup"],
    ["UniMoral", "Can models predict actions, types, factors, and consequences?", "Llama action F1 ranges from .506 to .662", "Narrower versions of four tasks"],
    ["MoReBench", "Does reasoning meet expert criteria?", "Harmless 81.1%; logical 47.9%", "Keyword check only"],
    ["MoralLens", "Does reasoning order change reasons and choices?", "CD GAP .230 to .052; utility .641 to .792", "Keyword check only"],
    ["Value Kaleidoscope", "How do value tasks change with model size?", "Most gains occur before 3B", "Different models and scoring"],
  ];
  const table = slide.tables.add({
    rows: values.length,
    columns: 4,
    left: 82,
    top: 170,
    width: 1116,
    height: 424,
    columnWidths: [175, 370, 315, 256],
    values,
  });
  styleTable(table, values.length, 4, { bodySize: 14, headerSize: 14, headerFill: C.coral });
  table.cells.block({ row: 1, column: 0, rowCount: 5, columnCount: 1 }).textStyle.bold = true;
  table.cells.block({ row: 1, column: 2, rowCount: 5, columnCount: 1 }).textStyle.bold = true;
  addText(slide, "Keep paper scores and CEI scores separate. They answer related but different questions.", {
    left: 92, top: 620, width: 1096, height: 34,
  }, { fontSize: 19, bold: true, color: C.ink, alignment: "center" });
  setNotes(slide, [
    "Sources: data/paper_protocol_map.csv; data/paper_visual_results.csv; evidence/canonical-audit/PAPER_REPO_EVIDENCE_LEDGER.csv; docs/PAPER_REVIEW.md.",
    "The five papers are MoralBench, UniMoral, MoReBench, MoralLens, and Value Kaleidoscope. ValuePrism is the related CEI benchmark.",
    "No exact local result replication is documented for any of the five. Evidence classes and missing identity fields differ by paper.",
    "The 37-row 0/17/4/16 crosswalk on slide 26 covers UniMoral and ValuePrism only; it is not a five-paper status count.",
  ]);
}

// Slide 8: audited partition.
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "CEI evidence audit: 78 of 143 results support main findings",
    "The other 65 results are checks, a separate multimodal extension, or exclusions.",
    { label: "EVIDENCE MAP", fill: C.blueSoft, color: C.blue },
  );
  const chart = slide.charts.add("doughnut", {
    position: { left: 92, top: 178, width: 620, height: 430 },
    categories: ["Primary text", "Sensitivity-only", "Multimodal extension", "Excluded"],
    series: [{
      name: "Audit cells",
      values: [78, 26, 9, 30],
      points: [
        { idx: 0, fill: C.teal },
        { idx: 1, fill: C.gold },
        { idx: 2, fill: C.blue },
        { idx: 3, fill: C.muted },
      ],
      valuesFormatCode: "0",
    }],
    doughnutOptions: { holeSize: 64, firstSliceAngle: 270 },
    dataLabels: {
      showValue: false,
      showCategoryName: false,
      showPercent: false,
      position: "outEnd",
      textStyle: { typeface: family, fontSize: 14, fill: C.ink, bold: true },
    },
    hasLegend: false,
    chartFill: C.bg,
    chartLine: { fill: "none", width: 0 },
    plotAreaFill: C.bg,
    plotAreaLine: { fill: "none", width: 0 },
  });
  applyPresentationChartFont(chart, { fontFamily: family });
  addText(slide, "143", { left: 315, top: 340, width: 170, height: 70 }, {
    fontSize: 44,
    bold: true,
    alignment: "center",
  });
  addText(slide, "audit cells", { left: 315, top: 404, width: 170, height: 28 }, {
    fontSize: 16,
    color: C.muted,
    alignment: "center",
  });
  const rows = [
    [C.teal, "78 · Main text · 55%", "Support the main task findings"],
    [C.gold, "26 · Checks only · 18%", "Use to test robustness"],
    [C.blue, "9 · Multimodal · 6%", "Report as a separate extension"],
    [C.muted, "30 · Excluded · 21%", "Do not use for model claims"],
  ];
  rows.forEach((row, index) => {
    const top = 220 + index * 82;
    slide.shapes.add({
      geometry: "ellipse",
      position: { left: 788, top: top + 7, width: 18, height: 18 },
      fill: row[0],
      line: { fill: "none", width: 0 },
    });
    addText(slide, row[1], { left: 820, top, width: 310, height: 28 }, { fontSize: 19, bold: true });
    addText(slide, row[2], { left: 820, top: top + 31, width: 310, height: 35 }, { fontSize: 14, color: C.muted });
  });
  addText(slide, "The other 65 results should not be used for headline model claims.", {
    left: 782, top: 608, width: 380, height: 40,
  }, { fontSize: 16, color: C.blue, bold: true });
  setNotes(slide, [
    "Source: evidence/canonical-audit/figures/data/audit_partition.csv.",
    "Counts: 78 primary text + 26 sensitivity-only text + 9 multimodal extension + 30 excluded = 143.",
    "The chart is a composition of audited cells, not a model-performance distribution.",
  ]);
}

await addEvidenceImageSlide({
  title: "CEI evidence audit: what each result group can support",
  subtitle: "143 saved results are split into main findings, checks, multimodal results, and exclusions.",
  sourcePath: "evidence/canonical-audit/figures/01_audit_partition_flow.png",
  alt: "Audit partition flow separating primary text, sensitivity-only text, multimodal extension, and excluded cells.",
  claim: "Each result can support only the type of claim assigned to its group.",
  howToRead: "Follow each result group to the claim it can support.",
  boundary: "A file check confirms that the package is intact. It does not make weak or excluded evidence stronger.",
  tag: { label: "EVIDENCE MAP", fill: C.blueSoft, color: C.blue },
  cropTop: 0.17,
});

await addEvidenceImageSlide({
  title: "MoralBench: different models have the highest saved score",
  subtitle: "CEI local result. x = model; y = task score; dot = score; line = saved 95% range.",
  sourcePath: "assets/results/01_common_roster_task_results.png",
  alt: "Four MoralBench task panels showing model scores and saved uncertainty ranges for the same five models.",
  claim: "The highest saved score belongs to different models on different MoralBench tasks.",
  howToRead: "Within each panel, x is model and y is the named score. A dot is the score. A line is its 95% range.",
  boundary: "Agreement and accuracy stay separate. These ranges are not direct tests between two models.",
  tag: { label: "MAIN RESULTS", fill: C.tealSoft, color: C.teal },
  cropTop: 0.08,
  cropBottom: 0.47,
});

await addEvidenceImageSlide({
  title: "MoralBench: all model pairs have overlapping 95% ranges",
  subtitle: "CEI local result. 28 of 28 MFQ pairs and 45 of 45 vignette pairs overlap.",
  sourcePath: "assets/results/02_precision_by_task.png",
  alt: "Two cards showing that the saved 95% score ranges overlap for 28 of 28 MFQ model pairs and 45 of 45 vignette model pairs.",
  claim: "The available ranges do not identify a leader.",
  howToRead: "Each number counts model pairs with overlapping 95% ranges within one task.",
  boundary: "This is not a direct model-pair test. Question-level scores and stronger uncertainty estimates are missing.",
  tag: { label: "MAIN RESULTS", fill: C.tealSoft, color: C.teal },
  cropTop: 0.15,
  cropBottom: 0.31,
});

await addEvidenceImageSlide({
  title: "MoralBench: all 18 saved intervals are wider than .30",
  subtitle: "CEI local result. x = accuracy; y = model; dot = score; line = saved 95% range.",
  sourcePath: "evidence/canonical-audit/figures/03_primary_uncertainty.png",
  alt: "Forest plot of MoralBench comparison-task scores and nominal 95 percent intervals by model.",
  claim: "The available intervals do not resolve the small score gaps.",
  howToRead: "x is accuracy and y is model. A dot is the score. A line is its saved 95% range.",
  boundary: "The calculation does not use paired model answers or related-question structure. It does not test human validity.",
  tag: { label: "MAIN RESULTS", fill: C.tealSoft, color: C.teal },
});

await addEvidenceImageSlide({
  title: "MoralBench + UniMoral: keep the 3 score types separate",
  subtitle: "CEI local result. x = score within one metric; each line = one task's five-model range.",
  sourcePath: "evidence/canonical-audit/figures/04_task_diagnostic_spread.png",
  alt: "Diagnostic spread across eight benchmark tasks with separate accuracy, preference, and METEOR panels.",
  claim: "A single average would mix unlike measures.",
  howToRead: "Each colored line runs from the lowest to the highest saved model score for one task.",
  boundary: "A high score in one panel cannot be compared with a high score in another. There is no overall moral score here.",
  tag: { label: "DIAGNOSTIC", fill: C.purpleSoft, color: C.purple },
  portrait: true,
});

await addEvidenceImageSlide({
  title: "UniMoral: only 4 of 12 family and task comparisons rise twice",
  subtitle: "Exploratory CEI result. Bars = 12 comparisons; lines = Gemma at 4B, 12B, and 27B.",
  sourcePath: "assets/results/03_size_paths.png",
  alt: "Size path summary bars and a Gemma counterexample line chart.",
  claim: "Larger variants are not consistently higher in this saved set.",
  howToRead: "The bars count 12 family and task combinations. The lines show Gemma at 4B, 12B, and 27B.",
  boundary: "The Gemma vertical axis is zoomed. Size is not the only model difference. No uncertainty ranges were saved.",
  tag: { label: "SIZE · EXPLORATORY", fill: C.goldSoft, color: "#8B5F00" },
  portrait: true,
});

await addEvidenceImageSlide({
  title: "UniMoral size: 3 of 6 family and task comparisons change direction",
  subtitle: "Exploratory CEI result. x = published size category, ordered only; y = accuracy; labels = model + B.",
  sourcePath: "assets/results/03_size_action_typology_detail.png",
  alt: "Detailed size paths for UniMoral action and typology accuracy across named model variants.",
  claim: "Three of six action and typology paths change direction across three sizes.",
  howToRead: "x is published model size within one family. y is accuracy. Each point is one named model on one task.",
  boundary: "Each line stays within one family and task. No saved uncertainty ranges or raw run archive are available.",
  tag: { label: "SIZE · EXPLORATORY", fill: C.goldSoft, color: "#8B5F00" },
  cropTop: 0.18,
  cropBottom: 0.05,
});

await addEvidenceImageSlide({
  title: "UniMoral + ValuePrism: 3 of 5 size paths change direction",
  subtitle: "Exploratory CEI result. x = published size category, ordered only; y = named metric; labels = model + B.",
  sourcePath: "assets/results/03_size_consequence_relevance_detail.png",
  alt: "Detailed size paths for UniMoral consequence METEOR and ValuePrism relevance accuracy.",
  claim: "Three of five complete consequence and relevance paths change direction across three sizes.",
  howToRead: "x is published model size. y is the metric named in each panel. Text match and accuracy stay separate.",
  boundary: "The CEI ValuePrism test is not a repeat of the paper's Kaleido experiment. No uncertainty ranges were saved.",
  tag: { label: "SIZE · EXPLORATORY", fill: C.goldSoft, color: "#8B5F00" },
  cropTop: 0.18,
  cropBottom: 0.05,
});

await addEvidenceImageSlide({
  title: "UniMoral: Qwen is higher on 3 tasks; DeepSeek on 2",
  subtitle: "Exploratory CEI result. x = later minus earlier score; y = task; metrics stay separate.",
  sourcePath: "assets/results/04_release_period_paths.png",
  alt: "Endpoint changes for Qwen and DeepSeek across UniMoral tasks, with accuracy and METEOR separated.",
  claim: "Later releases are not higher on every task.",
  howToRead: "x is later score minus earlier score. y is task. Right of zero is higher. Left is lower.",
  boundary: "All scores were tested on May 28 or 29, 2026. Release date describes the model, not the test date.",
  tag: { label: "RELEASE · EXPLORATORY", fill: C.goldSoft, color: "#8B5F00" },
  portrait: true,
});

await addEvidenceImageSlide({
  title: "DeepSeek reverses on UniMoral action and typology",
  subtitle: "Exploratory CEI result. x = model release quarter; y = accuracy; labels = model + B.",
  sourcePath: "assets/results/04_release_action_typology_detail.png",
  alt: "Chronological release paths for UniMoral action, typology, and factor accuracy.",
  claim: "The model version changes the result we report.",
  howToRead: "x is model release quarter and y is accuracy. Each point names the model and published size.",
  boundary: "Release quarter is model metadata, not test time. The lines do not show a cause. The available files have no saved uncertainty ranges or raw run archive.",
  tag: { label: "RELEASE · EXPLORATORY", fill: C.goldSoft, color: "#8B5F00" },
  cropTop: 0.18,
  cropBottom: 0.05,
});

await addEvidenceImageSlide({
    title: "UniMoral and ValuePrism: later Qwen falls on consequence and rises on relevance",
    subtitle: "Exploratory CEI result. x = model release quarter; y = named metric; labels = model + B.",
    sourcePath: "assets/results/04_release_period_paths_detail_b.png",
    alt: "Chronological release paths for UniMoral consequence METEOR and ValuePrism relevance accuracy.",
    claim: "Later Qwen falls on consequence text match and rises on ValuePrism relevance.",
    howToRead: "x is model release quarter. y is the metric named in each panel. Each point names a model and size.",
    boundary: "Consequence uses text match. Relevance uses accuracy. Release quarter is model metadata. The available files have no saved uncertainty ranges or raw run archive.",
    tag: { label: "RELEASE · EXPLORATORY", fill: C.goldSoft, color: "#8B5F00" },
    cropTop: 0.10,
    cropBottom: 0.37,
});

// Slide 20: manual bubble scatter for exact direct labels.
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "UniMoral action: 671B DeepSeek releases range from .453 to .660",
    "Every point names the model, release date, published size, and CEI accuracy.",
    { label: "BUBBLE VIEW", fill: C.goldSoft, color: "#8B5F00" },
  );
  const plot = { left: 110, top: 190, width: 810, height: 390 };
  const yMin = 0.40;
  const yMax = 0.72;
  const xMin = Date.parse("2024-09-01T00:00:00Z");
  const xMax = Date.parse("2026-05-15T00:00:00Z");
  const xFor = date => plot.left + ((Date.parse(`${date}T00:00:00Z`) - xMin) / (xMax - xMin)) * plot.width;
  const yFor = value => plot.top + plot.height - ((value - yMin) / (yMax - yMin)) * plot.height;

  [0.4, 0.5, 0.6, 0.7].forEach(tick => {
    const y = yFor(tick);
    addRule(slide, plot.left, y, plot.width, C.grid, 1);
    addText(slide, tick.toFixed(1), { left: 62, top: y - 12, width: 40, height: 24 }, {
      fontSize: 13,
      color: C.muted,
      alignment: "right",
    });
  });
  const dateTicks = [
    ["2024-09-01", "Sep 2024"],
    ["2025-03-01", "Mar 2025"],
    ["2025-09-01", "Sep 2025"],
    ["2026-03-01", "Mar 2026"],
  ];
  dateTicks.forEach(([date, label]) => {
    const x = xFor(date);
    slide.shapes.add({
      geometry: "line",
      position: { left: x, top: plot.top, width: 0, height: plot.height },
      fill: "none",
      line: { style: "solid", fill: C.grid, width: 1 },
    });
    addText(slide, label, { left: x - 48, top: plot.top + plot.height + 8, width: 96, height: 24 }, {
      fontSize: 13,
      color: C.muted,
      alignment: "center",
    });
  });
  slide.shapes.add({
    geometry: "line",
    position: { left: plot.left, top: plot.top + plot.height, width: plot.width, height: 0 },
    fill: "none",
    line: { style: "solid", fill: C.ink, width: 2 },
  });
  slide.shapes.add({
    geometry: "line",
    position: { left: plot.left, top: plot.top, width: 0, height: plot.height },
    fill: "none",
    line: { style: "solid", fill: C.ink, width: 2 },
  });
  addText(slide, "Model release date", { left: 395, top: 622, width: 250, height: 28 }, {
    fontSize: 16,
    bold: true,
    alignment: "center",
  });
  addText(slide, "UniMoral action accuracy", { left: 10, top: 330, width: 220, height: 26 }, {
    fontSize: 15,
    bold: true,
    alignment: "center",
  }).rotation = -90;

  const points = [
    { model: "Qwen2.5-7B Instruct", date: "2024-09-19", score: 0.634904, b: 7.61, label: "7.61B total", color: C.teal, dx: 10, dy: -58, w: 176 },
    { model: "DeepSeek V3-0324", date: "2025-03-24", score: 0.452755, b: 671, label: "671B main / 37B active", color: C.purple, dx: 54, dy: -12, w: 210 },
    { model: "DeepSeek V3.1", date: "2025-08-21", score: 0.660064, b: 671, label: "671B main / 37B active", color: C.purple, dx: -214, dy: -88, w: 210 },
    { model: "DeepSeek V3.2", date: "2025-12-01", score: 0.645606, b: 671, label: "671B main / 37B active", color: C.purple, dx: -115, dy: 55, w: 170 },
    { model: "Qwen3.5-9B", date: "2026-02-27", score: 0.652778, b: 9, label: "9B total", color: C.teal, dx: -104, dy: -78, w: 160 },
    { model: "DeepSeek V4 Flash", date: "2026-04-22", score: 0.639344, b: 284, label: "284B main / 13B active", color: C.purple, dx: -111, dy: 101, w: 175 },
  ];
  points.forEach(point => {
    const x = xFor(point.date);
    const y = yFor(point.score);
    const radius = 6 * Math.sqrt(point.b / 7.61);
    slide.shapes.add({
      geometry: "ellipse",
      position: { left: x - radius, top: y - radius, width: radius * 2, height: radius * 2 },
      fill: `${point.color}CC`,
      line: { style: "solid", fill: C.white, width: 2 },
    });
    const labelX = x + point.dx;
    const labelY = y + point.dy;
    addText(slide, `${point.model}\n${point.date} · ${point.label}\naccuracy ${point.score.toFixed(3)}`, {
      left: labelX,
      top: labelY,
      width: point.w,
      height: 62,
    }, { fontSize: 12, bold: true, color: point.color });
  });
  addText(slide, "Same published size, different scores", { left: 962, top: 208, width: 250, height: 46 }, {
    fontSize: 16,
    bold: true,
    color: "#8B5F00",
  });
  addText(slide, "DeepSeek 671B", { left: 962, top: 278, width: 250, height: 30 }, {
    fontSize: 20, bold: true, color: C.ink,
  });
  addText(slide, ".453   .660   .646", { left: 962, top: 318, width: 250, height: 42 }, {
    fontSize: 25, bold: true, color: C.purple,
  });
  addText(slide, "These 6 points do not show a steady size or date pattern.", {
    left: 962, top: 398, width: 250, height: 76,
  }, { fontSize: 20, bold: true, color: C.ink });
  addText(slide, "Bubble area shows published total or main-model B. DeepSeek labels also show active B.", {
    left: 962, top: 494, width: 250, height: 60,
  }, { fontSize: 14, color: C.muted });
  addText(slide, "Only 6 saved results. No uncertainty ranges. Some served-model details were not saved.", {
    left: 962, top: 574, width: 250, height: 62,
  }, { fontSize: 14, color: C.muted });
  setNotes(slide, [
    "Sources: data/model_release_periods.csv; data/results/release_period_task_points.csv; evidence/model-parameter-sources.csv.",
    "x-axis = verified source_event_date. y-axis = UniMoral action accuracy. Bubble area is proportional to published total/main-model parameters.",
    "Every point is one stored aggregate evaluated May 28-29, 2026. Release date is metadata, not evaluation time.",
    "DeepSeek points show published main and active parameter counts; total/main parameters are not inference compute.",
    "No saved uncertainty estimates or raw-log replay are available for this selected grid.",
  ]);
}

// Slide 21: MoralBench paper result.
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "MoralBench paper: the top model differs across 4 tests",
    "Paper result. It asks whether model choices align with human ratings.",
    { label: "PAPER 1", fill: C.coralSoft, color: C.coral },
  );
  const panels = [
    { title: "MFQ binary · summed score (raw)", max: 65, axisTitle: "Paper summed score (raw)", top: 186, left: 78, values: [54.2, 58.5, 49.9, 54.7, 56.6], best: 1 },
    { title: "Vignette binary · summed score (raw)", max: 60, axisTitle: "Paper summed score (raw)", top: 186, left: 660, values: [48.1, 52.6, 44.4, 50.3, 52.8], best: 4 },
    { title: "MFQ comparison · mean correct choices", max: 20, axisTitle: "Mean correct choices (retained N=20)", top: 424, left: 78, values: [8.2, 8.0, 9.6, 12.4, 9.8], best: 3 },
    { title: "Vignette comparison · mean correct choices", max: 24, axisTitle: "Mean correct choices (retained N=24)", top: 424, left: 660, values: [10.4, 13.2, 10.8, 14.2, 13.8], best: 3 },
  ];
  const models = ["Zephyr", "LLaMA-2", "Gemma-1.1", "GPT-3.5", "GPT-4"];
  panels.forEach(panel => {
    addText(slide, panel.title, { left: panel.left, top: panel.top - 28, width: 520, height: 24 }, {
      fontSize: 16,
      bold: true,
      color: C.ink,
    });
    const chart = slide.charts.add("bar", {
      position: { left: panel.left, top: panel.top, width: 520, height: 185 },
      categories: models,
      series: [{
        name: "Paper result",
        values: panel.values,
        fill: C.blue,
        points: panel.values.map((_, idx) => ({ idx, fill: idx === panel.best ? C.coral : C.blue })),
        valuesFormatCode: "0.0",
      }],
      barOptions: { direction: "bar", grouping: "clustered", gapWidth: 30 },
      xAxis: {
        visible: true,
        textStyle: { typeface: family, fontSize: 10, fill: C.ink },
        line: { fill: "none", width: 0 },
      },
      yAxis: {
        visible: true,
        title: panel.axisTitle,
        min: 0,
        max: panel.max,
        numberFormatCode: "0",
        textStyle: { typeface: family, fontSize: 10, fill: C.muted },
        majorGridlines: { style: "solid", fill: C.grid, width: 1 },
      },
      dataLabels: {
        showValue: true,
        position: "outEnd",
        textStyle: { typeface: family, fontSize: 10, fill: C.ink, bold: true },
      },
      ...chartBase(),
    });
    applyPresentationChartFont(chart, { fontFamily: family });
  });
  addText(slide, "The paper does not report confidence ranges or the maximum binary score. The saved task files contain 20 MFQ and 24 vignette pairs.", {
    left: 90, top: 614, width: 1110, height: 20,
  }, { fontSize: 12, color: C.muted, alignment: "center" });
  addText(slide, "Paper inconsistency: Gemma-1.1 vignette prints 44.4, while its six printed subscores sum to 51.8.", {
    left: 90, top: 634, width: 1110, height: 20,
  }, { fontSize: 12, color: C.coral, bold: true, alignment: "center" });
  addText(slide, "LLaMA-2 has the top MFQ binary score. GPT-4 has the top vignette binary score. GPT-3.5 tops both comparison tests.", {
    left: 90, top: 658, width: 1110, height: 28,
  }, { fontSize: 18, bold: true, color: C.coral, alignment: "center" });
  setNotes(slide, [
    "Source: MoralBench paper, Tables 1 and 2; data/paper_visual_results.csv.",
    "Binary raw totals and comparison correct-point totals are separate scales and are shown in separate panels.",
    "The paper used temperature 0.7 and five repetitions but did not report confidence intervals or significance tests for these tables. The paper does not explicitly state binary denominators or ceilings.",
    "The comparison score is one point per pair. The retained official-style task files contain 20 MFQ and 24 vignette pairs; the dataset fingerprint is not pinned by the paper.",
    "Local MoralBench tasks are approximate protocol bridges, not exact paper replications; do not subtract local and paper scores.",
  ]);
}

// Slide 22: UniMoral question-to-local-reach table.
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "UniMoral paper: CEI does not test all paper questions",
    "No matching CEI test for cues, languages, or story sources; 4 task types are related but different.",
    { label: "PAPER 2", fill: C.coralSoft, color: C.coral },
  );
  const values = [
    ["Paper question", "Paper result", "CEI measure", "Relation"],
    ["Can models predict an annotator's selected action?", "Llama: .5057 to .6617 weighted F1", "No-persona accuracy on annotator labels", "Related task, different score"],
    ["Can models classify moral typology?", "Llama: .1742 to .5701 weighted F1", "No-cue accuracy", "Related task, different score"],
    ["Can models identify the factor behind a choice?", "Llama: .0630 to .3859 weighted F1", "No-cue accuracy", "Related task, different score"],
    ["Can models generate a plausible consequence?", "Derived from 6 paper-table language cells: BLEU .0138, METEOR .0968, BERTScore .7193", "METEOR and offline BERTScore, no BLEU", "Related task, different setup"],
    ["Do cues, language, and story source matter?", "Higher with cues, in some languages, and for psychological rather than Reddit stories", "No matching comparison", "Not tested"],
  ];
  const table = slide.tables.add({
    rows: values.length,
    columns: 4,
    left: 82,
    top: 178,
    width: 1116,
    height: 370,
    columnWidths: [355, 300, 235, 226],
    values,
  });
  styleTable(table, values.length, 4, { bodySize: 15, headerSize: 15, headerFill: C.coral });
  table.cells.block({ row: 1, column: 0, rowCount: 5, columnCount: 1 }).textStyle.bold = true;
  table.cells.block({ row: 1, column: 3, rowCount: 5, columnCount: 1 }).assign({
    fill: C.white,
    textStyle: { typeface: family, fontSize: 15, color: C.ink, bold: true },
  });
  addText(slide, "Paper numbers and CEI numbers are not directly comparable.", {
    left: 92, top: 606, width: 1096, height: 42,
  }, { fontSize: 21, bold: true, alignment: "center" });
  setNotes(slide, [
    "Sources: UniMoral paper; data/paper_visual_results.csv; data/paper_protocol_map.csv; evidence/canonical-audit/PAPER_REPO_EVIDENCE_LEDGER.csv.",
    "Paper headline task families are action prediction, moral typology classification, factor attribution, and consequence generation.",
    "Paper values: Llama-only AP weighted F1 0.5057-0.6617; MTC 0.1742-0.5701; FAA 0.0630-0.3859. Consequence values are derived unweighted means of six displayed language cells: BLEU about 0.0138, METEOR about 0.0968, and multilingual BERTScore about 0.7193.",
    "The paper does not report confidence intervals for these values. The consequence means are analyst-derived, not paper-reported aggregates.",
    "The canonical ledger has 7 approximate and 6 unavailable UniMoral rows. Paper and local metrics differ for AP/MTC/FAA.",
    "Local no-cue runs cannot establish the paper's cue, language, or source-condition findings.",
    "The AP no-persona aggregate still uses annotator-specific target labels; it is not a generic population-level action prediction score.",
    "The local consequence evidence includes live METEOR and a separate 1,782-row offline BERTScore F1 bridge; scorer and protocol identities are not exact.",
  ]);
}

// Slide 23: MoReBench paper bars.
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "MoReBench paper: harmlessness 81.1%, logical process 47.9%",
    "Paper question: which parts of a model's written reasoning before the final answer meet expert criteria?",
    { label: "PAPER 3", fill: C.coralSoft, color: C.coral },
  );
  const chart = slide.charts.add("bar", {
    position: { left: 110, top: 190, width: 790, height: 390 },
    categories: ["Identify / recall", "Process clear", "Process logical", "Outcome helpful", "Outcome harmless"],
    series: [{
      name: "Displayed Table 2 average",
      values: [52.7, 53.6, 47.9, 50.1, 81.1],
      fill: C.blue,
      points: [
        { idx: 0, fill: C.blue },
        { idx: 1, fill: C.blue },
        { idx: 2, fill: C.coral },
        { idx: 3, fill: C.gold },
        { idx: 4, fill: C.teal },
      ],
      valuesFormatCode: "0.0",
    }],
    barOptions: { direction: "bar", grouping: "clustered", gapWidth: 35 },
    xAxis: {
      visible: true,
      textStyle: { typeface: family, fontSize: 15, fill: C.ink },
      line: { fill: "none", width: 0 },
    },
    yAxis: {
      visible: true,
      title: "Expert criteria satisfied (%)",
      min: 0,
      max: 100,
      majorUnit: 20,
      numberFormatCode: "0",
      textStyle: { typeface: family, fontSize: 13, fill: C.muted },
      majorGridlines: { style: "solid", fill: C.grid, width: 1 },
    },
    dataLabels: {
      showValue: true,
      position: "outEnd",
      textStyle: { typeface: family, fontSize: 16, fill: C.ink, bold: true },
    },
    ...chartBase(),
  });
  applyPresentationChartFont(chart, { fontFamily: family });
  addText(slide, "81.1%\nharmless", { left: 958, top: 230, width: 240, height: 92 }, {
    fontSize: 28,
    bold: true,
    color: C.teal,
  });
  addText(slide, "47.9%\nlogical process", { left: 958, top: 350, width: 240, height: 92 }, {
    fontSize: 28, bold: true, color: C.coral,
  });
  addText(slide, "The CEI keyword check is not the same expert review.", {
    left: 958, top: 486, width: 240, height: 64,
  }, { fontSize: 14, color: C.muted });
  addText(slide, "x = expert criteria satisfied (%)", {
    left: 300, top: 586, width: 420, height: 24,
  }, { fontSize: 14, bold: true, color: C.muted, alignment: "center" });
  addText(slide, "Paper Table 2 uses thinking traces: written reasoning before the final answer. Nearby text gives different summaries.", {
    left: 120, top: 616, width: 1050, height: 30,
  }, { fontSize: 15, color: C.muted, alignment: "center" });
  setNotes(slide, [
    "Source: MoReBench paper, displayed Table 2; data/paper_visual_results.csv.",
    "These are displayed averages for thinking traces, which the paper treats as written reasoning before the final answer: Identify 52.7, Clear 53.6, Logical 47.9, Helpful 50.1, Harmless 81.1 percent.",
    "Nearby prose reports 41.5 logical and 77.5 harmless plus different other summaries; this internal conflict is explicitly disclosed.",
    "These are not final-response results. For models whose internal reasoning is not available, the paper says these traces may be generated summaries.",
    "The local four-keyword proxy is not the paper's expert-weighted Regular/Hard score and cannot reproduce this result.",
  ]);
}

// Slide 24: MoralLens order effect.
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "MoralLens paper: reasoning first shifts reasons and choices",
    "Reason score: .230 to .052. Larger-group choices: .641 to .792.",
    { label: "PAPER 4", fill: C.coralSoft, color: C.coral },
  );
  const panels = [
    {
      left: 88,
      top: 190,
      width: 530,
      title: "CD GAP",
      subtitle: "−1 deontological · +1 consequentialist",
      min: -1,
      max: 1,
      post: 0.230,
      pre: 0.052,
      result: "Reasoning first shifts the mean toward duty-based reasons",
    },
    {
      left: 662,
      top: 190,
      width: 530,
      title: "Utility",
      subtitle: "Share choosing the larger group",
      min: 0,
      max: 1,
      post: 0.641,
      pre: 0.792,
      result: "Reasoning first raises larger-group choices",
    },
  ];
  panels.forEach((panel, index) => {
    addCard(slide, { left: panel.left, top: panel.top, width: panel.width, height: 365 }, {
      fill: C.white,
      line: index === 0 ? C.purple : C.teal,
      width: 2,
    });
    addText(slide, panel.title, { left: panel.left + 28, top: panel.top + 24, width: 220, height: 34 }, {
      fontSize: 26,
      bold: true,
      color: index === 0 ? C.purple : C.teal,
    });
    addText(slide, panel.subtitle, { left: panel.left + 28, top: panel.top + 62, width: panel.width - 56, height: 28 }, {
      fontSize: 14,
      color: C.muted,
    });
    const axisLeft = panel.left + 58;
    const axisTop = panel.top + 170;
    const axisWidth = panel.width - 116;
    addRule(slide, axisLeft, axisTop, axisWidth, C.grid, 3);
    const xFor = value => axisLeft + ((value - panel.min) / (panel.max - panel.min)) * axisWidth;
    [panel.min, (panel.min + panel.max) / 2, panel.max].forEach(tick => {
      const x = xFor(tick);
      slide.shapes.add({
        geometry: "line",
        position: { left: x, top: axisTop - 8, width: 0, height: 16 },
        fill: "none",
        line: { style: "solid", fill: C.grid, width: 2 },
      });
      addText(slide, tick.toFixed(index === 0 ? 0 : 1), { left: x - 24, top: axisTop + 12, width: 48, height: 22 }, {
        fontSize: 12,
        color: C.muted,
        alignment: "center",
      });
    });
    const postX = xFor(panel.post);
    const preX = xFor(panel.pre);
    addRule(slide, Math.min(postX, preX), axisTop, Math.abs(postX - preX), index === 0 ? C.purple : C.teal, 5);
    [
      [postX, panel.post, "Decide → explain", C.gold, -54],
      [preX, panel.pre, "Reason → decide", index === 0 ? C.purple : C.teal, 38],
    ].forEach(([x, value, label, color, dy]) => {
      slide.shapes.add({
        geometry: "ellipse",
        position: { left: x - 10, top: axisTop - 10, width: 20, height: 20 },
        fill: color,
        line: { style: "solid", fill: C.white, width: 2 },
      });
      addText(slide, `${label}\n${value.toFixed(3)}`, {
        left: x - 72,
        top: axisTop + dy,
        width: 144,
        height: 43,
      }, { fontSize: 13, bold: true, color, alignment: "center" });
    });
    addText(slide, panel.result, { left: panel.left + 28, top: panel.top + 282, width: panel.width - 56, height: 56 }, {
      fontSize: 20,
      bold: true,
      alignment: "center",
    });
  });
  addText(slide, "The CEI keyword check does not reproduce CD GAP, Utility, or the reasoning-order test.", {
    left: 120, top: 610, width: 1040, height: 32,
  }, { fontSize: 18, bold: true, color: C.coral, alignment: "center" });
  setNotes(slide, [
    "Source: MoralLens paper, Table 2; data/paper_visual_results.csv.",
    "Post-decision to pre-decision: CD GAP 0.230 to 0.052; Utility 0.641 to 0.792.",
    "Because -1 is deontological and +1 consequentialist, reasoning first shifts the mean toward deontology; both overall means remain slightly positive.",
    "Utility is the frequency of choosing the larger group in size-imbalanced scenarios, not moral quality.",
    "The local keyword adapter is proxy-only and cannot reproduce the 16-rationale judge or the reasoning-order effect.",
  ]);
}

// Slide 25: ValuePrism paper scaling.
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "Value Kaleidoscope paper: most gains occur before 3B",
    "Paper question: how do four value-task scores change from 60M to 11B?",
    null,
  );
  const categories = ["60M", "220M", "770M", "3B", "11B"];
  const panels = [
    { left: 78, top: 188, title: "Relevance accuracy", values: [0.660, 0.835, 0.872, 0.884, 0.891], min: 0, max: 1, color: C.teal, format: "0.000" },
    { left: 662, top: 188, title: "Valence accuracy", values: [0.597, 0.745, 0.792, 0.808, 0.819], min: 0, max: 1, color: C.blue, format: "0.000" },
    { left: 78, top: 430, title: "Generation perplexity ↓", values: [2.86, 2.53, 2.34, 2.23, 2.22], min: 2.0, max: 3.0, color: C.gold, format: "0.00" },
    { left: 662, top: 430, title: "Explanation perplexity ↓", values: [5.70, 4.23, 3.52, 3.14, 2.99], min: 2.5, max: 6.0, color: C.purple, format: "0.00" },
  ];
  panels.forEach(panel => {
    addText(slide, panel.title, { left: panel.left, top: panel.top - 28, width: 520, height: 24 }, {
      fontSize: 16,
      bold: true,
    });
    const chart = slide.charts.add("line", {
      position: { left: panel.left, top: panel.top, width: 520, height: 185 },
      categories,
      series: [{
        name: panel.title,
        values: panel.values,
        line: { style: "solid", fill: panel.color, width: 4 },
        marker: { symbol: "circle", size: 8 },
        valuesFormatCode: panel.format,
      }],
      lineOptions: { grouping: "standard", smooth: false, varyColors: false },
      xAxis: {
        visible: true,
        title: "Kaleido variant · categorical spacing",
        textStyle: { typeface: family, fontSize: 10, fill: C.ink },
        line: { style: "solid", fill: C.grid, width: 1 },
        majorGridlines: null,
      },
      yAxis: {
        visible: true,
        title: panel.title.includes("perplexity") ? "Perplexity" : "Test accuracy (fraction)",
        min: panel.min,
        max: panel.max,
        numberFormatCode: panel.format,
        textStyle: { typeface: family, fontSize: 9, fill: C.muted },
        majorGridlines: { style: "solid", fill: C.grid, width: 1 },
      },
      dataLabels: {
        showValue: true,
        position: "outEnd",
        textStyle: { typeface: family, fontSize: 9, fill: C.ink, bold: true },
      },
      ...chartBase(),
    });
    applyPresentationChartFont(chart, { fontFamily: family });
  });
  addText(slide, "Paper result. CEI ValuePrism uses different models and tests. Size labels are evenly spaced, not numeric distance.\nRelevance compares a GPT-4 example for this situation with one from another. Valence uses GPT-4 Supports / Opposes / Either. Not human judgments.", {
    left: 90, top: 620, width: 1100, height: 34,
  }, { fontSize: 12, color: C.muted, alignment: "center" });
  addText(slide, "From 3B to 11B: relevance +.007, valence +.011, generation perplexity −.01, explanation perplexity −.15.", {
    left: 90, top: 658, width: 1100, height: 30,
  }, { fontSize: 18, bold: true, color: C.coral, alignment: "center" });
  setNotes(slide, [
    "Source: Value Kaleidoscope paper, Table 13; data/paper_visual_results.csv.",
    "Relevance and valence are accuracy. Generation and explanation are perplexity where lower is better. They remain separate panels.",
    "The paper reports no confidence intervals or pre-defined saturation threshold; the claim is descriptive, not 'saturation'.",
    "The local ValuePrism route uses different models and protocols. Paper and local scores must not share a comparison axis.",
    "Relevance uses contrastive synthetic labels: a GPT-4-generated positive for this situation versus a negative from other situations.",
    "Valence uses GPT-4 Supports/Opposes/Either targets. Neither accuracy is a human judgment or normative correctness score.",
  ]);
}

// Slide 26: direct evidence-status count. Keep the dense row-level matrix in the source bundle.
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "CEI has 0 exact repeats of UniMoral or Value Kaleidoscope",
    "Across 37 paper-to-CEI comparison rows: 17 are related but different, 4 are indirect, and 16 cannot be compared.",
    null,
  );
  const rows = [
    ["Exact repeat", 0, C.coral],
    ["Related but different", 17, C.gold],
    ["Indirect check", 4, C.purple],
    ["Cannot compare", 16, "#9AA2AA"],
  ];
  const barLeft = 390;
  const barWidth = 610;
  rows.forEach(([label, value, color], index) => {
    const top = 200 + index * 92;
    addText(slide, label, { left: 100, top: top + 10, width: 260, height: 36 }, {
      fontSize: 22,
      bold: true,
    });
    slide.shapes.add({
      geometry: "rect",
      position: { left: barLeft, top: top + 12, width: barWidth, height: 30 },
      fill: "#E8E7E2",
      line: { fill: "none", width: 0 },
    });
    if (value > 0) {
      slide.shapes.add({
        geometry: "rect",
        position: { left: barLeft, top: top + 12, width: barWidth * value / 37, height: 30 },
        fill: color,
        line: { fill: "none", width: 0 },
      });
    } else {
      addRule(slide, barLeft, top + 27, 8, color, 5);
    }
    addText(slide, `${value} of 37`, { left: 1025, top: top + 4, width: 150, height: 46 }, {
      fontSize: 24,
      bold: true,
      color,
      alignment: "right",
    });
  });
  addText(slide, "Scope: 13 UniMoral rows + 24 ValuePrism rows. Related evidence is not a repeat of the paper test.", {
    left: 100, top: 598, width: 1080, height: 34,
  }, { fontSize: 18, bold: true, alignment: "center" });
  addText(slide, "The detailed row-by-row matrix is in the evidence audit folder.", {
    left: 100, top: 645, width: 1080, height: 24,
  }, { fontSize: 13, color: C.muted, alignment: "center" });
}

// Slides 27-31: zoomed panels keep every model and B label legible at presentation size.
await addEvidenceImageSlide({
  title: "UniMoral: different models have the highest saved score",
  subtitle: "CEI local result. x = model; y = task score; dot = score; line = saved 95% range.",
  sourcePath: "assets/results/01_common_roster_task_results.png",
  alt: "Four UniMoral task panels showing model scores and saved uncertainty ranges for the same five models.",
  claim: "The highest saved score belongs to different models on different UniMoral tasks.",
  howToRead: "Within each panel, x is model and y is the named score. A dot is the score. A line is its 95% range.",
  boundary: "Accuracy and text match stay separate. These ranges are not direct tests between two models.",
  tag: { label: "DETAIL", fill: C.tealSoft, color: C.teal },
  cropTop: 0.53,
  cropBottom: 0.08,
});

await addEvidenceImageSlide({
  title: "UniMoral factor size: Gemma rises; Qwen and Llama reverse",
  subtitle: "Exploratory CEI result. x = published size category, ordered only; y = factor accuracy; labels = model + B.",
  sourcePath: "assets/results/03_size_factor_detail.png",
  alt: "Detailed model-size paths for UniMoral factor accuracy.",
  claim: "Gemma rises at both size steps. Qwen and Llama change direction.",
  howToRead: "Move left to right within one family. Each point names the model and its published size.",
  boundary: "Size is not isolated from training differences. The available files have no saved uncertainty ranges or raw run archive.",
  tag: { label: "DETAIL", fill: C.goldSoft, color: "#8B5F00" },
  cropTop: 0.12,
  cropBottom: 0.08,
});

await addEvidenceImageSlide({
  title: "ValuePrism valence size: Llama falls, then rises",
  subtitle: "Exploratory CEI result. x = published size category, ordered only; y = valence accuracy; labels = model + B.",
  sourcePath: "assets/results/03_size_valence_detail.png",
  alt: "Detailed model-size path for ValuePrism valence accuracy.",
  claim: "The complete Llama path falls from 3B to 8B, then rises at 70B.",
  howToRead: "Move left to right along the Llama line. Each point names the model and its published size.",
  boundary: "Only Llama has all three sizes. CEI ValuePrism is not the paper's Kaleido test. The available files have no saved uncertainty ranges or raw run archive.",
  tag: { label: "DETAIL", fill: C.goldSoft, color: "#8B5F00" },
  cropTop: 0.12,
  cropBottom: 0.08,
});

await addEvidenceImageSlide({
  title: "UniMoral factor releases: DeepSeek falls .038; Qwen changes .002",
  subtitle: "Exploratory CEI result. x = model release quarter; y = factor accuracy; labels = model + B.",
  sourcePath: "assets/results/04_release_factor_detail.png",
  alt: "Chronological release paths for UniMoral factor accuracy.",
  claim: "From first to last saved release, DeepSeek is lower and Qwen is nearly unchanged.",
  howToRead: "Move left to right within one family. Each point names the model and its published size.",
  boundary: "Release quarter is model metadata, not test time. It does not explain the change. All scores were tested in May 2026; no saved uncertainty ranges.",
  tag: { label: "DETAIL", fill: C.goldSoft, color: "#8B5F00" },
  cropTop: 0.12,
  cropBottom: 0.08,
});

await addEvidenceImageSlide({
  title: "ValuePrism valence releases: Qwen +.187; DeepSeek -.062",
  subtitle: "Exploratory CEI result. x = model release quarter; y = valence accuracy; labels = model + B.",
  sourcePath: "assets/results/04_release_valence_detail.png",
  alt: "Chronological release paths for ValuePrism valence accuracy.",
  claim: "From first to last saved release, Qwen is higher and DeepSeek is lower.",
  howToRead: "Move left to right within one family. Each point names the model and its published size.",
  boundary: "Release quarter is model metadata, not test time. CEI ValuePrism is not the paper's Kaleido test. The available files have no saved uncertainty ranges or raw run archive.",
  tag: { label: "DETAIL", fill: C.goldSoft, color: "#8B5F00" },
  cropTop: 0.12,
  cropBottom: 0.08,
});

// Slide 32: readable action order after the evidence appendix.
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "Next: check the current evidence before buying more model runs",
    "Research priority, not a model result. Read from top to bottom.",
    null,
  );
  const actions = [
    ["Review 12 cases where parsing may be wrong", "no new model runs", C.teal],
    ["Check duplicate labels and verify scores using the paper's method", "no new model runs", C.teal],
    ["Run human validation", "human study", "#C878A7"],
    ["Add MoralBench comparison items", "new items + reruns", C.blue],
    ["Rerun 14 answers that hit the length limit, using one fixed limit", "targeted runs", C.gold],
    ["Complete 30 image and text results only if needed", "high cost", "#9AA2AA"],
    ["Repeat Kaleido and UniMoral paper conditions only if we plan a replication claim", "model access + scoring", "#D65A00"],
  ];
  actions.forEach(([action, cost, color], index) => {
    const top = 164 + index * 66;
    addText(slide, String(index + 1), { left: 84, top: top + 1, width: 42, height: 34 }, {
      fontSize: 22,
      bold: true,
      color,
      alignment: "center",
    });
    addText(slide, action, { left: 145, top, width: 785, height: 34 }, {
      fontSize: 18,
      bold: true,
    });
    addText(slide, cost, { left: 960, top: top + 1, width: 235, height: 32 }, {
      fontSize: 16,
      bold: true,
      color,
      alignment: "right",
    });
    if (index < actions.length - 1) addRule(slide, 145, top + 49, 1050, C.grid, 1);
  });
  addText(slide, "Run paid models only after these checks.", {
    left: 145, top: 646, width: 1050, height: 30,
  }, { fontSize: 18, bold: true, color: C.coral });
}

await addCoreSlide(8, "MoralBench and UniMoral: what we can report now.");

const speakerNotesPath = path.join(workspaceDir, "data", "full_slide_speaker_notes.json");
const speakerNotes = JSON.parse(await fs.readFile(speakerNotesPath, "utf8"));
const slideItems = presentation.slides.items;
if (!Array.isArray(speakerNotes) || speakerNotes.length !== 33 || slideItems.length !== 33) {
  throw new Error("The full deck and speaker-note file must each contain exactly 33 slides.");
}
const seenNoteSlides = new Set();
for (const entry of speakerNotes) {
  const requiredFields = ["context", "read", "meaning", "limit", "sources"];
  if (!Number.isInteger(entry.slide) || entry.slide < 1 || entry.slide > 33 || seenNoteSlides.has(entry.slide)) {
    throw new Error(`Invalid or duplicate speaker-note slide number: ${entry.slide}`);
  }
  for (const field of requiredFields) {
    if (typeof entry[field] !== "string" || entry[field].trim() === "") {
      throw new Error(`Slide ${entry.slide} speaker notes are missing ${field}.`);
    }
  }
  seenNoteSlides.add(entry.slide);
  setNotes(slideItems[entry.slide - 1], [
    `Context: ${entry.context}`,
    `How to read: ${entry.read}`,
    `Meaning: ${entry.meaning}`,
    `Limit: ${entry.limit}`,
    "Reference only:",
    `Sources: ${entry.sources}`,
  ]);
}

const requirements = {
  explicitTotalSlideCount: 33,
  requiredNativeTableOwnerSlides: [7, 22],
  requiredNativeChartOwnerSlides: [8, 21, 23, 25],
  materializeLiteralChartWorkbooks: true,
};
const buildDir = path.join(workspaceDir, ".codex-full-slides-build");
const candidateDir = path.join(buildDir, "candidates");
const validatedDir = path.join(buildDir, "validated");
const receiptDir = path.join(buildDir, "receipts");
await fs.mkdir(candidateDir, { recursive: true });
await fs.mkdir(validatedDir, { recursive: true });
await fs.mkdir(receiptDir, { recursive: true });
await fs.mkdir(path.dirname(OUTPUT_PPTX), { recursive: true });
const buildId = `${Date.now()}-${process.pid}`;
const candidatePath = path.join(candidateDir, `candidate-${buildId}.pptx`);
const validatedPath = path.join(validatedDir, `validated-${buildId}.pptx`);
const receiptPath = path.join(receiptDir, `validation-${buildId}.json`);
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const result = await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath: validatedPath,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
    "--require-native-table-slide", "7",
    "--require-native-table-slide", "22",
  ],
  requiredNativeTableOwnerSlides: requirements.requiredNativeTableOwnerSlides,
  fontPolicy: { basis: "design", families: [family] },
  verifyArtifactToolImport: true,
  receiptPath,
});

const tempOutput = `${OUTPUT_PPTX}.${buildId}.tmp`;
await fs.copyFile(validatedPath, tempOutput);
await fs.rename(tempOutput, OUTPUT_PPTX);
const outputBytes = await fs.readFile(OUTPUT_PPTX);
const outputSha256 = createHash("sha256").update(outputBytes).digest("hex");
if (outputSha256 !== result.finalSha256) {
  throw new Error(`Published full deck hash ${outputSha256} differs from validated hash ${result.finalSha256}.`);
}

process.stdout.write(`${JSON.stringify({
  output: OUTPUT_PPTX,
  slides: 33,
  outputSha256,
  receiptPath,
  result,
}, null, 2)}\n`);
