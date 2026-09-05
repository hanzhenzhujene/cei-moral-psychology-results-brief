# Results readout

## One-screen answer

| Research question | Answer | Implication |
|---|---|---|
| Does one model lead all eight tasks? | No. The top saved score changes by task. | Keep task results separate. |
| Can the comparison tests show a leader? | No. For every pair of models, their two saved 95% score ranges overlap: 28 of 28 MFQ pairs and 45 of 45 vignette pairs. | Restore answers and scores by question; check scoring and labels. |
| Do scores rise at both size steps? | Only 4 of 12 rise twice; 7 switch direction; 1 falls twice. | Size is a clue, not a rule. |
| Are later Qwen and DeepSeek versions better on every task? | No: Qwen has 3 higher and 1 lower endpoint; DeepSeek has 2 higher and 2 lower. | Release period is metadata, not progress. |

## What the benchmark papers actually ask

| Paper | Human-readable research question | Local reach |
|---|---|---|
| MoralBench | Do model choices track human ratings, and can a model choose the statement people rated higher? | Approximate task-family match. |
| UniMoral | Can a model predict actions, moral frameworks, influencing factors, and plausible consequences? Do cues change the result? | Approximate for the four task families; cue claims unavailable. |
| MoReBench | Does model reasoning cover expert-defined considerations, trade-offs, logic, and outcomes? | Related question, different test; local score is proxy-only. |
| MoralLens | Which rationales appear, and do they change when reasoning comes before versus after a decision? | Related question, different test; local score is proxy-only. |

There are **0 exact local replications**. The size and release views below are local follow-up questions, not restatements of the papers' main claims.

## 1. Common-roster task results

![Five-model task result chart](../assets/results/01_common_roster_task_results.png)

The main chart uses the only five models that clear every one of the eight primary text-task gates: Claude Haiku 4.5, Claude Opus 4.8, GPT-5.4, GPT-5.4 mini, and Qwen3 8B.

| Task block | Metric | Saved scored rows per model | What the chart supports |
|---|---|---:|---|
| MFQ and vignette agreement | Normalized preference | 20 and 24 | Task-specific agreement levels, with material uncertainty |
| MFQ and vignette comparison | Accuracy | 20 and 24 | The saved 95% score ranges do not resolve a model order; the two model ranges overlap for every pair within each task |
| UniMoral action, typology, and factor | Accuracy | 8,784; 3,492; 3,492 | Point estimates differ by task; nominal row-level intervals are narrow |
| UniMoral consequence | METEOR | 1,782 | A generation metric that must not be averaged with accuracy or preference |

The chart does not show a moral score. It shows eight distinct measurements. The narrow UniMoral intervals also do not account for scenario or annotator clustering, route drift, contamination, construct error, or representative human validity.

Source: [`common_roster_primary.csv`](../data/results/common_roster_primary.csv), filtered from the current canonical primary interval table.

## 2. Can the comparison tests identify a leader?

![Two cards showing complete pairwise overlap on both accuracy comparison tests](../assets/results/02_precision_by_task.png)

This section uses all primary models: 8 for MFQ compare and 10 for vignette compare, not the five-model roster above. For every pair of models, the two saved 95% score ranges overlap: all 28 MFQ pairs and all 45 vignette pairs. These are separate score ranges, not direct tests of the difference between two models, so they do not resolve a leader.

| Accuracy test | Saved models × questions | Overlapping model pairs |
|---|---:|---:|
| MFQ compare | `8 × 20` | `28/28 (100%)` |
| Vignette compare | `10 × 24` | `45/45 (100%)` |

Restore answers and scores by question, check scoring and labels, then compare models directly. Ask people whether the test matches human judgment; add items only if the order stays unclear. The full task-width table remains available as supporting data, but widths from different metrics should not be compared on one scale.

Sources: [`primary_confidence_intervals.csv`](../evidence/canonical-audit/figures/data/primary_confidence_intervals.csv) for the saved ranges and pairwise-overlap counts; [`task_precision.csv`](../data/results/task_precision.csv) for the supporting width table, which keeps each metric labeled.

## 3. Model size paths

![Bar and line charts showing that larger UniMoral model variants do not move every task upward](../assets/results/03_size_paths.png)

| Concrete read | Exact result |
|---|---|
| UniMoral-only local follow-up | Of 12 complete family × UniMoral task paths, 4 rise at both steps, 7 change direction, and 1 falls at both steps. |
| Cleanest same-generation counterexample | Gemma factor accuracy rises `.578 → .601 → .613`, while Gemma typology falls `.597 → .579 → .570`. |
| What each point means | One saved aggregate for one named model on one task. The Gemma x-axis names all three models and their published `4B → 12B → 27B` counts. |
| Full selected-grid extension | Adding the three complete ValuePrism paths gives 5 rising, 9 changing direction, and 1 falling across 15 complete paths. |
| Coverage limit | Qwen has no complete ValuePrism path, and Gemma has no complete valence path. Missing routes are not zeros. |

