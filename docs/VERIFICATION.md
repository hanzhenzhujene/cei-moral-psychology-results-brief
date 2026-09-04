# Verification record

Verified on 3 September 2026 for the results-first release.

The research-lead slide deck was added and verified on 4 September 2026.

## Result lineage

| Check | Outcome |
|---|---|
| Canonical manifested bundle | 31 of 31 artifact hashes and byte counts pass |
| Canonical partition | `78 primary / 26 sensitivity / 9 extension / 30 excluded = 143` |
| Canonical intervals | 78 unique cells; 18 intervals wider than `.30`, all on the two comparison tasks |
| Compare-task overlap | `28/28` MFQ pairs and `45/45` vignette pairs overlap marginally |
| Common roster | 40 unique cells = 5 models × 8 tasks; values match the canonical table |
| Selected-grid snapshot | Both CSVs match the pinned source byte for byte; statuses are `102 success / 13 error / 4 cancelled`; no raw evaluation archives are present |
| Size answer | The UniMoral-only headline counts 12 complete family × task paths: `4 rise twice / 7 change direction / 1 falls twice`. Its concrete Gemma example binds six plotted labels to factor `.578 → .601 → .613` and typology `.597 → .579 → .570` for the named 4B, 12B, and 27B variants |
| Size audit detail | The collapsed six-task table retains 18 cells and 15 complete paths: `5 rising / 9 mixed / 1 falling`. Two full-resolution path figures retain 45 scored points split `27 / 18`; all `45/45` carry a named-model + published-B label |
| Release answer | The UniMoral-only headline keeps accuracy and METEOR separate. Qwen has `3 higher / 1 lower` endpoints; DeepSeek has `2 higher / 2 lower`. All eight plotted endpoint deltas are bound to their source rows |
| Release audit detail | The collapsed six-task table retains 12 cells: Qwen `5 higher / 1 lower` and DeepSeek `3 higher / 3 lower`. Two full-resolution path figures retain 35 scored points split `18 / 17`; all `35/35` carry a named-model + published-B label |
| Evaluation date | Every selected-grid score plotted in the size and release views was evaluated on 28–29 May 2026. Release quarter describes the model, not the evaluation date |
| Parameter labels | 15 unique named models match revision-pinned official model cards; MoE labels preserve the published basis and active B; DeepSeek uses main-model counts excluding auxiliary/MTP weights; served provider, quantization, and checkpoint revision remain unknown |
| Missingness | No error, cancelled, or missing row is plotted as zero |
| Protocol-budget drift | Qwen3-32B total `107,375` reasoning tokens; DeepSeek V4 total `1,171,189` confirmed from source metadata |

Ten PNG/SVG figure pairs and seven result tables were generated twice consecutively. All 27 generated files were byte-identical across the two builds.

## Independent validators

The personal-repo validator passed with the pinned source checkout supplied:

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_site.py \
  --source-repo /path/to/moral-psychology-benchmark
