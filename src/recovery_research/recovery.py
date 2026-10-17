"""Recovery strategies for controlled DAG experiments.

Policies only observe task execution status and simulated sink-audit alerts. Hidden
failure labels and clean reference outputs are used only after decisions for metrics.
"""
from __future__ import annotations

import networkx as nx

from .workflow import Workflow
from .simulator import Simulator, RunState, TaskRecord
from .failure_injection import FailureEvent, FailureSchedule

STRATEGIES = ("none", "full_restart", "failed_task_retry", "dependency_aware")


def run_strategy(
    workflow: Workflow,
    event: FailureEvent,
    seed: int,
    strategy: str,
    max_retries: int = 2,
    validation_enabled: bool = True,
    audit_sensitivity: float = 1.0,
    audit_false_positive_rate: float = 0.0,
) -> dict:
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy {strategy!r}")
    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")
    if not 0 <= audit_sensitivity <= 1 or not 0 <= audit_false_positive_rate <= 1:
        raise ValueError("Audit parameters must be in [0, 1]")

    schedule = FailureSchedule(seed, event)
    sim = Simulator(workflow, schedule, validation_enabled=validation_enabled)
    state = RunState()
    order = workflow.topological_order()
    attempts = {n: 0 for n in order}

    def record_blocked(task: str, phase: str) -> None:
        state.records[task] = TaskRecord(task, "blocked", valid=False)
        state.execution_log.append({
            "task_id": task, "status": "blocked", "observed_failure_kind": None,
            "detected": False, "cost": 0.0, "retry_number": None,
            "phase": phase, "inputs": "unavailable", "output": None,
        })

    def execute_one(task: str, phase: str) -> TaskRecord:
        deps = workflow.tasks[task].dependencies
        if any(dep not in state.records or not state.records[dep].valid or state.records[dep].status != "completed" for dep in deps):
            record_blocked(task, phase)
            return state.records[task]
        if attempts[task] > 0:
            state.retries += 1
        rec = sim.execute_task(task, state, retry_number=attempts[task], phase=phase)
        attempts[task] += 1
        return rec

    def retry_observed_task(task: str, phase: str) -> None:
        # Explicit execution exceptions and task-level detected corruptions are
        # observable. Hidden corruptions remain apparently completed and are not retried.
        for _ in range(max_retries):
            rec = state.records.get(task)
            if rec is None or rec.status not in {"failed", "invalid_output"}:
                break
            if not rec.detected:
                break
            next_rec = execute_one(task, phase)
            if next_rec.status == "completed" and next_rec.valid:
                break

    def execute_pass(phase: str, local_retry: bool) -> None:
        for task in order:
            rec = execute_one(task, phase)
            if local_retry and rec.status in {"failed", "invalid_output"} and rec.detected:
                retry_observed_task(task, phase=f"{phase}_local_retry")

    def has_observed_problem() -> bool:
        return any(rec.status in {"failed", "invalid_output", "blocked"} for rec in state.records.values())

    def current_audit(round_id: int) -> list[str]:
        return sim.audit_sinks(state, seed, round_id, audit_sensitivity, audit_false_positive_rate)

    def selective_recovery(alerted_sinks: list[str], phase: str) -> None:
        # Sink-level symptoms do not identify the source. Start with the ancestor
        # cone of each alerted sink. Re-executing any node can change its output, so
        # every cached descendant of a recomputed node must also be invalidated; this
        # prevents stale sibling-branch outputs when branches share an upstream node.
        # Disconnected components remain reusable.
        affected: set[str] = set(alerted_sinks)
        for sink in alerted_sinks:
            affected.update(nx.ancestors(workflow.graph, sink))
        recomputed_ancestors = set(affected)
        for node in list(recomputed_ancestors):
            affected.update(nx.descendants(workflow.graph, node))
        for task in affected:
            state.records.pop(task, None)
        for task in order:
            if task not in affected:
                continue
            rec = execute_one(task, phase)
            if rec.status in {"failed", "invalid_output"} and rec.detected:
                retry_observed_task(task, phase=f"{phase}_local_retry")

    # Initial execution. Local retry policies respond to visible task-level failures.
    execute_pass("initial", local_retry=strategy in {"failed_task_retry", "dependency_aware"})

    if strategy == "full_restart":
        for round_id in range(1, max_retries + 1):
            alerts = current_audit(round_id - 1)
            if not has_observed_problem() and not alerts:
                break
            state.restarts += 1
            state.records.clear()
            execute_pass(f"full_restart_{round_id}", local_retry=False)
    elif strategy in {"failed_task_retry", "dependency_aware"}:
        for round_id in range(1, max_retries + 1):
            alerts = current_audit(round_id - 1)
            if not alerts:
                break
            if strategy == "dependency_aware":
                selective_recovery(alerts, phase=f"dependency_recovery_{round_id}")
            else:
                # Baseline: retry only the alerted sink. If its dependencies contain
                # hidden corruption, retrying the sink cannot repair the upstream cause.
                for sink in alerts:
                    for _ in range(max_retries):
                        deps = workflow.tasks[sink].dependencies
                        if any(d not in state.records or not state.records[d].valid or state.records[d].status != "completed" for d in deps):
                            break
                        rec = execute_one(sink, phase=f"sink_retry_{round_id}")
                        if rec.status == "completed" and rec.valid:
                            break
    # No-recovery baseline deliberately takes no corrective action.

    # Evaluation only: hidden truth is inspected after the policy has finished.
    all_correct, incorrect_nodes, incorrect_sinks = sim.evaluate_correctness(state)
    reference_failure_nodes = {entry["task_id"] for entry in schedule.ground_truth}
    oracle_affected: set[str] = set(reference_failure_nodes)
    for failed_node in reference_failure_nodes:
        oracle_affected.update(workflow.descendants(failed_node))

    counts: dict[str, int] = {}
    for entry in state.execution_log:
        if entry["status"] in {"completed", "failed", "invalid_output"}:
            counts[entry["task_id"]] = counts.get(entry["task_id"], 0) + 1
    extra_executions = sum(max(0, count - 1) for count in counts.values())
    unnecessary_reexecutions = sum(
        max(0, counts.get(task, 0) - 1)
        for task in workflow.tasks
        if task not in oracle_affected
    )

    ground_truth = schedule.ground_truth
    event_count = len(ground_truth)
    detected_event_count = sum(bool(entry["detected"]) for entry in ground_truth)
    missed_event_count = event_count - detected_event_count
    audit_events = state.audit_alert_events
    audit_tp = sum(bool(e["ground_truth_incorrect"]) for e in audit_events)
    audit_fp = len(audit_events) - audit_tp
    audit_incorrect_opportunities = sum(int(r["incorrect_sinks"]) for r in state.audit_round_summaries)
    audit_fn = max(0, audit_incorrect_opportunities - audit_tp)
    audit_precision = audit_tp / (audit_tp + audit_fp) if (audit_tp + audit_fp) else float("nan")
    audit_recall = audit_tp / (audit_tp + audit_fn) if (audit_tp + audit_fn) else float("nan")
    audit_f1 = (2 * audit_precision * audit_recall / (audit_precision + audit_recall)
                if audit_precision == audit_precision and audit_recall == audit_recall and (audit_precision + audit_recall) > 0
                else (0.0 if audit_precision == audit_precision and audit_recall == audit_recall else float("nan")))
    # Final workflow success is sink correctness; all-node correctness is reported
    # separately because a non-sink intermediate can be wrong without changing a sink.
    sink_records_valid = all(
        n in state.records and state.records[n].status == "completed" and state.records[n].valid
        for n in workflow.sinks()
    )
    final_success = int(not incorrect_sinks and sink_records_valid)

    return {
        "strategy": strategy,
        "seed": int(seed),
        "topology": "custom",
        "workflow_size": len(order),
        "final_success": final_success,
        "all_nodes_correct": int(all_correct),
        "incorrect_nodes_at_end": len(incorrect_nodes),
        "incorrect_sinks_at_end": len(incorrect_sinks),
        "total_cost": round(state.total_cost, 6),
        "task_executions": state.executions,
        "extra_task_executions": extra_executions,
        "unnecessary_reexecutions": unnecessary_reexecutions,
        "retries": state.retries,
        "restarts": state.restarts,
        "ground_truth_failures": event_count,
        "detected_events": detected_event_count,
        "missed_events": missed_event_count,
        "detection_recall": detected_event_count / event_count if event_count else 1.0,
        "audit_alert_events": len(audit_events),
        "audit_true_positive_alerts": audit_tp,
        "audit_false_positive_alerts": audit_fp,
        "audit_alert_precision": audit_precision,
        "audit_recall": audit_recall,
        "audit_f1": audit_f1,
        "audit_false_negative_sinks": audit_fn,
        "audit_rounds": len(state.audit_round_summaries),
        "final_incorrect_sinks": len(incorrect_sinks),
        "execution_log": state.execution_log,
    }
