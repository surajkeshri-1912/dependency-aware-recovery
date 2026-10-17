# SOP Project Summary (Use Only If It Accurately Reflects Your Work)

## Short description

**Dependency-Aware Failure Recovery in Multi-Agent Workflows:** a reproducible simulator-based study comparing no recovery, full workflow restart, failed-task retry, and dependency-aware recovery under controlled execution failures and silent output corruption.

## Draft SOP paragraph

“My practical work on multi-agent systems motivated me to investigate reliability beyond successful execution. I developed a simulator-based experimental framework for dependency-aware failure recovery in task workflows represented as directed acyclic graphs. The framework models transient and persistent execution failures, silent output corruption, downstream error propagation, and imperfect sink-level auditing. I compared full-workflow restart, failed-task retry, and a dependency-aware recovery policy, measuring final sink correctness, simulated execution cost, and unnecessary recomputation across multiple workflow topologies and detection settings. This preliminary study helped me understand the trade-offs between recovery reliability and execution overhead, while highlighting the limitations of synthetic tasks and oracle-assisted validation. I would like to extend this work toward realistic LLM-agent traces, stronger failure-localization methods, and recovery policies that can be evaluated under imperfect verification.”

## Before including this paragraph

- Make sure you personally understand the source code, experimental conditions, and definitions of all metrics.
- Replace broad descriptions with specific contributions you implemented and can demonstrate.
- Do not call the simulator an LLM experiment; no live LLM is used in the core benchmark.
- Do not claim novelty or publication-quality findings based on this prototype alone.
- If you did not personally execute the code on your own computer, do not imply that you did. State that the project was developed and tested in the available environment, then independently reproduce the results before submitting.