```

It checks the canonical and selected-source manifests, all 80 derived point rows, all size and release summaries, and the 15-model parameter ledger. It also verifies:

- the 8-slide PPTX package, 16:9 canvas, 3 native tables, 4 native charts, 4 linked workbooks, and 8 sourced notes;
- the slide 2 leader table and slide 3–6 chart caches against the repo CSVs, plus each chart cache against its embedded workbook;
- `18/12` values in the collapsed semantic audit tables;
- the six Gemma answer labels in both desktop and mobile size figures;
- the eight endpoint-delta labels in both desktop and mobile release figures;
- all `45/35` named-model + B labels in the split path figures;
- image dimensions, portrait and landscape contracts, SVG safety, axis bounds, local links, PDF hashes, claim language, credentials, and private paths.

The outer canonical validator also passed:

```sh
PYTHONDONTWRITEBYTECODE=1 python work/validate_audit.py
```

Its report confirmed 31 manifested artifacts, 42 links, the `78/26/9/30` partition, 18 wide intervals, the `17 approximate / 4 proxy-only / 16 unavailable / 0 exact` UniMoral and ValuePrism crosswalk, and a clean pinned analysis checkout.

## Site and visual QA

| Surface | Outcome |
|---|---|
| Local references | 57 HTML and 52 Markdown references resolve |
| Images | 8 of 8 `<img>` elements have alt text and correct intrinsic dimensions. The two headline charts also have dedicated, dimensioned mobile `<source>` images |
| Desktop | Chrome/Playwright passed at `1440 × 1000`: the size and release charts select their desktop sources and render at `1084 px` wide; the page has no horizontal overflow; both audit tables start closed; all 30 cells fit when opened; the console is clean |
| Mobile | Chrome/Playwright passed at `390 × 844`: the charts select dedicated portrait sources and render at `316 × 570` and `316 × 728`; the page has no horizontal overflow; all 30 audit cells fit when opened; the console is clean |
| Mobile readability | The former `720 px` horizontal chart scrollers were removed. Mobile receives stacked portrait figures with full model names, published B values, direct point labels, and no swipe requirement. The sticky navigation is disabled at this width so it cannot cover a chart |
| Audit access | The six-task tables remain collapsed by default, and four full-resolution path-figure links retain every named model, published B value, task, and score |
| Visual inspection | All ten PNGs were inspected at full resolution. The two headline figures and their mobile counterparts show no observed title, label, or edge clipping; the four audit-detail figures retain `45/45` and `35/35` direct labels |
| Accessibility | Model and family series use marker shapes and line styles in addition to color. Headline figures have descriptive alt text, and the underlying audit views remain semantic HTML |

The README preview points directly to the size-answer chart. The main site embeds the size and release answer charts; full-resolution PNG and SVG links sit immediately below each figure.

## Slide deck QA

| Check | Outcome |
|---|---|
| Story | 8 slides; one claim per slide; task results, precision, size, release, paper fit, and action remain separate |
| Native objects | 4 editable charts and 3 editable tables |
| Evidence labels | Main results, exploratory, paper-review, and decision claims are visibly separated |
| Metrics | Accuracy, normalized preference, and METEOR are not combined into one score or axis |
| Model labels | Size and release examples show the named model and published parameter basis, including active parameters for MoE models |
| Package validation | Slide count, native-object ownership, relationship targets, nested workbook links, chart formulas, font policy, layout geometry, and first-party import checks pass |
| Source-to-slide validation | The public repo validator independently opens the PPTX and recomputes the slide 2–6 table and chart values from CSV evidence |
| Repeat build | The semantic validator runs before an atomic rename replaces the stable deck. The PPTX container SHA can change with generated package metadata, so the content contract is rechecked after every build |
| Visual inspection | All 8 slides were rendered at 1280 × 720 and inspected at full resolution; no observed overlap, clipping, or compressed screenshots |
| Share copies | The repo includes an 8-page view-only PDF and eight 2560 × 1440 PNGs. Every page was rendered again and inspected at full resolution |
| Portability | The PDF and PNGs use the verified slide render, so layout does not depend on the viewer's fonts or PowerPoint renderer |

The editable deck is `slides/cei-moral-psychology-results-deck.pptx`. The share copies are `slides/cei-moral-psychology-results-deck.pdf` and `slides/rendered/`. The source is `scripts/build_slides.mjs`; technical caveats and citations are retained in speaker notes.

## Repository and hygiene

- Pinned source clone: clean `main` at `b3a348684692f615d789392692ce34a1359192d3`.
- Canonical evidence commit: resolvable 40-character SHA `276acecd603761e6ff61bd6e2685fbb87f0eaa47`.
- The malformed upstream 41-character token is retained only as an explicit provenance record.
- Six poster and internal-report PDFs match their retained SHA-256 values.
- No local absolute user paths, common credential patterns, or private keys were found in release text.
- No model, judge, or paid provider evaluation was run. No Slack, Notion, or CEI organization write occurred.

## Limits that verification does not remove

The analysis checkout is clean now, but original run provenance is not: 63 of 78 primary cells record a dirty run state and 15 are blank. The checks do not restore canonical raw `.eval` archives or poster replay packets, establish served model or dataset identity beyond saved metadata, provide cluster-aware uncertainty, rule out contamination, or establish representative human validity. The canonical bundle records hashes for its outer generator and validator, but those two source files are not copied into this personal repository.
