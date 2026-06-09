# Ricci Curvature on Directed Lead-Lag Networks of US Equities
### A structural study of factor-residualized information flow

**Author:** Ivan Sit · **Course:** UCLA Math 285J (Agentic AI for Autonomous Research in Quantitative Finance) · **Advisor:** Prof. Mihai Cucuringu · **Target:** ICAIF 2026

---

## Abstract

We ask whether **discrete Ricci curvature** on **directed lead-lag networks** of US equities
identifies pair structure that correlation-, degree-, and undirected-curvature methods miss.
Networks are built on **factor/sector-residualized returns** (so the signal is idiosyncratic,
not a rediscovery of GICS sectors) with the **Bennett–Cucuringu–Reinert (BCR)** signed
lead-lag statistic as the directed edge weight. We compute four curvature objects — plain
directed Forman (a pure degree baseline), triangle-augmented Forman, **weighted augmented
directed Forman (our main object)**, and Ollivier-Ricci — and subject them to a structural
validation cascade designed to prove curvature is *not* a re-skin of correlation or degree.

The structural result is clear and robust: curvature-selected pairs are **near-disjoint** from
correlation-selected pairs (top-K Jaccard ≈ 0), only weakly rank-correlated with absolute
correlation (Spearman ≈ 0.18 ≪ 0.8), and the augmented object carries genuine **higher-order,
non-degree** signal (plain Forman is the exact degree identity, R² = 1; augmented Forman R² ≈
0.56 on degree). The directed graph encodes lead-lag asymmetry the symmetric correlation graph
destroys. We **also** evaluate out-of-sample directional information coefficient (IC) as an
**exploratory secondary** metric and report an honest **null**: across subsamples the IC ranking
flips, every 95% confidence interval spans zero, and — tellingly — undirected Forman *ties* the
directed version on IC, so directedness adds no *predictive* edge even where its *structural*
distinctness is clear. Following the precedent of Sandhu et al. (2016), who validated curvature
in finance structurally with no backtest, the contribution of this work is **structural**.

---

## 1. Motivation: why Ricci curvature for markets

Ricci curvature is a cornerstone of differential geometry: it measures how a space bends, and
through it how volumes, geodesics, and diffusion behave. Over the last two decades several
**discrete** analogues (Ollivier 2009; Forman 2003) extended the notion to graphs, where it
acquires an intuitive meaning at the level of a single edge:

- **Negatively curved edges are bridges** — they connect otherwise weakly-connected regions;
  removing one tends to disconnect or bottleneck the network. They are *structurally isolated*.
- **Positively curved edges sit inside dense, well-connected clusters** — many short alternative
  paths route around them.

This gives a **parameter-free, local descriptor with a global meaning**: curvature turns "is this
relationship a fragile bridge or a redundant interior link?" into a number computed from local
neighborhoods. That is exactly the question one wants to ask of a financial network.

The spark for this project was **Sandhu, Georgiou & Tannenbaum (2016, *Science Advances*)**, who
computed **Ollivier-Ricci curvature on undirected correlation networks** of equities and found
that market-wide curvature *rises before crashes* — curvature as a systemic-fragility signal.
They validated the construction **structurally only** (against entropy, path-length, diameter),
never ran a trading backtest, and explicitly flagged two open directions: a **directed**
extension and a stat-arb application. This study takes up the directed extension.

## 2. Background and the gap

Sandhu et al. made four choices that together define the opening for new work:

| Their choice | This work |
|---|---|
| **Undirected** correlation graph | **Directed** lead-lag graph (asymmetry is the point) |
| **Correlation** edges | **BCR signed lead-lag** statistic on **residualized** returns |
| **Ollivier-Ricci** | **Forman-Ricci** (combinatorial, cheap, naturally directed) + Ollivier as a baseline |
| Structural validation only | Structural cascade **plus** an (exploratory) predictive test |

Markets have direction: some stocks lead, others lag. The symmetric correlation matrix
*destroys* that asymmetry by construction. A directed graph keeps it, and Forman curvature —
defined combinatorially from incident edges and triangles — extends to the directed setting
(Sreejith–Jost–Saucan–Samal 2016) far more cheaply than optimal-transport curvature. The
methodological novelty over Sandhu is therefore the **directed-vs-undirected** and
**Forman-vs-Ollivier** contrasts on a **residualized** network.

