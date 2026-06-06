r"""Structural validation cascade (CLAUDE.md §7.1) — the methodological contribution.

Proves curvature is not a re-skin of correlation / degree / sector:

(i)   Spearman rank corr between F(e) and |rho_ij| across edges  -> must be < 0.8.
(ii)  Top-K Jaccard overlap of curvature-ranked vs correlation-ranked pairs -> small.
(iii) Degree-preserving configuration-model null (Maslov-Sneppen) -> per-edge
      z-score of triangle embeddedness; |z| > 2 = real higher-order structure.
(iv)  Residual orthogonalization: regress F on degrees (+ |rho|); the residual is
      the isolated topological signal. Plain Forman -> R^2 = 1 (degree identity).

Plus: Benjamini-Hochberg multiplicity control, a time-ordered train/val/test
split, and bootstrap stability of curvature rankings.
"""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

__all__ = [
    "spearman_curvature_vs_corr",
    "topk_jaccard",
    "config_model_zscores",
    "residual_orthogonalization",
    "benjamini_hochberg",
    "train_val_test_split",
    "bootstrap_curvature_stability",
]


# (i) ---------------------------------------------------------------------- #
def spearman_curvature_vs_corr(curvature: pd.Series, abs_corr: pd.Series) -> float:
    """Spearman rank correlation between curvature and |rho| across edges.

    Aligns on the shared index (edge keys). A value well below 0.8 supports the
    claim that curvature is not a monotone re-encoding of correlation strength.
    """
    aligned = pd.concat([curvature.rename("curv"), abs_corr.rename("rho")], axis=1).dropna()
    if len(aligned) < 3:
        return float("nan")
    rho, _ = spearmanr(aligned["curv"], aligned["rho"])
    return float(rho)


# (ii) --------------------------------------------------------------------- #
def topk_jaccard(rank_a: pd.Series, rank_b: pd.Series, k: int | float) -> float:
    """Top-K Jaccard overlap between two rankings (smaller index value = ranked
    first; pass curvature ascending so most-negative is "top"). ``k`` may be an
    int count or a fraction in (0,1]."""
    n = min(len(rank_a), len(rank_b))
    kk = int(np.ceil(k * n)) if 0 < k <= 1 else int(k)
    kk = max(1, min(kk, n))
    top_a = set(rank_a.nsmallest(kk).index)
    top_b = set(rank_b.nsmallest(kk).index)
    union = top_a | top_b
    return len(top_a & top_b) / len(union) if union else 0.0


# (iii) -------------------------------------------------------------------- #
def _common_neighbors(UG: nx.Graph, u, v) -> int:
    return len((set(UG.neighbors(u)) & set(UG.neighbors(v))) - {u, v})


@dataclass
class NullResult:
    zscores: pd.Series          # per observed edge
    frac_significant: float     # fraction with |z| > 2
    n_null: int


def config_model_zscores(
    G: nx.Graph | nx.DiGraph,
    n_null: int = 200,
    swap_mult: int = 10,
    seed: int | None = 0,
) -> NullResult:
    """Maslov-Sneppen degree-preserving null on triangle embeddedness.

    The plain Forman term is fixed by degree, so the *higher-order* content lives
    in the triangle (common-neighbour) count. We rewire the undirected projection
    while preserving the degree sequence (``double_edge_swap``) and, for each
    observed edge's endpoint pair, build the null distribution of its
    common-neighbour count. ``z = (obs - mean_null) / std_null``; ``|z| > 2`` means
    the pair's triangle embeddedness is not explained by degree alone.
    """
    rng = np.random.default_rng(seed)
    UG = G.to_undirected() if G.is_directed() else G
    obs_edges = list(UG.edges())
    obs_cn = {e: _common_neighbors(UG, *e) for e in obs_edges}

    null_vals: dict[tuple, list[int]] = {e: [] for e in obs_edges}
    n_edges = UG.number_of_edges()
    for _ in range(n_null):
        H = UG.copy()
        if n_edges >= 2 and UG.number_of_nodes() >= 4:
            try:
                nx.double_edge_swap(
                    H, nswap=swap_mult * n_edges, max_tries=swap_mult * n_edges * 20,
                    seed=int(rng.integers(0, 2**31 - 1)),
                )
            except nx.NetworkXError:
                pass  # too few swappable edges; H stays = UG (conservative)
        for e in obs_edges:
            null_vals[e].append(_common_neighbors(H, *e))

    z = {}
    for e in obs_edges:
        arr = np.asarray(null_vals[e], dtype=float)
        sd = arr.std(ddof=1) if arr.size > 1 else 0.0
        z[e] = (obs_cn[e] - arr.mean()) / sd if sd > 0 else 0.0
    zs = pd.Series(z, name="z")
    frac_sig = float((zs.abs() > 2).mean()) if len(zs) else 0.0
    return NullResult(zscores=zs, frac_significant=frac_sig, n_null=n_null)


