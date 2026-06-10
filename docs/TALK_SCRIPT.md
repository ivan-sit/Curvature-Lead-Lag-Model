# Talk script — CRISP: Curvature of Residualized, Signed Lead-Lag Pairs
### ~18–22 minutes · 24 slides · spoken first-person · mid-project seminar

> Delivery: this is a *research update / skeleton of the final paper*, not a finished project.
> Spine = **two hypotheses → answer both honestly**: H1 (structural distinctness) **confirmed**;
> H2 (predictive edge) **rejected** across 25 years. If short on time, compress slides 2–3
> (motivation) and merge the two agentic slides (20–21). Don't oversell — the honesty is the point.

---

### Slide 1 — Title: CRISP  (~30s)
"Hi everyone. The project is **CRISP** — Curvature of Residualized, Signed lead-lag Pairs. The
one-line version: if you treat the market as a *directed* network and measure its **curvature**,
that curvature reveals **structure** correlation misses — but, as I'll show honestly, it does
**not** help you predict. Let me walk through how I got there."

### Slide 2 — Curvature, on a graph  (~65s)
"What curvature means on a graph. It's a single number per edge. **Negative** = a *bridge*,
connecting otherwise separate regions — structurally isolated. **Positive** = an *interior link*
inside a dense cluster. So it answers one question locally: is this connection a fragile bridge or
a redundant interior link? That's exactly what I want to ask about pairs of stocks."

### Slide 3 — Why I got into Ricci curvature  (~60s)
"The seed was Sandhu et al., 2016, in Science Advances. They put Ollivier-Ricci curvature on equity
**correlation** networks and found curvature **rises before crashes** — curvature as a fragility
signal. It reframes the market as a *shape* whose bottlenecks you can measure. That's what made me
want to push it further."

### Slide 4 — The opening they left  (~60s)
"Here's the opening. Their graph was the **correlation** matrix — which is symmetric. But markets
have *direction*: some stocks lead, others lag, and a symmetric graph erases that. So the research
question: **does Ricci curvature on the *directed*, residualized lead-lag network reveal structure
the undirected correlation view cannot?**"

### Slide 5 — Two hypotheses  (~60s)
"Two falsifiable hypotheses. **H1, structural** — primary: curvature-flagged pairs are
*structurally distinct* from correlation, degree, and undirected curvature. **H2, predictive** —
secondary: those pairs also carry out-of-sample directional information. The claim rests on H1;
H2 is exploratory. I answer both at the end."

### Slide 6 — Related literature & contribution  (~65s)
"Where this sits. Sandhu used Ollivier-Ricci on undirected correlation nets — I make it directed
and use Forman. Forman and Samal give the curvature formulas — I make them directed, weighted, and
residualized. Bennett-Cucuringu-Reinert give the signed lead-lag estimator — I adopt it as the edge
weight. And Tian-Lubberts-Weber give line-graph curvature clustering, which I use in pair-space.
The **gap**: nobody has put directed curvature on a *residualized lead-lag* graph. That's the
contribution."

### Slide 7 — The pipeline  (~65s)
"The machinery — six automated stages. Residualize returns; build the directed lead-lag network;
compute four curvature objects; build the line graph and pair-communities; run the validation
cascade; out come the structurally isolated pairs. It runs end-to-end without me in the loop."

### Slide 8 — Step 1: Residualized, directed network  (~70s)
"Two key choices. I residualize *before* building the graph — otherwise market and sector dominate
and curvature just rediscovers GICS sectors. And the edge weight is the Bennett-Cucuringu-Reinert
signed lead-lag statistic — it's antisymmetric, so each pair becomes a directed edge from leader to
lagger. Lag is picked per pair; intraday uses a within-day estimator so pairs never cross the
overnight gap."

### Slide 9 — Step 2: Four curvature objects  (~70s)
"Four curvatures, as an ablation. Plain directed Forman is just four minus the endpoint degrees —
a pure **degree baseline**. Triangle-augmented adds the first higher-order term. My **main object**
is weighted-augmented-directed Forman — lead-lag strength, triangles, and direction. And
Ollivier-Ricci is the transport-based contrast. Each row adds one ingredient, so I can see exactly
where any signal comes from."

### Slide 10 — Step 3: The validation cascade  (~65s)
"The methodological core — proving curvature isn't correlation or degree in disguise. Spearman of
curvature against absolute correlation; top-K overlap of the picked pairs; a degree-preserving
rewiring null; and a regression that strips out degree and correlation and keeps the residual. Plus
multiplicity control and a strict train/validate/test split."

### Slide 11 — Data  (~55s)
"All institutional WRDS. CRSP daily for the long span; Compustat GICS for residualization; and TAQ
30-minute intraday, where lead-lag actually lives. Every network is built on residualized returns."

### Slide 12 — Two regimes, two horizons  (~70s)
"Two horizons. Intraday: 30-minute bars, lead-lag of 30 to 90 minutes, ~155 names, 2019. Daily:
close-to-close, one to five days, S&P 500. One honest caveat: **daily spans the full 2000–2024;
intraday is 2019 only**, because 25 years of 30-minute TAQ is over a hundred hours of pulls. So
intraday is the high-frequency cross-check; daily is the long backbone."

### Slide 13 — RESULTS divider  (~15s)
"So — two hypotheses, two answers."