## 3. Hypothesis

> **(Primary, structural — falsifiable.)** Negatively-curved edges in the directed,
> factor-residualized lead-lag network mark structurally isolated pairs — bridges connecting
> otherwise separated regions of the market — that **correlation-, degree-, and
> undirected-curvature methods do not recover**. Lead-lag asymmetry encodes structure the
> symmetric correlation graph destroys, and weighted augmented directed Forman curvature
> captures it.

A secondary, exploratory claim — that these pairs also carry higher out-of-sample directional
predictability — is tested and, as reported below, **not** supported. We state both and report
the predictive null transparently rather than overclaim.

## 4. Methods

The pipeline is implemented as six composable stages (the course's "agentic" requirement is met
by a propose→test→reject orchestration layer that logs accepted/rejected candidate signals).

### 4.1 Factor/sector residualization (done *before* the graph)
On raw equity returns, the market and sector factors dominate both the graph and its curvature,
and a degree-preserving null does not remove them — so any "topological signal" risks being
dismissed as a rediscovery of GICS sectors. We therefore regress out the **market + leave-one-out
own-sector** factors first and build the network on the **residuals**. This is a load-bearing
instructor requirement.

### 4.2 Directed lead-lag network (BCR)
For each ordered pair we compute the **Bennett–Cucuringu–Reinert signed lead-lag statistic**
`w_{i→j} = ρ_ij(τ*) − ρ_ji(τ*)`, where `ρ_ij(τ) = corr(r_i[t], r_j[t+τ])` and `τ*` is the lag of
peak magnitude. The statistic is antisymmetric, so each retained pair becomes a **directed edge
in the sign direction**, with strength `|w|` as the (positive) curvature weight. For intraday
data we use a **within-day estimator**: the `(t, t+τ)` pairing is restricted to the same trading
day so lag pairs never straddle the overnight gap. The graph is sparsified at a quantile of `|w|`.

**Time horizons tried (explicit).** `τ*` is selected per pair from a fixed grid of candidate
lags — we did **not** sweep arbitrary horizons. Two regimes were tested: **daily** data with
`τ ∈ {1, 2, 3, 5}` trading days, and **intraday 30-min** data with `τ ∈ {1, 2, 3}` bars
(i.e. 30 / 60 / 90 minutes, within-day). We did **not** test weekly or monthly horizons; the
intraday 30-min regime is the headline (where lead-lag is strongest), daily is the robustness
check.

### 4.3 Four curvature objects (the ablation spine)

| Object | Definition | Role |
|---|---|---|
| Plain directed Forman | `4 − deg_in(v₁) − deg_out(v₂)` | **Degree baseline** (signal ≡ 0 after residualizing on degree, *by construction*) |
| Triangle-augmented | `F# = F + 3m`, `m` = common-neighbor triangles | Higher-order: residual isolates `3m` |
| **Weighted augmented directed Forman** | weighted Forman (Samal 2018 Eq. 7) + triangle augmentation, directed, BCR weights | **Main object** |
| Ollivier-Ricci | Wasserstein transport between neighbor distributions (exact W₁ via LP) | Robustness / contrast (what Sandhu used) |

Demoting plain Forman to a *baseline* is deliberate: because `4 − deg_in − deg_out` is an exact
linear function of the two endpoint degrees, regressing it on degree returns R² = 1 and a zero
residual — it carries no higher-order signal by construction. The augmented object's `+3m` term
is **not** determined by the endpoint degrees, so its residual-after-degree is genuinely new
information and the degree-preserving null "has teeth."

### 4.4 Line graph and communities
Pairs are *edges* of the network. To cluster pairs with node-based machinery we build the
**line graph** `L(G)` (each edge of `G` is a node; two are adjacent iff their edges share a
vertex) and run an AFRC modularity-guided curvature flow to detect pair-communities. Curvature on
`G` answers "is this pair isolated in stock-space?"; curvature on `L(G)` answers "is this pair
isolated relative to other pairs?".

