# Research Methodology

## Research question

When a failure occurs in a dependent workflow, can dependency-aware selective recovery reduce re-execution cost while preserving final task reliability compared with full restart and simpler retry policies?

## Experimental unit

One trial is defined by a workflow topology and size, a fault model, a task-level detection setting, a sink-audit setting, a random seed, and a recovery strategy. The same condition and seed are run across strategies. Task/attempt-specific fault events are deterministically keyed by seed, task ID, and attempt index so execution order does not shift the random stream.

## Workflow model

A workflow is a directed acyclic graph (DAG). Each node is a deterministic task, and each directed edge means that the child consumes the parent's output. Task costs are fixed positive numbers. The simulator's task function depends on all declared input values, allowing an injected output corruption to influence downstream computations.

Supported topologies: linear, branching, parallel/merge, and layered. The benchmark uses synthetic deterministic tasks, not real LLM calls.

## Fault model

- **Transient execution failure:** an attempt fails visibly to the runtime. For transient events, configured probability is sampled on each attempt until the per-task occurrence cap is reached.
- **Persistent execution failure:** every targeted attempt fails until the recovery budget is exhausted. The occurrence cap is intentionally ignored for this fault type.
- **Output corruption:** a task completes with a wrong value. The task-level validator detects corruption with configured probability; otherwise the wrong value is treated as valid by the recovery policy and can propagate downstream.

The event schedule stores ground truth for evaluation. Recovery policies do not inspect the ground-truth schedule.

## Recovery strategies

1. **No recovery:** execute the workflow once and stop.
2. **Full restart:** restart the complete workflow after observed execution problems or sink-audit alerts, subject to a bounded restart budget.
3. **Failed-task retry:** retry visible task-level failures; after a sink audit alert, retry the alerted sink only. This is a deliberately limited baseline and cannot fix a hidden upstream corruption by itself.
4. **Dependency-aware recovery:** retry visible task-level failures. After an alerted sink, recompute the sink's ancestor cone. Since recomputing any node can change its output, all descendants of recomputed nodes are invalidated and recomputed too. Disconnected components can be reused. This prevents stale outputs in sibling branches that share a recomputed ancestor.

## Audit model

The simulator computes clean reference outputs for scoring and to model an audit with configurable sensitivity and false-positive rate. The recovery policy receives only the IDs of sinks that the simulated audit alerts on. The policy does not receive the clean outputs, ground-truth source-failure IDs, or the true correctness labels.

This is an oracle-assisted *simulation of a noisy sink validator*, not a claim that real LLM tasks have a perfect answer oracle. Audit sensitivity and false-positive rate are experimental variables.

## Independent variables

Recovery strategy, workflow topology, workflow size, fault type, fault probability, task-level corruption detection coverage, sink-audit sensitivity, sink-audit false-positive rate, retry budget, and random seed.

## Outcomes

- **Final sink success:** all sink outputs are correct and safely completed.
- **All-node correctness:** every task output is correct and completed; this is stricter than final sink success.
- **Execution cost:** sum of configured costs for actual task executions.
- **Extra task executions:** executions beyond the first execution of a task.
- **Unnecessary re-executions:** extra executions of tasks outside the oracle-scored affected set (injected fault nodes plus their descendants). This metric uses hidden truth only for evaluation and should be interpreted as a simulator-specific diagnostic.
- **Task-level detection recall:** fraction of injected fault events flagged by the task-level mechanism. Explicit execution exceptions are observable; detection coverage applies to corruption.
- **Sink-audit precision/recall/F1:** calculated against evaluation-only sink correctness labels over each audit opportunity. Precision is undefined when no sink alerts occur; it is reported as missing, not as perfect.
- **Retries/restarts:** additional task executions and full workflow restart count are reported separately.

## Hypotheses

- H1: Dependency-aware recovery reduces unnecessary recomputation when unaffected disconnected components can be reused.
- H2: Its cost/reliability trade-off depends on topology and fault location.
- H3: Imperfect task-level detection and imperfect sink audits can reduce recovery success.
- H4: Its cost advantage diminishes when a fault or alerted sink connects most of the graph.
- H5: False-positive audits can increase cost without improving correctness.

Each hypothesis can be contradicted by results. The report should retain negative and null findings.

## Experimental controls and statistics

- Reuse task graph, task costs, configuration, and seed across strategies for each matched condition.
- Save trial-level observations; never infer results from chart images.
- Aggregate separately by topology, size, fault type, probabilities, audit settings, and strategy.
- Report means, medians, standard deviations, and paired bootstrap confidence intervals for candidate-minus-baseline differences.
- Treat bootstrap intervals as uncertainty summaries, not as automatic proof of causality or significance.
- Do not pool unlike conditions without labeling the average across conditions.

## Threats to validity

1. **Construct validity:** synthetic task correctness and task cost do not capture semantic correctness, token usage, or API latency.
2. **Oracle assumption:** the audit model is simulated using known clean outputs; real validators may be correlated with the model and can miss errors.
3. **Fault realism:** failures are injected by a simple configurable schedule, not sampled from real LLM execution traces.
4. **Policy scope:** the dependency-aware policy receives sink symptoms, not the exact faulty source. It uses a conservative recomputation scope.
5. **Fairness:** task/attempt schedules match where the same task attempt is reached, but strategies can diverge in how many attempts they make. Full restart and selective recovery naturally execute different sets of nodes.
6. **External validity:** findings apply to this simulator unless replicated on actual LLM-agent workflows or real traces.

## Reproducibility

All conditions are configurable in YAML. Raw results are saved in `raw_results.csv`, summaries in `aggregated_metrics.csv`, metadata in `run_metadata.json`, and plots/paired comparisons in the analysis output directory. The random seed and configuration must be included when reporting a result.