### Slide 14 — H1: Curvature is not correlation  (~65s)
"Distinctness, both horizons. The overlap between curvature-picked and correlation-picked pairs is
essentially **zero**. The rank correlation between curvature and absolute correlation is 0.18
intraday, 0.07 daily — both far below 0.8. So curvature's isolated pairs are *not* correlation's
co-moving pairs, and that holds across 25 years. This is the headline."

### Slide 15 — H1: A clean degree ablation  (~65s)
"Is curvature just degree? Plain Forman regresses on degree with R-squared exactly **one** — the
pure baseline, and proof the test is calibrated. But augmented Forman is 0.56 intraday, 0.18 daily
— so **44 to 82 percent** is *not* degree. That extra is the triangle term — real higher-order
structure, at both horizons."

### Slide 16 — H1: The network is triangle-sparse  (~55s)
"One honest finding. The network is **triangle-sparse**, and only ~1% of triangles are within a
GICS sector. Two consequences: community separability is intrinsically limited there — I'm careful
about that — and the structure curvature finds is **cross-sector**, which a sector view would miss.
A finding, not a bug."

### Slide 17 — H2: The predictive test, both horizons  (~80s)
"The hard question — does it *predict*? Out-of-sample directional IC. Intraday 2019: Forman leads
the baselines, but every confidence interval spans zero — I can't call it real. The daily test,
walk-forward across 21 windows and 25 years, is decisive: curvature's IC is **negative**, with a CI
that excludes zero, while **correlation does best**, significantly positive. The intraday 'Forman
leads' does **not** replicate. No predictive edge for curvature."

### Slide 18 — Verdict: did the two hypotheses hold?  (~70s)
"The verdict. **H1 — confirmed.** Zero overlap with correlation, real non-degree signal, robust
across 25 years. **H2 — not supported.** Never significant intraday, and negative over 25 daily
years while correlation wins. And note: even where H1 holds, undirected ties directed on
prediction — directedness is *structurally* informative, not *predictively*. The paper stands on
H1; I report H2's null transparently."

### Slide 19 — Robustness & ablations  (~55s)
"This is stress-tested. The four-object ablation isolates where signal comes from; two horizons;
a 21-window walk-forward rather than one split; five baselines including correlation,
cointegration, and undirected Forman; and I settled the triangle convention with the data, not by
assumption."

### Slide 20 — Agentic AI workflow: where it was used  (~70s)
"Since this is the agentic-AI course — where the tools actually went. An agent built the entire
six-module pipeline and 50 tests; ran the WRDS data pulls autonomously; caught its own bugs,
including a TAQ memory bug and a gitignore data-loss bug; designed experiments like the within-day
estimator and the walk-forward; and generated this deck, the report, and the talk script. The
reflection: building and testing this pipeline, pulling 25 years of data plus intraday TAQ, running
a 21-window walk-forward, *and* writing it up — that's days instead of months."

### Slide 21 — Agentic AI: what worked vs. what needed a human  (~60s)
"But it wasn't hands-off. The machine did the building — pipeline, data, debugging, experiments.
The **researcher** did the judgment: the decision to reframe from predictive to structural, the
decision *not* to p-hack toward significance, and the domain calls on horizons, coverage, and how
to read an honest null. Agentic AI did the building; human judgment set the framing."

### Slide 22 — Limitations  (~55s)
"Limitations, plainly. Intraday is 2019 only, by cost. The network is triangle-sparse, which limits
community methods. The directed line-graph and directed curvature-gap are theoretically open, so I
use the undirected reduction. IC is at a fixed k, not pre-registered. And the daily universe is
survivor-biased within each window."

### Slide 23 — Future work & submission  (~55s)
"Future work. Point the same directed-curvature tools at *other* market graphs, beyond lead-lag.
Develop the directed line-graph and curvature-gap theory — possibly with Melanie Weber. If I
revisit prediction, do it as a pre-registered confirmatory test. And the big deferred-by-cost
experiment is multi-year intraday. Target: extend to an 8-page ACM sigconf for **ICAIF 2026,
deadline August 2**."

### Slide 24 — Project Status Overview  (~45s)
"Where things stand. **Completed**: the full pipeline and tests, the four curvature objects, the
structural cascade, the two-horizon 25-year predictive test, the WRDS data, and the write-up.
**In progress**: the agentic propose-test-reject orchestrator, the LaTeX main file, and expanding
the bibliography. **Remaining before the final**: the directed line-graph theory, multi-year
intraday if budget allows, and the final eight-page write-up. Thanks — happy to take questions."

---

## Q&A — likely questions, short answers
- **"Why only one year of intraday?"** Daily covers all 25 years; 30-min TAQ for 25 years is ~100+
  hours of pulls, so intraday 2019 is a cross-check. The daily walk-forward is the long test.
- **"Are returns adjusted?"** Daily uses CRSP total return (dividend + split adjusted) plus a
  delisting adjustment. Intraday uses within-day returns only, so overnight corporate actions never
  enter — no adjustment needed.
- **"Isn't a null result a failure?"** No — Sandhu et al. published a curvature-in-finance study
  with no backtest at all. H1 (structural distinctness) is the contribution; reporting H2's null
  is what makes it credible.
- **"Why Forman, not Ollivier?"** Forman is combinatorial, cheap, and extends naturally to directed
  graphs; Ollivier is the robustness contrast — and it's negative on prediction too.
- **"Novelty over Sandhu?"** Directed not undirected, lead-lag not correlation, on residualized
  returns — the directed-vs-undirected structural contrast is the new result.
- **"Where did agentic AI fall short?"** It needed a human for the framing decision (structural vs
  predictive) and the discipline not to over-search for a significant predictive result.
