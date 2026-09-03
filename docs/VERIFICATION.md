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
| Size view | 45 scored points; 15 complete paths = `5 rising / 9 mixed / 1 falling` |
| Release-period view | 35 scored points across 12 Qwen or DeepSeek family-task paths |
| Missingness | No error, cancelled, or missing row is plotted as zero |
| Protocol-budget drift | Qwen3-32B total `107,375` reasoning tokens; DeepSeek V4 total `1,171,189` confirmed from source metadata |

The four charts and six result tables were generated twice consecutively. All 14 generated files were byte-identical across the two builds.

## Independent validators

The personal-repo validator passed with the pinned source checkout supplied:

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_site.py \
  --source-repo /path/to/moral-psychology-benchmark
```

It checked the canonical and selected-source manifests, derived result lineage, legacy firewalls, local links, image dimensions, SVG safety and semantics, chart axis bounds, PDF hashes, claim language, credentials, and private paths.

The outer canonical validator also passed:

```sh
PYTHONDONTWRITEBYTECODE=1 python work/validate_audit.py
```

Its report confirmed 31 manifested artifacts, 42 links, the `78/26/9/30` partition, 18 wide intervals, the `17 approximate / 4 proxy-only / 16 unavailable / 0 exact` UniMoral and ValuePrism crosswalk, and a clean pinned analysis checkout.

## Site and visual QA

| Surface | Outcome |
|---|---|
| Local references | 45 HTML and 44 Markdown references resolve |
| Images | 8 of 8 have alt text and correct intrinsic dimensions; all load after scrolling |
| Desktop | Checked at `1440 × 1000` and `1440 × 900`; no page-level horizontal overflow |
| Mobile | Checked at `390 × 844` and `320 × 700`; no page-level horizontal overflow |
| Mobile chart detail | Each chart scrolls inside its own `270–340 px` container with an `820 px` readable canvas; a swipe cue is visible |
| Navigation | Decision anchor resolves, and the decision surface appears before the evidence appendices |
| Console | No warnings or errors at the checked widths |
| Original figures | All four PNGs inspected at full resolution; no clipping or illegible labels found |
| Accessibility | Model/family series use marker shapes and line styles in addition to color |

The README preview was regenerated from the final results-first hero.

## Repository and hygiene

- Pinned source clone: clean `main` at `b3a348684692f615d789392692ce34a1359192d3`.
- Canonical evidence commit: resolvable 40-character SHA `276acecd603761e6ff61bd6e2685fbb87f0eaa47`.
- The malformed upstream 41-character token is retained only as an explicit provenance record.
- Six poster and internal-report PDFs match their retained SHA-256 values.
- No local absolute user paths, common credential patterns, or private keys were found in release text.
- No model, judge, or paid provider evaluation was run. No Slack, Notion, or CEI organization write occurred.

## Limits that verification does not remove

The analysis checkout is clean now, but original run provenance is not: 63 of 78 primary cells record a dirty run state and 15 are blank. The checks do not restore canonical raw `.eval` archives or poster replay packets, establish model or dataset identity beyond saved metadata, provide cluster-aware uncertainty, rule out contamination, or establish representative human validity. The canonical bundle records hashes for its outer generator and validator, but those two source files are not copied into this personal repository.
