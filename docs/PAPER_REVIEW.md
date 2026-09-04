# Relevant benchmark paper review

## Read status

The four primary papers were downloaded and reviewed for methods, results, authors' interpretation, limitations, and fit to the local evaluator. The three newly retrieved external PDFs were used for review but are not redistributed in this repository.

| Benchmark | Primary paper | Code and data | Review status |
|---|---|---|---|
| MoralBench | Ji et al., “MoralBench: Moral Evaluation of LLMs,” ACM SIGKDD Explorations 27(1), 2025. [arXiv PDF](https://arxiv.org/pdf/2406.04428) | [Official repository](https://github.com/agiresearch/MoralBench) | Full 10-page paper read. |
| UniMoral | Kumar & Jurgens, ACL 2025 Long Papers, Best Resource Paper. [Paper](https://aclanthology.org/2025.acl-long.294/) · [PDF](https://aclanthology.org/2025.acl-long.294.pdf) | [Repository](https://github.com/shivanik96/UniMoral) · [Dataset](https://huggingface.co/datasets/shivaniku/UniMoral) | Full paper, appendices, and limitations reviewed. |
| MoReBench | Chiu et al., ICLR 2026. [arXiv PDF](https://arxiv.org/pdf/2510.16380) · [OpenReview](https://openreview.net/pdf?id=RMwJXp5Kb1) | [Repository](https://github.com/morebench/morebench) · [Dataset](https://huggingface.co/datasets/morebench/morebench) | Main paper and all relevant methods, scoring, validation, results, and caveat appendices reviewed. |
| MoralLens | Samway et al., EMNLP 2025 Main. [Paper](https://aclanthology.org/2025.emnlp-main.1563/) · [PDF](https://aclanthology.org/2025.emnlp-main.1563.pdf) | [Repository](https://github.com/keenansamway/moral-lens) | Full main paper, experiment details, validation, robustness, and limitations reviewed. |

## The four paper questions in plain language

| Paper | What the paper is trying to answer | What the current local evidence can answer | Match |
|---|---|---|---|
| MoralBench | Do model choices track human ratings on moral-foundation statements and vignettes? Can a model choose the statement people rated higher? | Fresh agreement and forced-choice results with saved intervals, under a different model roster and administration. | Approximate |
| UniMoral | Can a model predict an annotator's action, moral framework, and influencing factors, and generate plausible consequences? How do cues, language, and scenario source affect those results? | No-cue label accuracy for action, typology, and factor tasks, plus consequence METEOR. It cannot test the paper's cue, language, or source claims. | Approximate for task families; unavailable for cue claims |
| MoReBench | Does the reasoning process cover expert-defined considerations, trade-offs, logical steps, and outcomes? Do scale and general capability predict this? | The local evaluator only checks whether four generic reasoning-word groups appear. That is not the paper's expert-weighted score. | Proxy only for performance |
| MoralLens | Which consequentialist or deontological rationales appear? Do they change when reasoning comes before versus after the decision? | The local adapter checks keyword detectability and one binary expected-direction pattern. It cannot reproduce the paper's rationale judge or order effect. | Proxy only for performance |

The size and release-period charts in the results brief are local follow-up questions. They are not claims that the four papers asked or answered those questions. The headline views use only the four UniMoral task families; ValuePrism remains in the full audit tables.

## Replication verdict

| Exact | Approximate | Proxy-only | Unavailable |
|---:|---|---|---|
| **0** | MoralBench task families; UniMoral task families | MoReBench performance; MoralLens performance | UniMoral cue claims; MoReBench-Theory; MoralLens paper metrics and order-effect replication |

## Protocol comparison

| Claim unit | Paper protocol | Local protocol | Match | Safe interpretation |
|---|---|---|---|---|
| MoralBench agreement | 20 MFQ and 24 vignette items; selected human score summed; temperature 0.7; five repetitions | Same-sized task families; score normalized to 0–1; temperature 0; different routes and models | Approximate | Same task family, different scale and administration. Do not compare paper totals with local values. |
| MoralBench comparison | 20 MFQ and 24 vignette pairs; one point for higher human-rated statement; five repetitions | Same accuracy family; one deterministic run; no demonstrated dataset fingerprint identity | Approximate | A fresh evaluation, not a reproduction of the paper's model ordering. |
| UniMoral AP/MTC/FAA | Six languages; cue conditions; weighted F1; 8,784 AP rows and 3,492 extensive rows | Default no-cue mode; accuracy; hosted 2026 route; different generation limits | Approximate | Agreement with UniMoral labels under a no-cue protocol, not personalized moral prediction. |
| UniMoral consequence generation | BLEU, METEOR, and multilingual BERTScore against human references | Live best-reference METEOR; separate offline BERTScore bridge for 1,782 rows | Approximate | Same metric families, but scorer, route, and aggregation are not identical. |
| UniMoral cue, language, and source findings | Cue effects, language patterns, psychological versus Reddit comparison | No matched cue counterfactual; stale stratification; missing raw calibration archives | Unavailable | The current run cannot confirm these paper findings. |
| MoReBench scenario ingestion | 500 public scenarios: 293 advisor and 207 agent; expert criteria with weights −3 to +3 | Loads 500 public rows with the same role counts; release fingerprint not pinned | Approximate | Scenario alignment is plausible, not revision-exact. |
| MoReBench performance | Expert-criterion Regular and length-corrected Hard scores; long outputs and thinking traces | Four generic keyword checks; think blocks removed; maximum 1,024 tokens | Proxy-only | Local values measure generic reasoning-word coverage, not MoReBench performance. |
| MoReBench-Theory | 150 examples across five ethical theories | Data file exists; no evaluator or saved result | Unavailable | No local theory-specific finding. |
| MoralLens dataset | 640 English trolley vignettes; 85 models; five samples; 425,600 responses | 672 rows including 32 Species extensions; one sample; temperature 0; different prompts | Approximate | Dataset overlap exists; administration differs materially. |
| MoralLens performance | Gemini assigns 16 rationales; CDGAP and Utility; invalid-output retries | Keyword counts and a binary expected-direction pattern; think blocks removed | Proxy-only | Local values cannot establish consequentialist or deontological reasoning or reproduce the paper's order effect. |

## Authors' interpretation and our safe wording

| Benchmark | Authors' interpretation | Research-lead-safe wording |
|---|---|---|
| MoralBench | Reports different model leaders across MFQ/vignette agreement and comparison, framed as moral identity and alignment. | Small forced-choice sets measure agreement with human-derived labels. The paper reports no intervals and does not establish moral identity or deep understanding. |
| UniMoral | Contextual cues improve performance; some languages perform better; psychological scenarios outperform Reddit; MTC/FAA remain difficult. | These are protocol-specific descriptive patterns. The paper lacks a no-context counterfactual and does not document tests behind several “significant” statements. |
| MoReBench | General capability benchmarks and scale do not predict procedural moral reasoning; models are weak on logical process and favor some theories. | Correlations are small within the tested sample and judge. The thinking-versus-final Hard correlation is `r=.472, p=.08`; more evidence is needed. |
| MoralLens | Pre-decision reasoning is more deontological and has higher Utility than post-decision explanation. | The paper finds an order effect under its 85-model, five-sample protocol. It also warns that chain-of-thought may be unfaithful and that the taxonomy, forced choice, judge, and Western two-framework split are limited. |

## Paper-quality flags

- MoralBench repeats runs but reports no confidence intervals or significance tests.
- UniMoral reports 8,784 total rows in Table 1 and Appendix A.5 but 5,256 in section 3.2.
- MoReBench main-text average percentages differ from its displayed table averages.
- MoralLens human judge validation is useful but small: one evaluator labeled 64 responses, the second eight, with eight overlapping cases.

## What this changes in Poster 1

The four papers are separate measurement coordinates, not one interchangeable “competence” family:

- MoralBench: preference agreement and forced comparison;
- UniMoral: annotator-label prediction and consequence similarity;
- MoReBench: expert-rubric procedural reasoning;
- MoralLens: rationale classification and order effects.

The page must not relabel these as one common accuracy or one common rubric score. The machine-readable comparison is in [`../data/paper_protocol_map.csv`](../data/paper_protocol_map.csv).
