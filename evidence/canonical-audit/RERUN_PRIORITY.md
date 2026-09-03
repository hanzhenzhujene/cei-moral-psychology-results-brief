# Rerun and evidence-acquisition priority

## Recommendation

**Highest information value:** repair existing measurement evidence first, then run **Gate M human validation**. More model rows do not resolve whether the instrument measures the intended construct. For statistical ranking, the best new model-evaluation spend is an **independent item-bank expansion** on the two low-precision MoralBench compare tasks—not repeat calls on the same deterministic prompts.

| Rank | Action | What it resolves | Incremental cost | Precondition |
|---:|---|---|---|---|
| 1 | Adjudicate 12 parser-flagged cells from saved rescore entries | separates formatting failure from task performance | none if raw archives are accessible | raw archives for promotion; otherwise retain sensitivity status |
| 2 | Audit UniMoral duplicate-label disagreement and paper-style metrics | estimates the no-persona ceiling and any target disagreement | none | gated dataset plus saved predictions/raw archives |
| 3 | Run Gate M human validation | tests whether benchmark labels and outputs reflect intended constructs | human-study cost | sampling and ethics plan |
| 4 | Expand MoralBench compare item banks | narrows model-comparison uncertainty | new item creation plus reruns | version a new benchmark; repeats of deterministic items do not count |
| 5 | Rerun 14 reasoning-overflow text cells under a pinned budget | measures dependence on reasoning/output budget | targeted model calls | fixed provider routes, budgets, and promotion policy |
| 6 | Fill 30 excluded M3oralBench model-task cells with images | broadens multimodal model coverage | high multimodal cost | only if the release needs cross-model multimodal claims |
| 7 | Run pinned Kaleido and cue-conditioned UniMoral replications | creates an actual paper-to-repo bridge | model access plus scoring | only if a replication claim is a release objective |

## 1–2. No-provider-cost repair

### Parser adjudication

The 12 parseability cells already have entries in the tracked `rescore_overrides.csv`; 11 entries reach at least 0.95 parseability and one reaches 0.875. Review raw outputs against a frozen parser and a human spot-check rubric. If raw archives remain absent, document that override-only adjudication is insufficient for promotion. This work can recover interpretability without new model calls.

### UniMoral disagreement and paper-style metrics

In no-persona mode, identical scenario/action inputs retain three annotator-specific targets. Whether those targets conflict, and how often, has not yet been quantified. Compute:

- duplicate-prompt modal-label ceiling;
- label entropy and unanimous/disputed strata;
- accuracy and weighted F1 by language, cue availability, and psychological/Reddit source;
- scenario-cluster bootstrap intervals.

This distinguishes target ambiguity from model failure. It needs the gated dataset and saved predictions/raw archives, which are not present in the fresh clone, but it does not require provider calls.

## 3. Gate M human validation

This is the highest-value **new evidence** because it targets construct validity and missing perspectives. Pre-register the unit of analysis, disagreement policy, sampling frame, languages/demographics, and stopping rule. Report distributional disagreement—not only majority agreement. Include explicit checks that framework labels are understood as measurement coordinates rather than correct answers.

## 4. Independent-N expansion

Current compare sets have 20 MFQ and 24 vignette items per model. Near a 0.5 rate, a Wilson 95% interval reaches full width ≤0.20 at about **n=93**, or +73 MFQ and +69 vignette items. At observed rates, targets range about n=60–93, requiring +63–73 items for most rows; the observed high-rate Gemma vignette row is the exception at +36.

Repeating the same temperature-zero items does not add independent item-level N. Create a versioned new item bank, preserve the current set as an anchor, and sample from the intended construct domain. A full-width target is only descriptive planning; formal model-difference power should use a paired design and expected discordance.

## 5. Reasoning-budget sensitivity

Fourteen text cells are affected. Rerun only these cells with frozen routes, explicit reasoning/output budgets, and a declared comparison plan. Keep both primary-budget and extended-budget outcomes; do not silently replace the frozen protocol.

## 6. Multimodal completion

Filling the 30 excluded M3oral cells entails ten models across 2,320 judgment + 1,160 foundation + 1,160 response samples: **46,400 image-bearing sample evaluations**. This is worthwhile only if the release needs a cross-model multimodal claim. The current nine-cell extension already supports a bounded three-model pilot.

## 7. Paper-protocol replication

Move this higher only if a release objective requires a replication claim. A valid bridge must pin dataset fingerprints, checkpoint revision/quantization/backend, prompts, decoding, software/scorer revisions, aggregation, and scenario-level uncertainty. For Value Kaleidoscope, run the actual Kaleido weights. For UniMoral, reproduce cue conditions and weighted F1; a no-persona accuracy run is not enough.

![Priority ladder](figures/05_evidence_acquisition_priority.png)

[Machine-readable priority table](figures/data/rerun_priority.csv)
