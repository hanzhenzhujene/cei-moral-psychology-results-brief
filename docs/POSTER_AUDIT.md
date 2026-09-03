# Four-poster claim audit

## Release verdict

| Poster | Current status | Preserve | Hold as numerical result |
|---|---|---|---|
| Family Competence | Unsupported and stale | Competence/profile separation; pipeline integrity; Gate M boundary | Score panels, judge deltas, cost, repair counts, route conclusions |
| Family Profile | Unsupported and stale | Profiles are not rankings; coder agreement is not validity | MFT/Kohlberg profiles, agreement and kappa, Schwartz gate counts, coder-run records |
| Bidirectional Alignment | Stale | Validation architecture; judge agreement is not validity | All result counts, agreement, cost, coverage, seal, and judge numbers |
| Administration | Stale | Administration is part of the measurement; no profile ranking | 189 score cells, bundle-gate numbers, all experiment values |

Use this banner on every poster until the source packet is restored:

> Legacy design artifact. Numerical results are not reproducible from this repository checkout.

## Provenance audit

| Check | Result | Implication |
|---|---|---|
| Claimed evidence commit `3261ddd9` | Not present in the pinned repository or its Git history | The claimed evidence state cannot be checked out. |
| Seal digest `be0a11a3a4d7` | No matching manifest or content in the checkout | The seal cannot be verified. |
| Locators such as `FC-R`, `FP-R`, `COMP`, and `PM1-C…` | No tracked source files | Poster locators cannot be resolved. |
| Per-cell judge and coder records | Absent | Scores, agreement, kappa, resumption, null handling, and cost cannot be recalculated. |
| Poster generators | Absent | The PDFs are orphaned binary presentation artifacts. |
| Poster addition to Git | Added together on August 27 as untracked project assets | No source packet was added alongside them. |
| Current canonical audit | Different tasks and evidence surface | It cannot be used to validate MP-v2 S1/S2/S3 or Family C/P values. |

## Poster 1 — Family Competence

[Open the original PDF](../evidence/posters/FC_POSTER.pdf)

| Poster-reported claim | Internal check | Evidence status | Release correction |
|---|---|---|---|
| 13 models, four run groups, 1,326 judged cells, 2,142 scheduled verdicts, 2,141 scored, one no-verdict | Arithmetic is internally consistent | Roster only verified; result ledger absent | Keep as legacy geometry, not current verified coverage. |
| 21 × 9 score surface | Matches the Administration poster table | Unsupported | Move to historical appendix; see `data/cogalign_legacy_scores.csv`. |
| B2: 306 pairs, mean absolute difference `.1618`, exact agreement `.471` | Matches BiAlign poster | Unsupported | Show only as poster-reported. |
| B3: 510 pairs, mean absolute difference `.1476`, exact agreement `.537` | Matches BiAlign poster | Unsupported | Show only as poster-reported. |
| B3 appears more consistent on selected statistics | `within .25` is `.850` for B2 and `.839` for B3, the opposite direction | Selective emphasis risk | Show the complete statistic table or predeclare one primary measure. |
| S2 is usually above S3 | Internally matches the 189-cell table | Unsupported | Do not infer model ability without raw cells and uncertainty. |
| Missing debrief created a false low-score headline and was later withdrawn | Narrative is self-consistent | Raw traces and fix are absent | Preserve as a pipeline-integrity lesson, not as verified experimental history. |
| Cost totals and alternate estimates | Arithmetic is coherent | Receipts absent | Remove from the result page until receipts are restored. |

The strongest communication is not which model scored highest. It is that a missing response channel can be mistaken for a substantive model result unless completeness is checked before scoring.

## Poster 2 — Family Profile

[Open the original PDF](../evidence/posters/FP_POSTER.pdf)

| Poster-reported claim | Internal check | Evidence status | Release correction |
|---|---|---|---|
| 38 Kohlberg + 32 MFT + 204 Schwartz = 274 values per model | Arithmetic passes | Source records absent | Use only as legacy administration design. |
| 204 / 274 = 74% never reaches a coder | Arithmetic passes | Source records absent | Describe the measurement pipeline, not model behavior. |
| 18 MFT panels × two coders × six foundations | Figure exists | Unsupported | Gray out numerical profiles. |
| 18 Kohlberg panels × two coders × three schemas | Figure exists | Unsupported | Gray out numerical profiles. |
| MFT purity agreement `.943`; other channels `.660–.785` | Matches BiAlign table | Unsupported | Label as poster-reported channel reliability. |
| Kohlberg register `.933`, primary `.827`, secondary `.648`, confidence `.538` | Matches BiAlign table | Unsupported | Use only to motivate channel-specific review. |
| Schwartz minimum sample is 30 bundles; original administration produced three | Poster says no priority vector was released | Unsupported count; absence in current checkout verified | Say no reproducible Schwartz profile is available. |

### Definite wording error

The poster says: “Six legs: 1,645 records per leg, 3,290 in total.” This is impossible because `6 × 1,645 = 9,870`.

Likely intended wording:

> Across the three arcs, each of the two coder identities contributed 1,645 records. The six arc-level executions therefore contain 3,290 records in total.

This still requires confirmation from the missing receipts.

## Poster 3 — Bidirectional Alignment

[Open the original PDF](../evidence/posters/20260810-BIALIGN_V2_POSTER.pdf)

| Statistic | First run group | Second run group | Evidence status |
|---|---:|---:|---|
| Paired cells | 306 | 510 | Poster-reported only |
| Mean absolute difference | .1618 | .1476 | Poster-reported only |
| Median absolute difference | .0500 | .0000 | Poster-reported only |
| Exact agreement | .471 | .537 | Poster-reported only |
| Within .10 | .670 | .749 | Poster-reported only |
| Within .25 | .850 | .839 | Poster-reported only |
| Signed mean, leg 2 minus leg 1 | +.0403 | +.0599 | Poster-reported only |

The design lesson is sound: consistency between two automated judges is a property of the judge pair and does not validate either judge. The result table is not reproducible in the current checkout and predates the later instrument seal.

## Poster 4 — Administration

[Open the original PDF](../evidence/posters/20260810-COGALIGN_V2_POSTER.pdf)

| Poster-reported claim | Evidence status | Release correction |
|---|---|---|
| 189 model × school × setting scores | Unsupported; no input, judge, scorer, or uncertainty package | Treat as a historical illustration only. |
| 18 of 18 sample-floor checks declined at three bundles against a floor of 30 | Unsupported | Keep only as poster-reported design history. |
| A later five-model arm reached 30 bundles and was permitted | Unsupported | Do not present as recovered validity. |
| All five recovery outcomes remained indeterminate because two of three criteria lacked sealed implementation | Unsupported but important limitation | Preserve the limitation with the same evidence label. |
| Current instrument postdates all shown scores | Stated by the poster itself | The table is stale by its own disclosure. |

The safe takeaway is that administration belongs in sample identity. A model, prompt, task item, and scorer are not enough if the number and construction of response bundles change.

## Required recovery packet

For each poster result, restore:

1. item and rubric manifest;
2. subject outputs;
3. judge or coder outputs;
4. model route and revision;
5. prompt and scorer versions;
6. aggregation code;
7. uncertainty method and unit;
8. receipts for cost claims;
9. resolvable source commit and seal;
10. current-seal regeneration log.

Until then, the one-to-one machine-readable ledger is [`../data/poster_claims.csv`](../data/poster_claims.csv).