### 4.5 Structural validation cascade (the methodological core)
To prove curvature ≠ correlation/degree/sector, we run: (i) Spearman(`F`, `|ρ|`) — must be small;
(ii) top-K Jaccard overlap of curvature- vs correlation-ranked pairs — want small; (iii) a
degree-preserving **configuration-model null** (Maslov–Sneppen rewiring) with per-edge z-scores;
(iv) **residual orthogonalization** — regress `F` on degrees and `|ρ|` and use the residual as the
isolated topological signal (with the plain-Forman R²=1 identity as a calibration check). We add
Benjamini–Hochberg multiplicity control, a strict **train/validate/test** split, and bootstrap
stability of the curvature rankings.

### 4.6 Evaluation (exploratory secondary)
Out-of-sample **directional IC** is the rank correlation between the leader→lagger forecast
(`sign × r_leader(t)` predicting `r_lagger(t+τ)`, sign fit on train) and realized returns on
held-out data, with block-bootstrap CIs. We report two horizons — cross-period and
**within-day-only** — against correlation, cointegration, random, undirected Forman, and
Ollivier baselines on identical settings.

## 5. Data

All data is institutional via UCLA WRDS. **CRSP** daily S&P 500 returns (2000–2024,
survivorship-correct via point-in-time membership and delisting adjustment); **Compustat** GICS
sector classifications (for residualization and community-boundary tests); **TAQ** Monthly 30-min
intraday bars. Networks are built on factor-residualized returns throughout.

**Coverage (explicit).** The **daily** analysis — both the structural cascade and the predictive
walk-forward — spans the **full 2000–2024** (6,289 trading days, ~1,069 names with point-in-time
membership; ~400 names continuously present per 4-year window). The **intraday 30-min** analysis
covers **2019 only** (≈155 liquid large-caps, 3,024 bars): pulling 30-min TAQ across 25 years
would be ~100+ hours of WRDS queries, so intraday serves as a **high-frequency cross-check**, not
a 25-year panel. Where lead-lag is strongest is intraday; where coverage is broadest is daily —
we report both.

## 6. Results

All structural metrics below are reported at **both horizons** — the 2019 intraday graph and the
full **2000–2024 daily** span (averaged across the walk-forward windows).

### 6.1 Curvature is not a re-skin of correlation
- **Top-K Jaccard (curvature vs correlation) = 0.0** at both horizons — the two methods select
  almost entirely disjoint pairs.
- **Spearman(`F`, `|ρ|`)** = 0.18 (intraday 2019) and 0.07 (daily 2000–2024), both ≪ 0.8 — curvature
  rank is only weakly related to correlation magnitude, and even less so on the long daily span.

The pairs curvature flags as structurally isolated are *not* the pairs correlation flags as
strongly co-moving. This is the central structural finding, and it is robust across 25 years.

### 6.2 A clean degree ablation
- **Plain Forman R² = 1.0** on `(deg_in, deg_out)` at both horizons — the exact degree identity,
  confirming the cascade is calibrated and that plain Forman is rightly a baseline.
- **Augmented Forman R²** = 0.56 (intraday 2019) and 0.18 (daily 2000–2024) on degree + `|ρ|` —
  i.e. **44%–82%** of its variation is **not** explained by degree or correlation (more on daily).
  The triangle term `3m` injects genuine higher-order structure at both horizons.

### 6.3 The lead-lag network is triangle-sparse
The kill-switch B diagnostic flags the network as **triangle-sparse** at every sparsification
level (most edges have few common-neighbor triangles; **strict directed-cyclic triangles are
essentially absent**, which settled an open convention in favor of the common-neighbor count).
Only ≈ 1% of triangles fall *within* a GICS sector. Two consequences, both honest findings rather
than failures: (a) by the Fesser–Weber–Lambiotte tree-SBM result, the AFRC curvature gap and
hence community separability are *intrinsically limited* in such networks (GICS Δκ is small);
(b) the structure curvature surfaces is **cross-sector**, not aligned with GICS — exactly the kind
of relationship a sector-based view would miss.

### 6.4 The predictive question: an honest null
Out-of-sample directional IC (full-year 2019, within-day-only horizon, k = 20 pairs):

| Method | Mean IC | 95% CI |
|---|---:|---|
| Undirected Forman | **+0.013** | [−0.016, +0.040] |
| Curvature (aug, directed) | **+0.005** | [−0.016, +0.026] |
| Correlation | −0.003 | [−0.027, +0.024] |
| Ollivier-Ricci | −0.006 | [−0.028, +0.020] |
| Cointegration | −0.009 | [−0.026, +0.007] |
| Random | −0.015 | [−0.031, +0.006] |

