# Claim boundaries

Use this file as a release-language contract. “Allowed” statements require the named qualifier; “not supported” statements cross the available evidence boundary.

## Comparison vocabulary

| Status | Required meaning |
|---|---|
| Exact | Same construct, task/data revision and slice, model revision/backend, prompt/decoding, scorer, and aggregation. No performance row meets this bar. |
| Approximate | A task or metric family overlaps, but one or more identity/protocol dimensions differ. Numeric deltas are contextual, not replications. |
| Proxy-only | Related construct or label name, but the measurement target differs. Do not report a numeric performance delta. |
| Unavailable | The repository lacks the required task, condition, model, metric, human protocol, or stratification. |

## Release claims

| Topic | Allowed | Not supported | What would change the boundary |
|---|---|---|---|
| Audit coverage | “The frozen audit contains 78 primary text, 26 sensitivity text, 9 multimodal extension, and 30 excluded cells.” | “The benchmark has 113 valid cells.” | Keep the four evidence classes explicit. |
| Primary status | “These 78 cells pass the declared operational gates.” | “These results are fully validated.” | Clean provenance, raw reproducibility, construct validation, and uncertainty review. |
| Sensitivity | “Twenty-six cells diagnose parser or budget dependence.” | Pooling them into headline means/ranks. | Predeclared promotion policy plus matched reruns or audited rescoring. |
| Multimodal | “Nine image-bearing extension cells exist for three models.” | Treating 30 text-only M3oral runs as weak multimodal evidence. | Correct image-bearing reruns under one frozen protocol. |
| Paper replication | “Paper links are approximate, proxy-only, or unavailable.” | “We replicated UniMoral or Value Kaleidoscope.” | Full protocol/model/data/scorer identity and uncertainty. |
| Llama bridge | “Same checkpoint name; task-aligned; metric/protocol-mismatched.” | “Exact same-model replication.” | Pin the paper and repo model revision, backend, prompts, decoding, and scorer. |
| ValuePrism relevance | “Accuracy on contrastive synthetic labels: positives were GPT-4-generated for the situation; negatives came from other situations.” | “Human value importance” or “normative relevance.” | Direct, representative human labeling and a declared construct. |
| ValuePrism valence | “Accuracy against GPT-4's Supports/Opposes/Either labels.” | “Moral correctness” or “acceptability.” | Human/normative protocol with explicit disagreement treatment. |
| UniMoral AP | “No-persona agreement with annotator-specific reference choices; within-scenario disagreement is unquantified.” | “Personalized moral prediction” under the paper protocol. | Cue-conditioned evaluation and duplicate-label disagreement analysis. |
| Saturation | “Some agreement point estimates cluster high; ValuePrism has small descriptive upper-end scale increments; compare tasks have wide marginal intervals and unresolved ranks.” | “Simple moral benchmarks are saturated” or “moral reasoning is solved.” | Predefined saturation criterion, adequate independent N, ceiling/error analysis, and richer transfer tests. |
| Model ranking | Task-specific, metric-specific descriptions with intervals. | One moral leaderboard or averages across accuracy, preference, METEOR, and keyword heuristics. | A justified common construct and calibrated composite—not currently available. |
| Understanding | “The model produces outputs aligned with a benchmark scorer under this protocol.” | “The model genuinely understands morality.” | No single benchmark establishes this; requires convergent behavioral and causal evidence. |
| Normative values | “Frameworks provide measurement coordinates.” | “This benchmark defines the correct values for AI systems.” | Legitimate normative governance cannot be inferred from benchmark scores alone. |
| Human validity | “Gate M is not yet run.” | “The instrument reflects plural human values.” | Preregistered human validation, representation checks, disagreement reporting, and error taxonomy. |

## Metric firewall

- **Accuracy:** proportion matching a discrete reference label or accepted reference set, including tied MTC/FAA maxima.
- **Normalized preference:** continuous agreement/preference score; not accuracy.
- **METEOR:** reference-overlap similarity for generated consequences; not correctness or human approval.
- **Keyword heuristic:** diagnostic text match; never interchangeable with accuracy.
- **Weighted F1:** the UniMoral paper's AP/MTC/FAA metric; not reproduced by repository accuracy.
- **BERTScore:** semantic reference overlap; not human validation.
- **Human pairwise win rate/correlation:** distinct protocols; do not relabel them “accuracy.”

Keep metrics on separate rows, panels, and claims. Never average them into a single moral score.

## Framework firewall

Moral foundations, ethical typologies, contributing factors, values, rights, duties, and cultural questionnaires are **coordinate systems for measurement**. They expose different slices of behavior and disagreement. They do not provide a canonical ordering of models or the correct values for an AI system. Family-C competence evidence and Family-P profile evidence must remain separate; moral profiles must not be ranked.

## Minimum claim key

Every numerical statement should identify, directly or by linked table:

`task × dataset revision/slice × model route/revision × prompt/protocol × metric/scorer × evidence class × n × uncertainty × commit`

If a key component is missing, say so. If the dataset or model revision is unpinned, do not write “exact.”
