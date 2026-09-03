# CEI moral psychology results brief

This repository turns the Jenny onboarding page, four MP-v2 posters, two internal reports, and four benchmark papers into one evidence-aware readout for a research lead.

## Start here

1. Open [`index.html`](index.html) for the visual readout.
2. Read [`docs/RESEARCH_LEAD_BRIEF.md`](docs/RESEARCH_LEAD_BRIEF.md) for the decision summary.
3. Use [`docs/POSTER_AUDIT.md`](docs/POSTER_AUDIT.md) for the poster-by-poster claim review.
4. Use [`docs/PAPER_REVIEW.md`](docs/PAPER_REVIEW.md) for the benchmark paper and implementation comparison.
5. Use [`docs/ONBOARDING_AUDIT.md`](docs/ONBOARDING_AUDIT.md) for the original page completion check.
6. Use [`docs/VERIFICATION.md`](docs/VERIFICATION.md) for the pre-push check record.

## Bottom line

| Question | Answer |
|---|---|
| Is the original onboarding page current? | No. It is an August 27 snapshot and predates the September 1 canonical audit. |
| Are the four poster PDFs present? | Yes. |
| Can their numerical results be independently reproduced from the pinned source checkout? | No. All four supporting source packages are missing. |
| Were the four relevant benchmark papers obtained and read? | Yes. The full papers, methods, results, and relevant limitations were reviewed. |
| Did this repository reproduce any paper exactly? | No. MoralBench and UniMoral are approximate matches; MoReBench and MoralLens are proxy-only for performance claims. |
| What is safe to communicate now? | The canonical audit counts, the measurement design, the evidence gaps, and the next decisions. |

The banked experiment phase is closed. Evidence validation is not. This repository does not rank moral profiles, combine incompatible metrics, or treat agreement between automated judges as human validity.

## Evidence layers

| Layer | Status | Use |
|---|---|---|
| Canonical benchmark audit | Manifested and independently validated within its tracked-artifact scope | Current counts, task-level metrics, uncertainty, and claim boundaries |
| Four MP-v2 posters | Static legacy artifacts; supporting records and generators are absent | Design history and poster-reported observations only |
| Two internal reports | Provisional internal interpretation; not independently replayed here | Context, limitations, and hypotheses |
| Four external papers | Primary papers read in full or in full relevant scope | Method comparison and authors' interpretations |

## Repository map

| Location | Purpose |
|---|---|
| `index.html` | Responsive visual readout |
| `data/` | Machine-readable status, paper, and poster tables |
| `docs/` | Human-readable audits and handoff notes |
| `evidence/canonical-audit/` | Unmodified copy of the validated audit bundle |
| `evidence/posters/` | Unmodified poster PDFs |
| `evidence/internal-reports/` | The two user-provided internal reports |
| `assets/posters/` | Web previews generated from the poster PDFs |

## Source pins

- Pinned source repository: `main` at `b3a348684692f615d789392692ce34a1359192d3`
- Canonical evidence snapshot: `276acecd603761e6ff61bd6e2685fbb87f0eaa47d`
- Canonical partition: `78 primary text + 26 sensitivity text + 9 multimodal extension + 30 excluded = 143`
- Paper crosswalk in the canonical audit: `0 exact + 17 approximate + 4 proxy-only + 16 unavailable = 37`

## External activity

No model or judge evaluation was run for this brief. No paid provider call, Slack post, Notion update, or CEI organization repository write was made. The GitHub repository is private by default.
