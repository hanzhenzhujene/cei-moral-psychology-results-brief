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

for (const [name, value] of Object.entries({
  PRESENTATIONS_SKILL_DIR: SKILL_DIR,
  WORKSPACE_PYTHON: RUNTIME_PYTHON,
  VALIDATION_PYTHON,
  ARTIFACT_TOOL_DIR,
  RUNTIME_NODE_MODULES,
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
const FINAL_PPTX = path.join(workspaceDir, "slides", "cei-moral-psychology-results-deck.pptx");

const {
  resolvePresentationFont,
  applyPresentationChartFont,
  finalizePresentation,
} = await import(pathToFileURL(
  path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs"),
).href);

await fs.mkdir(TMP_DIR, { recursive: true });
await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });

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
  addText(slide, title, { left: 72, top: 36, width: 910, height: 62 }, {
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
  if (tag) addTag(slide, tag.label, tag.fill, tag.color);
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
  addText(slide, "Publish task results.\nDo not rank the models.", {
    left: 88, top: 132, width: 930, height: 178,
  }, { name: "cover-title", fontSize: 54, bold: true, autoFit: "shrinkText" });
  addText(slide, "CEI moral psychology benchmark", {
    left: 92, top: 334, width: 720, height: 40,
  }, { fontSize: 24, color: C.teal, bold: true });
  addText(slide, "Research lead readout · 4 September 2026", {
    left: 92, top: 382, width: 760, height: 34,
  }, { fontSize: 18, color: C.muted });
  addRule(slide, 92, 474, 720, C.grid, 2);
  addText(slide, "Why: the highest saved score changes by task, and saved ranges overlap on both comparison tests.", {
    left: 92, top: 500, width: 965, height: 72,
  }, { fontSize: 24, color: C.ink, autoFit: "shrinkText" });
  addText(slide, "Share the task results with their limits. Size and release slides are early clues, not final answers.", {
    left: 92, top: 602, width: 980, height: 36,
  }, { fontSize: 17, color: C.muted });
  setNotes(slide, [
    "Claim: publish task-level results, but do not create an overall model ranking.",
    "Sources: docs/RESEARCH_LEAD_BRIEF.md; data/results/research_question_takeaways.csv.",
    "Boundary: current task aggregates and saved uncertainty do not establish human validity, causal effects, or one cross-metric moral score.",
  ]);
}

// Slide 2: task leaders
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "No model has the highest saved score on all eight tasks",
    "Highest saved score for each task, using the same five models",
    { label: "MAIN RESULTS", fill: C.tealSoft, color: C.teal },
  );
  const values = [
    ["Task", "Highest saved score", "Score type", "Model"],
    ["MFQ agreement", ".884", "Agreement score", "GPT-5.4 mini"],
    ["Vignette agreement", ".920", "Agreement score", "GPT-5.4"],
    ["MFQ compare", ".550", "Accuracy", "Haiku + Qwen tie†"],
    ["Vignette compare", ".625", "Accuracy", "Haiku + GPT-5.4 tie†"],
    ["UniMoral action", ".668", "Accuracy", "Claude Haiku 4.5"],
    ["UniMoral typology", ".651", "Accuracy", "Claude Opus 4.8"],
    ["UniMoral factor", ".609", "Accuracy", "Claude Haiku 4.5"],
    ["UniMoral consequence", ".152", "Text-match score", "Claude Opus 4.8"],
  ];
  const table = slide.tables.add({
    rows: values.length,
    columns: 4,
    left: 96,
    top: 170,
    width: 1088,
    height: 430,
    columnWidths: [330, 190, 225, 343],
    values,
  });
  styleTable(table, values.length, 4, { bodySize: 17, headerSize: 16 });
  table.cells.block({ row: 1, column: 3, rowCount: 2, columnCount: 1 }).assign({
    fill: C.tealSoft,
    textStyle: { typeface: family, fontSize: 17, color: C.teal, bold: true },
  });
  table.cells.block({ row: 3, column: 3, rowCount: 2, columnCount: 1 }).assign({
    fill: C.goldSoft,
    textStyle: { typeface: family, fontSize: 17, color: "#8B5F00", bold: true },
  });
  table.cells.block({ row: 5, column: 3, rowCount: 4, columnCount: 1 }).assign({
    fill: C.purpleSoft,
    textStyle: { typeface: family, fontSize: 17, color: C.purple, bold: true },
  });
  addText(slide, "† The uncertainty ranges overlap on the two comparison tasks. We cannot tell who leads.", {
    left: 96, top: 620, width: 1080, height: 30,
  }, { fontSize: 16, color: C.coral });
  addText(slide, "Each task uses its own score. Do not compare numbers from different rows.", {
    left: 96, top: 652, width: 1080, height: 26,
  }, { fontSize: 15, color: C.muted });
  setNotes(slide, [
    "Each row shows the highest saved point estimate for that task among Claude Haiku 4.5, Claude Opus 4.8, GPT-5.4, GPT-5.4 mini, and Qwen3 8B.",
    "Sources: data/results/common_roster_primary.csv; docs/RESULTS_READOUT.md section 1.",
    "The MFQ compare top value is shared by Claude Haiku 4.5 and Qwen3 8B. The vignette compare top value is shared by Claude Haiku 4.5 and GPT-5.4.",
    "Values belong to different metrics. The visible labels translate normalized preference and METEOR into plain language.",
    "Do not average preference, accuracy, and METEOR or treat this table as a moral leaderboard.",
  ]);
}

