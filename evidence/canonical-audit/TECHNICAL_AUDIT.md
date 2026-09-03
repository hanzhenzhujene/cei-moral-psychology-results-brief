# Technical audit

## Scope and source precedence

This audit is pinned to repository merge commit `b3a348684692f615d789392692ce34a1359192d3`. Three upstream audit artifacts record the malformed 41-character token `276acecd603761e6ff61bd6e2685fbb87f0eaa47d`; this audit normalizes it to the resolvable 40-character commit `276acecd603761e6ff61bd6e2685fbb87f0eaa47`. No files in the cloned repository were edited. The evidence precedence used here is:

1. `results/index/latest/mft_audit_all_runs.csv` plus `mft_audit_evidence.{json,md}` for inclusion classes and counts.
2. `mft_primary_valid_only.csv` for primary scores and score provenance.
3. `mft_audit_sensitivity_only.csv`, joined to `mft_matrix_long.csv`, for failure-mode and rescore diagnostics.
4. Audit evidence JSON/Markdown for the nine multimodal extension cells.
5. Recomputed intervals from the current 78 primary rows; the checked-in confidence file is not current.
6. `reproducibility_manifest.json` for archive pointers, subject to checksum-label and archive-availability caveats.

Older root reports, the August 27 freeze manifest, onboarding counts, broad generated analyses, and inventory reports are navigation aids—not canonical evidence for the September 1 MFT audit.

## Cell accounting

| Evidence class | Count | Metric detail |
|---|---:|---|
| Primary text | 78 | 48 accuracy, 19 normalized preference, 11 METEOR |
| Sensitivity-only text | 26 | 12 parseability, 14 reasoning-budget overflow |
| Multimodal extension | 9 | 6 accuracy, 3 keyword heuristic |
| Excluded | 30 | invalid modality; no score interpretation |
| **Total** | **143** | **13 models × 11 tasks** |

The 78 primary cells split into 37 MoralBench and 41 UniMoral cells. The 26 sensitivity cells split into 15 MoralBench and 11 UniMoral cells. The extension is exactly three models × three M3oralBench tasks. The 30 excluded cells are the other ten models × three M3oralBench tasks.

## Quality-gate diagnostics

### Parseability

Twelve sensitivity cells fail the original parseability gate. All have entries in the single tracked `rescore_overrides.csv`; 11 entries reach at least 0.95 parseability, while Llama-4-Scout vignette compare reaches 0.875. This is strong evidence that most are output-format/parser-policy failures, but rescore success is not automatic permission to promote rows. Promotion requires a frozen parser, human spot audit, and declared policy.

### Reasoning-budget overflow

Fourteen text cells fail for reasoning/output budget behavior. Their high max-token-stop rates and low visible-completion fractions mean the saved scores confound task performance with the protocol budget. Extended-budget results are sensitivity evidence, not replacements for the frozen primary protocol.

### Modality

The nine extension rows have image-bearing samples. The 30 excluded M3oralBench rows do not. Text-only scores on an image-required task are not weak measurements of the same ability; they are invalid measurements of a different input condition.

## Uncertainty method

- Accuracy: two-sided 95% Wilson interval using `n_correct` and `n_scored`; for the Gemma UniMoral action parser rescore, successes are reconstructed from the canonical rescored proportion because tracked `n_correct` remains raw.
- Normalized preference and METEOR: saved mean ± 1.95996 × saved standard error, clipped to [0,1].
- No cross-metric pooling or averaging.
- A full interval width over 0.30 is flagged as materially wide for descriptive ranking.

The current-primary recomputation has 18 wide intervals, all on MoralBench compare tasks. Within MFQ compare, all 28 model pairs have overlapping **marginal** intervals; within vignette compare, all 45 do. This is a conservative rank-instability warning, not a paired model-difference test. Required item counts in the source CSV hold the observed rate fixed; they are planning approximations, not power guarantees under a new item distribution.

## Stale and contradictory surfaces