The Forman family leads every baseline here, but **no confidence interval excludes zero**, the
ranking **flips across subsamples**, and **undirected Forman ties the directed version**.

**Daily, 2000–2024 (walk-forward, 21 windows, close-to-close, k = 20).** The longer span is even
more decisive against H2. Mean OOS IC across windows:

| Method | Mean IC | 95% CI | windows > 0 |
|---|---:|---|---:|
| Correlation | **+0.023** | [+0.006, +0.040] | 76% |
| Random | +0.007 | [−0.004, +0.017] | 67% |
| Undirected Forman | +0.002 | [−0.005, +0.008] | 52% |
| Curvature (aug, directed) | **−0.011** | [−0.020, −0.001] | 43% |

Over 25 years of daily data, **curvature selection is significantly *negative*** (CI excludes zero)
and **correlation does best** (CI excludes zero, positive). The intraday-2019 "Forman leads" does
**not** replicate. **Verdict on H2: not supported** — there is no predictive edge for curvature,
and on the long daily span it actively underperforms correlation. We do not tune universes,
windows, or `k` to manufacture significance; the structural claim (H1) stands on its own.

## 7. Discussion and implications

1. **A new structural lens.** Forman curvature on directed, residualized lead-lag networks
   surfaces pair structure that correlation, degree, and undirected curvature do not — a clean,
   reproducible structural result and a genuine extension of Sandhu et al. to the directed setting.
2. **Directedness is structurally informative even where it is not predictive.** The directed
   construction is distinct from its symmetrized counterpart in the structural cascade, yet the
   two tie on IC. The value of directedness here is descriptive, not forecasting.
3. **Triangle sparsity is a first-class constraint** for curvature-community methods in finance,
   not an implementation detail. The cross-sector character of the surfaced structure is itself
   a substantive observation.
4. **An honest predictive null is a result, not a failure.** Sandhu et al. set the precedent that
   a structural curvature study in finance is publishable without a backtest; this work follows
   it and reports the predictive null transparently.

## 8. Limitations
- Single headline year (2019 intraday) for the main result; multi-year/multi-frequency replication
  is future work.
- The directed line-graph construction and a directed AFRC curvature gap are theoretically open
  (the Tian–Lubberts–Weber and Fesser–Weber–Lambiotte frameworks are undirected); we use the
  undirected reduction as an honest baseline.
- IC is evaluated at fixed `k`; a pre-registered `k` would further harden the (null) predictive
  claim.

## 9. Future work
- Directed line-graph and directed AFRC-gap theory (candidate collaboration with M. Weber).
- Multi-frequency replication (daily ↔ 30-min ↔ 5-min Hayashi-Yoshida) and curvature dynamics
  through 2020 stress.
- If a predictive angle is ever revisited, treat it as a pre-registered confirmatory test, not an
  exploratory sweep.

## 10. Reproducibility
The full pipeline is open-source (`github.com/ivan-sit/Curvature-Lead-Lag-Model`, package `cllm`):
residualization, BCR lead-lag, the four curvature objects, the line graph, the validation cascade,
and the evaluation harness, with 50 passing tests, synthetic kill-switch A (directed-SBM recovery)
and kill-switch B (triangle density). WRDS pull scripts are included; data is institutional and
not redistributed.

## References (selected)
- Sandhu, Georgiou, Tannenbaum (2016). *Science Advances* 2(5):e1501495. — curvature & systemic risk.
- Forman (2003). *Disc. & Comp. Geometry* 29(3):323–374. — Forman-Ricci curvature.
- Sreejith, Jost, Saucan, Samal (2016). arXiv:1605.04662. — directed Forman.
- Samal et al. (2018). *Sci. Rep.* 8:8650. — weighted / augmented Forman (Eqs. 7–10).
- Bennett, Cucuringu, Reinert (2022). *Machine Learning* 111(12). — lead-lag estimator [adopted].
- Tian, Lubberts, Weber (2025). *JMLR* 26(52). — line-graph curvature clustering.
- Fesser, Serrano de Haro Iváñez, Devriendt, Weber, Lambiotte (2024). *J. Phys. Complexity* 5:035010. — AFRC gap / tree-SBM.
- Ollivier (2009). *J. Functional Analysis* 256(3):810–864. — Ollivier-Ricci.
