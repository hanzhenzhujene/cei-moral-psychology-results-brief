# Relevant benchmark paper review

## Replication verdict

| Exact | Approximate | Proxy-only | Unavailable |
|---:|---|---|---|
| **0** | MoralBench task families; UniMoral task families; ValuePrism relevance and valence task families | MoReBench performance; MoralLens performance; broader ValuePrism interpretation | UniMoral cue claims; MoReBench-Theory; MoralLens paper metrics and order-effect replication; Value Kaleidoscope generation, explanation, and human tests |

Approximate means a similar question tested differently. Proxy-only means a rough substitute, not the paper's measure. Unavailable means not tested here.

Use these papers to explain what each benchmark tests. Do not compare their scores with ours or describe the local runs as replications.

## Read status

The five primary papers were downloaded and reviewed for methods, results, authors' interpretation, limitations, and fit to the local evaluator. External PDFs used for review are not redistributed in this repository.

| Benchmark | Primary paper | Code and data | Review status |
|---|---|---|---|
| MoralBench | Ji et al., “MoralBench: Moral Evaluation of LLMs,” ACM SIGKDD Explorations 27(1), 2025. [PDF](https://arxiv.org/pdf/2406.04428v2) | [Repository](https://github.com/agiresearch/MoralBench) | Full 10-page paper read. |
| UniMoral | Kumar & Jurgens, ACL 2025 Long Papers, Best Resource Paper. [PDF](https://aclanthology.org/2025.acl-long.294.pdf) | [Repository](https://github.com/shivanik96/UniMoral) · [Dataset](https://huggingface.co/datasets/shivaniku/UniMoral) | Full paper, appendices, and limitations reviewed. |
| MoReBench | Chiu et al., ICLR 2026. [PDF](https://arxiv.org/pdf/2510.16380v2) | [Repository](https://github.com/morebench/morebench) · [Dataset](https://huggingface.co/datasets/morebench/morebench) | Main paper and all relevant methods, scoring, validation, results, and caveat appendices reviewed. |
| MoralLens | Samway et al., EMNLP 2025 Main. [PDF](https://aclanthology.org/2025.emnlp-main.1563.pdf) | [Repository](https://github.com/keenansamway/moral-lens) | Full main paper, experiment details, validation, robustness, and limitations reviewed. |
| Value Kaleidoscope paper | “Value Kaleidoscope,” AAAI 2024. [PDF](https://arxiv.org/pdf/2309.00779v2) | CEI benchmark: ValuePrism uses different models and prompts. | Main paper, Table 13, human-evaluation results, dataset checks, and limitations reviewed. |

## The five paper questions in plain language

| Paper | What the paper is trying to answer | What the current local evidence can answer | Match |
|---|---|---|---|
| MoralBench | Do model choices track human ratings on moral-foundation statements and vignettes? Can a model choose the statement people rated higher? | Fresh agreement and forced-choice results with saved intervals, under a different model roster and administration. | Approximate |
| UniMoral | Can a model predict an annotator's action, moral framework, and influencing factors, and generate plausible consequences? How do cues, language, and scenario source affect those results? | No-cue label accuracy for action, typology, and factor tasks, plus consequence METEOR. It cannot test the paper's cue, language, or source claims. | Approximate for task families; unavailable for cue claims |
| MoReBench | Does the reasoning process cover expert-defined considerations, trade-offs, logical steps, and outcomes? Do scale and general capability predict this? | The local evaluator only checks whether four generic reasoning-word groups appear. That is not the paper's expert-weighted score. | Proxy only for performance |
| MoralLens | Which consequentialist or deontological rationales appear? Do they change when reasoning comes before versus after the decision? | The local adapter checks keyword detectability and one binary expected-direction pattern. It cannot reproduce the paper's rationale judge or order effect. | Proxy only for performance |
| Value Kaleidoscope paper | Can small Kaleido models predict value relevance and valence, generate value lists, and explain them? How do these results change with model size? | The CEI ValuePrism benchmark tests related relevance and valence tasks with different models, prompts, and scoring. It has no matching generation, explanation, or human test. | Approximate for two task families; unavailable for the other paper tests |

The size and release-period charts in the results brief are local follow-up questions. They are not claims that the five papers asked or answered those questions. The eight-slide core view uses MoralBench and UniMoral; the full deck adds ValuePrism and keeps its scores separate.

## Protocol comparison

| Claim unit | Paper protocol | Local protocol | Match | Safe interpretation |
|---|---|---|---|---|
| MoralBench agreement | The paper sums the selected human score, uses temperature 0.7, and repeats each test five times; it does not state the item count | The retained task files contain 20 MFQ and 24 vignette items; score normalized to 0–1; temperature 0; different routes and models | Approximate | Same task family, different scale and administration. Do not compare paper totals with local values. |
| MoralBench comparison | The paper gives one point for choosing the higher human-rated statement and repeats the test five times; it does not state the pair count | The retained task files contain 20 MFQ and 24 vignette pairs; one deterministic run; no demonstrated dataset fingerprint identity | Approximate | A fresh evaluation, not a reproduction of the paper's model ordering. |
| UniMoral AP/MTC/FAA | Six languages; cue conditions; weighted F1; 8,784 AP rows and 3,492 extensive rows | Default no-cue mode; accuracy; hosted 2026 route; different generation limits | Approximate | Agreement with UniMoral labels under a no-cue protocol, not personalized moral prediction. |
| UniMoral consequence generation | BLEU, METEOR, and multilingual BERTScore against human references | Live best-reference METEOR; separate offline BERTScore bridge for 1,782 rows | Approximate | Same metric families, but scorer, route, and aggregation are not identical. |
| UniMoral cue, language, and source findings | Cue effects, language patterns, psychological versus Reddit comparison | No matched cue counterfactual; stale stratification; missing raw calibration archives | Unavailable | The current run cannot confirm these paper findings. |
| MoReBench scenario ingestion | 500 public scenarios: 293 advisor and 207 agent; expert criteria with weights −3 to +3 | Loads 500 public rows with the same role counts; release fingerprint not pinned | Approximate | Scenario alignment is plausible, not revision-exact. |
| MoReBench performance | Expert-criterion Regular and length-corrected Hard scores; long outputs and thinking traces | Four generic keyword checks; think blocks removed; maximum 1,024 tokens | Proxy-only | Local values measure generic reasoning-word coverage, not MoReBench performance. |
| MoReBench-Theory | 150 examples across five ethical theories | Data file exists; no evaluator or saved result | Unavailable | No local theory-specific finding. |
| MoralLens dataset | 640 English trolley vignettes; 85 models; five samples; 425,600 responses | 672 rows including 32 Species extensions; one sample; temperature 0; different prompts | Approximate | Dataset overlap exists; administration differs materially. |
| MoralLens performance | Gemini assigns 16 rationales; CDGAP and Utility; invalid-output retries | Keyword counts and a binary expected-direction pattern; think blocks removed | Proxy-only | Local values cannot establish consequentialist or deontological reasoning or reproduce the paper's order effect. |
| ValuePrism relevance and valence | Kaleido 60M–11B accuracy against GPT-4-derived synthetic targets | Prompted LLM accuracy under a different route, model roster, and parser | Approximate | Related task families only. The paper and local scores are not direct baselines for each other. |
| Value Kaleidoscope generation, explanation, and human tests | Perplexity plus human preference, correctness, and relevance checks | No matching local test | Unavailable | Local classification accuracy cannot replace the paper's generation or human evaluation. |

## What the papers say—and what we can safely say

| Benchmark | Authors' interpretation | What we can safely say |
|---|---|---|
| MoralBench | Reports different model leaders across MFQ/vignette agreement and comparison, framed as moral identity and alignment. | Small forced-choice sets measure agreement with human-derived labels. The paper reports no intervals and does not establish moral identity or deep understanding. |
| UniMoral | Contextual cues improve performance; some languages perform better; psychological scenarios outperform Reddit; MTC/FAA remain difficult. | These are protocol-specific descriptive patterns. The paper lacks a no-context counterfactual and does not document tests behind several “significant” statements. |
| MoReBench | General capability benchmarks and scale do not predict procedural moral reasoning; models are weak on logical process and favor some theories. | Correlations are small within the tested sample and judge. The thinking-versus-final Hard correlation is `r=.472, p=.08`; more evidence is needed. |
| MoralLens | Pre-decision reasoning is more deontological and has higher Utility than post-decision explanation. | The paper finds an order effect under its 85-model, five-sample protocol. It also warns that chain-of-thought may be unfaithful and that the taxonomy, forced choice, judge, and Western two-framework split are limited. |
| Value Kaleidoscope paper | Larger Kaleido variants improve the four Table 13 measures, with much smaller displayed changes from 3B to 11B than at earlier size steps. | This is a descriptive paper result without confidence intervals or a pre-defined saturation test. Relevance and valence accuracy use GPT-4-derived targets, not human or normative correctness. |

## Paper-quality flags

- MoralBench repeats runs but reports no confidence intervals or significance tests.
- UniMoral reports 8,784 total rows in Table 1 and Appendix A.5 but 5,256 in section 3.2.
- MoReBench main-text average percentages differ from its displayed table averages.
- MoralLens human judge validation is useful but small: one evaluator labeled 64 responses, the second eight, with eight overlapping cases.
- Value Kaleidoscope Table 13 reports no confidence intervals. Its relevance and valence targets are GPT-4-derived, while separate human studies answer different questions.

## Implication for benchmark framing

The five papers test different things. They should not be treated as one “competence” benchmark:

- MoralBench: preference agreement and forced comparison;
- UniMoral: annotator-label prediction and consequence similarity;
- MoReBench: expert-rubric procedural reasoning;
- MoralLens: rationale classification and order effects.
- Value Kaleidoscope paper: value relevance, valence, generation, explanation, and human evaluation. The related CEI benchmark is ValuePrism.

The page must not relabel these as one common accuracy or one common rubric score. The machine-readable comparison is in [`../data/paper_protocol_map.csv`](../data/paper_protocol_map.csv).
