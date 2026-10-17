# Experimental Results: Executed Simulator Runs

**Status:** This report summarizes the full configured synthetic simulation that was actually executed in the development environment. It is not an LLM-agent evaluation, and the pooled values are descriptive summaries over the configured conditions.

## Run details

- Configuration: `configs/full_experiment.yaml`
- Topologies: linear, branching, parallel/merge, layered
- Workflow sizes: 6 and 10 tasks
- Fault types: transient execution failure and output corruption
- Fault probabilities: 0.0, 0.1, 0.25
- Task-level corruption detection coverage: 0.5, 1.0
- Sink-audit sensitivity: 0.5, 1.0
- Sink-audit false-positive rate: 0.0, 0.02
- Seeds: 101–110
- Strategies: none, full restart, failed-task retry, dependency-aware recovery
- Raw rows: 15,360 (3,840 rows per strategy)
- Unit tests: 26 passed in the development environment

The raw data are in `results/full_final/raw_results.csv`; condition-aware summaries are in `results/full_final/aggregated_metrics.csv`; the run configuration is in `results/full_final/run_metadata.json`. Plots and condition-specific paired comparisons are in `results/full_final_analysis/`.

## Descriptive pooled summary

The following values average over the configured condition grid. Because conditions vary in topology, fault type, detection, audit sensitivity, and false-positive rate, these pooled values are an overview only; they should not replace condition-specific analysis.

| Strategy | Final sink success rate | Mean simulated execution cost | Mean task executions | Mean unnecessary re-executions |
|---|---:|---:|---:|---:|
| No recovery | 0.567 | 12.783 | 6.662 | 0.000 |
| Full restart | 0.862 | 21.568 | 11.271 | 1.496 |
| Failed-task retry | 0.957 | 17.129 | 8.914 | 0.008 |
| Dependency-aware recovery | 0.987 | 18.395 | 9.555 | 0.251 |

These figures are outputs from this simulator's current configuration, not universal performance claims. In this particular run, dependency-aware recovery had a higher pooled final-success rate and lower pooled simulated cost than full restart, but it used more cost than the failed-task retry baseline. The comparison is affected by the fault model, audit assumptions, and the fact that different strategies execute different task-attempt histories.

## Matched comparisons: dependency-aware minus baseline

Matched rows share topology, workflow size, fault type/probability, task-level detection coverage, audit sensitivity/false-positive rate, validation setting, and seed. The following exploratory intervals use a percentile bootstrap over matched trial-condition differences. The grid includes repeated experimental conditions and should not be treated as a formal independent-sample hypothesis test.

| Baseline | Outcome | Mean paired difference | Exploratory 95% bootstrap interval |
|---|---|---:|---:|
| Full restart | Final sink success | +0.125 | [+0.114, +0.136] |
| Full restart | Simulated execution cost | -3.173 | [-3.433, -2.934] |
| Full restart | Unnecessary re-executions | -1.245 | [-1.328, -1.167] |
| Failed-task retry | Final sink success | +0.030 | [+0.025, +0.036] |
| Failed-task retry | Simulated execution cost | +1.266 | [+1.106, +1.439] |
| No recovery | Final sink success | +0.420 | [+0.405, +0.436] |

Interpretation: within this synthetic setup, dependency-aware recovery appears to trade additional simulated cost relative to failed-task retry for improved final sink success. It has lower cost than full restart in the pooled matched comparison. These are exploratory simulator findings only. A real LLM-agent evaluation and a stronger validation design are required before claiming practical superiority.

## Diagnostic corruption demonstration

The single-seed `configs/delayed_corruption_demo.yaml` run injects an undetected root corruption into a six-task linear workflow and gives the sink audit sensitivity 1.0 with false-positive rate 0.0.

| Strategy | Final sink success | Simulated cost | Task executions |
|---|---:|---:|---:|
| No recovery | 0 | 12 | 6 |
| Failed-task retry | 0 | 18 | 8 |
| Full restart | 1 | 24 | 12 |
| Dependency-aware recovery | 1 | 24 | 12 |

The dependency-aware method does not save cost over full restart on this linear graph because the affected workflow is the entire graph. The demo illustrates mechanics, not a statistically general result.

## Persistent-failure stress test

The `configs/persistent_failure_stress.yaml` run injects a persistent visible failure at task `T02`. All strategies have final sink success 0 in this condition, as expected when the targeted failure never stops within the retry budget. Dependency-aware recovery has more execution cost in this configuration because the current conservative sink-level recovery policy can recompute broad connected regions even when the root cause remains persistent. This is an important negative result and suggests a future improvement: detect repeated failure at the same node and stop futile recovery early.

## Conclusions supported by these runs

1. The code can run the configured synthetic experiment, save raw observations, aggregate condition-specific results, and create plots.
2. In this simulator, recovery strategy affects final sink success and simulated task cost.
3. Topology and audit settings should be inspected separately; a pooled average hides important interactions.
4. A persistent fault can defeat every current strategy; retries are not a universal solution.
5. The results do **not** establish that the policy improves real LLM-agent systems, that the algorithm is novel, or that the work is publication-ready.

## Next scientific validation steps

- Use real multi-agent traces or reproducible LLM-agent tasks.
- Replace the oracle-backed audit with a realistic validator, unit tests, evidence checking, or human labels.
- Pre-register a narrow hypothesis and choose trial counts based on desired precision/power.
- Include ablations and compare with published failure-recovery methods where code/data are available.
- Inspect raw trial data and per-condition paired comparisons before presenting results.
