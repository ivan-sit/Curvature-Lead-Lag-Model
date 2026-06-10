"""The agentic orchestrator must genuinely discriminate — not rubber-stamp."""

from cllm.data import load_synthetic
from cllm.orchestrator import AcceptRules, Orchestrator, default_grid, propose


def test_propose_enumerates_grid():
    grid = default_grid()
    cands = propose(grid)
    expected = (len(grid["residualize"]) * len(grid["threshold"])
                * len(grid["triangle_mode"]) * len(grid["curvature"]))
    assert len(cands) == expected
    assert all("residualize" in c.config and "curvature" in c.config for c in cands)


def test_plain_forman_is_always_rejected_as_degree_baseline():
    # plain Forman is an exact function of degree -> R2-on-degree == 1 -> must be
    # rejected by the critic at every residualization/threshold. The augmented
    # object is the one that can pass. This proves the loop is not rubber-stamping.
    bundle = load_synthetic(n_assets=40, n_periods=1500, n_lead_lag_pairs=6, seed=1)
    orch = Orchestrator(rules=AcceptRules(), lags=(1, 2, 3), selection_k=15, null_iters=0)
    result = orch.run(bundle)

    plain = [d for d in result["decisions"] if d.config["curvature"] == "F_plain"]
    assert plain, "expected plain-Forman candidates"
    assert all(not d.accepted for d in plain), "plain Forman must be rejected (degree baseline)"
    assert all(any("degree" in r for r in d.reasons) for d in plain)

    # the log is auditable and complete
    assert result["n_candidates"] == len(result["decisions"])
    assert result["n_accepted"] + result["n_rejected"] == result["n_candidates"]
    md = orch.findings_markdown(result)
    assert "propose → test → reject" in md and "reject" in md
