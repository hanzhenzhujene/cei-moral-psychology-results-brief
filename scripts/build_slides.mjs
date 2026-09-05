import fs from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import { spawn } from "node:child_process";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

const workspaceDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SKILL_DIR = process.env.PRESENTATIONS_SKILL_DIR;
const RUNTIME_PYTHON = process.env.WORKSPACE_PYTHON;
const VALIDATION_PYTHON = process.env.VALIDATION_PYTHON;
const ARTIFACT_TOOL_DIR = process.env.ARTIFACT_TOOL_DIR;
const RUNTIME_NODE_MODULES = process.env.RUNTIME_NODE_MODULES;
const SLIDE_DECK_OUTPUT = process.env.SLIDE_DECK_OUTPUT;

for (const [name, value] of Object.entries({
  PRESENTATIONS_SKILL_DIR: SKILL_DIR,
  WORKSPACE_PYTHON: RUNTIME_PYTHON,
  VALIDATION_PYTHON,
  ARTIFACT_TOOL_DIR,
  RUNTIME_NODE_MODULES,
  SLIDE_DECK_OUTPUT,
})) {
  if (!value || !path.isAbsolute(value)) {
    throw new Error(`${name} must be set to an absolute path.`);
  }
}

function runChecked(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      ...options,
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", chunk => { stdout += chunk; });
    child.stderr.on("data", chunk => { stderr += chunk; });
    child.once("error", reject);
    child.once("exit", (code, signal) => {
      if (code === 0) {
        resolve({ stdout, stderr });
        return;
      }
      reject(new Error(
        `Command failed (${signal ?? code}): ${command}\n${stderr || stdout}`,
      ));
    });
  });
}

const { Presentation, PresentationFile } = await import(pathToFileURL(
  path.join(ARTIFACT_TOOL_DIR, "dist/artifact_tool.mjs"),
).href);

const TMP_DIR = path.join(workspaceDir, ".codex-slides-build");
const DECK_NAME = "cei-moral-psychology-results-deck.pptx";
const PUBLIC_PPTX = path.join(workspaceDir, "slides", DECK_NAME);
const FINAL_PPTX = path.resolve(SLIDE_DECK_OUTPUT);
const outputParent = path.dirname(FINAL_PPTX);
const stagingRoot = path.dirname(outputParent);
if (
  FINAL_PPTX === PUBLIC_PPTX
  || path.basename(FINAL_PPTX) !== DECK_NAME
  || path.basename(outputParent) !== "slides"
  || path.dirname(stagingRoot) !== workspaceDir
  || !path.basename(stagingRoot).startsWith(".codex-slide-release-")
) {
  throw new Error("SLIDE_DECK_OUTPUT must be the publisher-created private staging deck path.");
}

const {
  resolvePresentationFont,
  applyPresentationChartFont,
  finalizePresentation,
} = await import(pathToFileURL(
  path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs"),
).href);

await fs.mkdir(TMP_DIR, { recursive: true });
await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
const workspaceReal = await fs.realpath(workspaceDir);
const outputParentReal = await fs.realpath(path.dirname(FINAL_PPTX));
const stagingRootReal = path.dirname(outputParentReal);
if (
  path.basename(outputParentReal) !== "slides"
  || path.dirname(stagingRootReal) !== workspaceReal
  || !path.basename(stagingRootReal).startsWith(".codex-slide-release-")
) {
  throw new Error("SLIDE_DECK_OUTPUT staging path resolves outside the workspace release directory.");
}

const family = resolvePresentationFont({ fontFamily: "Aptos" });
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

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
    position: { left: 1024, top: 40, width: 184, height: 34 },
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
    fontSize: 36,
    bold: true,
    autoFit: "shrinkText",
  });
  if (subtitle) {
    addText(slide, subtitle, { left: 82, top: 99, width: 1060, height: 36 }, {
      name: "slide-subtitle",
      fontSize: 18,
      color: C.muted,
    });
  }
  addRule(slide, 72, 142, 1136, C.grid, 1);
}

function styleTable(table, rows, columns, options = {}) {
  table.borders.assign({ style: "solid", fill: C.grid, width: 1 });
  table.cells.block({ row: 0, column: 0, rowCount: rows, columnCount: columns }).assign({
    fill: C.white,
    textStyle: { typeface: family, fontSize: options.bodySize ?? 17, color: C.ink },
    margins: { left: 12, right: 12, top: 7, bottom: 7 },
  });
  table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount: columns }).assign({
    fill: options.headerFill ?? C.ink,
    textStyle: { typeface: family, fontSize: options.headerSize ?? 16, color: C.white, bold: true },
  });
}

