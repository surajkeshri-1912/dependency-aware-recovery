"""Deterministic, task/attempt-specific fault injection for workflow experiments.

Execution exceptions (transient/persistent) are visible to the runtime. The
``detection_probability`` parameter applies to corrupted outputs, which can be
silently accepted when the task-level validator misses them.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random


@dataclass(frozen=True)
class FailureEvent:
    kind: str  # transient, persistent, corruption
    probability: float
    detection_probability: float = 1.0
    max_occurrences: int = 1
    target_tasks: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.kind not in {"transient", "persistent", "corruption"}:
            raise ValueError(f"Unsupported failure kind: {self.kind}")
        for name, value in (("probability", self.probability), ("detection_probability", self.detection_probability)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.max_occurrences < 1:
            raise ValueError("max_occurrences must be >= 1")
        if self.target_tasks is not None and (not self.target_tasks or any(not t for t in self.target_tasks)):
            raise ValueError("target_tasks must be None or a non-empty tuple of task IDs")


class FailureSchedule:
    """Reproducible fault source.

    The random stream is derived from (seed, task ID, attempt index), so the same
    task-attempt receives the same injected event regardless of other tasks' order.
    For transient/corruption events, ``max_occurrences`` caps event count per task.
    A persistent fault occurs on every targeted attempt until the policy exhausts
    its retry budget; ``max_occurrences`` intentionally does not disable it.

    ``ground_truth`` is for evaluation only. Recovery policies must not inspect it.
    """

    def __init__(self, seed: int, event: FailureEvent):
        self.seed = int(seed)
        self.event = event
        self.invocations: dict[str, int] = {}
        self.occurrences: dict[str, int] = {}
        self.ground_truth: list[dict] = []

    def sample(self, task_id: str, validation_enabled: bool = True) -> tuple[str | None, bool]:
        attempt = self.invocations.get(task_id, 0)
        self.invocations[task_id] = attempt + 1
        if self.event.target_tasks is not None and task_id not in self.event.target_tasks:
            return None, False

        previous_occurrences = self.occurrences.get(task_id, 0)
        key = f"{self.seed}:{task_id}:{attempt}".encode("utf-8")
        sub_seed = int.from_bytes(hashlib.sha256(key).digest()[:8], "big")
        rng = random.Random(sub_seed)

        if self.event.kind == "persistent":
            occurs = True
        elif previous_occurrences >= self.event.max_occurrences:
            occurs = False
        else:
            occurs = rng.random() < self.event.probability

        if not occurs:
            return None, False

        self.occurrences[task_id] = previous_occurrences + 1
        if self.event.kind in {"transient", "persistent"}:
            # An execution exception is observable to the runtime.
            detected = True
        else:
            detected = validation_enabled and (rng.random() < self.event.detection_probability)

        self.ground_truth.append({
            "task_id": task_id,
            "kind": self.event.kind,
            "detected": bool(detected),
            "occurrence": previous_occurrences + 1,
            "attempt": attempt,
        })
        return self.event.kind, bool(detected)
