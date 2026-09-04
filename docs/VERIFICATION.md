# Verification record

Verified on 3 September 2026 for the results-first release.

## Result lineage

| Check | Outcome |
|---|---|
| Canonical manifested bundle | 31 of 31 artifact hashes and byte counts pass |
| Canonical partition | `78 primary / 26 sensitivity / 9 extension / 30 excluded = 143` |
| Canonical intervals | 78 unique cells; 18 intervals wider than `.30`, all on the two comparison tasks |
| Compare-task overlap | `28/28` MFQ pairs and `45/45` vignette pairs overlap marginally |
| Common roster | 40 unique cells = 5 models × 8 tasks; values match the canonical table |
| Selected-grid snapshot | Both CSVs match the pinned source byte for byte; statuses are `102 success / 13 error / 4 cancelled` |
| Size view | 18-cell headline matrix; 45 scored points split `27 / 18` across two landscape audit figures; all `45/45` have a direct model + B label; 15 complete paths = `5 rising / 9 mixed / 1 falling` |
| Release-period view | 12-cell headline matrix; 35 scored points split `18 / 17` across two landscape audit figures; all `35/35` have a direct model + B label; endpoint directions are Qwen `5 higher / 1 lower` and DeepSeek `3 higher / 3 lower`; all plotted evaluations ran on 28–29 May 2026 |
| Parameter labels | 15 unique named models match revision-pinned official model cards; MoE labels preserve the published basis and active B; DeepSeek uses main-model counts excluding auxiliary/MTP weights; served provider, quantization, and checkpoint revision remain unknown |
| Missingness | No error, cancelled, or missing row is plotted as zero |
| Protocol-budget drift | Qwen3-32B total `107,375` reasoning tokens; DeepSeek V4 total `1,171,189` confirmed from source metadata |

The eight PNG/SVG figure pairs and seven result tables were generated twice consecutively. All 23 generated files were byte-identical across the two builds.

## Independent validators

The personal-repo validator passed with the pinned source checkout supplied:

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_site.py \
  --source-repo /path/to/moral-psychology-benchmark
```

It checked the canonical and selected-source manifests, all 80 derived point rows, all 12 release endpoint summaries, the 15-model parameter ledger, exact evidence bindings for all `18/12` responsive HTML cells, exact `GID → value` bindings for the `18/12` static matrix cells, and exact `GID → label` bindings for all `45/35` size and release detail points. It also checked legacy firewalls, local links, image dimensions and landscape aspect ratios, SVG safety and semantics, chart axis bounds, PDF hashes, claim language, credentials, and private paths.

The outer canonical validator also passed:

```sh
PYTHONDONTWRITEBYTECODE=1 python work/validate_audit.py
```

Its report confirmed 31 manifested artifacts, 42 links, the `78/26/9/30` partition, 18 wide intervals, the `17 approximate / 4 proxy-only / 16 unavailable / 0 exact` UniMoral and ValuePrism crosswalk, and a clean pinned analysis checkout.

## Site and visual QA

| Surface | Outcome |
|---|---|
| Local references | 51 HTML and 52 Markdown references resolve |
| Images | 6 of 6 site images have alt text and correct intrinsic dimensions; the two headline matrices are semantic HTML and do not depend on image loading |
| Desktop | Chrome/Playwright passed at `1440 × 1000`: both matrices use family columns, all 30 evidence-bound cells fit the content width, the smallest visible matrix text is `12.8 px`, the page has no horizontal overflow, both audit sections start closed, their links become visible when opened, and the console is clean |
| Mobile | Chrome/Playwright passed at `390 × 844`: both matrices reflow task by task with model family and B context repeated in each cell; the smallest visible matrix text remains `12.8 px`, the page has no horizontal overflow, and the exact model + B audit figures remain available through four full-resolution links |
| Mobile chart detail | Only the two dense primary evidence charts retain contained `820 px` horizontal overflow; the size and release headline matrices no longer use a forced `1,180 px` width |
| Navigation | Decision anchor resolves, and the decision surface appears before the evidence appendices |
| Browser rerun | Automated Chrome/Playwright QA passed on desktop and mobile with zero console or page errors; it asserted 30 responsive cells, no clipped cell bounds, and a `12 px` minimum computed matrix font size |
| Original figures | All eight landscape PNGs were inspected at full resolution; the four audit-detail figures contain `45/45` and `35/35` direct labels with no detected label-box overlap or clipping |
| Accessibility | Model/family series use marker shapes and line styles in addition to color |

The README preview now points directly to the compact size-direction matrix.

## Repository and hygiene

- Pinned source clone: clean `main` at `b3a348684692f615d789392692ce34a1359192d3`.
- Canonical evidence commit: resolvable 40-character SHA `276acecd603761e6ff61bd6e2685fbb87f0eaa47`.
- The malformed upstream 41-character token is retained only as an explicit provenance record.
- Six poster and internal-report PDFs match their retained SHA-256 values.
- No local absolute user paths, common credential patterns, or private keys were found in release text.
- No model, judge, or paid provider evaluation was run. No Slack, Notion, or CEI organization write occurred.

## Limits that verification does not remove

The analysis checkout is clean now, but original run provenance is not: 63 of 78 primary cells record a dirty run state and 15 are blank. The checks do not restore canonical raw `.eval` archives or poster replay packets, establish model or dataset identity beyond saved metadata, provide cluster-aware uncertainty, rule out contamination, or establish representative human validity. The canonical bundle records hashes for its outer generator and validator, but those two source files are not copied into this personal repository.
