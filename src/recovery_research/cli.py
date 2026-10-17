"""Command-line interface for validation, experiments, and analysis."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from .experiments import load_config, run_experiment
from .workflow import make_workflow
from .plotting import create_plots
from .metrics import aggregate_results
from .statistics import paired_policy_comparisons, pooled_paired_comparisons


def main() -> None:
    parser = argparse.ArgumentParser(prog="recovery-research")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate config and workflow definitions")
    validate.add_argument("--config", required=True)

    run = sub.add_parser("run", help="Run configured experiments")
    run.add_argument("--config", required=True)
    run.add_argument("--output", default="results/run")
    run.add_argument("--overwrite", action="store_true", help="Allow overwriting result CSVs in the output directory")

    analyze = sub.add_parser("analyze", help="Analyze raw results and create plots")
    analyze.add_argument("--results", required=True, help="Path to raw_results.csv or its containing directory")
    analyze.add_argument("--output", default="results/analysis")
    analyze.add_argument("--baseline", default="full_restart")
    analyze.add_argument("--candidate", default="dependency_aware")

    args = parser.parse_args()
    if args.command == "validate":
        cfg = load_config(args.config)
        for family in cfg.get("topologies", ["linear"]):
            for size in cfg.get("workflow_sizes", [6]):
                workflow = make_workflow(str(family), int(size))
                if cfg.get("failure_task_ids"):
                    missing = set(cfg["failure_task_ids"]) - set(workflow.tasks)
                    if missing:
                        raise ValueError(f"failure_task_ids not present in {family}/{size}: {sorted(missing)}")
        print(f"Configuration and workflow definitions valid: {args.config}")
    elif args.command == "run":
        output = Path(args.output)
        raw_path = output / "raw_results.csv"
        summary_path = output / "aggregated_metrics.csv"
        if not args.overwrite and (raw_path.exists() or summary_path.exists()):
            raise FileExistsError(f"Results already exist in {output}; choose a new directory or pass --overwrite")
        cfg = load_config(args.config)
        frame, summary = run_experiment(cfg, output)
        print(f"Saved {len(frame)} trial-strategy rows to {output.resolve()}")
        print(f"Saved {len(summary)} condition/strategy summaries")
        print(summary.head(20).to_string(index=False))
    elif args.command == "analyze":
        source = Path(args.results)
        if source.is_dir():
            source = source / "raw_results.csv"
        frame = pd.read_csv(source)
        output = Path(args.output)
        output.mkdir(parents=True, exist_ok=True)
        summary = aggregate_results(frame)
        summary.to_csv(output / "aggregated_metrics.csv", index=False)
        comparisons = paired_policy_comparisons(frame, candidate=args.candidate, baseline=args.baseline)
        comparisons.to_csv(output / "paired_comparisons.csv", index=False)
        pooled_comparisons = pooled_paired_comparisons(frame, candidate=args.candidate, baseline=args.baseline)
        pooled_comparisons.to_csv(output / "pooled_paired_summary.csv", index=False)
        pooled_metrics = [c for c in ["final_success", "total_cost", "task_executions", "unnecessary_reexecutions", "retries", "restarts"] if c in frame.columns]
        pooled_summary = frame.groupby("strategy", as_index=False)[pooled_metrics].mean()
        pooled_summary.to_csv(output / "pooled_strategy_summary.csv", index=False)
        paths = create_plots(source, output / "plots")
        print(f"Saved analysis to {output.resolve()}")
        print(f"Condition-specific paired comparisons: {len(comparisons)} rows")
        print(f"Pooled paired summary: {len(pooled_comparisons)} rows")
        print("Created plots:")
        for path in paths:
            print(f" - {path}")


if __name__ == "__main__":
    main()
