# CEI moral psychology results brief

This private repository turns the benchmark outputs into a results-first readout for a research lead. It answers four practical questions with charts, keeps unlike metrics separate, and states what each result can and cannot support.

![UniMoral size-path overview and concrete Gemma counterexample](assets/results/03_size_paths.png)

## Start here

1. Read [`docs/ONE_MINUTE_READOUT.md`](docs/ONE_MINUTE_READOUT.md) for the decision and the four main results.
2. Open [`slides/cei-moral-psychology-results-deck.pptx`](slides/cei-moral-psychology-results-deck.pptx) for the 8-slide research-lead story.
3. Open [`index.html`](index.html) for the full visual readout.
4. Read [`docs/RESULTS_READOUT.md`](docs/RESULTS_READOUT.md) for the evidence and limits behind every chart.
5. Use [`data/results/`](data/results/) for the plotted rows and derived tables.
6. Use the poster, paper, and onboarding audits only when those evidence layers are relevant.

## What the results say

| Research question | Result | Implication | Evidence level |
|---|---|---|---|
| Do the consistently covered models form one stable order? | No. Across five models and eight text tasks, no model is the point-estimate leader on every task. | Report task results separately. Do not publish one moral leaderboard. | Current primary aggregate; tracked-artifact audit |
| Where does sampling uncertainty block a model order? | Every interval wider than `.30` belongs to the two MoralBench comparison tasks. Their median widths are `.395` and `.370`. | Recover paired outcomes first; expand the item banks if the order remains unresolved. | Current primary aggregate; tracked-artifact audit |
| Across complete selected UniMoral paths, do scores rise at both size steps? | Only 4 of 12 rise twice; 7 change direction and 1 falls twice. The full six-task extension, including ValuePrism, is 5 / 9 / 1 across 15 paths. | Treat size as a task-specific hypothesis, not a general result. | Exploratory selected grid |
| Do later named-model endpoints move every UniMoral task higher? | No. Qwen has 3 higher and 1 lower endpoint; DeepSeek has 2 higher and 2 lower. The six-task extension is 5 / 1 and 3 / 3. All were evaluated May 28–29, 2026. | Treat release quarter as model metadata, not a progress timeline. | Exploratory selected grid |

The first two answers come from the current 78-cell primary text partition. The size and release-period views come from a separate selected-grid snapshot with no saved uncertainty and no referenced raw `.eval` logs in the fresh clone.

## Evidence boundaries

| Layer | What exists | Safe use |
|---|---|---|
| Canonical benchmark audit | 78 primary text, 26 sensitivity text, 9 multimodal extension, and 30 excluded cells | Current task results, nominal uncertainty, status, and claim boundaries |
| Selected-grid snapshot | 102 scored aggregate rows plus 17-model metadata | Exploratory family, size, and release-period patterns only |
| Four MP-v2 posters | Four static PDFs | Design history and poster-reported observations; the replay packets are absent |
| Four external papers | Primary papers reviewed; 0 exact local replications | Method and interpretation context, not direct score baselines |

The repository contains substantial benchmark result data. What is missing is different: canonical raw archives, the separate poster replay packets, clustered uncertainty, and representative human validation. Agreement among automated judges is not proof of moral correctness.

## Repository map

| Location | Purpose |
|---|---|
| `index.html` | Responsive visual result brief |
| `slides/` | Editable 8-slide research-lead deck |
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
