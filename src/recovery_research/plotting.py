"""Plots generated from saved raw experimental data, never hard-coded results."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def create_plots(results_csv: str | Path, output_dir: str | Path) -> list[Path]:
    source = Path(results_csv)
    if source.is_dir():
        source = source / "raw_results.csv"
    if not source.exists():
        raise FileNotFoundError(f"Could not find raw result CSV: {source}")
    frame = pd.read_csv(source)
    if frame.empty:
        raise ValueError("Cannot plot an empty result file")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []

    def save(fig, name: str) -> None:
        path = out / name
        fig.tight_layout()
        fig.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        created.append(path)

    # For overview plots, explicitly average across remaining conditions; detailed
    # condition-specific values remain available in aggregated_metrics.csv.
    if "failure_probability" in frame.columns:
        group = frame.groupby(["failure_probability", "strategy"], as_index=False)["final_success"].mean()
        fig, ax = plt.subplots(figsize=(8, 5))
        for strategy, data in group.groupby("strategy"):
            data = data.sort_values("failure_probability")
            ax.plot(data["failure_probability"], data["final_success"], marker="o", label=strategy)
        ax.set(title="Final task success by injected failure probability", xlabel="Configured failure probability", ylabel="Final success rate (mean across other conditions)", ylim=(-0.03, 1.03))
        ax.legend()
        ax.grid(True, alpha=0.25)
        save(fig, "success_by_failure_probability.png")

    if "topology" in frame.columns:
        group = frame.groupby(["topology", "strategy"], as_index=False)["total_cost"].mean()
        pivot = group.pivot(index="topology", columns="strategy", values="total_cost")
        fig, ax = plt.subplots(figsize=(9, 5))
        pivot.plot(kind="bar", ax=ax)
        ax.set(title="Mean simulated execution cost by topology", xlabel="Workflow topology", ylabel="Mean simulated cost (averaged across other conditions)")
        ax.tick_params(axis="x", rotation=20)
        ax.legend(title="Strategy")
        ax.grid(True, axis="y", alpha=0.25)
        save(fig, "cost_by_topology.png")

    if "unnecessary_reexecutions" in frame.columns:
        group = frame.groupby("strategy", as_index=False)["unnecessary_reexecutions"].mean().sort_values("strategy")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(group["strategy"], group["unnecessary_reexecutions"])
        ax.set(title="Mean unnecessary re-executions", xlabel="Recovery strategy", ylabel="Mean count per trial (oracle-scored; see limitations)")
        ax.tick_params(axis="x", rotation=20)
        ax.grid(True, axis="y", alpha=0.25)
        save(fig, "unnecessary_reexecutions.png")

    if "audit_sensitivity" in frame.columns:
        group = frame.groupby(["audit_sensitivity", "strategy"], as_index=False)["final_success"].mean()
        fig, ax = plt.subplots(figsize=(8, 5))
        for strategy, data in group.groupby("strategy"):
            data = data.sort_values("audit_sensitivity")
            ax.plot(data["audit_sensitivity"], data["final_success"], marker="o", label=strategy)
        ax.set(title="Final success under different sink-audit sensitivities", xlabel="Audit sensitivity", ylabel="Final success rate (mean across other conditions)", ylim=(-0.03, 1.03))
        ax.legend()
        ax.grid(True, alpha=0.25)
        save(fig, "success_by_audit_sensitivity.png")

    if "failure_kind" in frame.columns:
        group = frame.groupby(["failure_kind", "strategy"], as_index=False)["total_cost"].mean()
        pivot = group.pivot(index="failure_kind", columns="strategy", values="total_cost")
        fig, ax = plt.subplots(figsize=(8, 5))
        pivot.plot(kind="bar", ax=ax)
        ax.set(title="Mean simulated cost by failure type", xlabel="Failure type", ylabel="Mean simulated cost (averaged across other conditions)")
        ax.tick_params(axis="x", rotation=0)
        ax.legend(title="Strategy")
        ax.grid(True, axis="y", alpha=0.25)
        save(fig, "cost_by_failure_type.png")

    return created
