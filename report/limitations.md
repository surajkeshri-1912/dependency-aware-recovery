# Limitations, Validity, and Research Integrity

## What this project implements

- Four DAG topology generators and DAG validation.
- Deterministic per-task/per-attempt fault scheduling.
- Transient, persistent, and corrupted-output faults.
- A distinction between observable execution exceptions and corrupted outputs missed by a task validator.
- Downstream output dependence, so hidden corruptions can propagate.
- A configurable noisy final sink-audit model with sensitivity and false-positive rate.
- Four recovery baselines: no recovery, full restart, failed-task retry, and dependency-aware recovery.
- Conservative invalidation: when a node is recomputed, all cached descendants are recomputed to prevent stale values in sibling branches.
- Condition-aware result aggregation, bootstrap uncertainty intervals, paired comparisons, and plots generated from raw CSV results.
- Unit tests for persistent failures, hidden corruption, false-positive audits, disconnected-branch preservation, and stale sibling-branch prevention.

## Remaining limitations

1. **Not an actual LLM benchmark.** The task function is deterministic and synthetic. No language model, prompt, tool API, or semantic task is run in the core experiments.
2. **Oracle-backed audit simulation.** The evaluator knows the clean reference output to simulate audit sensitivity. Real tasks need independent verifiers, tests, trusted evidence, or human review; those verifiers can be imperfect in ways not represented here.
3. **Simple fault model.** Faults are sampled per task and attempt. Correlated failures, shared prompt failures, tool outages, cascading state mutations, agent collusion, and recovery-induced failures are not fully modeled.
4. **Conservative source localization.** The policy sees sink-level alerts rather than the original corrupted node. It recomputes an ancestor cone and all descendants of recomputed nodes. This is safe for the simulator's dependency semantics but may redo substantial work.
5. **Synthetic costs.** Task costs are arbitrary configurable units, not tokens, dollars, energy, or wall-clock latency. Claims must use the term *simulated execution cost*.
6. **No broad novelty claim.** Fault injection, agent resilience, trace replay, error propagation, and dependency-guided repair are active areas. This repository is a reproducible prototype and baseline study. It does not establish a novel algorithm or publishable contribution by itself.
7. **Limited statistical power in quick runs.** The quick test is for pipeline verification. It should not be used to claim general superiority. The full experiment also needs a critical interpretation and, if a formal paper is intended, a justified power/precision plan.
8. **Paired runs can diverge.** A recovery strategy changes which attempts occur; deterministic per-task/per-attempt random streams reduce order effects but cannot force identical event histories after strategies diverge.
9. **Metric limitations.** “Unnecessary re-executions” is scored using the simulator's hidden affected set. It is a diagnostic metric, not something available to a real recovery policy.
10. **Packaging and environment.** Passing tests in one environment does not guarantee successful installation on every computer. Follow the README's supported Python version and record any local installation issue.

## Required before a publication or strong SOP claim

- Read and compare the related papers listed in `literature_review.md`.
- Add a narrow, defensible gap statement based on algorithmic differences, not just the topic title.
- Evaluate the method on actual LLM-agent workflows or public execution traces if the research claim concerns LLM agents.
- Include at least one realistic validator and compare it with the oracle-assisted audit model.
- Increase seeds or design the experiment around a pre-specified precision/power target.
- Inspect raw trial data and paired comparisons, including negative results.
- Have a supervisor or experienced researcher review the methodology before claiming novelty.

## Integrity statement

Do not report proposed hypotheses as results. Do not describe a synthetic simulator as an LLM experiment. Do not claim that the dependency-aware method outperforms alternatives unless the results and uncertainty analysis support that conclusion under the stated conditions.
