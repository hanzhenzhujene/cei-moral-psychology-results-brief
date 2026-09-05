# Research lead brief

## Decision

Publish each task's current result and uncertainty, with its evidence limits. Label the size and version findings as exploratory. Do not publish the old MP-v2 poster numbers until the original run files are restored.

The central finding is simple: no model stays on top across tasks. The two MoralBench comparison tests cannot reliably show a leader, and the observed size and release-period paths do not all move in the same direction.

## Result to decision

| Question | Evidence-backed answer | Research implication | Release decision |
|---|---|---|---|
| Is there one consistently best model? | No. Among the five models with main audited results on all eight tasks, the highest saved score changes by task. | Keep the task results separate. | Publish the task panels; reject a global leaderboard. |
| Can the comparison tests tell us which model leads? | No. Marginal score ranges overlap for all 28 MFQ and all 45 vignette model pairs. These are one-model-at-a-time ranges, not paired comparisons. | Restore every model's answer and score for each question, then compare the same questions directly. | Check scoring and labels before adding more questions. |
| Do scores rise after both size steps on the four UniMoral tasks? | Not consistently. Of 12 complete model-family × task paths, 4 rise twice, 7 switch direction, and 1 falls twice. Gemma factor rises while Gemma typology falls across the same 4B→12B→27B sequence. | Bigger is not always better; size alone cannot explain the differences. | Use this as an exploratory result only. |
| Do later Qwen and DeepSeek versions score higher on every UniMoral task? | No. Qwen has 3 higher and 1 lower endpoint; DeepSeek has 2 higher and 2 lower. | Every plotted row was evaluated May 28–29, 2026; release period describes the model, not the evaluation time. | Do not present this as a progress trend. |

## Three decisions for the research lead

1. Share each task's current result and uncertainty now, with the evidence limits beside it.
2. Restore every model's answer and score for each question. Check scoring and labels, then compare models on the same questions.
3. Run the planned human review (Gate M): ask people whether the test matches human judgment. Add more questions only if the model order is still unclear.

## Highest-value next action

Restore the question-level answers and scores, check scoring and labels, and compare models on the same questions. Then run human review. Add new comparison questions only if the model order is still unclear.

## What is current, and what is exploratory

| Evidence layer | Coverage | Interpretation boundary |
|---|---:|---|
| Canonical primary text | 78 cells | Current task-level aggregate evidence. Saved intervals are nominal and do not capture all dependence or validity risks. |
| Common roster used in the main chart | 40 cells: 5 models × 8 tasks | Fairer visual coverage, but still not a ranking and not a human-validity result. |
| Exploratory model snapshot | 102 successful, 13 error, 4 cancelled rows | Family, size, and release metadata only. The fresh clone has no saved raw logs or uncertainty; two routes also show large reasoning-token drift despite control attempts. |
| Canonical UniMoral and ValuePrism crosswalk | 17 approximate, 4 proxy-only, 16 unavailable, 0 exact | Method context only; no exact numeric replication for those surfaces. |

## What changed after onboarding

| Area | Old page | Current evidence | Action |
|---|---|---|---|
| Canonical audit | 84 valid, 19 review, 39 invalid, 1 missing | 78 primary, 26 sensitivity, 9 multimodal extension, 30 excluded | Replace the stale categories rather than mapping them cell by cell. |
| Benchmark results | Appeared incomplete in the earlier review | Substantial aggregate and some sample-level evidence exists under `results/` | Use the current aggregate result layer; name the raw archives that remain absent. |
| Poster completion | Rendered visuals appeared as open tasks | The PDFs exist, but their original run files do not | Separate visual completion from numerical verification. |
| Relevant papers | Titles and simplified metrics only | Five primary papers reviewed; no exact replication | Compare methods and interpretations, not scores. |

## Poster appendix decision

| Poster | What can remain | Required before numerical publication |
|---|---|---|
| Family Competence | Pipeline-integrity lesson | Restore the cell ledger, verdict records, prompts, scorer, uncertainty, aggregation, and receipts. |
| Family Profile | “Profiles are not rankings” and the missing-Schwartz finding | Restore coder records and correct the `six legs × 1,645` wording. |
| Bidirectional Alignment | Validation architecture and “agreement is not validity” | Restore paired judge records and preregister Gate M. |
| Administration | Administration belongs in sample identity | Regenerate under the current seal with source manifests and uncertainty. |
