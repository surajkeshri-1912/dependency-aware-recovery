"""Condition-aware aggregation and standard detection metrics."""
from __future__ import annotations
import pandas as pd

CONDITION_COLUMNS = [
    "topology", "workflow_size", "failure_kind", "failure_probability",
    "detection_coverage", "audit_sensitivity", "audit_false_positive_rate",
    "validation_enabled",
]


def aggregate_results(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"strategy", "final_success", "total_cost", "task_executions", "retries", "seed"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required result columns: {sorted(missing)}")
    condition_columns = [c for c in CONDITION_COLUMNS if c in frame.columns]
    group_columns = condition_columns + ["strategy"]
    aggregations: dict[str, tuple[str, str]] = {
        "trials": ("seed", "count"),
        "final_success_rate": ("final_success", "mean"),
        "mean_cost": ("total_cost", "mean"),
        "median_cost": ("total_cost", "median"),
        "std_cost": ("total_cost", "std"),
        "mean_executions": ("task_executions", "mean"),
        "mean_extra_executions": ("extra_task_executions", "mean"),
        "mean_unnecessary_reexecutions": ("unnecessary_reexecutions", "mean"),
        "mean_retries": ("retries", "mean"),
        "mean_restarts": ("restarts", "mean"),
        "mean_detection_recall": ("detection_recall", "mean"),
        "mean_audit_precision": ("audit_alert_precision", "mean"),
        "mean_audit_recall": ("audit_recall", "mean"),
        "mean_audit_f1": ("audit_f1", "mean"),
        "mean_audit_false_positives": ("audit_false_positive_alerts", "mean"),
        "mean_audit_false_negatives": ("audit_false_negative_sinks", "mean"),
    }
    available = {key: val for key, val in aggregations.items() if val[0] in frame.columns}
    return frame.groupby(group_columns, as_index=False, dropna=False).agg(**available)


def detection_metrics(tp: int, fp: int, fn: int) -> dict[str, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}
