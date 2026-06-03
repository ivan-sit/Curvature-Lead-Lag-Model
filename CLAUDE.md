# CLAUDE.md — Project Specification & Build Guide

> **Read this entire file before writing any code.** It encodes the full research
> intention, every technical decision and its rationale, the exact equations, the
> data sources, the evaluation harness, and the known risks. The details here were
> hard-won through extended literature review and an advisor meeting; do not
> silently deviate from them.

---

## 1. One-paragraph project intention

Build an autonomous, agentic pipeline that applies **discrete Forman-Ricci
curvature to directed lead-lag networks of US equities** to select statistical
arbitrage pairs that are **structurally distinct** from those surfaced by
correlation-based methods. The scientific claim is *structural*, not merely
profit-based: negatively-curved edges in the directed lead-lag network mark
structurally isolated pairs (bridges between market regions) that
correlation/undirected-curvature methods overlook. The deliverable is a Math 285J
project (UCLA, advisor **Prof. Mihai Cucuringu**) explicitly engineered to become
an **ICAIF 2026 paper** (submission deadline **August 2, 2026**). The class is
infrastructure; the paper is the goal. Target: ~30% methodology, ~70% empirical.

---

## 2. Academic context (do not lose this framing)

- **Course:** UCLA Math 285J — Agentic AI for Autonomous Research in Quantitative Finance.
- **Advisor:** Prof. Mihai Cucuringu (`mihai@math.ucla.edu`). On board with ICAIF-first scoping.
- **Conference target:** ICAIF 2026, Milan, Nov 14–17. Paper deadline **Aug 2, 2026**.
  8-page ACM `sigconf` two-column, double-blind, no rebuttal. arXiv preprint allowed.
- **Closest prior work / baseline:** Sandhu, Georgiou, Tannenbaum (2016),
  *Science Advances* — used **Ollivier-Ricci on undirected correlation networks**
  for systemic risk; explicitly flagged directed extension + stat-arb as open
  problems. They validated **structurally only** (vs entropy/path/diameter), never
  against raw correlation, and never ran a backtest. This precedent is load-bearing.
- **Weber connection:** Cucuringu is a personal friend of **Melanie Weber**
  (Harvard). Her line-graph curvature clustering (Tian-Lubberts-Weber, JMLR 2025)
  and AFRC curvature gap (Fesser-Weber-Lambiotte, J. Phys. Complexity 2024) are
  central. An email to Weber (via Cucuringu intro) is planned — send only AFTER
  first empirical results exist.

---

## 3. Core hypothesis (the falsifiable claim)

> Negatively-curved edges in directed lead-lag networks mark structurally isolated
> pairs — bridges connecting otherwise separated regions of the market — that
> correlation- and undirected-curvature methods overlook. Lead-lag asymmetry
> encodes information the symmetric correlation graph destroys; discrete curvature
> on the *directed* graph captures it.

The empirical claim to support/refute: *AFRC-selected pairs on the directed
lead-lag network are (a) structurally distinct from correlation-selected pairs
under the validation cascade, and (b) achieve PnL performance under AlphaMark at
least competitive with correlation/cointegration/random baselines.*

---

## 4. Exact mathematics (use these forms verbatim; cite as shown)

### 4.1 Weighted Forman-Ricci (PRIMARY — use this, not the unweighted toy)

General weighted edge formula, Samal et al. 2018 Eq. (7) / Sreejith et al. 2016:

```
F(e) = w_e * [ w_v1/w_e + w_v2/w_e
               - Σ_{e_v1 ~ e}  w_v1 / sqrt(w_e * w_{e_v1})
               - Σ_{e_v2 ~ e}  w_v2 / sqrt(w_e * w_{e_v2}) ]
```

where `e_v ~ e` denotes edges incident to vertex `v` excluding `e` itself.

**Unweighted special case** (all weights = 1), Samal et al. 2018 Eq. (8):
`F(e) = 4 - deg(v1) - deg(v2)`. This is a TOY used for pedagogy only — DO NOT
use the unweighted form on real data; it treats weak and strong correlations
identically, which is incorrect.

### 4.2 Directed restriction (Sreejith-Jost-Saucan-Samal 2016, arXiv:1605.04662, Eq. 4)

For a directed edge `e = v1 → v2`: in the neighbor sums, include **only incoming
edges at v1** and **only outgoing edges at v2**, excluding self-loops and the
reverse edge `v2 → v1`. Unweighted directed reduction:
`F(e) = 4 - deg_in(v1) - deg_out(v2)`.

### 4.3 Augmented Forman-Ricci (AFRC) — second variant

