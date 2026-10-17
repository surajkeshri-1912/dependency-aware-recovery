from recovery_research.workflow import make_workflow, Workflow
from recovery_research.failure_injection import FailureEvent
from recovery_research.recovery import run_strategy, STRATEGIES


def test_all_strategies_return_expected_fields():
    w = make_workflow("branching", 6)
    event = FailureEvent("transient", 0.2, 1.0, 1)
    for strategy in STRATEGIES:
        result = run_strategy(w, event, 17, strategy, max_retries=2)
        assert result["strategy"] == strategy
        assert 0 <= result["final_success"] <= 1
        assert result["total_cost"] >= 0
        assert "unnecessary_reexecutions" in result


def test_no_failure_completes():
    w = make_workflow("linear", 5)
    event = FailureEvent("transient", 0.0)
    for strategy in STRATEGIES:
        result = run_strategy(w, event, 5, strategy)
        assert result["final_success"] == 1


def test_undetected_corruption_propagates_and_dependency_aware_audit_recovers():
    w = make_workflow("linear", 5)
    event = FailureEvent("corruption", 1.0, 0.0, 1, ("T00",))
    no_recovery = run_strategy(w, event, 19, "none", max_retries=2, validation_enabled=True)
    adaptive = run_strategy(w, event, 19, "dependency_aware", max_retries=2, validation_enabled=True)
    assert no_recovery["final_success"] == 0
    assert no_recovery["incorrect_nodes_at_end"] > 0
    assert adaptive["final_success"] == 1
    assert adaptive["audit_alert_events"] > 0


def test_disconnected_independent_branch_is_preserved():
    # A and B feed C; D is an unrelated independent sink.
    w = Workflow.from_edges({"A": 1, "B": 1, "C": 1, "D": 1}, [("A", "C"), ("B", "C")])
    event = FailureEvent("corruption", 1.0, 0.0, 1, ("A",))
    result = run_strategy(w, event, 23, "dependency_aware", max_retries=2)
    assert result["final_success"] == 1
    d_executions = sum(1 for row in result["execution_log"] if row["task_id"] == "D" and row["status"] == "completed")
    assert d_executions == 1


def test_hidden_corruption_changes_downstream_output_before_recovery():
    from recovery_research.simulator import Simulator, RunState
    from recovery_research.failure_injection import FailureSchedule
    w = make_workflow("linear", 3)
    event = FailureEvent("corruption", 1.0, 0.0, 1, ("T00",))
    sim = Simulator(w, FailureSchedule(31, event), validation_enabled=True)
    state = RunState()
    sim.execute_task("T00", state)
    sim.execute_task("T01", state)
    reference = sim.reference_outputs()
    assert state.records["T00"].valid is True
    assert state.records["T01"].output != reference["T01"]


def test_recomputed_shared_ancestor_invalidates_sibling_descendants():
    # A feeds B->D and C->E. If D is audited, re-executing A requires recomputing
    # both branches; otherwise E could retain an output derived from stale A.
    w = Workflow.from_edges(
        {"A": 1, "B": 1, "C": 1, "D": 1, "E": 1, "Z": 1},
        [("A", "B"), ("B", "D"), ("A", "C"), ("C", "E")],
    )
    event = FailureEvent("corruption", 1.0, 0.0, 1, ("A",))
    result = run_strategy(w, event, 29, "dependency_aware", max_retries=2)
    assert result["final_success"] == 1
    # E belongs to the same dependency-connected component as recomputed A.
    e_execs = sum(1 for row in result["execution_log"] if row["task_id"] == "E" and row["status"] == "completed")
    assert e_execs >= 2
    # Z is disconnected and must be preserved.
    z_execs = sum(1 for row in result["execution_log"] if row["task_id"] == "Z" and row["status"] == "completed")
    assert z_execs == 1


def test_false_positive_audit_causes_cost_but_not_incorrect_final_answer():
    w = make_workflow("linear", 4)
    event = FailureEvent("transient", 0.0)
    baseline = run_strategy(w, event, 8, "none")
    noisy = run_strategy(w, event, 8, "dependency_aware", audit_sensitivity=1.0, audit_false_positive_rate=1.0, max_retries=1)
    assert noisy["final_success"] == 1
    assert noisy["audit_false_positive_alerts"] > 0
    assert noisy["total_cost"] > baseline["total_cost"]


def test_persistent_failure_does_not_disappear_after_max_occurrences():
    w = make_workflow("linear", 4)
    event = FailureEvent("persistent", 1.0, 1.0, 1, ("T01",))
    result = run_strategy(w, event, 7, "dependency_aware", max_retries=2)
    assert result["final_success"] == 0
    assert result["ground_truth_failures"] > 1
