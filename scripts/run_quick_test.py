"""Convenience wrapper for a quick experiment; prefer the documented CLI."""
import argparse
from recovery_research.experiments import load_config, run_experiment

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/quick_test.yaml")
    parser.add_argument("--output", default="results/quick_script_run")
    args = parser.parse_args()
    config = load_config(args.config)
    frame, summary = run_experiment(config, args.output)
    print(f"Completed {len(frame)} trial-strategy rows in {args.output}")
    print(summary.to_string(index=False))