function setNotes(slide, lines) {
  slide.speakerNotes.textFrame.setText(lines);
  slide.speakerNotes.setVisible(true);
}

// Slide 1: decision
{
  const slide = presentation.slides.add();
  slide.background.fill = C.bg;
  addText(slide, "MoralBench + UniMoral", {
    left: 88, top: 100, width: 1080, height: 70,
  }, { name: "cover-title", fontSize: 52, bold: true, autoFit: "shrinkText" });
  addText(slide, "No model has the highest saved score on all 8 tasks.", {
    left: 92, top: 200, width: 1050, height: 72,
  }, { fontSize: 34, color: C.teal, bold: true });
  addRule(slide, 92, 304, 1040, C.grid, 2);
  addText(slide, "MoralBench comparison", {
    left: 92, top: 344, width: 330, height: 30,
  }, { fontSize: 18, color: C.muted, bold: true });
  addText(slide, "For every model pair, the two models' 95% score ranges overlap: 28 of 28 MFQ pairs and 45 of 45 vignette pairs.", {
    left: 92, top: 380, width: 1010, height: 52,
  }, { fontSize: 24, color: C.ink, autoFit: "shrinkText" });
  addText(slide, "UniMoral model size and release date", {
    left: 92, top: 466, width: 410, height: 30,
  }, { fontSize: 18, color: C.muted, bold: true });
  addText(slide, "Scores move up and down across tasks. Bigger or newer is not consistently higher here.", {
    left: 92, top: 502, width: 1010, height: 52,
  }, { fontSize: 24, color: C.ink, autoFit: "shrinkText" });
  addText(slide, "CEI research lead readout · 4 September 2026", {
    left: 92, top: 626, width: 760, height: 30,
  }, { fontSize: 17, color: C.muted });
  setNotes(slide, [
    "This is a CEI MoralBench and UniMoral summary for a research lead.",
    "Sources: docs/RESEARCH_LEAD_BRIEF.md; data/results/research_question_takeaways.csv.",
    "No model has the highest saved score on all eight tasks. The MoralBench comparison ranges do not identify a clear leader.",
    "These tasks do not show that one model is morally better or support one overall score.",
  ]);
}

// Slide 2: task leaders
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "MoralBench + UniMoral: no model has the top saved score on all 8 tasks",
    "CEI local result. Same five models; each row keeps its own score type.",
    { label: "MAIN RESULTS", fill: C.tealSoft, color: C.teal },
  );
  const values = [
    ["Task", "Highest saved score", "Score type", "Model"],
    ["MFQ agreement\nTrack benchmark human ratings of value statements", ".884", "Agreement score", "GPT-5.4 mini"],
    ["Vignette agreement\nTrack benchmark human ratings of moral stories", ".920", "Agreement score", "GPT-5.4"],
    ["MFQ compare\nPick the higher-rated value statement", ".550", "Accuracy", "Haiku + Qwen tie†"],
    ["Vignette compare\nPick the higher-rated moral story", ".625", "Accuracy", "Haiku + GPT-5.4 tie†"],
    ["UniMoral action\nMatch one recorded human choice", ".668", "Accuracy", "Claude Haiku 4.5"],
    ["UniMoral typology\nClassify the recorded choice into one of four types", ".651", "Accuracy", "Claude Opus 4.8"],
    ["UniMoral factor\nPick a top-rated factor for the recorded choice", ".609", "Accuracy", "Claude Haiku 4.5"],
    ["UniMoral consequence\nWrite what could happen next", ".152", "Text-match score", "Claude Opus 4.8"],
  ];
  const table = slide.tables.add({
    rows: values.length,
    columns: 4,
    left: 96,
    top: 170,
    width: 1088,
    height: 430,
    columnWidths: [400, 190, 210, 288],
    values,
  });
  styleTable(table, values.length, 4, { bodySize: 17, headerSize: 16 });
  table.cells.block({ row: 1, column: 0, rowCount: 8, columnCount: 1 }).assign({
    textStyle: { typeface: family, fontSize: 13, color: C.ink },
    margins: { left: 12, right: 12, top: 4, bottom: 4 },
  });
  table.cells.block({ row: 1, column: 3, rowCount: 8, columnCount: 1 }).assign({
    fill: C.white,
    textStyle: { typeface: family, fontSize: 17, color: C.ink, bold: true },
  });
  addText(slide, "† Every 95% range overlaps on both MoralBench comparison tasks. The apparent leaders are unresolved.", {
    left: 96, top: 620, width: 1080, height: 30,
  }, { fontSize: 16, color: C.coral, autoFit: "shrinkText" });
  addText(slide, "Each task uses its own score. Do not compare numbers from different rows.", {
    left: 96, top: 652, width: 1080, height: 26,
  }, { fontSize: 15, color: C.muted });
  setNotes(slide, [
    "Each row shows the highest saved point estimate for that task among Claude Haiku 4.5, Claude Opus 4.8, GPT-5.4, GPT-5.4 mini, and Qwen3 8B.",
    "Sources: data/results/common_roster_primary.csv; docs/PAPER_REVIEW.md protocol comparison; evidence/canonical-audit/CLAIM_BOUNDARIES.md.",
    "The MFQ compare top value is shared by Claude Haiku 4.5 and Qwen3 8B. The vignette compare top value is shared by Claude Haiku 4.5 and GPT-5.4.",
    "The UniMoral action, typology, and factor rows match saved annotator-specific labels under no-persona prompts; the consequence row matches generated text to saved human references. None infers a person's stable moral identity.",
    "Values belong to different metrics. Agreement, accuracy, and text match stay separate and should not be averaged.",
  ]);
}

