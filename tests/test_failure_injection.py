import pytest
from recovery_research.failure_injection import FailureEvent, FailureSchedule


def test_seeded_schedule_reproducible():
    event = FailureEvent("transient", 1.0, 1.0, 1)
    a, b = FailureSchedule(42, event), FailureSchedule(42, event)
    assert a.sample("A") == b.sample("A")


def test_invalid_probability_rejected():
    with pytest.raises(ValueError):
        FailureEvent("transient", 2.0)


def test_targeted_failure_does_not_affect_other_tasks():
    event = FailureEvent("corruption", 1.0, 0.0, 1, ("A",))
    schedule = FailureSchedule(3, event)
    assert schedule.sample("B") == (None, False)
    assert schedule.sample("A")[0] == "corruption"


def test_persistent_failure_occurs_on_every_attempt():
    schedule = FailureSchedule(7, FailureEvent("persistent", 0.0, 1.0, 1, ("A",)))
    assert schedule.sample("A")[0] == "persistent"
    assert schedule.sample("A")[0] == "persistent"
    assert schedule.sample("A")[0] == "persistent"


def test_corruption_detection_coverage_is_applied_to_validator():
    event = FailureEvent("corruption", 1.0, 0.0, 1, ("A",))
    schedule = FailureSchedule(3, event)
    kind, detected = schedule.sample("A", validation_enabled=True)
    assert kind == "corruption"
    assert detected is False
    assert schedule.ground_truth[-1]["detected"] is False


def test_execution_exception_is_runtime_observable():
    schedule = FailureSchedule(3, FailureEvent("transient", 1.0, 0.0, 1, ("A",)))
    kind, detected = schedule.sample("A")
    assert kind == "transient"
    assert detected is True
