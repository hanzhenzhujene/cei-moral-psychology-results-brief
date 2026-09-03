# Adversarial self-critique

## Bottom line

This audit is release-usable as a **tracked-artifact consistency and claim-boundary audit**, not as raw-result reproduction. The fresh clone does not contain the 143 canonical-audit `.eval` archives, four full UniMoral calibration `.eval` files, 42 ValuePrism broad-inventory accuracy `.eval` files, 4,640 M3oralBench images, gated UniMoral dataset snapshot, or exact paper model revisions. The most important conclusions survive that limitation: the four evidence classes reconcile to 143 cells; no paper performance row is exact; MoralBench compare ranks are unresolved by the available aggregate uncertainty; and measurement repair precedes broad reruns. Any claim about raw scorer reproducibility, human validity, or exact replication remains out of bounds.

## Conclusions under attack

| Major conclusion | Strongest alternative explanation | Selection / judge dependence | What could disappear under a reasonable re-analysis? |
|---|---|---|---|
| The canonical audit partition is 78 primary + 26 sensitivity + 9 extension + 30 excluded. | A different promotion policy could move parser-flagged cells into primary. | Entirely dependent on the frozen operational gates and modality rule. | Class membership could change; the 143-cell universe and current canonical accounting would not. |
| No paper performance comparison is exact. | A hidden paper checkpoint or scorer snapshot might match the repository more closely than documented. | Depends on a strict identity key: data, model, prompt, decoding, scorer, aggregation. | Some rows could become exact only after missing identities are demonstrated, not merely inferred from names. |
| MoralBench compare ranking is unresolved. | A paired item-level analysis could detect stable differences even when marginal intervals overlap. | Depends on aggregate Wilson intervals because paired predictions are absent. | The “unresolved” judgment could narrow or reverse after a valid paired test; the small item banks and missing paired evidence would remain. |
| Broad moral-benchmark saturation is unsupported. | High agreement scores and small upper-scale ValuePrism increments could reflect genuine task ceilings. | Depends on task selection, synthetic/reference labels, and no preregistered saturation criterion. | A bounded ceiling claim for a particular surface could emerge; a cross-task “morality is solved” claim still would not follow. |
| Repair and validation outrank indiscriminate reruns. | A release deadline might value coverage over construct validity. | This is a decision judgment, not a statistical theorem; it assumes the goal is defensible evidence. | The operational order could change under a different objective, but extra rows would still not repair target validity or provenance. |
| UniMoral target ambiguity needs measurement. | Repeated targets may agree almost perfectly. | Current concern is structural: identical no-persona inputs retain annotator-specific targets. | The ambiguity concern could largely disappear after measurement; it is therefore stated as unquantified, not as observed disagreement. |

## Adversarial checks

| Attack | Evidence examined | Disposition |
|---|---|---|
| Did the audit accidentally count all 113 non-excluded cells as one valid class? | Cell-level inclusion join and 143-row tally | No. Primary 78, sensitivity 26, extension 9 remain separate. |
| Did any figure pool metrics? | Figure source tables and axes | No. Accuracy, normalized preference, and METEOR have separate panels; keyword heuristics never enter primary figures. |
| Did paper percentages and repo proportions create fake deltas? | Ledger values and interpretation text | No direct deltas are claimed across mismatched protocols; paper display scales are normalized only where explicitly stated. |
| Was “same model” inferred from a name? | UniMoral paper/software/backend versus repo route | Downgraded to nominal checkpoint-name match. |
| Were ValuePrism labels treated as human moral truth? | Paper task construction and ledger | No. Relevance is contrastive synthetic labeling; valence predicts GPT-4 labels. Neither is relabeled as human moral truth. |
| Were small-N ranks overinterpreted? | Wilson intervals and all within-task marginal overlaps | No. The report treats overlap as a warning and explicitly notes that it is not a paired test. |
| Were narrow large-N errors mistaken for validity? | UniMoral/ValuePrism limitations | No. Prompt, dependency, contamination, route, and construct uncertainty are kept outside binomial SE. |
| Were excluded M3oral scores used as ability evidence? | Modality audit | No. All 30 remain no-inference exclusions. |
| Did the audit accept generated HTML/reports as canonical? | Precedence review | No. Multiple stale or contradictory surfaces are explicitly demoted. |
| Were paper claims invented? | Final ACL/AAAI papers, author arXiv v2 supplement, and official metadata | No secondary source used for paper claims; paper inconsistencies are flagged. |
| Did framework categories become a moral leaderboard? | Claim contract | No. Frameworks are measurement coordinates; profiles are not ranked. |
| Was new external state created? | Work log | No provider runs, GitHub writes, Slack, Notion, or repository edits. |

## Hidden assumptions and judge choices

