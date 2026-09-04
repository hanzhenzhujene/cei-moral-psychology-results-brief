# Jenny onboarding page audit

## Verdict

The Claude onboarding artifact is not current enough to publish or use as a completion tracker. It is an August 27 snapshot. The canonical audit changed after PR #33 on September 1.

The page also mixes three evidence systems that must stay separate:

1. the MP-v2 poster study;
2. the external benchmark matrix;
3. repository operations.

The benchmark CSVs listed under each poster do not contain the underlying MP-v2 poster evidence.

Use the [current results brief](../README.md) for benchmark results. Keep each poster as a separate historical artifact, and use the onboarding page only as an August 27 snapshot—not as the completion tracker.

## Current status correction

| Item | Onboarding page | Verified state |
|---|---:|---:|
| Models | 13 | 13 |
| Task variants | 11 | 11 |
| Primary text cells | 84 “valid” | 78 |
| Sensitivity text cells | 19 “needs review” | 26: 12 parser, 14 reasoning budget |
| Multimodal extension | Not separated | 9 |
| Excluded cells | 39 “invalid” | 30 |
| Missing | 1 | 0 |
| Models primary on all eight text tasks | 8 | 5 |
| Broad coverage heatmap | 534 / 832 complete | 535 / 832 marked complete |
| `all_scores.csv` | 1,882 rows | 1,886 rows |
| `scores.csv` | 3,177 rows | 3,246 rows |
| Gate M | Not run | Still not run |

Current release accounting is:

`78 primary text + 26 sensitivity text + 9 multimodal extension + 30 excluded = 143`

The “Opus × UniMoral action prediction missing” blocker is obsolete. The canonical row is present, primary, has `n=8,784`, and score `0.634563`.

## Completion matrix

“Static only” means a visual exists in a poster PDF, but its row-level source package is not available in this repository.

| Poster | Requested task | Status | Correction |
|---|---|---|---|
| Family Competence | Per-model score shapes | Static only | Already in the poster. Do not show as untouched work. |
| Family Competence | Cross-benchmark correlations | Not research-ready | Existing tables aggregate incompatible metrics and unsafe source surfaces. |
| Family Competence | Wilson interval widths | Complete in canonical audit | Use the 78-row recomputation: 18 wide intervals, all on MoralBench compare tasks. |
| Family Competence | Score heatmap with validity overlay | Stale | Existing image still uses the old roster state and missing Opus row. |
| Family Profile | MFT radar | Wrong requested form | The poster already contains line profiles. The repository radar is a heterogeneous benchmark aggregate. |
| Family Profile | Profile clustering | Not done | ICC and cosine similarity are proposal ideas only. |
| Family Profile | Kohlberg schema bars | Static only | Bars exist in the poster; coder inputs are absent. |
| Family Profile | Schwartz circumplex | Not available | The original arm missed the sample floor. A later five-model arm reached it, but downstream recovery remained indeterminate, so no reproducible profile is available. |
| Bidirectional Alignment | Judge-difference histogram | Static only | It exists in the Family C poster, not the current BiAlign poster. |
| Bidirectional Alignment | School × setting difference | Static only | It exists beside the histogram in the Family C poster. |
| Bidirectional Alignment | Channel reliability | Static only | Tables exist in Family P and BiAlign; source records are absent. |
| Bidirectional Alignment | Provenance visual | Not done | The referenced diagnostic image does not show Git or source completeness. |
| Administration | Cell completeness | Complete in canonical audit | Use the four-class canonical explorer, not the stale onboarding counts. |
| Administration | Administration yield | Static only | Poster reports 3 of 30 bundles and 18 of 18 declines. |
| Administration | Exclusion sensitivity | Partial | Parser rescoring exists; a complete preregistered sensitivity analysis does not. |
| Administration | Reproduce figures | Not complete | Raw archives and poster generators are absent from the fresh checkout. |

## Factual corrections by section

### Relevant benchmark table

| Benchmark | Page label | Correct local description |
|---|---|---|
| MoralBench | Accuracy | Agreement tasks are normalized-preference proxies; only comparison tasks use accuracy. |
| UniMoral | Accuracy / METEOR | AP/MTC/FAA use local accuracy in default no-cue mode; consequence generation uses METEOR plus a separate offline BERTScore bridge. The paper uses weighted F1 and BLEU/METEOR/BERTScore. |
| MoReBench | Rubric score | Four-marker keyword-coverage proxy. It is not the paper's expert-weighted Regular or Hard score. |
| MoralLens | Normalized preference | Framework-detectability proxy and binary expected-pattern match. Paper CDGAP and Utility are unavailable locally. |

### Family Competence

- `mft_matrix_long.csv` is a 143-row all-class matrix, not a 143-cell primary matrix.
- `model_task_confidence.csv` is stale at 84 rows.
- `paper_results_table.csv` is not safe evidence for the poster.
- The current 143-cell benchmark audit cannot validate the poster's S1/S2/S3 scores.

### Family Profile

- No Schwartz value-priority profile is available.
- `poster_external_profiles.png`, `poster_benchmark_supplement.csv`, and the radar chart combine incompatible benchmark metrics and are not Family P evidence.
- The profile cluster analysis is not complete.

### Bidirectional Alignment

- The page's `510 pairs, mean |Δ| 0.1476` describes only the second reported run group.
- A separate 306-pair group reports `mean |Δ| 0.1618`.
- Neither result can be reproduced from `mft_matrix_long.csv` because that file has one aggregate benchmark score rather than paired MP-v2 judge legs.

### Administration

- The coverage files listed on the page are not the source of the pseudo-respondent sample-floor gate.
- The poster reports 18 of 18 declines at 3 bundles against a floor of 30.
- It also reports a later five-model arm that reached 30 bundles but remained indeterminate because two recovery criteria lacked a sealed implementation.
- The displayed seven-step pipeline does not match the actual refresh target.

## Redesign rule

Use three reader layers:

| Layer | Question answered |
|---|---|
| Research lead dashboard | What is ready, what does it mean, and what decision is needed? |
| Four poster briefs | What did each poster report, how certain is it, and what must we not conclude? |
| Evidence appendix | Which file, commit, metric, row count, and pipeline supports the statement? |

Every result should have five fields: result, evidence, meaning, decision, and limit.

Move API setup, provider routing, credit history, and command details out of the main story. Replace jargon with concrete terms such as “run group,” “minimum sample requirement,” and “all expected records are present.”

## Source

Original artifact: [CEI Moral Psychology — Jenny Onboarding](https://claude.ai/code/artifact/4fce545b-4abd-4256-863f-714a51e9e82c)