The bar chart answers the denominator question; the paired Gemma lines make the implication concrete. Exact paths remain in two landscape audit figures: [UniMoral classification](../assets/results/03_size_paths_detail_a.svg) and [consequence plus ValuePrism](../assets/results/03_size_paths_detail_b.svg). All 45 audit points name the model and published B count.

This chart cannot show that size caused the changes: model generation, release period, and architecture also change, and no saved intervals or raw logs are available. Qwen's largest tier is a 235B-total / 22B-active MoE; total B is not inference compute. Qwen3-32B rows record 107,375 reasoning tokens despite control attempts.

Sources: [`size_path_summary.csv`](../data/results/size_path_summary.csv), [`size_task_points.csv`](../data/results/size_task_points.csv), and the revision-pinned model-card ledger in [`model-parameter-sources.csv`](../evidence/model-parameter-sources.csv).

## 4. Release-period paths

![Zero-centered dot plots of UniMoral endpoint changes for Qwen and DeepSeek](../assets/results/04_release_period_paths.png)

| Concrete read | Exact result |
|---|---|
| UniMoral-only local follow-up | Qwen has 3 higher and 1 lower endpoint; DeepSeek has 2 higher and 2 lower. |
| Accuracy panel | Qwen changes are `+.018`, `+.042`, and `+.002`; DeepSeek changes are `+.187`, `−.003`, and `−.038`. |
| Separate consequence panel | Qwen METEOR changes `−.027`; DeepSeek changes `+.019`. It is not plotted on the accuracy scale. |
| What each point means | One later-minus-earlier aggregate for the named Qwen or DeepSeek model path printed above the chart. A dagger marks a DeepSeek path that changes direction at an intermediate checkpoint. |
| Full selected-grid extension | Adding ValuePrism gives Qwen 5 higher and 1 lower endpoint; DeepSeek 3 higher and 3 lower. |
| Evaluation window | Every plotted row was evaluated on May 28–29, 2026. The quarter field describes the named model release, not evaluation time. |
| Same-B releases | DeepSeek V3-0324, V3.1, and V3.2 all carry 671B-main / 37B-active specifications, yet their task point estimates differ. Parameter count alone is not a model identity. |

The zero line gives the answer immediately: points on both sides mean later named models do not move every task in one direction. Exact chronological paths remain in two landscape audit figures: [UniMoral classification](../assets/results/04_release_period_paths_detail_a.svg) and [consequence plus ValuePrism](../assets/results/04_release_period_paths_detail_b.svg). All 35 audit points name the model and published B count.

This chart cannot show that release period caused the changes: generation, route, architecture, and parameter count also change. Release period is metadata, not evaluation time. The DeepSeek ValuePrism path ends at V3.2 because V4 was cancelled; Gemma has no valid newer comparison. DeepSeek V4 UniMoral rows record 1,171,189 reasoning tokens despite control attempts. The saved metadata lacks the served endpoint, quantization, and evaluated checkpoint revision.

Sources: [`release_path_summary.csv`](../data/results/release_path_summary.csv), [`release_period_task_points.csv`](../data/results/release_period_task_points.csv), and [`model-parameter-sources.csv`](../evidence/model-parameter-sources.csv).

## Evidence ladder

| Level | Use | Do not use it for |
|---|---|---|
| Current primary aggregate; tracked-artifact audit | Current task panels and nominal interval widths | Raw replay, human validity, causal claims, or a cross-metric rank |
| Sensitivity and multimodal extension | Robustness and extension questions | Quietly enlarging the primary set |
| Exploratory selected grid | Generating size and release hypotheses | Confirmatory claims or uncertainty-free ranking |
| Poster-reported legacy evidence | Design history | Numerical publication until replay packets return |
| Canonical UniMoral and ValuePrism crosswalk | Protocol and interpretation context | Claiming exact replication; that 37-row crosswalk has 0 exact matches |

## Visuals deliberately rejected

- A global leaderboard or “moral score,” because it would average accuracy, normalized preference, and METEOR.
- Radar-chart area comparisons, because area would imply commensurable constructs.
- A benchmark “hardest to easiest” order, because metric scales and tasks differ.
- Cross-benchmark correlations built from uneven coverage and incompatible measurements.
- Missing routes plotted as zero, because absence is not model failure.

The canonical limits and claim rules remain binding in [`CLAIM_BOUNDARIES.md`](../evidence/canonical-audit/CLAIM_BOUNDARIES.md) and [`TECHNICAL_AUDIT.md`](../evidence/canonical-audit/TECHNICAL_AUDIT.md).
