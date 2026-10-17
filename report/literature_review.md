# Focused Literature Review and Research Positioning

**Review date:** 17 October 2026  
**Scope:** LLM multi-agent reliability, failure attribution/recovery, and graph-based workflow fault tolerance.  
**Status:** Focused scoping review, not a systematic review. Search terms and selected sources are listed below; a complete PhD-level novelty claim requires reading the full papers and extending the search.

## Search scope

Search themes included: `LLM multi-agent faulty agents resilience`, `multi-agent failure debugging replay recovery`, `error propagation failure attribution LLM agents`, `agent dependency execution graph`, `DAG workflow fault tolerance selective recomputation`, and `LLM multi-agent collaboration benchmark`.

## Selected verified sources

### 1. Huang et al. (2025), *On the Resilience of LLM-Based Multi-Agent Collaboration with Faulty Agents*

- Venue: International Conference on Machine Learning (ICML 2025), Proceedings of Machine Learning Research, volume 267.
- Link: https://proceedings.mlr.press/v267/huang25ay.html
- Code: https://github.com/CUHK-ARISE/MAS-Resilience
- Relevance: Studies how faulty agents affect multi-agent collaboration structures and evaluates challenge/review mechanisms for resilience.
- Overlap: Controlled fault injection, downstream task reliability, and recovery from faulty outputs are already established topics.
- Implication: This project must not claim novelty for fault injection or for adding a reviewer alone.

### 2. Wang et al. (2025), *AgentDropout: Dynamic Agent Elimination for Token-Efficient and High-Performance LLM-Based Multi-Agent Collaboration*

- Venue: ACL 2025, Long Papers.
- Link: https://aclanthology.org/2025.acl-long.1170/
- Code: https://github.com/wangzx1219/AgentDropout
- Relevance: Studies removing redundant agents and communication links to improve communication efficiency and task performance.
- Overlap: Efficiency of multi-agent coordination and communication is already an active research area.
- Implication: Cost measurements should be explicit and should not be confused with communication efficiency when this simulator primarily measures task-execution cost.

### 3. Zhu et al. (2025), *MultiAgentBench: Evaluating the Collaboration and Competition of LLM Agents*

- Venue: ACL 2025, Long Papers.
- Link: https://aclanthology.org/2025.acl-long.421/
- Code: https://github.com/ulab-uiuc/MARBLE
- Relevance: Benchmarks collaboration/competition and compares coordination protocols and task completion.
- Overlap: Multi-agent evaluation, topology comparisons, and reproducible benchmarks are established practices.
- Implication: A useful research report should state why its task model and metrics differ from broader LLM-agent benchmarks.

### 4. Luan et al. (2026), *Repair or Resample? Rethinking Failure Debugging in LLM Multi-Agent Systems* (preprint)

- Link: https://arxiv.org/abs/2608.25920
- Relevance: Introduces SymTrace/SymFail for controlled replay and studies failure repair versus rerunning/resampling trajectories.
- Overlap: Execution traces, replay, selective intervention, and recovery evaluation directly overlap with the broad motivation here.
- Implication: A graph-based selective-recovery prototype should be positioned as a small simulator study, not as the first work on replay or repair.

### 5. Liao et al. (2026), *Error-Propagation Modeling for Failure Attribution in LLM-Based Multi-Agent Systems* (preprint)

- Link: https://arxiv.org/abs/2610.11600
- Relevance: Explicitly models error propagation and seeks decisive error attribution in LLM-based multi-agent execution.
- Overlap: Failure propagation and identifying causal sources are already being studied.
- Implication: This project does not implement a novel source-attribution algorithm. It models dependency-driven propagation and evaluates recovery policies under controlled assumptions.

### 6. Li et al. (2026), *Localizing Emergent Failures in Agentic AI: Recovering Minimal Repair Families via Counterfactual Replay* (preprint)

