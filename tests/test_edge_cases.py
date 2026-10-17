from recovery_research.workflow import make_workflow
from recovery_research.failure_injection import FailureEvent
from recovery_research.recovery import run_strategy

def test_persistent_failure_exhausts_retries_without_crash():
    w = make_workflow("linear", 4)
    event = FailureEvent("persistent", 1.0, 1.0, 100)
    result = run_strategy(w, event, 7, "dependency_aware", max_retries=1)
    assert result["final_success"] == 0
