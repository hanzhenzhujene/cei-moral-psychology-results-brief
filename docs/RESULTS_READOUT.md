# Results readout

## One-screen answer

| Research question | Answer | Implication |
|---|---|---|
| Is there one stable model order? | No. The point-estimate leader changes across tasks. | Keep the eight task results separate. |
| Where is precision weakest? | The two MoralBench comparison tasks. | Recover paired outcomes first; expand the item banks only if the order remains unresolved. |
| Does bigger reliably perform better? | No. Only 5 of 15 complete paths rise from small to medium to large. | Treat size patterns as family- and task-specific. |
| Do later named-route endpoints all move higher? | No. Qwen has 5 higher and 1 lower endpoint; DeepSeek has 3 higher and 3 lower endpoints. | Release quarter is model metadata, not a longitudinal progress trend. |

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

![Direction matrix for complete model-size paths](../assets/results/03_size_paths.png)

| Concrete read | Exact result |
|---|---|
| Overall direction | Of 15 complete family × task paths, 5 rise at every step, 9 change direction, and 1 falls. |
| Cleanest same-generation counterexample | Gemma factor accuracy rises `.578 → .601 → .613`, while Gemma typology falls `.597 → .579 → .570`. |
| Memorable bend | Qwen action moves `.649 → .479 → .634`; the largest named model does not exceed the smallest endpoint. |
| Coverage limit | Qwen has no complete ValuePrism path, and Gemma has no complete valence path. Missing rows are not zeros. |

The matrix is the executive view. Exact point paths remain in two landscape audit figures: [UniMoral classification](../assets/results/03_size_paths_detail_a.svg) and [consequence plus ValuePrism](../assets/results/03_size_paths_detail_b.svg). All 45 plotted points name the model and published B count.

This is exploratory aggregate evidence. It has no saved confidence intervals or raw-log replay. Qwen and Llama tiers also change model generation or release period, and Qwen’s largest tier changes from dense to a 235B-total / 22B-active MoE architecture. Published total B is therefore neither a controlled size intervention nor inference compute. Provider metadata also records 107,375 reasoning tokens across Qwen3-32B rows despite control attempts.

Sources: [`size_path_summary.csv`](../data/results/size_path_summary.csv), [`size_task_points.csv`](../data/results/size_task_points.csv), and the revision-pinned model-card ledger in [`model-parameter-sources.csv`](../evidence/model-parameter-sources.csv).

## 4. Release-period paths

![Endpoint direction matrix by recorded model release quarter](../assets/results/04_release_period_paths.png)

| Concrete read | Exact result |
|---|---|
| Qwen endpoints | 5 are higher and 1 is lower. Consequence METEOR moves `.124 → .097`; factor changes only `+.002`. |
| DeepSeek endpoints | 3 are higher and 3 are lower. Action moves `.453 → .639`; factor moves `.629 → .592`; typology changes only `−.003`. |
| Evaluation window | Every plotted row was evaluated on May 28–29, 2026. The quarter field describes the named model release, not evaluation time. |
| Same-B releases | DeepSeek V3-0324, V3.1, and V3.2 all carry 671B-main / 37B-active specifications, yet their task point estimates differ. Parameter count alone is not a model identity. |

The matrix is the executive view. Exact point paths remain in two landscape audit figures: [UniMoral classification](../assets/results/04_release_period_paths_detail_a.svg) and [consequence plus ValuePrism](../assets/results/04_release_period_paths_detail_b.svg). All 35 plotted points name the model and published B count.

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
