# Troubleshooting

## `ModuleNotFoundError: recovery_research`

Install the project in the active environment:

```bash
python -m pip install -e .
```

If the environment has no network access but all dependencies are already installed, try `python -m pip install --no-build-isolation -e .`. Alternatively, run from the repository root with `PYTHONPATH=src` (macOS/Linux) or `$env:PYTHONPATH='src'` (PowerShell).

## Dependency installation fails

Use Python 3.11 or newer and check internet access. Install `requirements.txt` inside the virtual environment. Do not install packages globally unless you intentionally want to.

## `FileExistsError` when running an experiment

The CLI avoids silently overwriting `raw_results.csv` and `aggregated_metrics.csv`. Pick a new output directory, or explicitly pass `--overwrite` if you intend to replace those files.

## No plot appears

Use the CLI `analyze` command and pass the directory containing `raw_results.csv` or the CSV path itself. Plots are saved as PNG files; they are not opened in a GUI.

## Why do two strategies have different failures?

The fault schedule is deterministic for each `(seed, task ID, attempt index)`, but strategies can execute different tasks and different numbers of attempts. More executions can therefore expose a policy to additional task-attempt fault opportunities. This is part of the stated simulation model and a threat to simplistic pooled comparisons.

## Why does selective recovery sometimes rerun many tasks?

The policy sees a sink-level symptom, not the true faulty source. It conservatively recomputes the ancestor cone and invalidates descendants of recomputed nodes. If a shared ancestor feeds multiple branches, those branches must be recomputed to avoid stale cached outputs. A disconnected component can remain cached.

## Why is audit precision blank?

When no audit alerts occur, precision is mathematically undefined because there are no positive predictions. The project leaves it missing instead of incorrectly reporting 1.0.
