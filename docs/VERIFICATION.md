# Verification record

Verified on 3 September 2026 before the first GitHub push.

## Content and evidence

- Canonical audit validator passed.
- Canonical partition confirmed: `78 / 26 / 9 / 30 = 143`.
- Canonical paper crosswalk confirmed: `0 exact / 17 approximate / 4 proxy-only / 16 unavailable`.
- Four poster PDFs were rendered and inspected at full poster aspect.
- Both user-provided internal reports were read in full relevant scope; all pages were rendered for visual inspection.
- MoralBench, UniMoral, MoReBench, and MoralLens primary papers were obtained and reviewed.
- Evidence PDF copies match their source SHA-256 values.

## Site and data

- 29 local `href` and `src` references checked; none missing.
- Markdown relative links checked; none missing.
- CSV parse checks passed:
  - `canonical_status.csv`: 8 rows, 4 columns
  - `cogalign_legacy_scores.csv`: 21 rows, 13 columns
  - `paper_protocol_map.csv`: 10 rows, 6 columns
  - `poster_claims.csv`: 21 rows, 7 columns
- All eight primary paper and code links returned HTTP 200.

## Visual QA

- Desktop view checked at 1280 × 720.
- Mobile views checked at 390 × 844 and 320 × 700.
- No horizontal page overflow at any checked width.
- All four poster previews loaded.
- No browser console errors remained.
- Research readout, evidence comparison, poster briefs, paper comparison, and decision surface were visually inspected.

## Hygiene

- No local absolute user paths found in committed text.
- No common GitHub, OpenAI, AWS, private-key, or API-key credential pattern found.
- Source clone remained clean on `main` at `b3a348684692f615d789392692ce34a1359192d3`.
- No model, judge, or paid provider evaluation was run.
- No Slack or Notion write occurred.

These checks validate the assembled brief and its tracked inputs. They do not restore the missing poster source package, run Gate M, prove paper-protocol identity, or provide human validity.
