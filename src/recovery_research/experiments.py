"""Config-driven experiments with raw trial-level data and reproducible metadata."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
import pandas as pd
import yaml

from .workflow import make_workflow
from .failure_injection import FailureEvent
from .recovery import run_strategy, STRATEGIES
from .metrics import aggregate_results


def load_config(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a YAML mapping")
    return config


def _as_list(config: dict, plural: str, singular: str, default):
    if plural in config:
        value = config[plural]
        return value if isinstance(value, list) else [value]
    if singular in config:
        return [config[singular]]
    return default


def run_experiment(config: dict, output_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    topologies = config.get("topologies", ["linear"])
    sizes = config.get("workflow_sizes", [6])
    seeds = config.get("seeds", [1, 2, 3])
    probabilities = config.get("failure_probabilities", [0.1])
    coverages = config.get("detection_coverages", [1.0])
    audit_sensitivities = config.get("audit_sensitivities", [1.0])
    audit_fps = config.get("audit_false_positive_rates", [0.0])
    kinds = _as_list(config, "failure_kinds", "failure_kind", ["transient"])
    strategies = config.get("strategies", list(STRATEGIES))
    target_tasks = config.get("failure_task_ids")
    max_occurrences = int(config.get("max_occurrences", 1))
    max_retries = int(config.get("max_retries", 2))
    validation_enabled = bool(config.get("validation_enabled", True))

    if not strategies or any(strategy not in STRATEGIES for strategy in strategies):
        raise ValueError(f"strategies must be a non-empty subset of {STRATEGIES}")
    if not seeds or not topologies or not sizes:
        raise ValueError("topologies, workflow_sizes, and seeds must not be empty")

    for family in topologies:
        for size_value in sizes:
            size = int(size_value)
            workflow = make_workflow(str(family), size)
            if target_tasks:
                missing = set(target_tasks) - set(workflow.tasks)
                if missing:
                    raise ValueError(f"failure_task_ids not present in {family}/{size} workflow: {sorted(missing)}")
            for kind in kinds:
                for probability in probabilities:
                    for coverage in coverages:
                        for audit_sensitivity in audit_sensitivities:
                            for audit_fp in audit_fps:
                                for seed_value in seeds:
                                    seed = int(seed_value)
                                    event = FailureEvent(
                                        kind=str(kind), probability=float(probability),
                                        detection_probability=float(coverage), max_occurrences=max_occurrences,
                                        target_tasks=tuple(target_tasks) if target_tasks else None,
                                    )
                                    for strategy in strategies:
                                        result = run_strategy(
                                            workflow, event, seed, str(strategy), max_retries=max_retries,
                                            validation_enabled=validation_enabled,
                                            audit_sensitivity=float(audit_sensitivity),
                                            audit_false_positive_rate=float(audit_fp),
                                        )
                                        result.update({
                                            "topology": str(family), "workflow_size": size,
                                            "failure_kind": str(kind), "failure_probability": float(probability),
                                            "detection_coverage": float(coverage),
                                            "audit_sensitivity": float(audit_sensitivity),
                                            "audit_false_positive_rate": float(audit_fp),
                                            "validation_enabled": validation_enabled,
                                        })
                                        result.pop("execution_log", None)
                                        rows.append(result)

    frame = pd.DataFrame(rows)
    summary = aggregate_results(frame)
    frame.to_csv(out / "raw_results.csv", index=False)
    summary.to_csv(out / "aggregated_metrics.csv", index=False)
    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "trial_strategy_rows": int(len(frame)),
        "unique_seeds": sorted({int(s) for s in seeds}),
        "note": "Raw rows are trial-strategy observations; all conclusions must be computed from these data.",
    }
    (out / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return frame, summary