- **Source precedence is a judgment.** The post-PR audit CSV/JSON is treated as canonical over older reports because it is newer, cell-complete, and exercised by consistency checks. A release owner could choose a different freeze, but must then publish a different explicit contract.
- **Uncertainty is conditional.** Wilson and saved-SE intervals condition on the tracked scored units. They omit scenario/annotator clustering, prompt selection, route drift, benchmark contamination, and construct error.
- **The `n≈93` target optimizes interval width, not rank power.** It is useful planning arithmetic near a 0.5 rate; it does not replace a paired power analysis based on discordant items.
- **Task alignment is graded conservatively.** Shared label names or metric families are insufficient when model, prompt, data revision, scorer, or aggregation differ.
- **Repository absence is not historical nonexistence.** Missing raw archives and images mean “not reproducible from the fresh clone,” not “never existed.”
- **Metrics do not share a cardinal scale.** Accuracy, preference, METEOR, keyword heuristics, weighted F1, and human judgments remain separate even when all lie numerically in [0,1].

## Corrective changes prompted by the adversarial pass

1. Recomputed the Gemma UniMoral action Wilson interval from the canonical rescored proportion rather than the stale raw `n_correct`; otherwise the point estimate could fall outside its own interval.
2. Reframed all compare-task overlap statements as **marginal interval** evidence and added the missing paired-test caveat.
3. Replaced “sidecars” with the actual evidence shape: 12 entries in one tracked rescore-override file.
4. Split the UniMoral model bridge into a nominal Llama checkpoint-name bridge and unavailable Phi/DeepSeek paper-model rows.
5. Labeled current ValuePrism minima as raw parsed-label ranges containing unadjudicated format/protocol failures, preventing failed parsing from masquerading as substantive model spread.
6. Replaced “ceiling compression” and untested power language with bounded terms: upper-scale clustering, small descriptive increments, diagnostic spread, wide marginal intervals, and unresolved ranks.
7. Corrected the UniMoral venue to ACL 2025 Volume 1: Long Papers and routed Value Table 13 details to the arXiv supplement while preserving the AAAI archival citation.
8. Repaired malformed Markdown table indentation and HTML structure, exposed uncertainty/provenance in the explorer, and linked each figure to its full-size asset.

## Technically correct but strategically unhelpful findings

- Reporting 18 wide intervals without saying they are concentrated in two compare tasks would imply broader imprecision than the evidence supports.
- Reporting narrow nominal errors for large UniMoral/ValuePrism rows without foregrounding dependence and construct error would create false confidence.
- Enumerating stale artifacts without a source-precedence rule would leave release owners unsure which surface to trust.
- Treating all missing paper surfaces as equally urgent would waste effort; human validation and parser/disagreement repair have higher decision value than recreating every paper table.
- A single “saturation score” would be easy to communicate but would erase metric semantics, evidence classes, and task-specific failure modes.

## Residual uncertainty

1. **Raw-output reproducibility:** tracked CSV/manifests can be cross-checked, and the saved BERTScore rows can be re-aggregated, but canonical-audit, calibration, and ValuePrism accuracy archives are absent.
2. **Dependency structure:** current intervals treat scored rows/items as the declared unit and do not model shared scenario/annotator clustering or paired model responses.
3. **Dataset identity:** both papers omit immutable dataset fingerprints; current exports are likely aligned but cannot be called revision-exact.
4. **Model identity:** paper checkpoints, current provider routes, and backend aliases are not revision-equivalent.
5. **Contamination:** recent hosted models may have seen public benchmark data; artifacts do not test this.
6. **Human validity:** Gate M is not run; agreement with benchmark labels is not agreement with representative people.
7. **Power planning:** n≈93 is a Wilson-width target, not a preregistered paired-comparison power calculation.
8. **Paper ambiguities:** UniMoral reports unsupported “significant” differences; Value Kaleidoscope has internal participant/missing-perspective inconsistencies and sparse interval reporting.

## What would falsify the readout

- A fully pinned paper-protocol rerun could produce an exact comparison and supersede the approximate ledger rows.
- Cluster-aware intervals could widen or shift the current uncertainty account.
- Human validation could show that current labels poorly represent the intended constructs, requiring stronger claim withdrawal.
- A larger independent item bank could reveal stable model differences hidden by current small N—or support a bounded task-specific ceiling claim.

## Verification record

The release candidate was checked in four layers:

- repository-native consistency: all 143 audit-cell assertions, 18/18 consistency checks, and 11 focused audit tests pass;
- output integrity: required files, ledger schema/statuses, 143-cell partition, 78 current-primary intervals, internal links/assets, one-page 300-dpi-class PNG/SVG/PDF figure sets, and the SHA-256 artifact manifest validate;
- visual behavior: all five figures were inspected at original resolution; the explorer was exercised at desktop and 390-pixel mobile widths, including search, status filters, reset, overflow, and console checks;
- hygiene: the cloned source repository remains clean, output text matches none of the four common credential patterns checked, and no provider, GitHub, Slack, or Notion write was made.

These checks verify the released artifacts and their tracked inputs. They do **not** overcome the raw-archive, model-identity, clustered-uncertainty, contamination, or human-validity limits above.
