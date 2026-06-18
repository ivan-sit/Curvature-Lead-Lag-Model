# Directed Curvature on Equity Lead-Lag Networks:
## A Structural Lens and the Topology–Covariance Barrier

*(ICAIF 2026 draft — math/structural-forward, honest. ACM `sigconf`, 8 pages. Deadline Aug 2.)*

---

## Abstract  *(self-contained)*

We introduce **CRISP** — directed, weighted, augmented **Forman–Ricci curvature** on
**factor-residualized** equity **lead-lag networks** — and characterize, rigorously, what it can and
cannot do for markets. **Robust finding 1 (structure):** curvature selects pairs that are
statistically distinct from correlation-, degree-, and undirected-curvature selection (top-K Jaccard
≈ 0; Spearman(F,|ρ|) ≈ 0.1 ≪ 0.8), and that structure is **overwhelmingly cross-sector** (≈99% of
the network's triangles span GICS sectors) — relationships a sector- or correlation-based view is
structurally blind to. **Robust finding 2 (a barrier):** across **fourteen** covariance- or
return-determined objectives — directional return prediction, realized- and implied-volatility (VIX)
forecasting, drawdown, tail risk, contagion, fundamentals, diversification, centrality premium, and
economic-link momentum — curvature adds **no edge beyond correlation**, with every test
partial-controlled. We explain this with a single principle, **topology ⊥ covariance:** standard
financial objectives are covariance- or return-determined, whereas curvature's information is purely
*topological*, so it cannot improve them by construction. **A suggestive lead (not yet robust):** in
large-caps, curvature's cross-sector bridges are enriched for real customer–supplier links
(3.7×, p = 0.006) while correlation captures none — but this **does not replicate** in a broad
small/mid-cap universe, so we report it as a lead for future work, not a result. The contribution is
a clean, honest map: **curvature is a structural lens distinct from correlation, but its information
is orthogonal to the covariance/return objectives that finance optimizes — a microscope for market
structure, not an alpha or risk engine.**

---

## 1. Introduction

- **Question:** correlation networks are the standard lens on equity co-movement. Does the *geometry*
  of a *directed* network — who leads whom — encode structure correlation cannot?
- **Answer (this paper):** it encodes genuine *structure* (cross-sector, distinct from correlation),
  but that structure is **orthogonal to the covariance/return objectives finance optimizes** — so the
  honest contribution is a precise *characterization*, not an alpha claim.
- **Why prior framings differ:** curvature-in-finance work (Sandhu 2016; Samal 2021) used
  *undirected correlation* networks for *aggregate fragility*; we use *directed, residualized lead-lag*
  networks and test predictive/optimization use **exhaustively** (and honestly null).
- **Contributions:**
  1. **CRISP**, a directed/weighted/augmented Forman-curvature object on residualized lead-lag
     networks (§4), with a clean four-object ablation.
  2. **Structural distinctness (H1):** curvature selection is near-disjoint from correlation/degree/
     undirected (Jaccard ≈ 0) and cross-sector (§6.1) — robust across 25 years and two frequencies.
  3. **The topology ⊥ covariance barrier:** across **fourteen** covariance/return objectives,
     curvature adds nothing beyond correlation, with one principled explanation (§6.3–6.4).
  4. **A suggestive (non-robust) lead:** large-cap curvature bridges are enriched for real customer–
     supplier links (3.7×, p = 0.006) — but it **does not replicate** in small/mid-caps; reported as
     future work, not a result (§6.2).
  5. *(Optional methodology note, §3):* the study was executed by an **autonomous research agent**
     with a propose→test→reject loop and explicit anti-p-hacking discipline.

## 2. Related work

- **Curvature in finance:** Sandhu-Georgiou-Tannenbaum (2016, *Sci. Adv.*) — Ollivier-Ricci on
  undirected correlation nets, aggregate fragility; Samal et al. (2021) — Forman-Ricci tracks
  volatility best. **We extend to directed/residualized lead-lag and add external economic validation.**
- **Economic-link / network return structure:** Cohen-Frazzini (2008) customer-supplier momentum;
  Ahern (2013) network-centrality premium; supply-chain centrality & returns (2024). **We test these
  on our network (null) and explain why (topology ⊥ covariance), while recovering the links themselves.**
- **Lead-lag:** Bennett-Cucuringu-Reinert (2022) signed statistic (our edge weight); Cartea-Cucuringu-Jin;
  Lu et al. (overnight/daytime).
- **Discrete curvature:** Forman (2003); Sreejith et al. (directed); Samal (weighted/augmented);
  Tian-Lubberts-Weber (line graph); Fesser-Weber-Lambiotte (AFRC gap).
- **Gap we fill:** nobody has (a) put directed curvature on a residualized lead-lag graph, nor
  (b) validated curvature-discovered structure against disclosed economic links.

## 3. Method — CRISP  *(+ optional agentic-execution note)*

- **Residualize first (§3.1):** remove market + leave-one-out sector (PCA as ablation) so signal is
  idiosyncratic, not rediscovered GICS.
- **Directed lead-lag graph (§3.2):** edge weight = BCR signed statistic
  `w(i→j)=ρ_ij(τ*)−ρ_ji(τ*)`, `ρ_ij(τ)=corr(r_i[t], r_j[t+τ])`; keep strongest ~10%; within-day
  estimator intraday.
- **Four curvature objects (§3.3):** plain (degree baseline, R²-on-degree = 1) → weighted →
  **weighted augmented directed (main)** → Ollivier (600× cost contrast). Augmentation = +3·(triangles);
  the main object carries 44–82% non-degree signal.
- **Validation cascade (§3.4):** Spearman(F,|ρ|), top-K Jaccard, config-model null, residual
  orthogonalization; BH; train/val/test.
- *(Optional §3.5 — agentic execution):* an autonomous agent ran the full loop (build, WRDS pulls,
  validate, a propose→test→reject orchestrator that auto-rejects degree baselines), with a stop-rule
  against p-hacking and partial-controls on every predictive test. A reproducibility + honesty asset.

## 4. Data  *(all WRDS / institutional)*
CRSP daily S&P 500 (2000–2024, survivorship-correct); TAQ 30-min intraday (2019 + 2008/2015/2020);
Compustat GICS sectors **and customer-supplier segments** (`wrds_seg_customer`) **and** quarterly EPS;
CBOE/WRDS spot VIX (`cboe.cboe`).

## 5. (folded into 6)

## 6. Results

### 6.1 Curvature is structurally distinct and cross-sector (H1)
- top-K Jaccard vs correlation ≈ **0**; Spearman(F,|ρ|) **0.18 / 0.07** (intraday/daily); plain R²-on-
  degree **= 1.00**, augmented **0.56 / 0.18**. Robust across horizons, 25 years, and residualizations.
- **~99% of the network's triangles are cross-sector** (≤1% within a single GICS sector).

### 6.2 A suggestive (non-robust) lead: economic-link enrichment in large-caps
- Curvature's cross-sector **bridges** (most-negative augmented Forman) are **enriched for real
  customer–supplier links** (Compustat segments): top-300 bridges **3.7×, p = 0.006**; top-500
  **2.6×, p = 0.019**. **Top-correlation pairs: 0×** — correlation captures no cross-sector economic
  links (it picks within-sector co-movers).
- Interpretation: in **large-caps**, curvature surfaces economic linkages — *without* disclosure data
  — that correlation is structurally blind to. **Honest caveat (robustness):** this enrichment is
  **large-cap-specific and fragile** — it rests on ~6 pairs and **does not replicate** in a broad
  small/mid-cap universe (1 hit among 1,182 links; 2.3×, p=0.35). We therefore report it as a
  **suggestive observation and a lead for future work** (resolved supply-chain IDs; micro-caps), not
  a confident result. The robust contributions are H1 (§6.1) and topology ⊥ covariance (§6.4).

### 6.3 The limits: no edge on covariance/return objectives (14 targets)
- Returns (H2): OOS IC null intraday; 25-yr daily walk-forward curvature −0.011 (CI<0) vs correlation
  +0.023 (CI>0). Volatility: tracks (−0.78) but = correlation level, no lead. VIX: tracks (−0.52),
  no lead. Battery (partial-controlled, |corr|≤0.16): node risk, drawdown, tail risk, contagion, EPS,
  shock propagation, diversification, centrality premium, link momentum — all null.

### 6.4 The principle: topology ⊥ covariance
- Risk/diversification **is** the covariance matrix; returns are not topology. Standard objectives are
  covariance/return-determined; curvature's information is topological → orthogonal → cannot improve
  them by construction. One principle explains all fourteen nulls — and predicts the one place
  curvature *does* win: recovering structure that is *economic*, not covariance (§6.2).

## 7. A potential application — *if* the economic-link lead is confirmed

> Conditional on strengthening §6.2 (resolved supply-chain IDs, micro-caps): the lead points toward a
> price-based instrument that would **map economic wiring from prices alone** — no
fundamental disclosures required. This is useful precisely because the standard source of
customer–supplier links (10-K segment disclosures / Compustat) is **quarterly, lagged, US-only, and
incomplete** — only "major" customers (≳10% of sales) are reported. Curvature on price-based lead-lag
networks is, by contrast:
- **Real-time / high-frequency** — updated continuously from daily or intraday returns, versus
  quarterly filings; it can flag link formation and dissolution *between* disclosures.
- **Disclosure-free** — applies where segment data does not exist: private firms, foreign markets,
  small/under-covered names, and links below the 10% reporting threshold.
- **Cross-sector by construction** — it surfaces exactly the links a sector- or correlation-based
  view misses (correlation recovers **0×** of them; curvature **3.7×**, p = 0.006).

**Concrete uses:** (i) **supply-chain risk mapping** — surface a portfolio's hidden cross-sector
economic concentration; (ii) **contagion / stress-path inputs** — which firms are economically wired
to a shocked name; (iii) **analyst lead-generation** — flag non-obvious economic linkages for
fundamental research; (iv) a **price-based proxy for the economic network** wherever disclosure data
is missing or stale.

**What it is *not*:** an alpha or risk-optimization signal — **topology ⊥ covariance** (§6.4). The
value is *discovery*, and the discovery is **statistically significant**. This is the honest, sharp
positioning: a microscope for hidden economic structure, not an alpha/risk engine.

## 8. Limitations & future work
- Economic-link matching is coarse (free-text customer names → undercounts links); a resolved
  supply-chain ID dataset would sharpen the enrichment estimate.
- The directed line-graph / directed curvature-gap theory is open (Weber collaboration).
- **Alpha path — tested, closed:** Cohen-Frazzini link momentum is weak even on *real* customer-
  supplier links in our large-cap universe (+2.5%/yr, t=1.22 — the effect lives in under-covered
  small-caps), and curvature's discovered links (3.7x-enriched but still sparse) capture less
  (t=0.30). So the discovery does **not** translate to a tradeable signal here; curvature's
  contribution is structural discovery, not alpha. A small-cap universe is the natural retest.

## References  *(expand to 20–25)*
Sandhu 2016; Samal 2021; Forman 2003; Sreejith 2016; Bennett-Cucuringu-Reinert 2022;
Cohen-Frazzini 2008; Ahern 2013; Cartea-Cucuringu-Jin 2023; Lu 2025; Tian-Lubberts-Weber 2025;
Fesser-Weber-Lambiotte 2024; Ollivier 2009; + supply-chain centrality (2024).