1. **Malformed source SHA:** `mft_audit_evidence.{json,md}` and `reproducibility_manifest.json` record `276acecd603761e6ff61bd6e2685fbb87f0eaa47d`, which is 41 characters and does not resolve. Removing the spurious final `d` yields `276acecd603761e6ff61bd6e2685fbb87f0eaa47`, a real commit and ancestor of the pinned source HEAD. The source consistency check missed this because it compares only the first eight characters. The source clone remains unchanged; the normalization is explicit in this audit's build provenance.
2. **Checked-in confidence file:** 84 rows reflect the old state. Membership reconciliation finds 73 overlaps, 11 rows no longer primary, and 5 current-primary rows missing. Its 21 wide flags become 18 under the current 78-cell set.
3. **Onboarding artifact / August 27 freeze:** `84 valid + 19 review + 39 invalid + 1 missing` predates PR #33. It also says all 39 M3oral cells are invalid, whereas the current audit has nine multimodal extensions and 30 exclusions.
4. **PR #33 body:** says Kimi has 4/8 primary and 4/8 review; canonical evidence says 2/8 primary and 6/8 sensitivity.
5. **`mft_report.html`:** headline counts are current, but five cells are displayed as primary despite canonical sensitivity status: Kimi MFQ agreement, Kimi vignette agreement, and Llama-4-Scout MFQ agreement/compare and vignette agreement.
6. **Gemma UniMoral action:** the report/wide matrix shows raw 0.6483; canonical primary evidence uses the parser rescore 0.6904599271.
7. **Reproducibility-manifest checksum label:** SHA-256 `a254c802…` is labeled `mft_audited_matrix.csv` but matches `mft_matrix_long.csv`; the actual current audited-matrix hash starts `c3edcc6b…`.
8. **Raw reproducibility:** all 143 canonical-audit `.eval` archives, all four full UniMoral calibration `.eval` files, all 42 referenced ValuePrism broad-inventory accuracy `.eval` files, and the 4,640 M3oralBench images are absent from the fresh clone. The BERTScore bridge preserves 1,782 per-row scores but not raw predictions/references. Tracked artifact consistency and BERTScore re-aggregation are testable; scorer/model-output reproduction is not.
9. **Matrix manifest language:** core validity intentionally counts all 39 M3oral cells as invalid, while the audit promotes nine into a separate extension. Its explanation that all 39 lack images is stale for those nine.
10. **Root README scope:** describes an older five-paper, 105-cell Option 1 release and does not route readers to the current 143-cell audit. This is a scope collision, not a count to merge.
11. **Broad generated analyses:** some average heterogeneous metrics and treat invalid-modality M3oral scores as difficulty evidence. They are unsuitable for ranking or saturation claims.
12. **UniMoral venue and bridge:** repository prose says “ACL Findings 2025” and “exact same-model.” The authoritative venue is ACL 2025 Volume 1: Long Papers, and only the checkpoint name is nominally shared.
13. **Stale UniMoral stratification:** `unimoral_stratified_stats.csv` has 1,561 rows / 39 model-task keys, but one key is now sensitivity-only, three current-primary keys are missing, and Gemma action retains raw 0.648338 rather than canonical rescore 0.690460. It cannot support a current language comparison without rebuilding.
14. **Paper internal limits:** UniMoral contains an 8,784-versus-5,256 count inconsistency and unsupported significance language. Value Kaleidoscope §4.2 reports 613 annotators, Appendix E reports 612, and demographic subgroup counts in Tables 19–21 sum to 468. Separately, the introduction's `>1%` missing-value statement conflicts with §4.1's 0.35% and Ethical Impact's `<1%`; the diverse-study 30% missing-perspective rate is a different protocol and construct. Tables 5, 6, and 13 report no CIs.

## Provenance quality

63/78 primary rows record `git_dirty=True`; the other 15 have blank run-level SHA/dirty fields. DeepSeek, GLM, and GPT-5.4 use multiple route aliases across primary tasks. One primary score is an offline parser rescore. Inspect version is consistently 0.3.200 and temperature is 0, but these facts do not establish backend identity. ValuePrism comparison context comes from broad `all_scores.csv`, outside the canonical 143-cell MFT audit; it is not headline evidence.

## Paper alignment details

### UniMoral

The final ACL paper evaluates six languages and four tasks. AP/MTC/FAA use weighted F1 under cue conditions. The repo bridge uses no-persona mode and accuracy. The paper's Llama checkpoint revision is unpinned; repo inference is routed through OpenRouter. Consequence METEOR/BERTScore use similar metric families but unpinned scorer/backends. There is no exact performance row under the full key: construct, task, dataset revision/slice, model revision, prompt, decoding, scorer, and aggregation.

The paper does not include a no-context row, so “context greatly improves performance” cannot be measured from its published cue table. Means derived from the rounded Table 4 cells span approximately 1.82 points. No CI or significance procedure is reported.

### Value Kaleidoscope / ValuePrism

Table 13 relevance and valence accuracy are the only task-aligned anchors. The paper trains FLAN-T5 Kaleido models; current repo rows prompt unrelated LLMs. Relevance positives encode GPT-4 generation and sampled negatives, not direct human relevance. Human list preference, correlation, transfer, entropy, false-balance, rights-coverage, and representation surfaces have no matched repository protocol.

## Verification already executed

- `python3 scripts/assert_consistency.py` — all 143-cell assertions passed.
- `python3 scripts/check_consistency.py` — 18/18 checks passed.
- `/opt/anaconda3/bin/python -m pytest tests/test_mft_audit.py -q` — 11 passed.

Output-artifact, render, link, and clean-worktree checks are recorded in [SELF_CRITIQUE.md](SELF_CRITIQUE.md).

## Machine-readable audit tables

- [Primary intervals](figures/data/primary_confidence_intervals.csv)
- [CI staleness reconciliation](figures/data/ci_staleness_reconciliation.csv)
- [Audit partition](figures/data/audit_partition.csv)
- [Sensitivity failure modes](figures/data/sensitivity_failure_modes.csv)
- [Task diagnostic spread](figures/data/task_diagnostic_spread.csv)
- [Evidence-status matrix](figures/data/evidence_status_matrix.csv)
