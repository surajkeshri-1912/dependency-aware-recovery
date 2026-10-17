"""Convenience wrapper for saved raw results."""
import argparse
from pathlib import Path
import pandas as pd
from recovery_research.metrics import aggregate_results
from recovery_research.plotting import create_plots
from recovery_research.statistics import paired_policy_comparisons, pooled_paired_comparisons

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True, help="Raw results CSV or directory containing it")
    parser.add_argument("--output", default="results/analysis")
    parser.add_argument("--baseline", default="full_restart")
    parser.add_argument("--candidate", default="dependency_aware")
    args = parser.parse_args()
    source = Path(args.results)
    if source.is_dir():
        source = source / "raw_results.csv"
    frame = pd.read_csv(source)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    aggregate_results(frame).to_csv(output / "aggregated_metrics.csv", index=False)
    paired_policy_comparisons(frame, candidate=args.candidate, baseline=args.baseline).to_csv(output / "paired_comparisons.csv", index=False)
    pooled_paired_comparisons(frame, candidate=args.candidate, baseline=args.baseline).to_csv(output / "pooled_paired_summary.csv", index=False)
    frame.groupby("strategy", as_index=False)[[c for c in ["final_success", "total_cost", "task_executions", "unnecessary_reexecutions", "retries", "restarts"] if c in frame.columns]].mean().to_csv(output / "pooled_strategy_summary.csv", index=False)
    for path in create_plots(source, output / "plots"):
        print(path)