// Slide 3: comparison overlap
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "MoralBench: each pair of models has overlapping 95% score ranges",
    "CEI local result. MFQ uses 8 models and 20 questions. Vignettes use 10 models and 24 questions.",
    { label: "MAIN RESULTS", fill: C.tealSoft, color: C.teal },
  );
  addText(slide, "MFQ value statements", { left: 110, top: 200, width: 460, height: 34 }, {
    fontSize: 23, bold: true, alignment: "center",
  });
  addText(slide, "28 / 28", { left: 110, top: 252, width: 460, height: 80 }, {
    fontSize: 58, bold: true, color: C.coral, alignment: "center",
  });
  addText(slide, "model pairs have overlapping 95% score ranges", { left: 110, top: 342, width: 460, height: 42 }, {
    fontSize: 18, color: C.ink, alignment: "center",
  });
  addText(slide, "Moral vignettes", { left: 710, top: 200, width: 460, height: 34 }, {
    fontSize: 23, bold: true, alignment: "center",
  });
  addText(slide, "45 / 45", { left: 710, top: 252, width: 460, height: 80 }, {
    fontSize: 58, bold: true, color: C.coral, alignment: "center",
  });
  addText(slide, "model pairs have overlapping 95% score ranges", { left: 710, top: 342, width: 460, height: 42 }, {
    fontSize: 18, color: C.ink, alignment: "center",
  });
  slide.shapes.add({
    geometry: "line",
    position: { left: 640, top: 205, width: 0, height: 175 },
    fill: "none",
    line: { style: "solid", fill: C.grid, width: 2 },
  });
  addText(slide, "These saved results do not separate a leader.", {
    left: 120, top: 456, width: 1040, height: 42,
  }, { fontSize: 27, bold: true, color: C.ink, alignment: "center" });
  addText(slide, "The ranges are not a direct model-pair test. Question-level scores and stronger uncertainty estimates are unavailable.", {
    left: 120, top: 522, width: 1040, height: 45,
  }, { fontSize: 16, color: C.muted, alignment: "center" });
  setNotes(slide, [
    "Source: evidence/canonical-audit/figures/data/primary_confidence_intervals.csv.",
    "The MFQ test has 8 models and 20 questions. The vignette test has 10 models and 24 questions.",
    "For every model pair, the two models' saved 95% score ranges overlap. This covers all 28 MFQ pairs and all 45 vignette pairs.",
    "This is not a paired model-difference test. Question-level scores and stronger uncertainty estimates are missing.",
  ]);
}

