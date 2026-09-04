# Results readout

## One-screen answer

| Research question | Answer | Implication |
|---|---|---|
| Is there one stable model order? | No. The point-estimate leader changes across tasks. | Keep the eight task results separate. |
| Where is precision weakest? | The two MoralBench comparison tasks. | Recover paired outcomes first; expand the item banks only if the order remains unresolved. |
| Across complete selected UniMoral paths, do scores rise at both size steps? | No. Only 4 of 12 rise twice; 7 change direction and 1 falls twice. | Treat size patterns as family- and task-specific. |
| Do later named-model endpoints move every UniMoral task higher? | No. Qwen has 3 higher and 1 lower endpoint; DeepSeek has 2 higher and 2 lower. | Release quarter is model metadata, not a longitudinal progress trend. |

## What the benchmark papers actually ask

| Paper | Human-readable research question | Local reach |
|---|---|---|
| MoralBench | Do model choices track human ratings, and can a model choose the statement people rated higher? | Approximate task-family match. |
| UniMoral | Can a model predict actions, moral frameworks, influencing factors, and plausible consequences? Do cues change the result? | Approximate for the four task families; cue claims unavailable. |
| MoReBench | Does model reasoning cover expert-defined considerations, trade-offs, logic, and outcomes? | Local performance score is proxy-only. |
| MoralLens | Which rationales appear, and do they change when reasoning comes before versus after a decision? | Local performance score is proxy-only. |

There are **0 exact local replications**. The size and release views below are local follow-up questions, not restatements of the papers' main claims.

## 1. Common-roster task results

![Five-model task result chart](../assets/results/01_common_roster_task_results.png)

The main chart uses the only five models that clear every one of the eight primary text-task gates: Claude Haiku 4.5, Claude Opus 4.8, GPT-5.4, GPT-5.4 mini, and Qwen3 8B.

| Task block | Metric | Saved scored rows per model | What the chart supports |
|---|---|---:|---|
| MFQ and vignette agreement | Normalized preference | 20 and 24 | Task-specific agreement levels, with material uncertainty |
| MFQ and vignette comparison | Accuracy | 20 and 24 | Available aggregate intervals do not resolve a model order; every pair overlaps marginally within each comparison task |
| UniMoral action, typology, and factor | Accuracy | 8,784; 3,492; 3,492 | Point estimates differ by task; nominal row-level intervals are narrow |
| UniMoral consequence | METEOR | 1,782 | A generation metric that must not be averaged with accuracy or preference |

The chart does not show a moral score. It shows eight distinct measurements. The narrow UniMoral intervals also do not account for scenario or annotator clustering, route drift, contamination, construct error, or representative human validity.

Source: [`common_roster_primary.csv`](../data/results/common_roster_primary.csv), filtered from the current canonical primary interval table.

## 2. Precision by task

![Median confidence interval width by task](../assets/results/02_precision_by_task.png)

| Task | Median full 95% interval width | Read |
|---|---:|---|
| MFQ compare | `.395` | Too wide to resolve a model order |
| Vignette compare | `.370` | Too wide to resolve a model order |
| MFQ agreement | `.220` | Material uncertainty |
| Vignette agreement | `.124` | Narrower, but still based on a small item bank |
| UniMoral factor | `.033` | Nominal row-level precision |
| UniMoral typology | `.032` | Nominal row-level precision |
| UniMoral action | `.020` | Nominal row-level precision |
| UniMoral consequence | `.012` | Nominal saved-standard-error precision |

All 18 individual intervals wider than `.30` occur in the two comparison tasks. This is a measurement-design finding: recover the paired outcomes first, then expand the item banks only if the order remains unresolved.

Sources: [`task_precision.csv`](../data/results/task_precision.csv) for the task medians; [`primary_confidence_intervals.csv`](../evidence/canonical-audit/figures/data/primary_confidence_intervals.csv) for the 18 individual wide intervals.

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

This is exploratory aggregate evidence. It has no saved confidence intervals or raw-log replay. Qwen and Llama tiers also change model generation or release period, and Qwen’s largest tier changes from dense to a 235B-total / 22B-active MoE architecture. Published total B is therefore neither a controlled size intervention nor inference compute. Provider metadata also records 107,375 reasoning tokens across Qwen3-32B rows despite control attempts.

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

Release quarter is descriptive metadata, not an intervention or progress timeline. Generation, route, architecture, and parameter count change together. DeepSeek relevance ends at V3.2 because the V4 route was cancelled; Gemma has no valid newer comparison. DeepSeek V4 rows record 1,171,189 reasoning tokens despite control attempts, and the saved metadata does not retain the served endpoint, quantization, or exact evaluated checkpoint revision.

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
