# Read this in one minute

## Decision

| Publish now | Keep exploratory | Fix or hold next |
|---|---|---|
| Results for each task | Model size patterns | Compare models on the same items |
| Saved uncertainty | Release period patterns | Check parsing and labels |
| Clear evidence limits | — | Hold poster numbers until replay files return |
| — | — | Run the planned human review |

**Publish the task results. Do not rank the models overall.**

## What the results mean

| Question | Short answer | Why it matters |
|---|---|---|
| Do any of the five models that ran all eight tasks lead every task? | No. The leader changes by task. | Show each task on its own. |
| Can the two comparison tasks rank models? | Not yet. Every model-by-model uncertainty range overlaps. | Recover results for the same items across models, then compare them directly. |
| Do scores go up each time model size goes up? | Only 4 of 12 selected UniMoral paths do. | Treat size as a clue, not a rule. |
| Does a later model release always score higher? | No. Qwen and DeepSeek move different tasks in different directions. | Release date is model information, not a progress measure. |

## Paper boundary

| What the papers give us | What they do not give us |
|---|---|
| Questions, methods, and interpretation context | A direct score baseline for these local runs |

None of the local runs exactly repeats a paper protocol. The papers help explain what each task measures. They do not turn the local scores into replications.

## Bottom line

| Say this | Do not say this |
|---|---|
| Performance depends on the task. | One model is morally best. |
| The two comparison tasks need better evidence. | The current comparison rank is settled. |
| Size and release patterns are exploratory. | Bigger or newer causes better moral performance. |
| Human validation is still pending. | Benchmark agreement proves moral correctness. |

## Quick definitions

| Term | Plain meaning |
|---|---|
| Top saved value | The highest stored number for that task. It is not a proven winner. |
| Saved interval | The stored uncertainty range around a result. |
| MFQ | Short statements about moral foundations. |
| METEOR | A text-similarity score for generated consequences. |
| Human validation | People check whether the benchmark measures the judgment we care about. |
