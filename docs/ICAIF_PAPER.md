# Autonomous Agentic Research in Quantitative Finance:
## A Self-Skeptical Case Study in Directed-Curvature Market Structure

*(ICAIF 2026 draft — agentic-AI-forward framing. ACM `sigconf`, 8 pages. Deadline Aug 2.)*

---

## Abstract  *(self-contained)*

We present an **agentic AI system that autonomously conducts a complete quantitative-finance
research program** — hypothesis formation, pipeline construction, institutional-data acquisition,
statistical validation, and a self-directed *propose → test → reject* experiment loop — and use it
to deliver a rigorous case study on the geometry of US equity markets. The agent builds **directed
lead-lag networks** of S&P 500 stocks from **factor-residualized** returns and analyzes them with
**discrete Forman–Ricci curvature** (the **CRISP** object: Curvature of Residualized, Signed
lead-lag Pairs). It establishes a **positive structural result**: curvature-selected pairs are
statistically distinct from those surfaced by correlation, degree, or undirected-curvature methods
(top-K Jaccard ≈ 0; Spearman ≈ 0.1, ≪ 0.8), and the structure it reveals is overwhelmingly
**cross-sector** — relationships a sector- or correlation-based view is structurally blind to. The
agent then subjects the construction to an **exhaustive battery of fourteen candidate applications**
— directional return prediction, realized- and implied-volatility (VIX) forecasting, drawdown, tail
risk, contagion, fundamentals (EPS), and portfolio diversification — and reports an **honest,
comprehensive negative**: across all of them, curvature provides no edge beyond plain
correlation/volatility, with every test partial-controlled so only signal *beyond* correlation
counts. We give a **principled explanation**: standard financial objectives are
**covariance-determined**, whereas curvature's unique information is **topological**, so the two are
orthogonal. The contribution is twofold: **(i)** a demonstration of agentic AI performing
rigorous, *self-skeptical* autonomous research in finance — including the discipline to reject its
own hypotheses and explain *why* — and **(ii)** a clean characterization of what network curvature
can and cannot do for markets: **a structural microscope, not an alpha or risk engine.**

---

## 1. Introduction

- **The shift ICAIF is undergoing:** from bespoke models to **agentic systems** (LLM agents,
  multi-agent workflows, autonomous research loops). The open question is not "can an agent generate
  ideas?" but "can an agent run a *rigorous, self-correcting* research program — and not fool
  itself?"
- **Our system** is a concrete answer: an agent that took a finance hypothesis end-to-end —
  literature framing, code, WRDS data, validation, ~14 experiments — and, crucially, **rejected the
  hypotheses that did not survive**, with logged reasons.
- **Why curvature / lead-lag as the testbed:** geometry gives a parameter-free structural lens
  (Sandhu 2016; Samal 2021); the **directed** lead-lag extension on **residualized** returns is
  novel; and the domain is rich enough to stress-test the agent's rigor.
- **Contributions:**
  1. An **agentic research pipeline** (6 stages + a propose→test→reject orchestrator) that runs the
     full loop autonomously, with auditable accept/reject logs and pinned provenance.
  2. A **positive structural finding (H1):** directed-curvature pairs are distinct from
     correlation/degree/undirected selection and live cross-sector.
  3. A **rigorous negative (H2 + 12 applications):** curvature adds no predictive or optimization
     value over correlation, and a **principled reason** (topology ⊥ covariance).
  4. A **methodological lesson** for agentic finance research: the agent's value is *honest
     filtering*, not idea generation.

## 2. Related work

- **Curvature in finance:** Sandhu, Georgiou, Tannenbaum (2016, *Sci. Adv.*) — Ollivier-Ricci on
  *undirected correlation* nets as a fragility indicator; Samal et al. (2021, *R.Soc.Open Sci.*,
  "Network geometry and market instability") — Forman-Ricci tracks volatility/fragility best among
  curvature measures. **We extend to directed lead-lag on residualized returns and test predictive
  use exhaustively.**
