# Build, Test, and Experiment Status

Last verified in the development environment on 17 October 2026.

## Automated tests

- `python -m pytest -q` — **26 passed**.
- Two quick experiment runs with the same config and seeds produced identical raw result tables.
- Coverage includes DAG validation, deterministic fault scheduling, transient/persistent/corruption fault semantics, hidden corruption propagation, noisy audits, false-positive overhead, disconnected-component preservation, shared-ancestor cache invalidation, metric aggregation, bootstrap intervals, and paired comparisons.

## Installation and CLI checks

- `python -m pip install --no-build-isolation -e .` — passed using dependencies already available in the development environment.
- A normal isolated `pip install -e .` attempt could not download build dependencies because the development environment had no network access. This is an environment limitation, not proof that a user installation will fail. The README includes both standard and fallback commands.
- Configuration validation — passed for `configs/quick_test.yaml`.
- Quick experiment — 240 trial-strategy rows generated.
- Full experiment — 15,360 trial-strategy rows generated from `configs/full_experiment.yaml`.
- Full experiment analysis — condition-aware summaries, 1,536 condition-specific paired comparison rows, 12 pooled paired-summary rows, pooled strategy summary, and five plots generated from raw CSV observations.
- Hidden-corruption demonstration — four strategy rows generated.
- Persistent-failure stress test — 12 strategy rows generated; the persistent fault remained unrecovered within the configured retry budget.

## Main result locations

- `results/full_final/raw_results.csv`
- `results/full_final/aggregated_metrics.csv`
- `results/full_final/run_metadata.json`
- `results/full_final_analysis/paired_comparisons.csv`
- `results/full_final_analysis/pooled_paired_summary.csv`
- `results/full_final_analysis/pooled_strategy_summary.csv`
- `results/full_final_analysis/plots/`
- `report/experimental_results.md`

## Research caveats

The simulator uses synthetic deterministic tasks, controlled faults, and an oracle-backed simulation of a noisy sink audit. It is not a real LLM-agent evaluation. The results are exploratory and condition-dependent; they do not establish novelty or general superiority. See `report/literature_review.md` and `report/limitations.md` before using the project in a PhD SOP.
