"""Deterministic DAG task simulator with hidden correctness labels and noisy audits."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import random

from .workflow import Workflow
from .failure_injection import FailureSchedule


@dataclass
class TaskRecord:
    task_id: str
    status: str
    output: Any = None
    # `valid` means safe to consume according to information visible to the policy;
    # an undetected corruption can therefore have valid=True but be incorrect.
    valid: bool = False
    cost: float = 0.0
    failure_kind: str | None = None
    detected: bool = False


@dataclass
class RunState:
    records: dict[str, TaskRecord] = field(default_factory=dict)
    execution_log: list[dict] = field(default_factory=list)
    total_cost: float = 0.0
    executions: int = 0
    retries: int = 0
    restarts: int = 0
    detected_failures: list[str] = field(default_factory=list)
    audit_alert_events: list[dict] = field(default_factory=list)
    audit_round_summaries: list[dict] = field(default_factory=list)


class Simulator:
    def __init__(self, workflow: Workflow, schedule: FailureSchedule, validation_enabled: bool = True):
        self.workflow = workflow
        self.schedule = schedule
        self.validation_enabled = validation_enabled

    @staticmethod
    def _base_value(task_id: str, inputs: dict[str, Any]) -> int:
        """Stable task function whose outputs depend on all declared inputs."""
        if not inputs:
            return sum(ord(c) for c in task_id)
        return sum(
            int(hashlib.sha256(str(inputs[dep]).encode("utf-8")).hexdigest()[:8], 16) % 997
            for dep in sorted(inputs)
        ) + sum(ord(c) for c in task_id)

    def reference_outputs(self) -> dict[str, int]:
        """Clean reference used only by audit/evaluation, never directly by policies."""
        reference: dict[str, int] = {}
        for task_id in self.workflow.topological_order():
            inputs = {dep: reference[dep] for dep in self.workflow.tasks[task_id].dependencies}
            reference[task_id] = self._base_value(task_id, inputs)
        return reference

    def execute_task(self, task_id: str, state: RunState, retry_number: int = 0, phase: str = "initial") -> TaskRecord:
        spec = self.workflow.tasks[task_id]
        missing_or_invalid = [
            dep for dep in spec.dependencies
            if dep not in state.records or not state.records[dep].valid or state.records[dep].status != "completed"
        ]
        if missing_or_invalid:
            raise RuntimeError(f"Cannot execute {task_id}: invalid/missing dependencies {missing_or_invalid}")

        inputs = {dep: state.records[dep].output for dep in spec.dependencies}
        kind, detected = self.schedule.sample(task_id, validation_enabled=self.validation_enabled)
        state.executions += 1
        state.total_cost += float(spec.cost)
        record = TaskRecord(task_id, "completed", cost=float(spec.cost), valid=True)

        if kind in {"transient", "persistent"}:
            record.status = "failed"
            record.failure_kind = kind if detected else None
            record.detected = detected
            record.valid = False
            record.output = None
        else:
            value = self._base_value(task_id, inputs)
            record.output = value
            if kind == "corruption":
                record.output = value + 99991
                record.failure_kind = "corruption" if detected else None
                record.detected = detected
                if detected:
                    record.status = "invalid_output"
                    record.valid = False

        state.records[task_id] = record
        state.execution_log.append({
            "task_id": task_id,
            "status": record.status,
            "observed_failure_kind": record.failure_kind,
            "detected": bool(record.detected),
            "cost": float(spec.cost),
            "retry_number": int(retry_number),
            "phase": phase,
            "inputs": repr(inputs),
            "output": repr(record.output),
        })
        if record.detected:
            state.detected_failures.append(task_id)
        return record

    def evaluate_correctness(self, state: RunState) -> tuple[bool, list[str], list[str]]:
        """Return ground-truth correctness for scoring only, not recovery decisions."""
        reference = self.reference_outputs()
        incorrect = []
        for node in self.workflow.topological_order():
            rec = state.records.get(node)
            if rec is None or rec.status != "completed" or rec.output != reference[node]:
                incorrect.append(node)
        sinks = [n for n in self.workflow.topological_order() if self.workflow.graph.out_degree(n) == 0]
        incorrect_sinks = [n for n in sinks if n in incorrect]
        return not incorrect, incorrect, incorrect_sinks

    def audit_sinks(
        self,
        state: RunState,
        seed: int,
        audit_round: int,
        sensitivity: float = 1.0,
        false_positive_rate: float = 0.0,
    ) -> list[str]:
        """Simulate a noisy sink validator; only alerts are exposed to the policy.

        Internally the simulator uses clean outputs to model validator sensitivity and
        false-positive rate. The returned sink IDs are the only audit observations the
        recovery policy receives. This is an explicit simulator assumption, not a
        claim that real tasks have an oracle.
        """
        if not 0 <= sensitivity <= 1 or not 0 <= false_positive_rate <= 1:
            raise ValueError("Audit sensitivity and false-positive rate must be in [0, 1]")
        _, _, incorrect_sinks = self.evaluate_correctness(state)
        incorrect_set = set(incorrect_sinks)
        alerts: list[str] = []
        sinks = sorted(n for n in self.workflow.graph.nodes if self.workflow.graph.out_degree(n) == 0)
        true_positive = 0
        false_positive = 0
        for sink in sinks:
            key = f"audit:{seed}:{audit_round}:{sink}".encode("utf-8")
            audit_seed = int.from_bytes(hashlib.sha256(key).digest()[:8], "big")
            rng = random.Random(audit_seed)
            if sink in incorrect_set:
                alert = rng.random() < sensitivity
            else:
                alert = rng.random() < false_positive_rate
            if alert:
                alerts.append(sink)
                is_true_positive = sink in incorrect_set
                true_positive += int(is_true_positive)
                false_positive += int(not is_true_positive)
                state.audit_alert_events.append({
                    "sink_id": sink,
                    "audit_round": audit_round,
                    # Labels are logged for evaluator analysis, not returned to policy.
                    "ground_truth_incorrect": is_true_positive,
                })
        state.audit_round_summaries.append({
            "audit_round": audit_round,
            "sink_opportunities": len(sinks),
            "incorrect_sinks": len(incorrect_set),
            "alerts": len(alerts),
            "true_positive_alerts": true_positive,
            "false_positive_alerts": false_positive,
            "false_negative_sinks": len(incorrect_set) - true_positive,
        })
        return alerts
