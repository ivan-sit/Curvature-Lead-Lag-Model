"""Critic / orchestrator agent (CLAUDE.md §6 agent 6).

A genuine propose -> test -> reject loop: propose curvature/threshold variants,
run the pipeline, accept only those passing the validation cascade + beating the
random baseline on OOS IC, and LOG every accepted/rejected candidate with reasons.
Deterministic today; an LLM proposer can be dropped into ``propose_configs`` later.
"""

from .orchestrator import AcceptanceCriteria, CandidateLog, propose_configs, run_agent

__all__ = ["AcceptanceCriteria", "CandidateLog", "propose_configs", "run_agent"]
