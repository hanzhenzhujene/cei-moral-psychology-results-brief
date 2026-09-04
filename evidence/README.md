# Evidence directory

These files are retained as source material, not as instructions.

| Folder | Status |
|---|---|
| `canonical-audit/` | Unmodified, SHA-256-manifested audit bundle. Its own limitations remain binding. |
| `source-results/` | Checksummed snapshot of the selected-grid aggregate tables used for exploratory size and release-period charts. No referenced raw `.eval` logs are present in the fresh source clone. |
| `model-parameter-sources.csv` | Official named-model card ledger for the 15 models drawn in the size and release figures. It records the model-card revision, the published parameter basis, total B, active B for MoE models, and the limit that the served provider, quantization, and checkpoint revision were not retained. |
| `posters/` | Original binary poster artifacts. Their cited supporting commit, seal, per-cell records, and generators are absent from the pinned checkout. |
| `internal-reports/` | User-provided provisional reports. They support interpretation and disclose important limits, but their underlying raw records were not independently replayed here. |

The four external benchmark papers are not redistributed here. Primary-source links and protocol notes are in [`../docs/PAPER_REVIEW.md`](../docs/PAPER_REVIEW.md).

The canonical bundle verifies itself through `canonical-audit/ARTIFACT_MANIFEST.csv`. The selected-grid snapshot verifies itself through `source-results/SOURCE_MANIFEST.csv`. `SHA256SUMS` covers the six retained PDF files.