Samal et al. 2018 Eq. (10), unweighted: `F#(e) = F(e) + 3m`, where `m` = number of
triangles containing `e`. The `+3` per triangle comes from Forman's general
`-d + 6` rule for filling a `d`-cycle as a 2-face (triangle d=3 → +3; quad d=4
→ +2; pentagon d=5 → +1; hexagon → 0; larger → negative). Restrict augmentation
to triangles only (Serrano de Haro Iváñez 2022) — pentagon-augmented variants
distort non-quasiconvex networks. Directed counterpart: count only triangles
compatible with the orientation of `e`.

Triangle count for edge `e=(u,v)`: `m(e) = |N(u) ∩ N(v)|` (common neighbors).
`O(min(deg u, deg v))` per edge. For directed: report both (a) strict cyclic
triangles and (b) common-neighbor count ignoring direction — the convention is
unsettled in the literature; let the data pick.

### 4.4 Edge weights (METHODOLOGICAL DECISION — primary choice)

Primary weighting = **Bennett-Cucuringu-Reinert signed lead-lag statistic**:

```
w_{i→j} = ρ_ij(τ*) − ρ_ji(τ*)
```

where `τ*` is the lag at which the cross-correlation peaks. Asymmetric by
construction — this is WHY the graph is directed; symmetric correlation would
destroy the directional information.