// Slide 4: size-path count
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "UniMoral: only 4 of 12 family and task comparisons rise twice",
    "Exploratory CEI result. Each comparison follows one model family on one task across three sizes.",
    { label: "EXPLORATORY", fill: C.goldSoft, color: "#8B5F00" },
  );
  const chart = slide.charts.add("bar", {
    position: { left: 150, top: 190, width: 980, height: 330 },
    title: "What happens across three model versions?",
    titlePlacement: "none",
    categories: ["Rise at both steps", "Change direction", "Fall at both steps"],
    series: [{
      name: "Complete paths",
      values: [4, 7, 1],
      fill: C.teal,
      points: [
        { idx: 0, fill: C.teal, line: { fill: "none", width: 0 } },
        { idx: 1, fill: C.gold, line: { fill: "none", width: 0 } },
        { idx: 2, fill: C.purple, line: { fill: "none", width: 0 } },
      ],
      valuesFormatCode: "0",
    }],
    barOptions: { direction: "bar", grouping: "clustered", gapWidth: 42 },
    hasLegend: false,
    xAxis: {
      visible: true,
      title: "Family and task combinations (12 total)",
      min: 0,
      max: 12,
      majorUnit: 3,
      numberFormatCode: "0",
      textStyle: { typeface: family, fontSize: 14, fill: C.muted },
      majorGridlines: { style: "solid", fill: C.grid, width: 1 },
    },
    yAxis: {
      visible: true,
      textStyle: { typeface: family, fontSize: 18, fill: C.ink },
      line: { fill: "none", width: 0 },
    },
    dataLabels: {
      showValue: true,
      position: "outEnd",
      textStyle: { typeface: family, fontSize: 20, fill: C.ink, bold: true },
    },
    chartFill: C.bg,
    chartLine: { fill: "none", width: 0 },
    plotAreaFill: C.bg,
    plotAreaLine: { fill: "none", width: 0 },
  });
  applyPresentationChartFont(chart, { fontFamily: family });
  addText(slide, "Each bar counts one model family on one task across three saved sizes.", {
    left: 150, top: 526, width: 900, height: 24,
  }, { fontSize: 14, color: C.muted });
  addText(slide, "4 rise twice · 7 change direction · 1 falls twice", {
    left: 150, top: 568, width: 860, height: 40,
  }, { fontSize: 26, bold: true, color: C.ink });
  addText(slide, "This is exploratory. Model versions also differ in training and release, and no confidence ranges were saved.", {
    left: 150, top: 618, width: 920, height: 30,
  }, { fontSize: 16, color: C.muted });
  setNotes(slide, [
    "Sources: data/results/size_path_summary.csv; data/results/size_task_points.csv.",
    "The 12 checks cover three model families and four UniMoral tasks. Each check follows three model sizes.",
    "Four checks rise twice, seven change direction, and one falls twice.",
    "Accuracy and METEOR stay separate. No saved uncertainty ranges or raw run archive are available.",
  ]);
}

// Slide 5: size example
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "UniMoral Gemma: factor rises while typology falls",
    "Exploratory CEI result. Gemma 3 at 4B, 12B, and 27B; the vertical axis is zoomed.",
    { label: "EXPLORATORY", fill: C.goldSoft, color: "#8B5F00" },
  );
  const chart = slide.charts.add("line", {
    position: { left: 105, top: 180, width: 1070, height: 410 },
    title: "Gemma 3 accuracy by model size",
    titlePlacement: "none",
    titleTextStyle: { typeface: family, fontSize: 20, fill: C.ink, bold: true },
    categories: ["Gemma 3-4B-IT\n(4B total)", "Gemma 3-12B-IT\n(12B total)", "Gemma 3-27B-IT\n(27B total)"],
    series: [
      {
        name: "Factor attribution",
        values: [0.578, 0.601, 0.613],
        line: { style: "solid", fill: "#2B78B8", width: 4 },
        marker: { symbol: "circle", size: 10 },
        valuesFormatCode: "0.000",
      },
      {
        name: "Moral typology",
        values: [0.597, 0.579, 0.570],
        line: { style: "dashed", fill: C.purple, width: 4 },
        marker: { symbol: "square", size: 10 },
        valuesFormatCode: "0.000",
      },
    ],
    lineOptions: { grouping: "standard", smooth: false, varyColors: false },
    hasLegend: true,
    legend: {
      position: "bottom",
      overlay: false,
      textStyle: { typeface: family, fontSize: 15, fill: C.ink },
    },
    xAxis: {
      visible: true,
      title: "Gemma variants ordered by published total parameters",
      textStyle: { typeface: family, fontSize: 15, fill: C.ink },
      line: { style: "solid", fill: C.grid, width: 1 },
      majorGridlines: null,
    },
    yAxis: {
      visible: true,
      title: "Accuracy",
      min: 0.54,
      max: 0.625,
      majorUnit: 0.02,
      numberFormatCode: "0.00",
      textStyle: { typeface: family, fontSize: 13, fill: C.muted },
      majorGridlines: { style: "solid", fill: C.grid, width: 1 },
    },
    dataLabels: {
      showValue: true,
      position: "outEnd",
      textStyle: { typeface: family, fontSize: 14, fill: C.ink, bold: true },
    },
    chartFill: C.bg,
    chartLine: { fill: "none", width: 0 },
    plotAreaFill: C.bg,
    plotAreaLine: { fill: "none", width: 0 },
  });
  applyPresentationChartFont(chart, { fontFamily: family });
  addText(slide, "4B to 27B: factor accuracy +.034 · moral typology accuracy −.027", {
    left: 118, top: 612, width: 730, height: 34,
  }, { fontSize: 21, bold: true, color: C.ink });
  addText(slide, "Each point is one saved task score. No uncertainty range or raw run archive is available.", {
    left: 118, top: 650, width: 920, height: 26,
  }, { fontSize: 15, color: C.muted });
  setNotes(slide, [
    "Sources: data/results/size_path_summary.csv; data/results/size_task_points.csv; evidence/model-parameter-sources.csv.",
    "Exact values: factor attribution .578 to .601 to .613; moral typology .597 to .579 to .570.",
    "Factor accuracy rises while moral typology accuracy falls as the named Gemma variants get larger.",
    "No saved uncertainty ranges or raw run archive are available. The versions also differ in training.",
  ]);
}

