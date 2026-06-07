"""End-to-end pipeline + agent integration tests on synthetic data."""

from cllm.agent import AcceptanceCriteria, propose_configs, run_agent
from cllm.data import DataBundle, load_synthetic
from cllm.pipeline import PipelineConfig, run_pipeline


def _bundle():
    return load_synthetic(n_assets=40, n_periods=1500, n_sectors=4,
                          n_lead_lag_pairs=8, lead_lag_strength=0.6, seed=0)


def test_databundle_aligns_sectors():
    b = _bundle()
    assert isinstance(b, DataBundle)
    assert list(b.sectors.index) == list(b.returns.columns)


def test_pipeline_runs_end_to_end():
    result = run_pipeline(_bundle(), PipelineConfig(threshold=0.88, selection_k=12, null_iters=40))
    # graph built
    assert result.graph.number_of_edges() > 0
    # all four curvature objects present
    assert {"F_plain", "F_weighted", "F_augmented", "ollivier"}.issubset(result.curvature.columns)
    # cascade computed with the key diagnostics
    assert result.cascade["plain_is_degree_identity"] in (True, False)
    assert result.cascade["augmented_R2"] <= 1.0
    # IC table has every benchmark method and finite numbers
    methods = set(result.ic_by_method.index)
    assert {"curvature(aug,directed)", "correlation", "cointegration", "random"}.issubset(methods)
    assert result.ic_by_method["mean_ic"].notna().any()


def test_pipeline_plain_forman_degree_identity_flag():
    # on the (non-reciprocal) lead-lag graph, plain Forman must be a degree identity
    result = run_pipeline(_bundle(), PipelineConfig(null_iters=30))
    assert result.cascade["plain_forman_R2"] > 0.999
    assert result.cascade["plain_is_degree_identity"]


def test_agent_logs_accept_and_reject():
    bundle = _bundle()
    configs = propose_configs(curvature_columns=("F_augmented",), thresholds=(0.88,),
                              selection_ks=(12,))
    # an impossible criterion forces a reject, proving the loop records reasons
    strict = AcceptanceCriteria(max_spearman=-1.0)
    run = run_agent(bundle, configs=configs, criteria=strict)
    assert run.n_total == 1
    assert len(run.rejected) == 1
    assert run.rejected[0].reasons  # non-empty reason list