Robustness-check weighting = Gower-Mantegna distance `sqrt(2(1 − ρ_ij))`
(Sandhu's undirected metric). Vertex weights `w_v = 1` initially, with sensitivity
analysis on weighted alternatives.

### 4.5 AFRC curvature gap (community-separability diagnostic)

```
Δκ = (κ_intra − κ_inter) / σ_pooled
```

**Critical caveat (Fesser-Weber-Lambiotte tree-SBM result):** the gap COLLAPSES
for tree-like / triangle-sparse communities — community detection then fails
*regardless* of planted structure. There is **no universal numeric Δκ
threshold**; it is relative and structure-dependent. See §8 Risk #1.

---

## 5. The line-graph trick (core conceptual mechanism)

Pairs are EDGES of the lead-lag network `G`. To cluster/select pairs with
node-based machinery, build the **line graph** `L(G)`:

- Every edge of `G` → a node of `L(G)`.
- Two `L(G)` nodes are adjacent iff their `G`-edges share a vertex.

Curvature on `G` answers "is this pair isolated in **stock-space**?". Curvature on
`L(G)` answers "is this pair isolated relative to **other pairs**?". Stat-arb
selection is fundamentally a pair-space question → operate on `L(G)`. Reference:
Tian, Lubberts, Weber, JMLR 2025 (line-graph curvature flow for community
detection, incl. mixed-membership).

**Selection rule (the actual answer to "which pairs do we trade"):** select pairs
that are **isolated in stock-space (low F on G)** but sit in **coherent communities
on L(G)** (sufficient Δκ). First property → uncrowdedness; second → coherent risk
story / not noise. Cutoffs are NOT hardcoded — sweep a grid
(curvature percentile ∈ {5,10,20%}, Δκ threshold ∈ {1,1.5,2}) and pick the
operating region where pairs pass the validation cascade (esp. config-model null
+ low Jaccard vs correlation). Report sensitivity across the sweep.

---

## 6. Pipeline architecture (6 agents)

1. **Network Constructor** — ingest WRDS returns; estimate pairwise lead-lag at
   lag τ (Bennett-Cucuringu-Reinert); build + sparsify the directed graph.
2. **Curvature Module** — compute weighted `F(e)` and augmented `F#(e)` per
   directed edge.
3. **Hypothesis Generator** — build `L(G)`; run AFRC curvature flow to cluster
   pairs; propose candidate pair sets under the §5 selection rule + threshold sweep.
4. **Structural Validator** — run the validation cascade (§7).
5. **Evaluation Agent** — convert selected pairs → position signals → benchmark
   PnL via **AlphaMark**.
6. **Critic / Orchestrator** — review outputs, flag inconsistencies, request
   reruns, draft findings. (LLM agent — this is the "agentic" requirement.)

---

## 7. Validation & evaluation (two SEPARATE things — keep both)

### 7.1 Structural validation cascade (the methodological contribution — KEEP)

Proves curvature ≠ a re-skin of correlation/degree. AlphaMark does NOT do this.

- **(i)** Spearman rank corr between `F(e)` and `|ρ_ij|` across edges — must be < 0.8.
- **(ii)** Top-K Jaccard overlap between curvature-ranked and correlation-ranked
  pairs — want small (target ~0.1–0.5).
- **(iii)** Degree-preserving configuration-model null (Maslov-Sneppen rewiring,
  ~1000 graphs); z-score per edge; `|z| > 2` = real higher-order structure.
- **(iv)** Residual orthogonalization: regress `F` on `deg_in(v1)`,
  `deg_out(v2)`, `|ρ_ij|`; use residual as isolated topological signal.
  `F# − F = 3m` isolates the triangle term directly.
- Plus: AFRC curvature gap Δκ, rolling-window stability, fraction of
  negatively-curved edges crossing community boundaries (GICS sectors).

### 7.2 Performance evaluation — AlphaMark (PnL harness)

`github.com/mcucurin/alphamark`. Standardized PnL benchmarking pipeline used by
Cucuringu's group. Inputs: financial time series + user-defined predictive
signals. Outputs: standardized risk-adjusted stats (Sharpe, drawdown, turnover,
hit rate) as an automated PDF report. Guide (Overleaf):
`https://www.overleaf.com/read/vkdtddmdmfxh#ffc936`. Contacts:
`dhruvpatel97@g.ucla.edu`, `lihaoran@g.ucla.edu`.

**Integration task:** Stage 3 outputs selected pairs. Must convert these into the
signal format AlphaMark expects (verify exact schema from the Guide / `main.py` /
`pipeline/` before coding the adapter — likely a per-asset per-timestamp position
or score matrix). Benchmark curvature-selected pairs vs correlation-distance,
correlation-matrix clustering, cointegration, and random-selection baselines on
**identical AlphaMark settings**.

> NOTE: We do NOT build a bespoke backtest, and we no longer use the old
> IC / OU-half-life / cointegration "signal-quality proxies" — AlphaMark
> supersedes them. The structural cascade (§7.1) stays.

---

## 8. Trading logic (how the portfolio actually works)

Curvature is a **selection** signal, NOT a directional one. Do **not** go
"long high-curvature stocks / short low-curvature." Two-stage:

1. Curvature + line-graph clustering → choose WHICH pairs enter the universe.
2. Within each selected pair, standard **mean-reversion**: form spread
   `s_t = r1(t) − β·r2(t)` (β from rolling cointegration fit); enter when
   `|z(s_t)| > 2` (long laggard / short leader); exit on reversion to mean.
3. Aggregate all pair positions → net per-stock position vector → feed to
   AlphaMark. Market-neutral by construction (each pair is dollar-balanced).
4. Diversify: take ~one representative pair per `L(G)` community to avoid
   loading the book on a single latent factor.

---

## 9. Data (WRDS — all sources institutional via UCLA)

| Phase | Source | Detail | Purpose |
|---|---|---|---|
| 1 | CRSP (WRDS) | Daily close-to-close, S&P 500, ~10 yrs, point-in-time index membership, delisting data | Pipeline validation; main results |
| 1 | Compustat (WRDS) | GICS sector classifications | Community-boundary tests (cascade) |
| 2 | TAQ (WRDS) | Open-to-close 30-min bars, exclude overnight | Intraday signal (lead-lag washed out daily) |
| 3 (stretch) | TAQ (WRDS) | 5-min bars, S&P 100, tick data | Hayashi-Yoshida estimator, async trading |

**Survivorship bias is mandatory to handle** — use CRSP point-in-time membership,
not today's S&P 500 constituents. Overnight returns are excluded in Phase 2
because they are macro-news-dominated, not microstructural.

---

## 10. Open risks & questions (address EARLY)

1. **Triangle sparsity / tree-SBM failure (HIGHEST PRIORITY).**
   Fesser-Weber-Lambiotte prove the curvature gap collapses for triangle-sparse
   communities → AFRC community detection can fail by their own theorem.
   **Week-1 diagnostic:** measure within-community triangle density of the real
   lead-lag networks. If triangle-sparse, the whole `L(G)`/AFRC approach is at
   risk and must be reconsidered before building on it. Do this BEFORE the full
   pipeline.
2. **Directed line graph.** Tian-Lubberts-Weber framework is *undirected*. Need a
   directed `L(G)` construction that preserves the graph↔line-graph curvature
   relationships. Possibly open — candidate Weber question / possible theory
   contribution.
3. **Directed AFRC curvature gap.** SBM recovery guarantees are undirected-only.
   A directed-SBM analog may be genuinely novel — potential centerpiece theory
   result for the ICAIF paper. Ask Weber.
4. **Directed triangle convention.** Unsettled in literature; implement both
   strict-cyclic and common-neighbor counts; report both.
5. **AlphaMark signal schema.** Confirm exact input format before writing the
   adapter (read the Guide + `pipeline/` first).

---

## 11. Build order (do NOT skip the early diagnostic)

1. **WRDS data pull** — CRSP daily S&P 500 (~10 yrs) + Compustat GICS. Parquet.
   Handle survivorship via point-in-time membership.
2. **Lead-lag network construction** — cross-correlation at lags τ ∈ {1,2,3,5}
   days; Bennett-Cucuringu-Reinert signed statistic as edge weight; sparsify.
3. **TRIANGLE-DENSITY DIAGNOSTIC (Risk #1)** — measure within-sector triangle
   density. Decision gate: if triangle-sparse, escalate before continuing.
4. **Curvature module** — weighted `F` (directed) + augmented `F#`. Validate
   against `GraphRicciCurvature` package on undirected toy first; the directed
   weighted form likely needs a custom implementation.
5. **Line graph + AFRC clustering** — build `L(G)`; AFRC curvature flow;
   communities; Δκ.
6. **Validation cascade** — the four tests + Δκ + stability + sector-bridge frac.
   Threshold sweep here.
7. **AlphaMark integration** — signal adapter; baselines; benchmark.
8. **Critic/orchestrator agent** — wrap the pipeline in the LLM-agent loop
   (course's "agentic" requirement).
9. **Write-up** — long-form 285J report = unconstrained draft → compress to
   8-page ACM `sigconf` for ICAIF.

---

## 12. Full citation list (use these exact references)

| Role | Citation |
|---|---|
| Stat-arb seminal (distance/correlation) | Gatev, Goetzmann, Rouwenhorst (2006) *Rev. Financial Studies* 19(3):797–827 |
| Stat-arb review | Krauss (2017) *J. Economic Surveys* 31(2):513–545 |
| Advisor's correlation-clustering stat arb | Cartea, Cucuringu, Jin (2023) ICAIF '23 |
| Lead-lag detection framework (advisor) | Bennett, Cucuringu, Reinert (2022) *Machine Learning* 111(12):4497–4538, arXiv:2201.08283 |
| HF async estimator | Hayashi, Yoshida (2005) *Bernoulli* 11(2):359–379 |
| Curvature-finance baseline | Sandhu, Georgiou, Tannenbaum (2016) *Science Advances* 2(5):e1501495 |
| Ollivier-Ricci (contrast) | Ollivier (2009) *J. Functional Analysis* 256(3):810–864 |
| Forman-Ricci original | Forman (2003) *Disc. & Comp. Geometry* 29(3):323–374 |
| Forman on networks | Sreejith, Mohanraj, Jost, Saucan, Samal (2016) *J. Stat. Mech.* P063206, arXiv:1603.00386 |
| Both variants, Eqs. 7/8/9/10 | Samal et al. (2018) *Sci. Rep.* 8:8650, arXiv:1712.07600 |
| Directed Forman, Eq. 4 | Sreejith, Jost, Saucan, Samal (2016) arXiv:1605.04662 |
| Augmentation hierarchy / triangle truncation | Serrano de Haro Iváñez (2022) arXiv:2212.01357 |
| Line-graph curvature clustering | Tian, Lubberts, Weber (2025) *JMLR* 26(52):1–67, arXiv:2307.10155 |
| AFRC + curvature gap + tree-SBM | Fesser, Serrano de Haro Iváñez, Devriendt, Weber, Lambiotte (2024) *J. Phys. Complexity* 5:035010, arXiv:2306.06474 |

Weber code: `github.com/Weber-GeoML` (AFRC_Community_Detection, Local_Curvature_Profile, kappakit).
Standard reference impl for Forman/Ollivier: `GraphRicciCurvature` (PyPI) — directed weighted
augmented variant likely needs a custom extension on top.

---

## 13. Hard rules / do-nots

- DO use weighted directed Forman on real data. DO NOT use the unweighted
  `4 − deg − deg` toy form for results.
- DO keep the structural validation cascade. It is the methodological
  contribution; AlphaMark does not replace it.
- DO run the triangle-density diagnostic before building the L(G)/AFRC stack.
- DO NOT build a bespoke backtest; AlphaMark is the PnL harness.
- DO NOT hardcode a Δκ threshold or a curvature percentile — sweep and report
  sensitivity; the cascade picks the operating point.
- DO NOT add more "agentic" infrastructure to chase ICAIF keywords — the graph/
  time-series contribution carries the paper; the agent loop is the wrapper.
- DO treat the directed line-graph construction and directed AFRC gap as open
  questions — flag, do not silently assume the undirected results transfer.
- Edge weight = Bennett-Cucuringu-Reinert signed lead-lag statistic
  `ρ_ij(τ*) − ρ_ji(τ*)`, NOT symmetric correlation.

---

## 14. Success definition

- **285J floor:** working pipeline, clean methodology, structural cascade run on
  real CRSP data, results documented.
- **ICAIF ceiling:** decisive empirical result that AFRC-selected pairs are
  structurally distinct AND competitive under AlphaMark vs baselines, ideally
  plus one novel theory bit (directed AFRC gap / directed line-graph result).
  8-page ACM `sigconf`, submitted Aug 2 2026.

The work over the next ~3 months determines which one this becomes. Optimize for
the empirical result; let it decide whether to submit.