// Slide 6: release endpoints
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "UniMoral releases: Qwen rises on 3 tasks, DeepSeek on 2",
    "Exploratory CEI result. Later score minus earlier score; consequence uses text match.",
    { label: "EXPLORATORY", fill: C.goldSoft, color: "#8B5F00" },
  );
  addText(slide, "Qwen: Qwen2.5 7B Instruct · 2024-09-19 · 7.61B total to Qwen3.5 9B · 2026-02-27 · 9B total", {
    left: 110, top: 158, width: 1000, height: 26,
  }, { fontSize: 14, color: C.teal, bold: true, autoFit: "shrinkText" });
  addText(slide, "DeepSeek: V3-0324 · 2025-03-24 · 671B main / 37B active to V4 Flash · 2026-04-22 · 284B main / 13B active", {
    left: 110, top: 186, width: 1060, height: 26,
  }, { fontSize: 14, color: C.purple, bold: true, autoFit: "shrinkText" });
  addText(slide, "DeepSeek labels show published main-model B and active B used per token.", {
    left: 110, top: 212, width: 980, height: 20,
  }, { fontSize: 12, color: C.muted });
  const chart = slide.charts.add("bar", {
    position: { left: 120, top: 238, width: 1030, height: 310 },
    title: "Accuracy change from earlier to later version",
    titlePlacement: "none",
    categories: ["Action", "Typology", "Factor"],
    series: [
      {
        name: "Qwen",
        values: [0.017873, 0.042383, 0.002005],
        fill: C.teal,
        valuesFormatCode: "+0.000;-0.000;0.000",
      },
      {
        name: "DeepSeek",
        values: [0.186589, -0.003150, -0.037514],
        fill: C.purple,
        valuesFormatCode: "+0.000;-0.000;0.000",
      },
    ],
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 52 },
    hasLegend: true,
    legend: {
      position: "bottom",
      overlay: false,
      textStyle: { typeface: family, fontSize: 15, fill: C.ink },
    },
    xAxis: {
      visible: true,
      title: "UniMoral task",
      textStyle: { typeface: family, fontSize: 15, fill: C.ink },
      line: { style: "solid", fill: C.grid, width: 1 },
      majorGridlines: null,
    },
    yAxis: {
      visible: true,
      title: "Change in accuracy",
      min: -0.05,
      max: 0.20,
      majorUnit: 0.05,
      numberFormatCode: "+0.00;-0.00;0.00",
      textStyle: { typeface: family, fontSize: 13, fill: C.muted },
      majorGridlines: { style: "solid", fill: C.grid, width: 1 },
    },
    dataLabels: {
      showValue: true,
      position: "outEnd",
      textStyle: { typeface: family, fontSize: 14, fill: C.ink, bold: true },
    },
    chartFill: C.bg,
    chartLine: { fill: "none", width: 0 },
    plotAreaFill: C.bg,
    plotAreaLine: { fill: "none", width: 0 },
  });
  applyPresentationChartFont(chart, { fontFamily: family });
  addText(slide, "Across all 4 tasks: Qwen is higher on 3 and lower on 1. DeepSeek is higher on 2 and lower on 2.", {
    left: 120, top: 560, width: 1030, height: 28,
  }, { fontSize: 18, bold: true, color: C.ink });
  addText(slide, "Separate metric · Consequence text match (METEOR): Qwen −.027 · DeepSeek +.019", {
    left: 120, top: 590, width: 1030, height: 26,
  }, { fontSize: 16, bold: true, color: C.coral });
  addText(slide, "All scores were tested 28–29 May 2026. Release date describes the model, not the test date. No uncertainty ranges were saved.", {
    left: 120, top: 628, width: 1030, height: 30,
  }, { fontSize: 14, color: C.muted });
  setNotes(slide, [
    "Sources: data/results/release_path_summary.csv; data/results/release_period_task_points.csv; data/model_release_periods.csv; evidence/model-parameter-sources.csv.",
    "Classification accuracy deltas shown: Qwen action +.017873, typology +.042383, factor +.002005; DeepSeek action +.186589, typology -.003150, factor -.037514.",
    "Consequence uses a separate text-match score. Its changes are Qwen -.026780 and DeepSeek +.018985.",
    "Every shown score was tested on 28 or 29 May 2026. Release date describes the model and does not show a cause.",
  ]);
}