// Slide 3: precision
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "Saved ranges overlap for every model pair in both tests",
    "Full primary panels: MFQ = 8 models × 20 questions; Vignette = 10 × 24.",
    { label: "MAIN RESULTS", fill: C.tealSoft, color: C.teal },
  );
  addText(slide, "Each bar = the median full width of saved 95% intervals across available models.", {
    left: 120, top: 149, width: 1030, height: 22,
  }, { fontSize: 15, color: C.muted });
  const categories = [
    "MFQ compare",
    "Vignette compare",
    "MFQ agreement",
    "Vignette agreement",
    "UniMoral factor",
    "UniMoral typology",
    "UniMoral action",
    "UniMoral consequence",
  ];
  const values = [0.395, 0.370, 0.220, 0.124, 0.033, 0.032, 0.020, 0.012];
  const chart = slide.charts.add("bar", {
    position: { left: 120, top: 177, width: 1030, height: 337 },
    title: "Median width of saved 95% ranges — wider means less sure",
    titlePlacement: "none",
    categories,
    series: [{
      name: "Interval width",
      values,
      fill: C.teal,
      points: values.map((_, idx) => ({
        idx,
        fill: idx < 2 ? C.coral : idx < 4 ? C.gold : C.teal,
        line: { fill: "none", width: 0 },
      })),
      valuesFormatCode: "0.000",
    }],
    barOptions: { direction: "bar", grouping: "clustered", gapWidth: 36 },
    hasLegend: false,
    xAxis: {
      visible: true,
      title: "Median full width of saved 95% interval",
      min: 0,
      max: 0.42,
      majorUnit: 0.10,
      numberFormatCode: "0.00",
      majorGridlines: { style: "solid", fill: C.grid, width: 1 },
      textStyle: { typeface: family, fontSize: 13, fill: C.muted },
    },
    yAxis: {
      visible: true,
      textStyle: { typeface: family, fontSize: 15, fill: C.ink },
      line: { fill: "none", width: 0 },
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
  addText(slide, "Direct evidence: saved ranges overlap for all 28 MFQ and all 45 Vignette model pairs.", {
    left: 120, top: 526, width: 1030, height: 30,
  }, { fontSize: 18, bold: true, color: C.coral });
  addText(slide, "Action: recover per-question outcomes and check scoring.", {
    left: 120, top: 580, width: 980, height: 32,
  }, { fontSize: 21, bold: true, color: C.ink });
  addText(slide, "Then compare models, run human review, and add questions only if still unclear.", {
    left: 120, top: 616, width: 1000, height: 28,
  }, { fontSize: 17, color: C.muted });
  setNotes(slide, [
    "Source: data/results/task_precision.csv.",
    "All 18 individual intervals wider than .30 occur in the two MoralBench comparison tasks.",
    "Denominator: all available primary models—8 on MFQ compare and 10 on vignette compare—not the five-model common roster.",
    "Within each comparison task, every model pair has overlapping marginal intervals: 28 of 28 MFQ pairs and 45 of 45 vignette pairs.",
    "This is not a paired model-difference test. The narrow UniMoral intervals are nominal row-level estimates and do not establish cluster-aware uncertainty or human validity.",
  ]);
}

// Slide 4: size-path count
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "Only 4 of 12 model-and-task cases rise twice",
    "Qwen, Gemma, and Llama × four tasks; model versions differ in more than size",
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
      title: "Model-family and task cases (12 total)",
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
  addText(slide, "Each bar counts model-family × task cases (12 total).", {
    left: 150, top: 526, width: 900, height: 24,
  }, { fontSize: 14, color: C.muted });
  addText(slide, "Size is one clue, not a general rule.", {
    left: 150, top: 568, width: 860, height: 40,
  }, { fontSize: 26, bold: true, color: C.ink });
  addText(slide, "Each case follows one model family on one task. Different score types stay separate.", {
    left: 150, top: 618, width: 920, height: 30,
  }, { fontSize: 16, color: C.muted });
  setNotes(slide, [
    "Sources: data/results/size_path_summary.csv; data/results/size_task_points.csv.",
    "Denominator: 12 complete paths equals three model families times four UniMoral tasks. Each path contains three named variants.",
    "Counts: 4 rise at both steps, 7 change direction, and 1 falls at both steps.",
    "Accuracy and METEOR stay separate.",
    "This slide counts within-task direction only. It does not average accuracy and METEOR. The selected grid has no saved confidence intervals or raw-log replay.",
  ]);
}

// Slide 5: size example
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "Gemma scores rise on one task and fall on another",
    "",
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
  addText(slide, "The larger named variants do not score higher on both tasks.", {
    left: 118, top: 612, width: 730, height: 34,
  }, { fontSize: 22, bold: true, color: C.purple });
  addText(slide, "Each point is one stored task score. Its uncertainty range and raw run archive are unavailable.", {
    left: 118, top: 650, width: 920, height: 26,
  }, { fontSize: 15, color: C.muted });
  setNotes(slide, [
    "Sources: data/results/size_path_summary.csv; data/results/size_task_points.csv; evidence/model-parameter-sources.csv.",
    "Exact values: factor attribution .578 to .601 to .613; moral typology .597 to .579 to .570.",
    "Across Qwen, Gemma, and Llama on four UniMoral tasks, 4 of 12 complete paths rise twice, 7 change direction, and 1 falls twice.",
    "No saved intervals or raw-log replay are available for this selected grid.",
    "This is exploratory selected-grid evidence. Parameter tier is descriptive metadata, not a controlled intervention. Qwen and Llama paths also change model generation or release period.",
  ]);
}

