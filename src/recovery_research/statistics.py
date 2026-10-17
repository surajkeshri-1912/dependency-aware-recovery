"""Reproducible uncertainty summaries and paired policy comparisons."""
from __future__ import annotations
import numpy as np
import pandas as pd


def bootstrap_mean_ci(values, seed: int = 2026, n_boot: int = 4000, confidence: float = 0.95) -> tuple[float, float]:
    """Percentile bootstrap CI for a mean; returns NaNs for an empty sample."""
    x = np.asarray(list(values), dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return float("nan"), float("nan")
    if len(x) == 1:
        return float(x[0]), float(x[0])
    rng = np.random.default_rng(seed)
    draws = rng.choice(x, size=(n_boot, len(x)), replace=True).mean(axis=1)
    alpha = (1.0 - confidence) / 2.0
    lo, hi = np.quantile(draws, [alpha, 1.0 - alpha])
    return float(lo), float(hi)


def paired_policy_comparisons(
    frame: pd.DataFrame,
    candidate: str = "dependency_aware",
    baseline: str = "full_restart",
    seed: int = 2026,
    n_boot: int = 4000,
) -> pd.DataFrame:
    """Compare candidate minus baseline within matched experimental conditions/seeds."""
    if frame.empty or "strategy" not in frame:
        return pd.DataFrame()
    key_candidates = [
        "topology", "workflow_size", "failure_kind", "failure_probability",
        "detection_coverage", "audit_sensitivity", "audit_false_positive_rate",
        "validation_enabled", "seed",
    ]
    keys = [c for c in key_candidates if c in frame.columns]
    metrics = [m for m in ("final_success", "total_cost", "unnecessary_reexecutions", "task_executions") if m in frame.columns]
    a = frame[frame.strategy == candidate][keys + metrics].copy()
    b = frame[frame.strategy == baseline][keys + metrics].copy()
    if a.empty or b.empty:
        return pd.DataFrame()
    merged = a.merge(b, on=keys, how="inner", suffixes=("_candidate", "_baseline"), validate="one_to_one")
    if merged.empty:
        return pd.DataFrame()
    group_keys = [k for k in keys if k != "seed"]
    rows = []
    grouped = merged.groupby(group_keys, dropna=False, sort=True) if group_keys else [((), merged)]
    for group_key, group in grouped:
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        base_info = dict(zip(group_keys, group_key))
        for metric in metrics:
            diffs = group[f"{metric}_candidate"].astype(float).to_numpy() - group[f"{metric}_baseline"].astype(float).to_numpy()
            lo, hi = bootstrap_mean_ci(diffs, seed=seed + len(rows), n_boot=n_boot)
            row = dict(base_info)
            row.update({
                "candidate": candidate, "baseline": baseline, "metric": metric,
                "matched_trials": int(len(diffs)), "mean_paired_difference_candidate_minus_baseline": float(np.mean(diffs)),
                "ci95_low": lo, "ci95_high": hi,
            })
            rows.append(row)
    return pd.DataFrame(rows)


def pooled_paired_comparisons(
    frame: pd.DataFrame,
    candidate: str = "dependency_aware",
    baseline: str = "full_restart",
    seed: int = 2026,
    n_boot: int = 4000,
) -> pd.DataFrame:
    """Exploratory pooled paired differences over all matched condition/seed rows.

    This intentionally pools across the configured grid. Its confidence intervals
    are descriptive and can be too narrow if condition combinations are treated as
    independent; condition-specific comparisons should remain the primary analysis.
    """
    keys = [c for c in [
        "topology", "workflow_size", "failure_kind", "failure_probability",
        "detection_coverage", "audit_sensitivity", "audit_false_positive_rate",
        "validation_enabled", "seed",
    ] if c in frame.columns]
    metrics = [m for m in ("final_success", "total_cost", "unnecessary_reexecutions", "task_executions") if m in frame.columns]
    candidate_rows = frame[frame.strategy == candidate][keys + metrics]
    baseline_rows = frame[frame.strategy == baseline][keys + metrics]
    if candidate_rows.empty or baseline_rows.empty:
        return pd.DataFrame()
    matched = candidate_rows.merge(baseline_rows, on=keys, how="inner", suffixes=("_candidate", "_baseline"), validate="one_to_one")
    if matched.empty:
        return pd.DataFrame()
    scopes: list[tuple[str, pd.DataFrame]] = [("all_conditions_pooled", matched)]
    if "failure_kind" in matched.columns:
        scopes.extend((f"failure_kind={kind}", group) for kind, group in matched.groupby("failure_kind", sort=True))
    rows = []
    for scope_index, (scope, group) in enumerate(scopes):
        for metric in metrics:
            differences = group[f"{metric}_candidate"].astype(float).to_numpy() - group[f"{metric}_baseline"].astype(float).to_numpy()
            lo, hi = bootstrap_mean_ci(differences, seed=seed + scope_index * 100 + len(rows), n_boot=n_boot)
            rows.append({
                "scope": scope,
                "candidate": candidate,
                "baseline": baseline,
                "metric": metric,
                "matched_trial_condition_pairs": int(len(differences)),
                "mean_paired_difference_candidate_minus_baseline": float(np.mean(differences)),
                "ci95_low_exploratory": lo,
                "ci95_high_exploratory": hi,
                "interpretation_note": "Descriptive bootstrap over matched trial-condition rows; not a formal significance test.",
            })
    return pd.DataFrame(rows)