// Slide 7: papers
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "How the local tests relate to five papers",
    "MoralBench, UniMoral, MoReBench, MoralLens, and Value Kaleidoscope",
    { label: "PAPER REVIEW", fill: C.purpleSoft, color: C.purple },
  );
  const values = [
    ["Paper", "What it asks", "Closest local evidence"],
    ["MoralBench", "Do model choices match human ratings?", "Related tasks, different setup"],
    ["UniMoral", "Can models predict actions, types, factors, and consequences?", "Narrower versions of four tasks"],
    ["MoReBench", "Does reasoning meet expert criteria?", "Keyword check only"],
    ["MoralLens", "Does reasoning order change reasons and choices?", "Keyword check only"],
    ["Value Kaleidoscope", "How do value tasks change with model size?", "Different models and scoring"],
  ];
  const table = slide.tables.add({
    rows: values.length,
    columns: 3,
    left: 82,
    top: 174,
    width: 1116,
    height: 402,
    columnWidths: [210, 590, 316],
    values,
  });
  styleTable(table, values.length, 3, { bodySize: 16, headerSize: 16, headerFill: C.purple });
  table.cells.block({ row: 1, column: 0, rowCount: 5, columnCount: 1 }).textStyle.bold = true;
  addText(slide, "None of the five is reproduced exactly. Paper scores and local scores stay separate.", {
    left: 92, top: 610, width: 1096, height: 34,
  }, { fontSize: 20, bold: true, color: C.ink, alignment: "center" });
  setNotes(slide, [
    "Sources: docs/PAPER_REVIEW.md; data/paper_protocol_map.csv.",
    "The five papers ask different questions and use different models, data, prompts, or scores.",
    "None is reproduced exactly by the CEI tests. Paper scores and CEI scores should stay separate.",
    "The 37-row comparison in the full deck covers UniMoral and ValuePrism only.",
  ]);
}

// Slide 8: action
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "MoralBench and UniMoral: what we can report now",
    "Report the 8 task results now. Do not publish one overall model rank.",
    { label: "DECISION", fill: C.coralSoft, color: C.coral },
  );
  const values = [
    ["When", "Action", "Reason"],
    ["Now", "Share each task result with its limits", "The saved results answer one task at a time"],
    ["Next", "Restore each model's answer and score for every question", "This lets us compare models on the same questions"],
    ["Then", "Check scoring and labels; have people review the test", "A benchmark score alone does not prove the test matches human judgment"],
    ["Only if still unclear", "Add more comparison questions", "New questions help after the scoring works correctly"],
  ];
  const table = slide.tables.add({
    rows: values.length,
    columns: 3,
    left: 92,
    top: 185,
    width: 1096,
    height: 360,
    columnWidths: [210, 430, 456],
    values,
  });
  styleTable(table, values.length, 3, { bodySize: 18, headerSize: 16, headerFill: C.coral });
  table.cells.block({ row: 1, column: 0, rowCount: 4, columnCount: 1 }).textStyle.bold = true;
  addText(slide, "Next: restore answers and scores, check scoring, compare models, and get human review.", {
    left: 92, top: 600, width: 1096, height: 46,
  }, { fontSize: 24, color: C.ink, bold: true, autoFit: "shrinkText" });
  setNotes(slide, [
    "Sources: docs/RESEARCH_LEAD_BRIEF.md; evidence/canonical-audit/RERUN_PRIORITY.md; evidence/canonical-audit/SELF_CRITIQUE.md.",
    "The order shown is a decision recommendation, not a statistical theorem.",
    "Benchmark agreement does not prove that the test matches human judgment.",
    "We still need the original answers and scores, better uncertainty estimates, exact model and dataset records, leakage checks, and representative human review.",
  ]);
}