# (iv) --------------------------------------------------------------------- #
@dataclass
class ResidualResult:
    residuals: pd.Series
    r_squared: float
    coefficients: dict

    @property
    def is_degree_identity(self) -> bool:
        """True when curvature is (near) perfectly explained by the regressors —
        the diagnostic that plain Forman is a degree object (R^2 ~ 1)."""
        return self.r_squared > 0.999


def residual_orthogonalization(
    curvature: pd.Series,
    features: pd.DataFrame,
) -> ResidualResult:
    """Regress curvature on degree (+ |rho|) features; residual = isolated signal.

    ``features`` columns are typically ``deg_in_src``, ``deg_out_dst``, ``abs_rho``.
    For plain Forman the fit is exact (R^2 = 1) and the residual is ~0 by
    construction; for the augmented/weighted variants the residual carries the
    higher-order signal.
    """
    df = pd.concat([curvature.rename("y"), features], axis=1).dropna()
    y = df["y"].to_numpy(dtype=float)
    X = df.drop(columns="y").to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(design, y, rcond=None)
    fitted = design @ beta
    resid = y - fitted
    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    coefs = dict(zip(["intercept", *features.columns], beta))
    return ResidualResult(
        residuals=pd.Series(resid, index=df.index, name="residual"),
        r_squared=float(r2),
        coefficients=coefs,
    )


# Multiplicity ------------------------------------------------------------- #
def benjamini_hochberg(pvalues: pd.Series, alpha: float = 0.05) -> pd.DataFrame:
    """Benjamini-Hochberg FDR control. Returns a frame with ``reject`` and
    ``p_adj`` (BH-adjusted p-values), index-aligned to the input."""
    from statsmodels.stats.multitest import multipletests

    p = pvalues.dropna()
    reject, p_adj, _, _ = multipletests(p.to_numpy(), alpha=alpha, method="fdr_bh")
    return pd.DataFrame({"reject": reject, "p_adj": p_adj}, index=p.index)


# Splits ------------------------------------------------------------------- #
def train_val_test_split(
    n_periods: int, fracs: tuple[float, float, float] = (0.6, 0.2, 0.2)
):
    """Time-ordered (no shuffle) contiguous split -> (train_idx, val_idx, test_idx).

    The §5 operating point is locked on ``val`` and evaluated once on ``test`` —
    never tuned on the test set."""
    if abs(sum(fracs) - 1.0) > 1e-9:
        raise ValueError("fracs must sum to 1")
    n_tr = int(round(fracs[0] * n_periods))
    n_va = int(round(fracs[1] * n_periods))
    tr = np.arange(0, n_tr)
    va = np.arange(n_tr, n_tr + n_va)
    te = np.arange(n_tr + n_va, n_periods)
    return tr, va, te


# Bootstrap ranking stability --------------------------------------------- #
def bootstrap_curvature_stability(
    returns: pd.DataFrame,
    curvature_fn,
    n_boot: int = 25,
    block: int = 20,
    seed: int | None = 0,
) -> dict:
    """Block-bootstrap the time series; report stability of the curvature ranking.

    ``curvature_fn(returns) -> pd.Series`` maps a returns panel to a per-edge
    curvature Series (e.g. build graph -> augmented Forman). We report the mean
    pairwise Spearman correlation of the curvature rankings across bootstrap
    resamples (rank stability under lead-lag estimation noise; CLAUDE.md §7.1).
    """
    rng = np.random.default_rng(seed)
    T = len(returns)
    n_blocks = int(np.ceil(T / block))
    series_list: list[pd.Series] = []
    for _ in range(n_boot):
        starts = rng.integers(0, max(1, T - block), size=n_blocks)
        idx = np.concatenate([np.arange(s, min(s + block, T)) for s in starts])[:T]
        boot = returns.iloc[idx].reset_index(drop=True)
        series_list.append(curvature_fn(boot))

    # pairwise Spearman over the shared edge set
    corrs = []
    for i in range(len(series_list)):
        for j in range(i + 1, len(series_list)):
            a, b = series_list[i], series_list[j]
            shared = a.index.intersection(b.index)
            if len(shared) >= 3:
                rho, _ = spearmanr(a.loc[shared], b.loc[shared])
                if np.isfinite(rho):
                    corrs.append(rho)
    return {
        "mean_rank_stability": float(np.mean(corrs)) if corrs else float("nan"),
        "n_comparisons": len(corrs),
        "n_boot": n_boot,
    }