- **Lead-lag estimation:** Bennett, Cucuringu, Reinert (2022) signed lead-lag statistic (adopted as
  the edge weight); Cartea-Cucuringu-Jin lead-lag clustering; Lu et al. overnight/daytime "tug of
  war."
- **Discrete curvature:** Forman (2003); Sreejith-Jost-Saucan-Samal (directed); Samal (weighted/
  augmented); Tian-Lubberts-Weber (line-graph clustering); Fesser-Weber-Lambiotte (AFRC gap).
- **Agentic AI in finance (ICAIF lineage):** LLM agents for investment management; agentic
  time-series workflows (TS-Agent); agent-based asset pricing (AAPM); FinRobot; multi-agent
  reflection. **Our novelty vs these: an agent that runs a *full empirical research program with
  rigorous negative-result discipline*, not a trading/QA agent.**
- **The gap:** nobody has (a) put directed curvature on a residualized lead-lag graph, nor (b)
  demonstrated an agent that autonomously establishes *and honestly bounds* a finance hypothesis.

## 3. The agentic research system  *(the ICAIF methodological core)*

- **Two-layer design** (decision vs execution): a human/decision layer sets goals and accept/reject
  criteria; an autonomous execution layer builds, runs, and judges.
- **Six-stage pipeline:** residualize → directed lead-lag (BCR) → four curvature objects →
  (line-graph, opt-in) → validation cascade → selected structure.
- **Propose → test → reject orchestrator:** proposes candidate signals over a grid (residualization
  × threshold × curvature object), runs the structural cascade, accepts/rejects with logged reasons.
  *Result it produced:* rejects plain Forman (R²-on-degree = 1.00, pure degree) every time, accepts
  augmented (0.45–0.67); H1 robust across market/sector/PCA residualizations.
- **Self-skepticism mechanisms:** strict train/validate/test; partial-controls on every predictive
  test (credit only signal beyond correlation/vol); BH multiplicity; explicit *stop rule* to prevent
  p-hacking; auditable findings log (`CURVATURE_IMPLICATIONS.md`).
- **Reproducibility:** open-source (`cllm`, 52 tests), WRDS pull scripts, pinned data/seeds/commit.
- **Where the agent worked vs needed a human:** built/tested/debugged/data-engineered autonomously;
  the *framing* (structural vs predictive) and the *discipline not to over-search* were human-set.

## 4. Method — CRISP

- **Residualize first (§4.1):** remove market + leave-one-out sector (and PCA, as ablation) so the
  signal is idiosyncratic, not rediscovered GICS.
- **Directed lead-lag graph (§4.2):** edge weight = BCR signed statistic
  `w(i→j) = ρ_ij(τ*) − ρ_ji(τ*)`, `ρ_ij(τ)=corr(r_i[t], r_j[t+τ])`; sparsify to strongest ~10%;
  within-day estimator for intraday.
- **Four curvature objects (§4.3, the ablation spine):** plain directed Forman (degree baseline) →
  weighted → **weighted augmented directed (main)** → Ollivier-Ricci (contrast). The main object is
  the only one that is simultaneously directed, weighted, and higher-order (triangle-augmented),
  at ~0 cost vs Ollivier's 600×.
- **Validation cascade (§4.4):** Spearman(F,|ρ|), top-K Jaccard, config-model null, residual
  orthogonalization; BH; train/val/test.

## 5. Data  *(all WRDS / institutional)*

- **CRSP** daily S&P 500, 2000–2024 (survivorship-correct) — structural cascade + the 25-yr
  predictive/risk battery.
- **TAQ** 30-min intraday — full-year 2019 (headline) + 2008/2015/2020 (regime robustness).
- **Compustat** GICS sectors (residualization, cross-sector tests) + quarterly EPS (fundamentals).
- **CBOE/WRDS** spot VIX (`cboe.cboe`) — implied-vol forecasting test.

