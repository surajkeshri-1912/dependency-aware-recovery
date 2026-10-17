"""Workflow DAG definitions and deterministic topology generators."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import networkx as nx


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    dependencies: tuple[str, ...] = ()
    cost: float = 1.0
    operation: str = "combine"

    def __post_init__(self) -> None:
        if not self.task_id or not self.task_id.strip():
            raise ValueError("Task IDs must be non-empty strings")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError(f"Duplicate dependencies for task {self.task_id!r}")
        if not math.isfinite(self.cost) or self.cost <= 0:
            raise ValueError(f"Task cost must be finite and positive: {self.task_id}")


@dataclass
class Workflow:
    tasks: dict[str, TaskSpec]
    graph: nx.DiGraph = field(init=False)

    def __post_init__(self) -> None:
        if not self.tasks:
            raise ValueError("A workflow must contain at least one task")
        self.graph = nx.DiGraph()
        for task_id, spec in self.tasks.items():
            if task_id != spec.task_id:
                raise ValueError(f"Task key {task_id!r} does not match spec id {spec.task_id!r}")
            self.graph.add_node(task_id)
        for task_id, spec in self.tasks.items():
            for dep in spec.dependencies:
                if dep not in self.tasks:
                    raise ValueError(f"Task {task_id!r} depends on missing task {dep!r}")
                self.graph.add_edge(dep, task_id)
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Workflow dependencies must form a directed acyclic graph (DAG)")

    def topological_order(self) -> list[str]:
        return list(nx.lexicographical_topological_sort(self.graph, key=str))

    def descendants(self, task_id: str) -> set[str]:
        if task_id not in self.tasks:
            raise KeyError(task_id)
        return nx.descendants(self.graph, task_id)

    def ancestors(self, task_id: str) -> set[str]:
        if task_id not in self.tasks:
            raise KeyError(task_id)
        return nx.ancestors(self.graph, task_id)

    def roots(self) -> list[str]:
        return sorted(n for n, degree in self.graph.in_degree() if degree == 0)

    def sinks(self) -> list[str]:
        return sorted(n for n, degree in self.graph.out_degree() if degree == 0)

    @classmethod
    def from_edges(cls, costs: dict[str, float], edges: list[tuple[str, str]]) -> "Workflow":
        deps = {node: [] for node in costs}
        for parent, child in edges:
            if child not in deps or parent not in deps:
                raise ValueError(f"Edge references unknown node: {(parent, child)}")
            deps[child].append(parent)
        return cls({n: TaskSpec(n, tuple(sorted(deps[n])), costs[n]) for n in costs})


def make_workflow(family: str, size: int = 8) -> Workflow:
    """Create deterministic linear, branching, parallel-merge, or layered DAGs."""
    if size < 2:
        raise ValueError("Workflow size must be at least 2")
    nodes = [f"T{i:02d}" for i in range(size)]
    edges: list[tuple[str, str]] = []
    if family == "linear":
        edges = [(nodes[i], nodes[i + 1]) for i in range(size - 1)]
    elif family == "branching":
        for i in range(1, size):
            edges.append((nodes[(i - 1) // 2], nodes[i]))
    elif family == "parallel_merge":
        if size == 2:
            edges = [(nodes[0], nodes[1])]
        else:
            edges.extend((nodes[0], nodes[i]) for i in range(1, size - 1))
            edges.extend((nodes[i], nodes[-1]) for i in range(1, size - 1))
    elif family == "layered":
        for i in range(1, size):
            edges.append((nodes[i - 1], nodes[i]))
            if i >= 2 and i % 2 == 0:
                edges.append((nodes[i - 2], nodes[i]))
    else:
        raise ValueError(f"Unknown workflow family: {family}")
    costs = {node: float(1 + (i % 3)) for i, node in enumerate(nodes)}
    return Workflow.from_edges(costs, edges)
