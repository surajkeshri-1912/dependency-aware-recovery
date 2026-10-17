# PhD Interview Guide: Dependency-Aware Failure Recovery

## One-minute explanation

“My project studies failure recovery in dependent multi-agent workflows. I represented a workflow as a directed acyclic graph, where tasks consume outputs from their dependencies. I built a deterministic simulator that injects transient execution failures, persistent failures, and completed-but-incorrect outputs. I compared four policies: no recovery, full workflow restart, retrying only a failed task, and dependency-aware recovery. The dependency-aware policy responds to a sink-level audit alert by recomputing the relevant ancestor cone and invalidating descendants of recomputed nodes so stale values are not reused. I evaluated final sink correctness, all-node correctness, simulated execution cost, extra executions, and audit behavior across different graph topologies and detection settings. The current results are preliminary and synthetic; my next step would be to validate the recovery policy against real LLM-agent traces and more realistic validators.”

## What is the research question?

Can dependency-aware selective recovery reduce re-execution cost while preserving final task reliability compared with full restart and simpler retry policies?

## Why use a DAG?

A directed acyclic graph explicitly represents data dependencies. If a task output changes, its downstream dependents may need to be recomputed. Tasks outside the affected dependency component may be reusable. This is a useful abstraction for agent workflows that pass intermediate results between agents, but a DAG may not represent all conversational loops or dynamic dependencies in real systems.

## What are the four baselines?

- **No recovery:** execute once and stop.
- **Full restart:** rerun the whole workflow after an observed problem or sink-audit alert.
- **Failed-task retry:** retry a visible failed task; after a sink alert, retry the sink only.
- **Dependency-aware recovery:** retry visible failures; after a sink alert, recompute an ancestor cone and invalidate descendants to avoid stale cached outputs.

The failed-task retry baseline is deliberately limited. A fair paper comparison should also include stronger published methods where reproducible implementations are available.

## What is the difference between a failure and corruption?

A visible execution failure produces no usable output. A corruption can produce an output that appears to be a successful execution but is semantically wrong. If the wrong output is consumed downstream, the error may propagate. The simulator models these separately because a retry mechanism that reacts only to exceptions cannot automatically catch silent corruption.

## How do you avoid leaking ground truth to the recovery policy?

The simulator records hidden injected-failure labels for evaluation. The policy sees task statuses and sink IDs returned by a simulated audit, not the hidden source-failure labels or clean reference outputs. The audit uses the clean reference internally to simulate a configurable sensitivity and false-positive rate. This is still an oracle-assisted simulation, which is a limitation rather than a realistic guarantee.

## What did you measure?

- Final sink success rate.
- All-node correctness.
- Simulated execution cost.
- Extra task executions and unnecessary re-executions.
- Task-level fault detection recall.
- Sink-audit precision, recall, F1, false positives, and false negatives.
- Retries and workflow restarts.

Simulated cost is an arbitrary sum of task costs. It is not token usage, API spending, energy, or wall-clock latency.

## What did the current experiment show?

Across the configured synthetic condition grid, the pooled final sink success rates were 0.567 for no recovery, 0.862 for full restart, 0.957 for failed-task retry, and 0.987 for dependency-aware recovery. Mean simulated costs were 12.783, 21.568, 17.129, and 18.395 respectively. These are descriptive results from this simulator and configuration, not evidence of performance on real LLMs. Dependency-aware recovery used more simulated cost than failed-task retry while achieving a higher pooled success rate, and used less cost than full restart in this run. The persistent-failure stress test showed that every policy can fail when the underlying fault never stops within the retry budget.

## What is the contribution?

The current deliverable is a reproducible experimental harness and baseline comparison, with explicit fault models, configurable task-level detection and noisy sink audits, cache invalidation, raw trial outputs, condition-aware summaries, and paired exploratory comparisons. It is not yet a validated novel algorithm. The literature already includes work on faulty-agent resilience, error propagation, replay, and graph-guided recovery.

## What are the main limitations?

1. The core experiment uses deterministic synthetic tasks rather than actual LLM calls.
2. The sink audit is simulated using clean reference outputs.
3. The dependency-aware method is conservative because it observes sink symptoms rather than localizing the true source.
4. The task-cost model does not measure tokens or API latency.
5. Results are sensitive to workflow topology, detection quality, fault schedules, and retry budgets.
6. Literature review is a focused scoping review, not a systematic review.

## What would you do next as a PhD researcher?

1. Read the related papers in `literature_review.md` and map the exact assumptions and recovery scopes.
2. Add a benchmark built from real, reproducible LLM-agent tasks or public execution traces.
3. Replace the oracle-backed audit with task-specific unit tests, evidence verification, or independent evaluators.
4. Compare against stronger published recovery/replay methods.
5. Design a narrow contribution—such as a better recovery-scope selection policy—and predefine hypotheses and metrics.
6. Run ablations, analyze failures, and report negative findings.

## Honest interview rule

Do not say “I proved this is novel” or “this improves real LLM agents.” Say that you built a preliminary simulator, observed specific trade-offs under controlled assumptions, and identified the validation steps required to establish external validity.