## 6. Results

### 6.1 Positive: curvature is structurally distinct (H1) and cross-sector
- top-K Jaccard vs correlation **≈ 0**; Spearman(F,|ρ|) **0.18** intraday / **0.07** daily (both
  ≪ 0.8); plain Forman R²-on-degree **= 1.00** (calibration), augmented **0.56 / 0.18** (44–82%
  non-degree). Robust across both horizons and 25 years; robust to residualization (orchestrator).
- **Cross-sector:** ~99% of the network's triangles span sectors (≤1% within a single GICS sector)
  → curvature highlights links a sector/correlation grouping cannot.

### 6.2 Negative: no predictive/optimization edge (H2 + the application battery)
- **Returns (H2):** OOS directional IC null intraday (CIs span 0); on the 25-yr daily walk-forward
  curvature IC **−0.011** (CI < 0) vs correlation **+0.023** (CI > 0). Curvature *underperforms*.
- **Volatility / fragility:** curvature tracks realized vol at **−0.78** (reproduces Sandhu/Samal)
  but is **equivalent to correlation level** and **does not lead** (partial ≈ 0).
- **VIX (implied vol):** tracks at −0.52 (worse than realized vol's +0.81 vs VIX); does **not lead**
  VIX controlling current VIX (~0); faint sub-threshold hint (~0.10) at 10–21d.
- **Battery (all partial-controlled, |corr| ≤ 0.16):** node-level stock risk, drawdowns, Δcurvature,
  dispersion, leadership concentration, market-return timing, skew/kurtosis tail risk, contagion,
  EPS earnings-risk, shock propagation, and **portfolio diversification** (structural diversification
  is *worse* than correlation diversification). All null.

### 6.3 The unifying explanation: topology ⟂ covariance
- Portfolio risk / diversification **is** the covariance matrix (= correlation); return prediction
  is not topology. Standard financial objectives are covariance- or return-determined; curvature's
  unique information is **topological** → orthogonal → cannot beat correlation at any of them by
  construction. This single principle explains all 14 nulls.

## 7. Discussion

- **What curvature *is* good for:** *descriptive / structural* — mapping hidden cross-sector wiring,
  flagging specific critical links for stress-testing, detecting structural regime change. It
  answers "what is the structure?" not "optimize my return/risk."
- **What it is *not*:** an alpha or risk-optimization input.
- **Agentic-AI lesson:** the system's scientific value was **rigorous, self-skeptical filtering** —
  it found a real structural result, exhaustively tested its uses, and *honestly bounded* it, with a
  stop-rule against p-hacking. This is the capability agentic finance research most needs and least
  demonstrates.

## 8. Limitations & future work

- Intraday is 2019 (headline) + 3 regime years, not a 25-yr intraday panel (TAQ cost).
- The line-graph / pair-community step is starved by triangle-sparsity; the **directed** line-graph
  and directed curvature-gap theory are open (candidate Weber collaboration).
- Curvature evaluated as a single object family; the agentic proposer is a bounded grid (an
  LLM-in-the-loop proposer is the natural extension).
- **Future:** (a) supply-chain *validation* — do curvature's cross-sector bridges match real
  customer–supplier links (WRDS `comp.seg_customer`)? a genuinely *structural* (non-covariance) test;
  (b) an LLM-proposer agent; (c) the descriptive systemic-risk monitoring product.

## References  *(to expand to 20–25 for submission)*
Sandhu et al. 2016; Samal et al. 2021; Forman 2003; Sreejith et al. 2016; Bennett-Cucuringu-Reinert
2022; Cartea-Cucuringu-Jin 2023; Lu et al. 2025; Tian-Lubberts-Weber 2025; Fesser-Weber-Lambiotte
2024; Ollivier 2009; + ICAIF agentic-AI line (LLM investment agents, TS-Agent, AAPM, FinRobot,
multi-agent reflection).
