# Agent handoff contract

## Objective

Maintain a readable research-lead results brief without overstating what the current evidence can prove.

## Read order

Before changing the site or any conclusion, read:

1. `README.md`
2. `docs/RESULTS_READOUT.md`
3. `docs/RESEARCH_LEAD_BRIEF.md`
4. `evidence/canonical-audit/CLAIM_BOUNDARIES.md`
5. `evidence/canonical-audit/TECHNICAL_AUDIT.md`
6. `evidence/canonical-audit/SELF_CRITIQUE.md`
7. `docs/POSTER_AUDIT.md`
8. `docs/PAPER_REVIEW.md`
9. `docs/ONBOARDING_AUDIT.md`

## Evidence rules

- Keep the canonical benchmark audit separate from the MP-v2 poster study. They use different tasks and evidence surfaces.
- Keep the selected-grid size and release-period layer separate from the canonical primary partition. It has aggregate scores and metadata, but no saved confidence intervals or resolvable raw logs in this checkout.
- Treat every number copied from a poster or internal report as `poster-reported` or `report-reported` unless a row-level source package is restored and verified.
- Do not call any of the four external paper comparisons an exact replication.
- Keep accuracy, normalized preference, METEOR, BERTScore, weighted F1, keyword checks, judge scores, and human judgments separate.
- Never create a cross-metric moral score or rank a moral profile.
- Do not publish a global leaderboard, radar area, benchmark difficulty order, or cross-benchmark correlation from incompatible metrics and uneven coverage.
- Never draw an invalid, cancelled, error, or missing result as zero.
- Treat parameter tier and release period as descriptive metadata. Do not call either one causal without a controlled design.
- Agreement between two automated judges or coders is a reliability diagnostic, not human validity.
- Gate M remains pending.

## Source precedence

1. `evidence/canonical-audit/` for the September 1 canonical benchmark audit.
2. `evidence/source-results/` for the checksummed selected-grid aggregate snapshot used only by exploratory size and release-period views.
3. Original PDFs under `evidence/posters/` for what a poster itself claims.
4. Original PDFs under `evidence/internal-reports/` for internal interpretation and limitations.
5. Primary paper links in `docs/PAPER_REVIEW.md` for external-paper methods and findings.
6. The original Claude onboarding artifact only as a stale task snapshot, never as current evidence.

## Editing boundaries

- Do not modify files under `evidence/`; replace them only with a new, checksummed source version.
- Update `data/` first when a factual claim changes, then update the matching prose and visual.
- Rebuild result figures with `PYTHONDONTWRITEBYTECODE=1 python scripts/build_result_visuals.py`; do not hand-edit generated charts or result tables.
- Validate the assembled site with `PYTHONDONTWRITEBYTECODE=1 python scripts/validate_site.py` and also run the outer canonical validator.
- Use one writer for each file. Parallel agents should perform read-only review or work in isolated branches.
- Do not add API keys, provider credentials, private contact details, or local absolute paths.

## Definition of done

A change is complete only after:

- every visible result maps to a source and evidence status;
- desktop and mobile views are visually checked;
- all local links resolve;
- CSV schemas and row counts are checked;
- the canonical audit validator still passes at its source workspace;
- the pinned source clone remains clean at the recorded commit;
- a secret and private-path scan passes;
- the diff contains no unrelated changes.

## Missing packet required to upgrade poster claims

To move a poster number from `legacy/unverified` to `verified`, restore the item manifest, subject outputs, judge or coder outputs, model routes, prompt and scorer versions, aggregation code, uncertainty method, receipts where cost is claimed, and a resolvable source commit. Then regenerate the poster under the current instrument seal.