const requirements = {
  explicitTotalSlideCount: 8,
  requiredNativeTableOwnerSlides: [2, 7, 8],
  requiredNativeChartOwnerSlides: [4, 5, 6],
  materializeLiteralChartWorkbooks: true,
};
const fontPolicy = { basis: "design", families: [family] };
const expectedSlideSizeEmu = "12192000,6858000";
const stagingDir = path.join(TMP_DIR, "finalizer");
const validatedDir = path.join(TMP_DIR, "validated");
await fs.mkdir(stagingDir, { recursive: true });
await fs.mkdir(validatedDir, { recursive: true });
const buildId = `${Date.now()}-${process.pid}`;
const candidatePath = path.join(stagingDir, `candidate-${buildId}.pptx`);
const validatedPath = path.join(validatedDir, `validated-${buildId}.pptx`);
const receiptPath = path.join(stagingDir, `validation-${buildId}.json`);
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
    "--expected-slide-size-emu", expectedSlideSizeEmu,
    "--validate-bullet-geometry",
    "--validate-heading-fit",
    "--require-native-table-slide", "2",
    "--require-native-table-slide", "7",
    "--require-native-table-slide", "8",
  ],
  requiredNativeTableOwnerSlides: requirements.requiredNativeTableOwnerSlides,
  fontPolicy,
  verifyArtifactToolImport: true,
  receiptPath,
});

// The finalizer checks structure and layout. The repo validator then opens the
// staged PPTX and recomputes its tables and charts from the CSV evidence before
// the stable public file is touched.
const semanticValidation = await runChecked(
  VALIDATION_PYTHON,
  [
    path.join(workspaceDir, "scripts", "validate_site.py"),
    "--slide-deck",
    validatedPath,
    "--skip-slide-exports",
  ],
  {
    cwd: workspaceDir,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
  },
);
if (!semanticValidation.stdout.includes("VALIDATION PASSED")) {
  throw new Error("Semantic validator exited successfully without a VALIDATION PASSED receipt.");
}

// Write only to the caller's private staging path. The release orchestrator
// renders and validates the full share bundle before touching public files.
const publishTempPath = path.join(
  path.dirname(FINAL_PPTX),
  `.${path.basename(FINAL_PPTX)}.${buildId}.tmp`,
);
try {
  await fs.copyFile(validatedPath, publishTempPath, fsConstants.COPYFILE_EXCL);
  const stagedBytes = await fs.readFile(publishTempPath);
  const stagedSha256 = createHash("sha256").update(stagedBytes).digest("hex");
  if (stagedSha256 !== result.finalSha256) {
    throw new Error(`Staged deck hash ${stagedSha256} differs from validated hash ${result.finalSha256}.`);
  }
  await fs.rename(publishTempPath, FINAL_PPTX);
} finally {
  await fs.rm(publishTempPath, { force: true });
}

const stagedOutputBytes = await fs.readFile(FINAL_PPTX);
const stagedOutputSha256 = createHash("sha256").update(stagedOutputBytes).digest("hex");
if (stagedOutputSha256 !== result.finalSha256) {
  throw new Error(`Staged deck hash ${stagedOutputSha256} differs from validated hash ${result.finalSha256}.`);
}

process.stdout.write(`${JSON.stringify({
  family,
  final: FINAL_PPTX,
  validatedPath,
  receiptPath,
  stagedOutputSha256,
  semanticValidation: "passed",
  publicFilesChanged: false,
  result,
}, null, 2)}\n`);
