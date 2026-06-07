r"""Propose-test-reject orchestration loop."""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from ..data import DataBundle
from ..pipeline import PipelineConfig, PipelineResult, run_pipeline

__all__ = ["AcceptanceCriteria", "CandidateLog", "propose_configs", "run_agent"]


@dataclass
class AcceptanceCriteria:
    """Thresholds a candidate must clear to be accepted (CLAUDE.md §7.1/§7.2)."""

    max_spearman: float = 0.8           # (i) curvature != correlation
    max_jaccard: float = 0.5            # (ii) low overlap with correlation ranking
    min_null_frac_sig: float = 0.05     # (iii) real higher-order structure
    require_degree_identity: bool = True  # (iv) plain Forman is a degree object
    beat_random_ic: bool = True         # OOS IC must exceed the random baseline

    def evaluate(self, result: PipelineResult) -> tuple[bool, list[str]]:
        c = result.cascade
        reasons: list[str] = []
        if not (c["spearman_F_vs_absrho"] < self.max_spearman):
            reasons.append(f"spearman {c['spearman_F_vs_absrho']:.2f} >= {self.max_spearman}")
        if not (c["topk_jaccard_vs_corr"] <= self.max_jaccard):
            reasons.append(f"jaccard {c['topk_jaccard_vs_corr']:.2f} > {self.max_jaccard}")
        if not (c["null_frac_significant"] >= self.min_null_frac_sig):
            reasons.append(f"null frac_sig {c['null_frac_significant']:.2f} < {self.min_null_frac_sig}")
        if self.require_degree_identity and not c["plain_is_degree_identity"]:
            reasons.append("plain Forman is not a degree identity (R^2<1) — graph may be reciprocal")
        if self.beat_random_ic:
            ic = result.ic_by_method["mean_ic"]
            curv_ic = ic.get("curvature(aug,directed)", float("nan"))
            rand_ic = ic.get("random", float("nan"))
            if not (curv_ic > rand_ic):
                reasons.append(f"curvature IC {curv_ic:.3f} <= random IC {rand_ic:.3f}")
        return (len(reasons) == 0), reasons


@dataclass
class CandidateLog:
    config: PipelineConfig
    accepted: bool
    reasons: list[str]
    cascade: dict
    ic_summary: dict


@dataclass
class AgentRun:
    accepted: list[CandidateLog] = field(default_factory=list)
    rejected: list[CandidateLog] = field(default_factory=list)

    @property
    def n_total(self) -> int:
        return len(self.accepted) + len(self.rejected)


def propose_configs(
    curvature_columns=("F_augmented", "F_weighted"),
    thresholds=(0.85, 0.90),
    triangle_modes=("common",),
    selection_ks=(15,),
    seed: int = 0,
) -> list[PipelineConfig]:
    """Enumerate candidate pipeline configurations (the curvature-percentile / Δκ /
    convention sweep of §5). An LLM proposer can replace this with adaptive search."""
    configs = []
    for col, thr, tmode, k in itertools.product(
        curvature_columns, thresholds, triangle_modes, selection_ks
    ):
        configs.append(PipelineConfig(
            curvature_column=col, threshold=thr, triangle_mode=tmode,
            selection_k=k, seed=seed,
        ))
    return configs


def run_agent(
    bundle: DataBundle,
    configs: list[PipelineConfig] | None = None,
    criteria: AcceptanceCriteria | None = None,
) -> AgentRun:
    """Run propose -> test -> reject over candidate configs; log every decision."""
    configs = configs or propose_configs()
    criteria = criteria or AcceptanceCriteria()
    run = AgentRun()
    for cfg in configs:
        result = run_pipeline(bundle, cfg)
        ok, reasons = criteria.evaluate(result)
        entry = CandidateLog(
            config=cfg, accepted=ok, reasons=reasons, cascade=result.cascade,
            ic_summary=result.ic_by_method["mean_ic"].to_dict(),
        )
        (run.accepted if ok else run.rejected).append(entry)
    return run
