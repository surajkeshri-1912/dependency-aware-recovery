# Dependency-Aware Failure Recovery in Multi-Agent Workflows

A reproducible **research prototype** for studying failure propagation and recovery policies in dependency graphs. The core experiments use a deterministic synthetic simulator. They do **not** execute real LLM agents, so the results must not be presented as evidence that a method improves real LLM-agent performance.

## Research question

> When a failure occurs in a dependent workflow, can dependency-aware selective recovery reduce re-execution cost while preserving final task reliability compared with full restart and simpler retry policies?

## What is included

- Four DAG topology families: linear, branching, parallel/merge, and layered.
- Fault models for transient execution exceptions, persistent exceptions, and completed-but-corrupted outputs.
- Task-level corruption detection coverage and a noisy final sink audit with configurable sensitivity and false-positive rate.
- Four policies: no recovery, full workflow restart, failed-task retry, and dependency-aware recovery.
- Cache invalidation that recomputes descendants of recomputed nodes, preventing stale outputs in sibling branches that share an upstream dependency.
- Trial-level CSVs, condition-aware summaries, paired candidate-versus-baseline comparisons with bootstrap confidence intervals, and plots generated from raw results.
- Automated tests for DAG validation, error propagation, persistent faults, noisy audits, and recovery edge cases.
- A focused literature review and methodology/limitations reports.

## Research integrity

The project is a reproducible simulator and baseline comparison, not a completed paper or a validated novel algorithm. Dependency-aware recovery, error propagation, agent resilience, and execution replay are already active research areas. See `report/literature_review.md` before writing a gap statement. The simulator's clean reference outputs are used to model noisy audits and score correctness; real tasks may not have such an oracle.

## Requirements

- Python 3.11 or newer.
- Internet access for first-time dependency installation unless the required packages are already available.
- No GPU, Docker, paid API key, or live LLM service is required for the core experiments.

## Windows PowerShell: install and run

Open PowerShell in the extracted `dependency-aware-recovery` directory.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m recovery_research.cli validate --config configs/quick_test.yaml
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m recovery_research.cli run --config configs/quick_test.yaml --output results/quick_run_1
.\.venv\Scripts\python.exe -m recovery_research.cli analyze --results results/quick_run_1 --output results/quick_run_1_analysis
```

The commands call the virtual environment's Python executable directly, so PowerShell script activation is not required. If you prefer activation and your execution policy allows it, run `\.venv\Scripts\Activate.ps1` and then use `python`.

If editable installation fails because the environment cannot download build dependencies, and you already installed the dependencies from `requirements.txt`, try:

```powershell
.\.venv\Scripts\python.exe -m pip install --no-build-isolation -e .
```

## macOS/Linux: install and run

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -e .
.venv/bin/python -m recovery_research.cli validate --config configs/quick_test.yaml
.venv/bin/python -m pytest -q
.venv/bin/python -m recovery_research.cli run --config configs/quick_test.yaml --output results/quick_run_1
.venv/bin/python -m recovery_research.cli analyze --results results/quick_run_1 --output results/quick_run_1_analysis
```

## Run the full experiment

The full configuration covers four topologies, two workflow sizes, transient and corruption faults, several fault/detection/audit settings, ten seeds, and four recovery policies. It produces 15,360 trial-strategy rows in the checked-in development run. Re-run it with:

```bash
# Windows PowerShell
.\.venv\Scripts\python.exe -m recovery_research.cli run --config configs/full_experiment.yaml --output results/full_run_1
.\.venv\Scripts\python.exe -m recovery_research.cli analyze --results results/full_run_1 --output results/full_run_1_analysis

# macOS/Linux
.venv/bin/python -m recovery_research.cli run --config configs/full_experiment.yaml --output results/full_run_1
.venv/bin/python -m recovery_research.cli analyze --results results/full_run_1 --output results/full_run_1_analysis
```

Choose a new output directory for every run. The CLI refuses to overwrite existing result CSVs unless you explicitly pass `--overwrite`.

## Diagnostic configurations

### Hidden corruption propagation

```bash
python -m recovery_research.cli run --config configs/delayed_corruption_demo.yaml --output results/corruption_demo_1
```

This injects one undetected corruption at the root of a linear graph. A simulated sink audit detects the resulting wrong output. In a linear graph, most or all tasks may need recomputation; selective recovery is not expected to save cost in every topology.

### Persistent failure stress test

```bash
python -m recovery_research.cli run --config configs/persistent_failure_stress.yaml --output results/persistent_stress_1
```

A persistent fault continues on every targeted attempt until the policy exhausts its retry budget. `max_occurrences` is ignored for persistent faults by design.

## Commands

```bash
python -m recovery_research.cli validate --config configs/quick_test.yaml
python -m recovery_research.cli run --config configs/quick_test.yaml --output results/run_1
python -m recovery_research.cli analyze --results results/run_1 --output results/analysis_1
python -m pytest -q
```

`analyze` writes `aggregated_metrics.csv`, `paired_comparisons.csv`, and plots to `plots/`.

## Output files

- `raw_results.csv`: one row per condition, seed, and recovery strategy.
- `aggregated_metrics.csv`: descriptive summaries grouped by experimental conditions and strategy.
- `run_metadata.json`: configuration and row count.
- `paired_comparisons.csv`: matched differences for dependency-aware recovery versus the selected baseline, with bootstrap confidence intervals.
- `plots/*.png`: charts generated from the saved CSV data.

## Main metrics

- **Final sink success:** all sink outputs are correct and safely completed.
- **All-node correctness:** every task is correct and completed; this is stricter than final sink success.
- **Simulated execution cost:** sum of configured task costs, not tokens, dollars, or real latency.
- **Extra task executions:** executions beyond a task's first execution.
- **Unnecessary re-executions:** extra executions outside the injected-fault node/descendant set, scored with hidden simulator labels. This is an evaluation-only diagnostic.
- **Task detection recall:** injected events detected by task-level mechanisms.
- **Audit precision/recall/F1:** sink-audit alerts compared with simulator correctness labels. Precision is undefined when no alerts occur and is left blank rather than reported as perfect.

## Recovery semantics

- `none`: run once, no corrective action.
- `full_restart`: restart the whole workflow after visible execution problems or sink-audit alerts.
- `failed_task_retry`: retry visible failed tasks; after an audit alert, retry only the alerted sink.
- `dependency_aware`: retry visible failures; after an audit alert, recompute the ancestor cone of alerted sinks and all descendants of recomputed nodes. Descendant invalidation is essential because recomputing a shared ancestor can change outputs in sibling branches. Disconnected components can be reused.

## Repository map

```text
src/recovery_research/   Simulator, workflow graph, fault model, policies, metrics, CLI
configs/                 Quick, full, corruption demo, persistent-failure configs
tests/                   Unit and regression tests
results/full_final/      Checked-in full experiment raw/aggregated outputs
results/full_final_analysis/ Plots and paired comparisons from that run
report/                  Literature review, methods, results, limitations, SOP and interview guides
```

## Limitations and Future Work

This project currently uses a synthetic workflow simulator to study how different recovery strategies behave when task failures or corrupted outputs occur. Although the simulator makes it possible to control experimental conditions and compare policies reproducibly, it does not capture all the challenges of real LLM-based multi-agent systems.

An important direction for future work is to evaluate these recovery strategies on workflows involving actual LLM agents. This would allow the study to examine realistic execution failures, imperfect output validation, and the trade-off between recovery cost and task reliability. Another challenge is to develop validation mechanisms that can identify incorrect outputs without relying on access to a known correct answer.

These extensions would help determine whether the observations from the current simulation generalize to practical agentic workflows.

