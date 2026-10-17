import pytest
from recovery_research.workflow import Workflow, TaskSpec, make_workflow


def test_topological_order_and_descendants():
    w = make_workflow("parallel_merge", 5)
    order = w.topological_order()
    assert order[0] == "T00"
    assert "T04" in w.descendants("T00")


def test_missing_dependency_rejected():
    with pytest.raises(ValueError):
        Workflow({"A": TaskSpec("A", ("MISSING",))})


def test_cycle_rejected():
    with pytest.raises(ValueError):
        Workflow({"A": TaskSpec("A", ("B",)), "B": TaskSpec("B", ("A",))})


def test_bad_cost_rejected():
    with pytest.raises(ValueError):
        Workflow({"A": TaskSpec("A", cost=0)})


def test_duplicate_dependency_rejected():
    with pytest.raises(ValueError):
        TaskSpec("A", ("B", "B"))


def test_parallel_merge_two_nodes_has_dependency():
    workflow = make_workflow("parallel_merge", 2)
    assert workflow.tasks["T01"].dependencies == ("T00",)
