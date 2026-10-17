# Architecture

1. `workflow.py` creates and validates DAGs.
2. `failure_injection.py` provides deterministic task/attempt-specific faults and evaluator-only ground-truth labels.
3. `simulator.py` executes deterministic task functions, propagates corrupted outputs, and simulates noisy sink audits.
4. `recovery.py` implements the four policies. Policy decisions use observed execution states and sink alert IDs, not hidden fault labels.
5. `experiments.py` reads YAML configurations and saves raw trial rows, summaries, and metadata.
6. `metrics.py` aggregates by all configured condition dimensions.
7. `statistics.py` computes bootstrap mean intervals and paired candidate-minus-baseline comparisons.
8. `plotting.py` creates figures directly from raw CSV observations.
9. `cli.py` exposes `validate`, `run`, and `analyze` commands.

## Dependency-aware invalidation

When the policy receives a sink alert, it cannot know the exact faulty source. It begins with the ancestor cone of that sink. Every recomputed node can produce a changed output, so its cached descendants are also invalidated and recomputed. This protects sibling branches sharing a recomputed ancestor from stale outputs. Disconnected components remain cached.

## Information boundary

The simulator knows clean reference outputs and injected fault labels for scoring. The policy does not receive these labels. The simulated audit exposes only sink IDs that it alerts on. This models an imperfect checker while retaining an oracle for reproducible evaluation. It does not imply that real LLM tasks have an oracle.