- Link: https://arxiv.org/abs/2608.29228
- Relevance: Uses dependency graphs and counterfactual replay to investigate sets of events whose repair restores success.
- Overlap: Graph-constrained replay and selective repair are highly relevant to the proposed problem.
- Implication: The simple ancestor-cone recovery implemented here is a baseline/prototype, not a claim to outperform graph-constrained counterfactual methods.

### 7. Graph workflow fault tolerance

Task-graph checkpointing and selective recovery predate LLM agents. For example, a survey on checkpointing discusses workflows represented as DAGs and the trade-offs of checkpoint placement and recovery:

- *A survey on checkpointing strategies: Should we always checkpoint à la Young/Daly?* ScienceDirect: https://www.sciencedirect.com/science/article/pii/S0167739X24003777

- Relevance: Dependency-aware recomputation is a classical workflow reliability concept. Applying a DAG model to agent workflows is not, by itself, a novel contribution.

## Research gap: what can and cannot be claimed

### Not defensible as a novelty claim

The following are already established concepts and should not be claimed as novel on their own:

- Injecting errors into agents or task outputs.
- Observing downstream failure propagation.
- Recording execution traces.
- Retrying failed tasks.
- Re-running only part of a workflow.
- Using a dependency graph to identify affected tasks.
- Comparing workflow topologies or measuring execution cost.

### Candidate contribution for this prototype

The project provides a transparent, configurable simulator for comparing four recovery baselines under matched task/attempt-specific fault schedules, with explicit task-level detection coverage, noisy sink audits, graph-based cache invalidation, and separate measurements of final sink correctness, all-node correctness, execution cost, and unnecessary recomputation.

This is a **candidate empirical contribution**, not yet a validated novel algorithm. The value at this stage is reproducibility and a controlled experimental harness. A stronger paper would need to identify a precise limitation in existing recovery methods and propose a differentiated algorithm or benchmark design, then validate it on realistic LLM-agent traces or tasks.

## Recommended next literature-review steps

1. Read the methods and limitations sections of all six LLM-agent papers above.
2. Compare the exact recovery scope: source-localized repair, sink symptom-based repair, trajectory replay, or full restart.
3. Compare what each method assumes about failure detection and access to ground truth.
4. Compare metrics: task success, repair success, number of calls, tokens, latency, and collateral recomputation.
5. Add at least one classical DAG workflow recovery source and one real LLM-agent benchmark to the comparison table.
6. Only then state a narrow gap. Do not use the phrase "no prior work" unless a systematic search supports it.

## Suggested comparison table

| Work | Setting | Failure information | Recovery/intervention | Cost metric | Main overlap |
|---|---|---|---|---|---|
| Huang et al. (2025) | LLM multi-agent collaboration | Injected faulty agents/outputs | Challenge/reviewer mechanisms and structure comparisons | Task performance/resilience | Fault injection and resilience |
| AgentDropout (2025) | LLM multi-agent collaboration | Communication/agent utility | Remove redundant agents/links | Token use and performance | Efficiency |
| MultiAgentBench (2025) | LLM multi-agent benchmark | Task/milestone outcomes | Compare coordination protocols | Task/collaboration scores | Evaluation methodology |
| Luan et al. (2026) | LLM MAS execution traces | Trace/replay anchors and annotated failures | Replay and symptom-driven intervention | Repair/replay metrics | Failure debugging and recovery |
| Liao et al. (2026) | LLM MAS traces | Propagation-aware candidates | Failure attribution/counterfactual verification | Attribution metrics | Error propagation |
| Li et al. (2026) | Agentic AI trajectories | Dependency graph and counterfactual replay | Graph-constrained joint replay | Replay calls and repair accuracy | Graph-guided repair |
| This project | Synthetic DAG simulator | Controlled fault schedule; configurable task and sink detection | Full restart, failed-task retry, ancestor-cone recovery | Simulated task cost and recomputation | Controlled comparison of simple recovery baselines |
