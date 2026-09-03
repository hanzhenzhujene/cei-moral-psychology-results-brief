# Agent handoff contract

## Objective

Maintain a readable research-lead results brief without overstating what the current evidence can prove.

## Read order

Before changing the site or any conclusion, read:

1. `README.md`
2. `docs/RESEARCH_LEAD_BRIEF.md`
3. `docs/POSTER_AUDIT.md`
4. `docs/PAPER_REVIEW.md`
5. `docs/ONBOARDING_AUDIT.md`
6. `evidence/canonical-audit/CLAIM_BOUNDARIES.md`
7. `evidence/canonical-audit/TECHNICAL_AUDIT.md`
8. `evidence/canonical-audit/SELF_CRITIQUE.md`

## Evidence rules

- Keep the canonical benchmark audit separate from the MP-v2 poster study. They use different tasks and evidence surfaces.
- Treat every number copied from a poster or internal report as `poster-reported` or `report-reported` unless a row-level source package is restored and verified.
- Do not call any of the four external paper comparisons an exact replication.
- Keep accuracy, normalized preference, METEOR, BERTScore, weighted F1, keyword checks, judge scores, and human judgments separate.
- Never create a cross-metric moral score or rank a moral profile.
- Agreement between two automated judges or coders is a reliability diagnostic, not human validity.
- Gate M remains pending.

## Source precedence

1. `evidence/canonical-audit/` for the September 1 canonical benchmark audit.
2. Original PDFs under `evidence/posters/` for what a poster itself claims.
3. Original PDFs under `evidence/internal-reports/` for internal interpretation and limitations.
4. Primary paper links in `docs/PAPER_REVIEW.md` for external-paper methods and findings.
5. The original Claude onboarding artifact only as a stale task snapshot, never as current evidence.

## Editing boundaries

- Do not modify files under `evidence/`; replace them only with a new, checksummed source version.
- Update `data/` first when a factual claim changes, then update the matching prose and visual.
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
