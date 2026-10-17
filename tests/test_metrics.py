import pandas as pd
from recovery_research.metrics import aggregate_results, detection_metrics
from recovery_research.statistics import bootstrap_mean_ci, paired_policy_comparisons, pooled_paired_comparisons


def test_aggregate():
    df = pd.DataFrame([{"strategy": "none", "seed": 1, "final_success": 1, "total_cost": 3, "task_executions": 3, "retries": 0}])
    out = aggregate_results(df)
    assert out.loc[0, "final_success_rate"] == 1


def test_detection_metrics():
    metrics = detection_metrics(8, 2, 2)
    assert round(metrics["precision"], 2) == 0.8
    assert round(metrics["recall"], 2) == 0.8


def test_bootstrap_ci_single_value():
    assert bootstrap_mean_ci([2.0]) == (2.0, 2.0)


def test_paired_comparisons_match_seed_and_conditions():
    frame = pd.DataFrame([
        {"strategy": "dependency_aware", "seed": 1, "topology": "linear", "workflow_size": 4, "failure_kind": "corruption", "failure_probability": 0.1, "detection_coverage": 0.5, "audit_sensitivity": 1.0, "audit_false_positive_rate": 0.0, "validation_enabled": True, "final_success": 1, "total_cost": 5, "unnecessary_reexecutions": 0, "task_executions": 5},
        {"strategy": "full_restart", "seed": 1, "topology": "linear", "workflow_size": 4, "failure_kind": "corruption", "failure_probability": 0.1, "detection_coverage": 0.5, "audit_sensitivity": 1.0, "audit_false_positive_rate": 0.0, "validation_enabled": True, "final_success": 1, "total_cost": 8, "unnecessary_reexecutions": 3, "task_executions": 8},
    ])
    out = paired_policy_comparisons(frame, n_boot=100)
    cost = out[out.metric == "total_cost"].iloc[0]
    assert cost["mean_paired_difference_candidate_minus_baseline"] == -3


def test_pooled_paired_comparisons_emits_overall_and_kind_scopes():
    frame = pd.DataFrame([
        {"strategy": "dependency_aware", "seed": 1, "topology": "linear", "workflow_size": 4, "failure_kind": "corruption", "failure_probability": 0.1, "detection_coverage": 0.5, "audit_sensitivity": 1.0, "audit_false_positive_rate": 0.0, "validation_enabled": True, "final_success": 1, "total_cost": 5, "unnecessary_reexecutions": 0, "task_executions": 5},
        {"strategy": "full_restart", "seed": 1, "topology": "linear", "workflow_size": 4, "failure_kind": "corruption", "failure_probability": 0.1, "detection_coverage": 0.5, "audit_sensitivity": 1.0, "audit_false_positive_rate": 0.0, "validation_enabled": True, "final_success": 1, "total_cost": 8, "unnecessary_reexecutions": 3, "task_executions": 8},
    ])
    out = pooled_paired_comparisons(frame, n_boot=100)
    assert "all_conditions_pooled" in set(out.scope)
    cost = out[(out.scope == "all_conditions_pooled") & (out.metric == "total_cost")].iloc[0]
    assert cost["mean_paired_difference_candidate_minus_baseline"] == -3
