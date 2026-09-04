# CEI moral psychology results brief

This private repository turns the benchmark outputs into a visual readout for a research lead.

**Decision: publish each task result with its limits. Do not rank the models overall.**

## Start here

1. Read the [`one-minute result`](docs/ONE_MINUTE_READOUT.md).
2. Open the [`slide gallery`](slides/README.md) or [`view-only PDF`](slides/cei-moral-psychology-results-deck.pdf).
3. Use the [`editable PowerPoint`](slides/cei-moral-psychology-results-deck.pptx) only when the deck needs to change.

![Task-by-task leaders across five models with main audited results on all eight tasks](slides/rendered/slide-02.png)

## What the results say

| Research question | Result | Implication | Evidence level |
|---|---|---|---|
| Among the five models with main audited results on all eight tasks, is there one stable order? | No. The highest saved score belongs to different models on different tasks. | Report task results separately. Do not publish one moral leaderboard. | Main audited results |
| Can the two comparison tests tell us which model leads? | No. Marginal score ranges overlap for all 28 MFQ and all 45 vignette model pairs. These are one-model-at-a-time ranges, not paired comparisons. | Restore every model's answer and score for each question. Check scoring and labels, then compare models directly. | Main audited results |
| Do scores keep rising as selected model variants get bigger? | Only 4 of 12 UniMoral score paths rise after both size steps; 7 switch direction and 1 falls twice. | Bigger is not always better. Treat size as an exploratory clue. | Exploratory dataset; no saved uncertainty |
| Do later Qwen and DeepSeek versions score higher on every UniMoral task? | No. Qwen has 3 higher and 1 lower endpoint; DeepSeek has 2 higher and 2 lower. All were evaluated May 28–29, 2026. | Newer is not always better. Release period is model metadata, not a progress trend. | Exploratory dataset; no saved uncertainty |

The first two findings use the main audited results. The size and version findings use a separate dataset that has no saved uncertainty estimates or original run files in the fresh clone.

## Evidence boundaries

| Layer | What exists | Safe use |
|---|---|---|
| Main audited benchmark set | 78 primary text, 26 sensitivity text, 9 multimodal extension, and 30 excluded cells | Current task results, saved uncertainty, status, and claim boundaries |
| Exploratory model snapshot | 102 scored aggregate rows plus 17-model metadata | Exploratory family, size, and release-period patterns only |
| Four MP-v2 posters | Four static PDFs | Design history and poster-reported observations; the original run files are absent |
| Four external papers | Primary papers reviewed; 0 exact local replications | Method and interpretation context, not direct score baselines |

The repository has aggregate benchmark results, but it lacks original raw run archives, the old poster run files, clustered uncertainty estimates, and representative human review. Agreement among automated judges is not proof of moral correctness.

## Repository map

| Location | Purpose |
|---|---|
| `index.html` | Detailed visual evidence and audit appendices |
| `slides/` | Editable PowerPoint, view-only PDF, and eight 2560 × 1440 slide images |
| `assets/results/` | Four headline charts plus four landscape audit-detail charts in PNG and SVG |
| `data/results/` | Exact plotted rows, direction summaries, and research-question tables |
| `docs/RESULTS_READOUT.md` | Chart-by-chart interpretation for a research lead |
| `docs/POSTER_AUDIT.md` | Poster claim audit and corrections |
| `docs/PAPER_REVIEW.md` | Paper methods and protocol comparison |
| `docs/ONBOARDING_AUDIT.md` | Original page completion check |
| `evidence/canonical-audit/` | Manifested copy of the validated audit bundle |
| `evidence/source-results/` | Checksummed selected-grid source snapshot |
| `scripts/` | Deterministic figure and slide builders plus the independent site validator |

## Rebuild and verify

```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/build_result_visuals.py
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_site.py
```

The repo validator also opens the PPTX. It checks the native tables, charts, embedded workbooks, notes, and the slide 2–6 values against the CSV evidence.

The slide builder uses the bundled Codex presentation runtime. In Codex, load the workspace dependencies to find the Node.js, Python, and package paths, then run:

```sh
PRESENTATIONS_SKILL_DIR=/absolute/path/to/presentations-skill \
WORKSPACE_PYTHON=/absolute/path/to/bundled-python \
VALIDATION_PYTHON=/absolute/path/to/python-with-repo-dependencies \
ARTIFACT_TOOL_DIR=/absolute/path/to/@oai/artifact-tool \
RUNTIME_NODE_MODULES=/absolute/path/to/bundled-node_modules \
/absolute/path/to/bundled-node scripts/build_slides.mjs
```

`WORKSPACE_PYTHON` is the bundled presentation runtime. `VALIDATION_PYTHON` must provide the repo validator dependencies (`beautifulsoup4`, `numpy`, `pandas`, and `Pillow`). The builder checks a private staging copy, recomputes its slide evidence, and then atomically replaces only the generated PPTX. It does not rewrite the reports.

When the outer audit workspace is available, run its additional source-level gate from that workspace:

```sh
PYTHONDONTWRITEBYTECODE=1 python work/validate_audit.py
```

That outer validator is not bundled in this personal results repo.

## Source pins

- Pinned source repository: `main` at `b3a348684692f615d789392692ce34a1359192d3`
- Canonical evidence snapshot: `276acecd603761e6ff61bd6e2685fbb87f0eaa47`
- Upstream artifacts recorded a malformed 41-character version of that SHA ending in `...aa47d`; this brief preserves the upstream record in provenance while using the resolvable 40-character commit.
- Canonical partition: `78 + 26 + 9 + 30 = 143`
- Canonical UniMoral and ValuePrism crosswalk: `0 exact + 17 approximate + 4 proxy-only + 16 unavailable = 37`

## External activity

No model or judge evaluation was run for this brief. No paid provider call, Slack post, Notion update, or CEI organization repository write was made. The only intended external write is this private personal GitHub repository.