// Slide 6: release endpoints
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "Later model versions score higher on some tasks and lower on others",
    "Score change on three UniMoral tasks",
    { label: "EXPLORATORY", fill: C.goldSoft, color: "#8B5F00" },
  );
  addText(slide, "Qwen: 2024-Q3 · Qwen2.5 7B Instruct (7.61B) → 2026-Q1 · Qwen3.5 9B (9B)", {
    left: 110, top: 158, width: 1000, height: 26,
  }, { fontSize: 14, color: C.teal, bold: true, autoFit: "shrinkText" });
  addText(slide, "DeepSeek: 2025-Q1 · V3-0324 (671B main, 37B active) → 2026-Q2 · V4 Flash (284B main, 13B active)", {
    left: 110, top: 186, width: 1060, height: 26,
  }, { fontSize: 14, color: C.purple, bold: true, autoFit: "shrinkText" });
  addText(slide, "main = published main-model parameters (auxiliary/MTP excluded); active = parameters used per token", {
    left: 110, top: 212, width: 980, height: 20,
  }, { fontSize: 12, color: C.muted });
  const chart = slide.charts.add("bar", {
    position: { left: 120, top: 238, width: 1030, height: 331 },
    title: "Score change from earlier to later version",
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
  addText(slide, "All endpoint runs were evaluated on 28–29 May 2026.", {
    left: 120, top: 594, width: 900, height: 32,
  }, { fontSize: 20, bold: true, color: C.ink });
  addText(slide, "Release period is model metadata, not a progress timeline; 28–29 May is the evaluation time.", {
    left: 120, top: 630, width: 940, height: 28,
  }, { fontSize: 15, color: C.muted, autoFit: "shrinkText" });
  addText(slide, "Exploratory: saved uncertainty is unavailable. Consequence uses a different score and is not shown.", {
    left: 120, top: 661, width: 940, height: 24,
  }, { fontSize: 13, color: C.muted, autoFit: "shrinkText" });
  setNotes(slide, [
    "Sources: data/results/release_path_summary.csv; data/results/release_period_task_points.csv; data/model_release_periods.csv; evidence/model-parameter-sources.csv.",
    "Classification accuracy deltas shown: Qwen action +.017873, typology +.042383, factor +.002005; DeepSeek action +.186589, typology -.003150, factor -.037514.",
    "Consequence uses METEOR and is not mixed into this accuracy chart. Its endpoint deltas are Qwen -.026780 and DeepSeek +.018985.",
    "Every plotted selected-grid score was evaluated on 28 or 29 May 2026. Release quarter is descriptive model metadata, not observation time or a causal intervention.",
  ]);
}

// Slide 7: papers
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "We did not exactly repeat any paper's experiment",
    "The papers help explain our questions. Their scores cannot be compared with ours.",
    { label: "PAPER REVIEW", fill: C.purpleSoft, color: C.purple },
  );
  addText(slide, "0 of 4", { left: 88, top: 230, width: 230, height: 105 }, {
    fontSize: 60, bold: true, color: C.coral, alignment: "center",
  });
  addText(slide, "papers repeated\nexactly", { left: 88, top: 342, width: 230, height: 80 }, {
    fontSize: 24, bold: true, color: C.ink, alignment: "center",
  });
  const values = [
    ["Paper", "Plain-language question", "How close is our test?"],
    ["MoralBench", "Do model choices match human ratings?", "Similar question"],
    ["UniMoral", "Can models predict choices, moral categories, influences, and what happens next?", "Some similar tasks"],
    ["MoReBench", "Does reasoning cover expert criteria?", "Different scoring"],
    ["MoralLens", "Do reasons change when a model explains before or after choosing?", "Different scoring"],
  ];
  const table = slide.tables.add({
    rows: values.length,
    columns: 3,
    left: 355,
    top: 180,
    width: 845,
    height: 360,
    columnWidths: [175, 470, 200],
    values,
  });
  styleTable(table, values.length, 3, { bodySize: 17, headerSize: 16, headerFill: C.purple });
  table.cells.block({ row: 1, column: 2, rowCount: 4, columnCount: 1 }).textStyle.bold = true;
  addText(slide, "Use the papers to explain our questions—not to compare scores.", {
    left: 355, top: 570, width: 845, height: 40,
  }, { fontSize: 21, bold: true, color: C.purple });
  addText(slide, "Our UniMoral run does not test prompt hints, language differences, or where the stories came from.", {
    left: 355, top: 618, width: 845, height: 28,
  }, { fontSize: 15, color: C.muted });
  setNotes(slide, [
    "Sources: docs/PAPER_REVIEW.md; data/paper_protocol_map.csv.",
    "MoralBench and UniMoral share approximate task families with the local evaluator, but model, data, prompt, metric, scorer, or aggregation identities differ.",
    "MoReBench and MoralLens local performance surfaces are proxy-only. Their paper metrics and judges are not reproduced.",
    "They are not direct score baselines. The visible status labels translate the protocol evidence into plain language.",
    "Do not use the canonical 37-row UniMoral and ValuePrism crosswalk as the denominator for all four papers. That ledger covers a different evidence scope.",
  ]);
}

