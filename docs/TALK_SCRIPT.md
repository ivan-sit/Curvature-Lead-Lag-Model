# Talk script — Ricci Curvature on Directed Lead-Lag Networks
### ~20 minutes · 18 slides · spoken first-person · structural-only framing

> Delivery notes: ~60–70s per slide. The spine is **two hypotheses → answer both honestly**:
> H1 (structural distinctness) is **confirmed**; H2 (predictive edge) is **rejected** across
> 25 years. Don't oversell. The honesty is the strength.

---

### Slide 1 — Title  (~30s)
"Hi everyone. I'm going to walk through a project that asks a geometry question about markets:
if you treat the stock market as a network and measure its *curvature*, does that curvature tell
you something correlation can't? The short version is — it tells you something **structural**
that correlation misses, but it does **not** help you predict. Let me show you how I got there."

### Slide 2 — Curvature, on a graph  (~70s)
"First, what curvature even means on a graph. In geometry, curvature is how a space bends. On a
network it lives on each edge and has one clean meaning. A **negatively** curved edge is a
*bridge* — it connects two otherwise separate regions; cut it and the network falls apart. A
**positively** curved edge sits inside a dense cluster where lots of other paths route around it.
So curvature is a single local number that answers a global question: *is this connection a
fragile bridge, or a redundant interior link?* That's the question I wanted to ask about pairs of
stocks."

### Slide 3 — Why I got into Ricci curvature  (~70s)
"The reason I went down this road is a 2016 Science Advances paper by Sandhu and co-authors. They
put Ollivier-Ricci curvature on equity *correlation* networks and found that market-wide curvature
**rises before crashes** — curvature as a fragility signal. What grabbed me is that it's a
*geometric* statement about the market, not a statistical one. It reframes the market as a shape
whose bottlenecks you can measure. So the natural question: can we push this further?"

### Slide 4 — The opening they left  (~70s)
"Here's the opening they left. Their network was built on the **correlation** matrix — which is
**symmetric**. But markets have *direction*: some stocks lead, others lag. A symmetric correlation
graph erases that asymmetry by construction. So my research question is: **does Ricci curvature on
the *directed* lead-lag network reveal structure the undirected correlation view cannot?** That's
the whole project in one sentence."

### Slide 5 — Two hypotheses  (~70s)
"I split that into two falsifiable hypotheses. **H1, structural** — the primary claim: pairs that
curvature flags are *structurally distinct* from what correlation, degree, and undirected curvature
flag. **H2, predictive** — the secondary, more ambitious claim: those same pairs also carry
out-of-sample directional information, leader predicting lagger. The paper's claim rests on H1; H2
is exploratory. I'll answer both at the end, honestly."

### Slide 6 — The pipeline  (~70s)
"Here's the machinery, six automated stages. One: residualize returns — strip out market and
sector. Two: build the directed lead-lag network. Three: compute four curvature objects. Four:
build the line graph and detect pair-communities. Five: the validation cascade — the test of
whether curvature is really distinct. Six: out comes a set of structurally isolated pairs. The
whole thing runs end-to-end without me in the loop."

### Slide 7 — Step 1: Residualized, directed network  (~75s)
"Two design choices matter here. First, I residualize *before* building the graph. On raw returns,
market and sector dominate everything, so curvature would just rediscover GICS sectors — my advisor
was emphatic about this. Second, the edge weight is the Bennett-Cucuringu-Reinert signed lead-lag
statistic: it's *antisymmetric*, so each pair becomes a directed edge pointing from leader to
lagger. The lag τ-star is picked per pair, and for intraday I use a within-day estimator so a pair
never straddles the overnight gap. The candidate horizons are on the next slide."

### Slide 8 — Step 2: Four curvature objects  (~75s)
"I don't use one curvature — I use four, as an ablation. Plain directed Forman is literally four
minus the two endpoint degrees, so it's a pure *degree baseline* — by design it carries no
higher-order signal. Triangle-augmented adds three for every triangle the edge sits in — that's the
first genuinely higher-order term. My **main object** is weighted-augmented-directed Forman: it
folds in the lead-lag strength, the triangles, and the direction. And Ollivier-Ricci, the
transport-based one Sandhu used, is my robustness contrast. The point of the ablation: each row
adds one ingredient, so I can see exactly where any signal comes from."

### Slide 9 — Step 3: The validation cascade  (~70s)
"This is the methodological core — proving curvature isn't just correlation or degree wearing a
hat. I check the Spearman correlation between curvature and absolute correlation — it has to be
small. I check the top-K overlap between curvature-picked and correlation-picked pairs. I run a
degree-preserving rewiring null. And I regress curvature on degree and correlation and keep only
the residual. Plus multiplicity control and a strict train/validate/test split. If curvature
survives all of this, it's real structure."

### Slide 10 — Data  (~60s)
"Everything is institutional WRDS data. CRSP daily returns — survivorship-correct — for the
robustness check. Compustat GICS sectors for residualization. And TAQ 30-minute intraday bars,
which is where lead-lag actually lives. Every network is built on residualized returns."

