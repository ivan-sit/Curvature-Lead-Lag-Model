# CLAUDE.md — Project Specification & Build Guide (v2)

> **Read this entire file before writing any code.** It encodes the full research
> intention, every technical decision and its rationale, the exact equations, the
> data sources, the evaluation harness, and the known risks. The details here were
> hard-won through extended literature review and an advisor meeting; do not
> silently deviate from them.

---

## 0. v2 changelog — what changed and why

This v2 incorporates the **consolidated reviewer feedback (June 3, 2026)** — an
initial methodological review, a second-reviewer pass, and **Prof. Cucuringu's own
notes** (the two instructor-flagged items: factor/sector residualization, and
"use, don't just cite" the group's lead-lag work). The spec's framing has shifted
from "curvature for stat-arb PnL" to **"curvature as a predictor of out-of-sample
leader–lagger information flow."** Concretely:

1. **Plain directed Forman is a degree object by definition.**
   `F(e) = 4 − deg_in(v₁) − deg_out(v₂)` is an exact linear function of the two
   endpoint degrees, so the residualization test (§7.1.iv) gives R²=1 and a
   residual identically 0 for plain Forman — the "topological signal" is 0 *by
   construction*, and the Maslov–Sneppen null leaves it essentially invariant.
   → **Plain Forman is now a degree BASELINE only.** The main object is
   **weighted augmented directed Forman.** We compare **four curvature objects**
   (§4.6): plain (baseline), triangle-augmented `F#=F+3m`, weighted-augmented
   (main), and Ollivier-Ricci (robustness/stretch).
2. **Residualize returns BEFORE building the graph** (Cucuringu, load-bearing).
   On raw equity returns, market + sector factors dominate both the lead-lag graph
   and the curvature; a config-model null preserves degree but does NOT remove
   sector/factor effects, so the "topological signal" risks merely rediscovering
   GICS sectors and a reviewer can dismiss the whole result. → Build the network
   on **factor/sector-residualized returns** (§4.5, §6 Agent 1, §9).
3. **Primary metric is out-of-sample directional IC, not PnL.**
   Negative-curvature bridges are a *predictability* story (leader today → lagger
   tomorrow), so the headline metric is **OOS directional IC**. This is a *study*
   of predictive structure, not a trading system. Mean-reversion and PnL are
   **secondary/optional** (§7.2, §8). **AlphaMark is NOT a core deliverable** in
   v2 — it is an optional "if time permits" PnL appendix; the entire study stands
   without it (cf. Sandhu et al., who validated structurally only, no backtest).
4. **Baselines widened to test the actual hypotheses** (§7.2): add
   **undirected Forman on the symmetrized graph** and **Ollivier-Ricci** as
   *curvature-method* baselines — these directly isolate the contribution of
   (a) directedness and (b) the curvature notion, which is the real novelty over
   Sandhu et al.
5. **Statistical rigor** (§7.1): Benjamini–Hochberg multiplicity control, a strict
   **train/validate/test** split, pre-registered or swept top-K, and **bootstrap
   stability of curvature rankings** (distinct from rolling-window stability;
   targets lead-lag estimation noise).
6. **Agentic layer = a genuine propose→test→reject loop** (§6 Agent 6): the agent
   proposes curvature variants / thresholds / null models; a validator agent
   *rejects* those failing the cascade; every accepted/rejected candidate is
   logged. (This supersedes v1's "keep it a thin wrapper" line — still bounded,
   but substantive enough to earn the "autonomous discovery" framing.)
7. **Use, don't just cite, the group's lead-lag work** (Cucuringu): adopt the
   **Bennett–Cucuringu–Reinert** estimator + significance framework + directed-
   clustering view; group refs added to §12 ([G1]–[G7]).
8. **Scope reduced** (§11): Phase 1 = daily **or 30-min** S&P 500 *residual*
   returns; main method = weighted augmented directed Forman; main metric = OOS
   directional IC; stretch = Ollivier-Ricci on S&P 100 + intraday Hayashi-Yoshida.
9. **Verify the ICAIF deadline/page limit** on the official site before locking
   the timeline (v1's Aug 2, 2026 is to be confirmed).

The sharpened one-line claim (adopt as the spine of the paper):

> *Weighted augmented directed Forman curvature on **factor-residualized** lead-lag
> networks predicts **out-of-sample** leader–lagger information flow that
> correlation, degree, and undirected curvature miss.*

---

## 1. One-paragraph project intention

Build an autonomous, agentic pipeline that applies **discrete Forman-Ricci
curvature to directed lead-lag networks of US equities** — built on
**factor/sector-residualized returns** — to identify pairs whose
**directed predictability** (out-of-sample leader→lagger information flow) is
**structurally distinct** from what correlation-, degree-, and undirected-
curvature methods surface. The scientific claim is *structural and predictive*,
not PnL: negatively-curved edges in the directed lead-lag network mark
structurally isolated pairs (bridges between market regions) that carry
out-of-sample directional information correlation/undirected-curvature methods
overlook. This is a **study of predictive structure**, not (yet) a trading system.
The deliverable is a Math 285J project (UCLA, advisor **Prof. Mihai Cucuringu**)
explicitly engineered to become an **ICAIF 2026 paper** (deadline to be confirmed;
v1 assumed **August 2, 2026**). The class is infrastructure; the paper is the
goal. Target: ~30% methodology, ~70% empirical.

---

## 2. Academic context (do not lose this framing)

- **Course:** UCLA Math 285J — Agentic AI for Autonomous Research in Quantitative Finance.
- **Advisor:** Prof. Mihai Cucuringu (`mihai@math.ucla.edu`). On board with ICAIF-first scoping.
- **Conference target:** ICAIF 2026, Milan, Nov 14–17. Paper deadline **to be
  confirmed on the official ICAIF site** (v1 assumed Aug 2, 2026; reviewer notes
  submissions historically fall around mid-year). 8-page ACM `sigconf` two-column,
  double-blind, no rebuttal. arXiv preprint allowed. Journal version after (see §5,
  venue strategy).
- **Closest prior work / baseline:** Sandhu, Georgiou, Tannenbaum (2016),
  *Science Advances* — used **Ollivier-Ricci on undirected correlation networks**
  for systemic risk; explicitly flagged directed extension + stat-arb as open
  problems. They validated **structurally only** (vs entropy/path/diameter), never
  against raw correlation, and **never ran a backtest** — precedent that a
  structural + predictive (IC) study without a PnL backtest is publishable. The
  **directed-vs-undirected contrast is the real novelty over Sandhu.**
- **Weber connection:** Cucuringu is a personal friend of **Melanie Weber**
  (Harvard). Her line-graph curvature clustering (Tian-Lubberts-Weber, JMLR 2025)
  and AFRC curvature gap (Fesser-Weber-Lambiotte, J. Phys. Complexity 2024) are
  central. An email to Weber (via Cucuringu intro) is planned — send only AFTER
  first empirical results exist.

---

## 3. Core hypothesis (the falsifiable claim)

> Negatively-curved edges in directed lead-lag networks (built on factor-
> residualized returns) mark structurally isolated pairs — bridges connecting
> otherwise separated regions of the market — that carry out-of-sample
> leader→lagger predictive information which correlation-, degree-, and
> undirected-curvature methods overlook. Lead-lag asymmetry encodes information the
> symmetric correlation graph destroys; weighted augmented discrete curvature on
> the *directed* graph captures it.

The empirical claim to support/refute: *weighted-augmented-directed-Forman-selected
pairs on the factor-residualized directed lead-lag network are (a) structurally
distinct from correlation-, degree-, and undirected-curvature-selected pairs under
the validation cascade, and (b) achieve higher **out-of-sample directional IC**
than those baselines.* PnL (mean-reversion via AlphaMark) is an optional secondary
confirmation, not the claim.

---

## 4. Exact mathematics (use these forms verbatim; cite as shown)

### 4.1 Weighted Forman-Ricci (PRIMARY family — use weighted/augmented, not the unweighted toy)

General weighted edge formula, Samal et al. 2018 Eq. (7) / Sreejith et al. 2016:

```
F(e) = w_e * [ w_v1/w_e + w_v2/w_e
               - Σ_{e_v1 ~ e}  w_v1 / sqrt(w_e * w_{e_v1})
               - Σ_{e_v2 ~ e}  w_v2 / sqrt(w_e * w_{e_v2}) ]
```

where `e_v ~ e` denotes edges incident to vertex `v` excluding `e` itself.

**Unweighted special case** (all weights = 1), Samal et al. 2018 Eq. (8):
`F(e) = 4 - deg(v1) - deg(v2)`. **This is a DEGREE BASELINE, not a result.** It is
an exact linear function of the two endpoint degrees, so regressing it on degree
(§7.1.iv) returns R²=1 and a zero residual — by construction it carries no
higher-order topological signal, and the degree-preserving null leaves it
invariant. Report it ONLY as the baseline against which the weighted/augmented
variants must demonstrate added signal.

### 4.2 Directed restriction (Sreejith-Jost-Saucan-Samal 2016, arXiv:1605.04662, Eq. 4)

For a directed edge `e = v1 → v2`: in the neighbor sums, include **only incoming
edges at v1** and **only outgoing edges at v2**, excluding self-loops and the
reverse edge `v2 → v1`. Unweighted directed reduction:
`F(e) = 4 - deg_in(v1) - deg_out(v2)`. **Pin this exact equation** (Sreejith et al.
2016, directed) and include a worked toy example in an appendix.

### 4.3 Augmented Forman-Ricci (AFRC) — the higher-order variant that matters

Samal et al. 2018 Eq. (10), unweighted: `F#(e) = F(e) + 3m`, where `m` = number of
triangles containing `e`. Because `m` is **not** determined by the two endpoint
degrees, the residual after regressing `F#` on degree isolates **exactly `3m`** —
this is the genuinely higher-order signal, and the rewiring null now "has teeth."
The `+3` per triangle comes from Forman's general `-d + 6` rule for filling a
`d`-cycle as a 2-face (triangle d=3 → +3; quad d=4 → +2; pentagon d=5 → +1;
hexagon → 0; larger → negative). Restrict augmentation to triangles only
(Serrano de Haro Iváñez 2022) — pentagon-augmented variants distort
non-quasiconvex networks. Directed counterpart: count only triangles compatible
with the orientation of `e`.

Triangle count for edge `e=(u,v)`: `m(e) = |N(u) ∩ N(v)|` (common neighbors).
`O(min(deg u, deg v))` per edge. For directed: report both (a) strict cyclic
triangles and (b) common-neighbor count ignoring direction — the convention is
unsettled in the literature; let the data pick. **Report the full distribution of
`m`** and verify the augmentation is not degenerate (directed cyclic triangles are
sparse; `m` may be 0 on most edges at typical thresholds — see §10 Risk #1).

### 4.4 Edge weights (METHODOLOGICAL DECISION — primary choice)

Primary weighting = **Bennett-Cucuringu-Reinert signed lead-lag statistic**:

```
w_{i→j} = ρ_ij(τ*) − ρ_ji(τ*)
```

where `τ*` is the lag at which the cross-correlation peaks. Asymmetric by
construction — this is WHY the graph is directed; symmetric correlation would
destroy the directional information. **Adopt the BCR estimator and significance
framework directly** (do not re-derive a lead-lag estimator — see §12 [G1], [G3]).
Robustness-check weighting = Gower-Mantegna distance `sqrt(2(1 − ρ_ij))`
(Sandhu's undirected metric). Vertex weights `w_v = 1` initially, with sensitivity
analysis on weighted alternatives. **Propagate edge uncertainty** from the lead-lag
estimate into the curvature rankings (bootstrap, §7.1).

### 4.5 Factor/sector residualization (INSTRUCTOR REQUIREMENT — do this before §4.4)

Build the lead-lag graph on **residual returns**, not raw returns. Minimum: remove
the **market + sector** components; stronger: use **factor residuals from a
standard factor model** (e.g., market + size/value/momentum + GICS-sector dummies).
Rationale (Cucuringu): on raw returns, market/sector factors dominate both the
graph and the curvature, and the degree-preserving null does not remove them, so
the "topological signal" can be dismissed as sector structure. This is as
important as the degree-baseline issue. Report results on both raw and residualized
returns to show the signal survives residualization.

### 4.6 The four curvature objects to compare (ablation spine)

| Object | Definition | Role |
|---|---|---|
| Plain directed Forman | `4 − deg_in(v1) − deg_out(v2)` | **Degree baseline** (signal ≡ 0 after residualizing on degree) |
| Triangle-augmented | `F# = F + 3m` | Higher-order: residual isolates `3m`; null has teeth |
| **Weighted augmented directed Forman** | §4.1 weighted + §4.3 augmentation, directed (§4.2), BCR weights (§4.4) | **MAIN METHOD** |
| Ollivier-Ricci | Wasserstein transport between neighbor distributions | Robustness / stretch (what Sandhu used) |

This four-way comparison turns the degree weakness into a clean, convincing
ablation. Also include the **undirected Forman on the symmetrized graph** as a
baseline (§7.2) to isolate the contribution of directedness.

### 4.7 AFRC curvature gap (community-separability diagnostic)

```
Δκ = (κ_intra − κ_inter) / σ_pooled
```

**Critical caveat (Fesser-Weber-Lambiotte tree-SBM result):** the gap COLLAPSES
for tree-like / triangle-sparse communities — community detection then fails
*regardless* of planted structure. There is **no universal numeric Δκ
threshold**; it is relative and structure-dependent. See §10 Risk #1.

---

## 5. The line-graph trick (core conceptual mechanism)

Pairs are EDGES of the lead-lag network `G`. To cluster/select pairs with
node-based machinery, build the **line graph** `L(G)`:

- Every edge of `G` → a node of `L(G)`.
- Two `L(G)` nodes are adjacent iff their `G`-edges share a vertex.

Curvature on `G` answers "is this pair isolated in **stock-space**?". Curvature on
`L(G)` answers "is this pair isolated relative to **other pairs**?". Pair selection
is fundamentally a pair-space question → operate on `L(G)`. Reference:
Tian, Lubberts, Weber, JMLR 2025 (line-graph curvature flow for community
detection, incl. mixed-membership). **Directedness caveat:** the TLW framework is
undirected; the directed `L(G)` construction is an open problem (§10 Risk #2) —
start with the undirected reduction as the honest baseline, flag the directed
construction as the theory track.

**Selection rule (which pairs we study):** select pairs that are **isolated in
stock-space (low weighted-augmented F on G)** but sit in **coherent communities on
L(G)** (sufficient Δκ). First property → structural uncrowdedness; second →
coherent risk story / not noise. Cutoffs are NOT hardcoded — sweep a grid
(curvature percentile ∈ {5,10,20%}, Δκ threshold ∈ {1,1.5,2}) and **lock the
operating point on a validation split** (NOT on the test set — §7.1). Report
sensitivity across the sweep.

---

## 6. Pipeline architecture (6 agents)

1. **Network Constructor** — ingest WRDS returns; **residualize on market + sector
   / factor model (§4.5)**; estimate pairwise lead-lag at lag τ
   (Bennett-Cucuringu-Reinert); build + sparsify the directed graph.
   Specify estimator, τ-selection, thresholding/sparsification, signed/weighted,
   and edge-uncertainty propagation explicitly.
2. **Curvature Module** — compute the **four objects (§4.6)** per directed edge:
   plain (baseline), augmented `F#`, weighted-augmented (main), Ollivier-Ricci.
3. **Hypothesis Generator** — build `L(G)`; run AFRC curvature flow to cluster
   pairs; propose candidate pair sets under the §5 selection rule + threshold sweep.
4. **Structural Validator** — run the validation cascade (§7.1) with BH multiplicity
   control and a strict train/validate/test split.
5. **Evaluation Agent** — convert selected pairs → directional forecasts → measure
   **out-of-sample directional IC (PRIMARY, §7.2)**; optional secondary PnL via
   mean-reversion / AlphaMark.
6. **Critic / Orchestrator (the "agentic" requirement)** — a genuine
   **propose→test→reject loop**: propose curvature variants, thresholds, and null
   models; the validator rejects those failing the cascade; **log every accepted
   and rejected candidate signal with reasons.** This is what makes "autonomous
   discovery" credible rather than scripted wrapping.

---

## 7. Validation & evaluation (two SEPARATE things — keep both)

### 7.1 Structural validation cascade (the methodological contribution — KEEP)

Proves curvature ≠ a re-skin of correlation/degree/sector. Apply to the
weighted/augmented objects (plain Forman's residual is 0 by construction — that is
the point of the baseline).

- **(i)** Spearman rank corr between `F(e)` and `|ρ_ij|` across edges — must be < 0.8.
- **(ii)** Top-K Jaccard overlap between curvature-ranked and correlation-ranked
  pairs — want small (target ~0.1–0.5). **Pre-register or sweep K.**
- **(iii)** Degree-preserving configuration-model null (Maslov-Sneppen rewiring,
  ~1000 graphs); z-score per edge; `|z| > 2` = real higher-order structure.
  (Has teeth for augmented/weighted; near-vacuous for plain Forman.)
- **(iv)** Residual orthogonalization: regress `F` on `deg_in(v1)`,
  `deg_out(v2)`, `|ρ_ij|`; use residual as isolated topological signal.
  `F# − F = 3m` isolates the triangle term directly. (Plain Forman → R²=1,
  residual ≡ 0 — demonstrate this explicitly as the baseline.)
- **Bootstrap stability of curvature rankings:** bootstrap over return windows /
  assets; report ranking stability. Distinct from rolling-window stability;
  directly addresses lead-lag estimation noise (§12 [G3]).
- **Multiplicity & splits:** Benjamini–Hochberg correction across the many edge-
  level tests; strict **train / validate / test** split with the operating point
  (§5 sweep) locked on validate, evaluated once on test.
- Plus: AFRC curvature gap Δκ, rolling-window stability, fraction of
  negatively-curved edges crossing community boundaries (GICS sectors).

### 7.2 Performance evaluation — PRIMARY: out-of-sample directional IC

The headline metric is the **out-of-sample directional information coefficient**:
the rank correlation between the curvature-implied leader→lagger forecast
(leader `r1(t)` predicting lagger `r2(t+τ)`; sign inherited from the lead-lag
estimate, not the curvature) and realized future returns, on held-out data.
Report **effect sizes with confidence intervals** and **block-bootstrap** the IC
differences across methods.

**Baselines (identical settings):**
- correlation-distance pair selection,
- correlation-matrix clustering (Cartea-Cucuringu-Jin, §12 [G5]),
- cointegration-selected pairs,
- random selection,
- **undirected Forman on the symmetrized graph** (isolates directedness),
- **Ollivier-Ricci** (isolates the curvature notion).

**Optional secondary — PnL (NOT a core v2 deliverable).** If time permits, convert
selected pairs → positions (mean-reversion, §8) → standardized risk-adjusted stats.
AlphaMark (`github.com/mcucurin/alphamark`) is the group's standardized PnL harness
and is the natural tool here, but the study **stands without it** (cf. Sandhu et
al., no backtest). If used: confirm the exact signal schema from the Guide
(`https://www.overleaf.com/read/vkdtddmdmfxh#ffc936`) / `main.py` / `pipeline/`
before writing the adapter (likely a per-asset per-timestamp position or score
matrix). Contacts: `dhruvpatel97@g.ucla.edu`, `lihaoran@g.ucla.edu`. Keep a
**minimal independent sanity backtest** so any AlphaMark result can't be an
integration artifact.

> NOTE: v1 dropped IC/OU-half-life in favor of AlphaMark. v2 REVERSES this per the
> reviewer/instructor reframe: **OOS directional IC is primary**, AlphaMark/PnL is
> optional secondary. The structural cascade (§7.1) stays the methodological core.

---

## 8. Trading / signal logic (predictability first; mean-reversion optional)

Curvature is a **selection** signal, NOT a directional one. Do **not** go
"long high-curvature stocks / short low-curvature."

**Primary (the study):** curvature + line-graph clustering → choose WHICH pairs
have isolated, coherent directed structure → measure their **out-of-sample
directional predictability (IC)**, leader→lagger, sign from the lead-lag estimate.

**Secondary / optional (only for the PnL appendix):**
1. Within each selected pair, standard **mean-reversion**: form spread
   `s_t = r1(t) − β·r2(t)` (β from rolling cointegration fit); enter when
   `|z(s_t)| > 2` (long laggard / short leader); exit on reversion to mean.
2. Aggregate all pair positions → net per-stock position vector → optional
   AlphaMark. Market-neutral by construction (each pair is dollar-balanced).
3. Diversify: take ~one representative pair per `L(G)` community to avoid loading
   the book on a single latent factor.

Note (reviewer §3.4): negative-curvature bridges are a *predictability* story
(IC/forecast), whereas OU-half-life/ADF/cointegration are *mean-reversion* metrics
about co-moving pairs — keep IC primary and explain why curvature should also
discover cointegrated spreads if the secondary PnL path is pursued.

---

## 9. Data (WRDS — all sources institutional via UCLA)

Build all networks on **factor/sector-residualized returns** (§4.5).

| Phase | Source | Detail | Purpose |
|---|---|---|---|
| 1 | CRSP (WRDS) | Daily **or 30-min** close-to-close, S&P 500, ~10 yrs, point-in-time index membership, delisting data | Pipeline validation; main results |
| 1 | Compustat (WRDS) | GICS sector classifications | Residualization + community-boundary tests |
| 2 | TAQ (WRDS) | Open-to-close 30-min bars, exclude overnight | Intraday signal (lead-lag washed out daily) |
| 3 (stretch) | TAQ (WRDS) | 5-min bars, S&P 100, tick data | Hayashi-Yoshida estimator, async trading |

**Survivorship bias is mandatory to handle** — use CRSP point-in-time membership,
not today's S&P 500 constituents. **Overnight vs daytime is a modeling decision,
not preprocessing** (§12 [G4]): excluding overnight returns is defensible (macro-
news-dominated, not microstructural) but treat it as an ablation axis, not a silent
choice. Daily lead-lag is weak — prefer 30-min/intraday for the headline; daily as
a robustness check.

---

## 10. Open risks & questions (address EARLY)

1. **Triangle sparsity / tree-SBM failure (HIGHEST PRIORITY).**
   Fesser-Weber-Lambiotte prove the curvature gap collapses for triangle-sparse
   communities → AFRC community detection can fail by their own theorem. Directed
   cyclic triangles are even rarer (`m` may be 0 on most edges). **Week-1
   diagnostic:** measure within-community triangle density of the real lead-lag
   networks and report the distribution of `m`. If triangle-sparse, the whole
   `L(G)`/AFRC approach is at risk and must be reconsidered before building on it.
   Do this BEFORE the full pipeline.
2. **Directed line graph.** Tian-Lubberts-Weber framework is *undirected*. Need a
   directed `L(G)` construction that preserves the graph↔line-graph curvature
   relationships. Possibly open — candidate Weber question / possible theory
   contribution.
3. **Directed AFRC curvature gap.** SBM recovery guarantees are undirected-only.
   A directed-SBM analog may be genuinely novel — potential centerpiece theory
   result for the ICAIF paper. Ask Weber.
4. **Directed triangle convention.** Unsettled in literature; implement both
   strict-cyclic and common-neighbor counts; report both.
5. **Degree-identity of plain Forman (RESOLVED by design).** Handled by demoting
   plain Forman to a baseline and foregrounding weighted/augmented (§4.6). Keep the
   explicit R²=1 demonstration as evidence the cascade is correctly calibrated.
6. **Factor/sector confounding (RESOLVED by design).** Handled by residualizing
   returns before graph construction (§4.5). Verify the signal survives on
   residualized returns, not just raw.
7. **AlphaMark signal schema (only if the optional PnL path is taken).** Confirm
   exact input format before writing any adapter.

---

## 11. Build order (do NOT skip the early diagnostics)

1. **WRDS data pull** — CRSP daily (or 30-min) S&P 500 (~10 yrs) + Compustat GICS.
   Parquet. Handle survivorship via point-in-time membership.
2. **Factor/sector residualization** — remove market + sector / factor-model
   components; produce residual-return series (§4.5).
3. **Lead-lag network construction** — BCR estimator; cross-correlation at lags
   τ ∈ {1,2,3,5}; signed statistic `ρ_ij(τ*) − ρ_ji(τ*)` as edge weight; sparsify;
   propagate edge uncertainty. Walk-forward; lock τ* per training window.
4. **KILL-SWITCH A — synthetic sanity:** run the full curvature→AFRC→Δκ pipeline on
   a planted directed-SBM to prove the code recovers known structure before
   trusting it on markets.
5. **KILL-SWITCH B — triangle-density diagnostic (Risk #1)** — within-sector
   triangle density + distribution of `m`, across sparsification levels. Decision
   gate: if triangle-sparse, escalate before continuing.
6. **Curvature module** — the four objects (§4.6): plain (baseline), augmented `F#`,
   weighted-augmented (main, directed), Ollivier-Ricci. Validate against
   `GraphRicciCurvature` on undirected toy first; the directed weighted form needs
   a custom implementation.
7. **Line graph + AFRC clustering** — build `L(G)` (undirected reduction first);
   AFRC curvature flow; communities; Δκ.
8. **Validation cascade** — the four tests + Δκ + stability + sector-bridge frac +
   **BH multiplicity + train/validate/test split + bootstrap ranking stability**.
   Threshold sweep here; operating point locked on validate.
9. **Primary evaluation — out-of-sample directional IC** vs all baselines (§7.2),
   with CIs and block-bootstrap.
10. **(Optional) secondary PnL** — mean-reversion signal; minimal sanity backtest;
    AlphaMark only if time permits.
11. **Critic/orchestrator agent** — wrap the pipeline in the LLM propose→test→reject
    loop (course's "agentic" requirement); log accepted/rejected candidates.
12. **Write-up** — long-form 285J report = unconstrained draft → compress to
    8-page ACM `sigconf` for ICAIF.

---

## 12. Full citation list (use these exact references)

### Group references — USE, don't just cite (Cucuringu; full list: math.ucla.edu/~mihai/fin.htm)

| Role | Citation |
|---|---|
| [G1] Lead-lag estimator + significance + directed clustering (ADOPT) | Bennett, Cucuringu, Reinert (2022) *Machine Learning* 111(12):4497–4538, arXiv:2201.08283 |
| [G2] Lead-lag detection + portfolio strategies (benchmark) | Cartea, Cucuringu, Jin (2023) "Detecting Lead-Lag Relationships in Stock Returns and Portfolio Strategies", SSRN 4599565 |
| [G3] Robust lead-lag detection (estimation noise → bootstrap) | Zhang, Cucuringu, Shestopaloff, Zohren (2025) *Applied Mathematical Finance* 32(2):91–127 |
| [G4] Overnight vs daytime lead-lag (modeling decision) | Lu, Zhang, Reinert, Cucuringu (2025) "A tug of war across the market", SSRN 5371952 |
| [G5] Correlation-matrix clustering stat-arb (correlation baseline) | Cartea, Cucuringu, Jin (2023) ICAIF '23, SSRN 4560455 |
| [G6] DTW for lead-lag | Zhang, Cucuringu, Shestopaloff, Zohren (2023) ICAIF '23, SSRN 4572554 |
| [G7] DeltaLag: learning dynamic lead-lag patterns | Zhou et al. (2025) ICAIF '25 |

### Proposal references

| Role | Citation |
|---|---|
| Stat-arb seminal (distance/correlation) | Gatev, Goetzmann, Rouwenhorst (2006) *Rev. Financial Studies* 19(3):797–827 |
| Stat-arb review | Krauss (2017) *J. Economic Surveys* 31(2):513–545 |
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

- DO build the lead-lag graph on **factor/sector-residualized returns** (§4.5)
  before computing any curvature. (Instructor requirement.)
- DO foreground **weighted augmented directed Forman** as the main object; treat
  plain `4 − deg − deg` Forman ONLY as the degree baseline. Compare all four
  objects (§4.6).
- DO make **out-of-sample directional IC** the primary metric. PnL/mean-reversion
  is optional secondary; **AlphaMark is NOT a core deliverable** in v2.
- DO keep the structural validation cascade with BH multiplicity, train/val/test
  split, and bootstrap ranking stability. It is the methodological contribution.
- DO run the synthetic sanity (kill-switch A) and triangle-density diagnostic
  (kill-switch B) before building the L(G)/AFRC stack.
- DO add curvature-method baselines: undirected Forman on the symmetrized graph and
  Ollivier-Ricci — these test the directedness and curvature-notion hypotheses.
- DO NOT hardcode a Δκ threshold or curvature percentile — sweep and lock the
  operating point on the validation split (never the test set).
- DO make the agent a genuine propose→test→reject loop with logged accept/reject
  decisions (§6 Agent 6) — substantive, but still the wrapper, not the science.
- DO treat the directed line-graph construction and directed AFRC gap as open
  questions — flag, do not silently assume the undirected results transfer.
- DO adopt the Bennett-Cucuringu-Reinert estimator + significance framework
  (§12 [G1]); edge weight = signed lead-lag statistic `ρ_ij(τ*) − ρ_ji(τ*)`, NOT
  symmetric correlation. Use the group refs, don't just cite them.

---

## 14. Success definition

- **285J floor:** working pipeline on factor-residualized CRSP data; the four
  curvature objects computed; structural cascade (with BH, splits, bootstrap) run;
  out-of-sample directional IC reported vs baselines; results documented.
- **ICAIF ceiling:** decisive empirical result that weighted-augmented-directed-
  Forman-selected pairs are (a) structurally distinct from correlation/degree/
  undirected-curvature AND (b) achieve higher out-of-sample directional IC than
  baselines, ideally plus one novel theory bit (directed AFRC gap / directed line-
  graph result). 8-page ACM `sigconf`, submitted by the confirmed ICAIF deadline.
  Optional PnL appendix strengthens the finance-venue case. Journal version
  (full multi-frequency study + Ollivier-Ricci comparison + curvature dynamics)
  after.

The work over the next ~3 months determines which one this becomes. Optimize for
the **out-of-sample IC + structural-distinctness** result; let it decide whether to
submit.