// Slide 8: action
{
  const slide = presentation.slides.add();
  addSlideFrame(
    slide,
    "Share task results now. Strengthen the test next.",
    "Better evidence makes the current results more useful",
    { label: "DECISION", fill: C.coralSoft, color: C.coral },
  );
  const values = [
    ["When", "Action", "Reason"],
    ["Now", "Share each task result with its limits", "The saved results answer one task at a time"],
    ["Next", "Recover per-question outcomes; check scoring and labels", "This lets us compare models directly"],
    ["Then", "Have people review the test", "A benchmark score does not prove the test matches human judgment"],
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
  addText(slide, "Best research next move", { left: 92, top: 582, width: 300, height: 30 }, {
    fontSize: 17, color: C.muted, bold: true,
  });
  addText(slide, "Recover per-question outcomes. Compare models. Then have people review the test.", {
    left: 92, top: 614, width: 1096, height: 46,
  }, { fontSize: 26, color: C.ink, bold: true, autoFit: "shrinkText" });
  setNotes(slide, [
    "Sources: docs/RESEARCH_LEAD_BRIEF.md; evidence/canonical-audit/RERUN_PRIORITY.md; evidence/canonical-audit/SELF_CRITIQUE.md.",
    "The order shown is a decision recommendation, not a statistical theorem.",
    "Benchmark agreement is not human validity. The visible wording translates that evidence boundary into plain language.",
    "The saved evidence still lacks canonical raw archives, clustered uncertainty, complete model and dataset identity, contamination testing, and representative human validation.",
  ]);
}

const requirements = {
  explicitTotalSlideCount: 8,
  requiredNativeTableOwnerSlides: [2, 7, 8],
  requiredNativeChartOwnerSlides: [3, 4, 5, 6],
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
  ],
  {
    cwd: workspaceDir,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: "1" },
  },
);
if (!semanticValidation.stdout.includes("VALIDATION PASSED")) {
  throw new Error("Semantic validator exited successfully without a VALIDATION PASSED receipt.");
}

// Stage beside the public file so the final rename stays on one filesystem.
// The rename is the only operation that replaces the stable public filename.
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

const publicBytes = await fs.readFile(FINAL_PPTX);
const publicSha256 = createHash("sha256").update(publicBytes).digest("hex");
if (publicSha256 !== result.finalSha256) {
  throw new Error(`Published deck hash ${publicSha256} differs from validated hash ${result.finalSha256}.`);
}

process.stdout.write(`${JSON.stringify({
  family,
  final: FINAL_PPTX,
  validatedPath,
  receiptPath,
  publicSha256,
  semanticValidation: "passed",
  publishedViaAtomicRename: true,
  result,
}, null, 2)}\n`);