### Slide 11 — Two regimes, two time horizons  (~70s)
"I ran the same method at two horizons. Intraday: 30-minute bars, lead-lag of one to three bars —
30 to 90 minutes — on about 155 large-caps for 2019. And daily: close-to-close, lead-lag of one to
five trading days, on the S&P 500. One coverage caveat I want to be upfront about: the **daily**
analysis spans the full **2000 to 2024**; the **intraday** is **2019 only**, because pulling 25
years of 30-minute TAQ would be over a hundred hours of queries. So intraday is the high-frequency
cross-check; daily is the long, broad backbone. No weekly or monthly."

### Slide 12 — RESULTS divider  (~15s)
"So — two hypotheses, two answers. Let me take them in turn."

### Slide 13 — H1: Curvature is not correlation  (~70s)
"First, distinctness, and I'm showing both horizons. The top-K overlap between curvature-picked and
correlation-picked pairs is essentially **zero** — they pick almost completely different pairs. The
rank correlation between curvature and absolute correlation is 0.18 intraday and 0.07 daily — both
far below the 0.8 line. So the pairs curvature calls structurally isolated are simply *not* the
pairs correlation calls strongly co-moving — and that holds across 25 years. This is the headline
result."

### Slide 14 — H1: A clean degree ablation  (~70s)
"Second, is curvature just node degree in disguise? Plain Forman regresses on degree with R-squared
exactly **one** — that's the pure baseline, and it confirms my test is calibrated. But the
*augmented* object has R-squared 0.56 intraday and 0.18 daily — meaning **44 to 82 percent** of it
is *not* explained by degree or correlation. That extra is the triangle term — genuine
higher-order structure. So curvature carries real information beyond connectivity, at both
horizons."

### Slide 15 — H1: The network is triangle-sparse  (~65s)
"One honest finding I want to flag, not hide. The lead-lag network is **triangle-sparse** — most
edges sit in very few triangles, and only about 1% of triangles fall *within* a GICS sector. Two
consequences: by a theorem of Fesser-Weber-Lambiotte, community separability is intrinsically
limited in sparse networks — so I'm careful there; and the structure curvature surfaces is
**cross-sector**, exactly what a sector-based view would miss. It's a finding, not a bug."

### Slide 16 — H2: The predictive test, both horizons  (~85s)
"Now the hard question — does any of this *predict*? Out-of-sample directional IC, both horizons.
Intraday 2019: the Forman family does lead the baselines — but every confidence interval spans
zero, so I can't call it real. And then the daily test, walk-forward across 21 windows, the full
25 years — this is decisive. Curvature's IC is **negative**, with a confidence interval that
**excludes zero on the wrong side**, while **correlation does best**, significantly positive. So
the intraday 'Forman leads' does **not** replicate. There is no predictive edge for curvature; on
the long span it actively underperforms correlation. I'm reporting that plainly."

### Slide 17 — Verdict: did the two hypotheses hold?  (~75s)
"So the verdict. **H1, structural distinctness — confirmed.** Zero overlap with correlation, low
rank correlation, real non-degree signal, robust across 25 years. **H2, predictive edge — not
supported.** Forman leads intraday but never significantly, and over 25 daily years curvature is
negative while correlation wins. And notice — even where H1 holds, undirected ties directed on
prediction, so directedness is *structurally* informative but not *predictively*. The paper stands
on H1, and I report H2's null transparently. That's the honest scientific result."

### Slide 18 — Where this could go  (~60s)
"Where this goes next. The toolkit isn't tied to lead-lag — maybe the more interesting move is to
point the same directed-curvature machinery at other market graphs entirely. There's open theory
on the directed line-graph and a directed curvature gap. And methodologically, this whole project
is a template for **autonomous, agent-driven research in quant finance**: an agent ran the full
loop — hypothesize, build, test, and honestly reject. Next is the write-up toward an ICAIF
submission. Happy to take questions."

---

## Q&A — likely questions, short answers
- **"Why only one year of intraday?"** Daily covers all 25 years; 30-min TAQ for 25 years is ~100+
  hours of pulls, so intraday 2019 is a cross-check, not the backbone. The daily walk-forward is
  the long test.
- **"Are returns adjusted?"** Daily uses CRSP total return (dividend + split adjusted) plus a
  delisting adjustment. Intraday uses within-day returns only, so overnight corporate actions
  never enter — no adjustment needed.
- **"Isn't a null result a failure?"** No — Sandhu et al. published a curvature-in-finance study
  with no backtest at all. The structural distinctness (H1) is the contribution; reporting H2's
  null is what makes it credible.
- **"Why Forman, not Ollivier?"** Forman is combinatorial and cheap, and extends naturally to
  directed graphs; Ollivier (optimal transport) is the robustness contrast — and it's negative on
  prediction too.
- **"What's the actual novelty over Sandhu?"** Directed instead of undirected, lead-lag instead of
  correlation, on residualized returns — and the directed-vs-undirected structural contrast is the
  new result.
