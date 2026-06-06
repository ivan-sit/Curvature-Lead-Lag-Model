# Execution Plan

Companion to `CLAUDE.md` (the spec). This is the *how* and *when*.

**Anchor date:** 2026-06-05. **ICAIF target:** ~2026-08-02 (to confirm on the
official site) → ~8 weeks. Solo. The plan front-loads the two kill-switches and
puts a **go/no-go gate at the end of Week 3** that decides ICAIF-push vs.
285J-floor + later journal version.

## Guiding principles

1. **Build everything on synthetic data first**, where ground truth is known, then
   swap in WRDS. Nothing is blocked on data access.
2. **Kill-switches before stack.** Prove the code recovers known structure
   (synthetic directed-SBM) and that real lead-lag graphs are not triangle-sparse
   *before* investing in the L(G)/AFRC machinery.
3. **Primary metric = out-of-sample directional IC.** PnL/AlphaMark is optional.
4. **Every claim gets an adversarial test** (config-model null, BH multiplicity,
   train/val/test split, bootstrap stability).

## Repo layout

```
src/cllm/
  synthetic.py    # planted directed-SBM + factor/lead-lag return generators
  network.py      # BCR lead-lag estimation -> directed graph -> sparsify
  residualize.py  # factor/sector residualization (BEFORE graph build)
  curvature.py    # 4 objects: plain / augmented F# / weighted / Ollivier-Ricci
  linegraph.py    # L(G), AFRC community detection, curvature gap Delta-kappa
  validation.py   # structural cascade + BH + splits + bootstrap stability
  evaluation.py   # OOS directional IC (primary) + baselines + block-bootstrap
  diagnostics.py  # kill-switch A (synthetic recovery), B (triangle density)
  data/           # WRDS adapter (stub) + free-data fallback
  pipeline.py     # end-to-end orchestration
  agent/          # propose-test-reject loop (LLM later; deterministic now)
tests/            # pytest, analytic + synthetic ground-truth checks
configs/          # yaml experiment configs (lags, sparsification, sweeps)
scripts/          # run_synthetic.py, run_wrds.py
```

## Phased schedule (8 weeks)

| Wk | Dates | Focus | Exit criterion / gate |
|---|---|---|---|
| 0 | Jun 5–7 | Scaffold, env, synthetic generators, curvature module + analytic tests | `pytest` green; curvature matches hand-computed values |
| 1 | Jun 8–14 | Data layer: WRDS CRSP+GICS (or free fallback), survivorship, residualization | Residualized returns validated; factor variance removed |
| 2 | Jun 15–21 | Lead-lag network (BCR), walk-forward + **Kill-switch A** (synthetic SBM recovery) | **GATE A:** pipeline recovers planted structure |
| 3 | Jun 22–28 | Full curvature on real graph + **Kill-switch B** (triangle density) | **GATE B (go/no-go):** not triangle-sparse → push ICAIF; else pivot |
| 4 | Jun 29–Jul 5 | Line graph + AFRC clustering + Delta-kappa; selection rule; sweep | Communities + Delta-kappa computed on real data |
| 5 | Jul 6–12 | Validation cascade (BH, splits, bootstrap); operating point on validate | **GATE C:** curvature structurally distinct from correlation/degree |
| 6 | Jul 13–19 | Primary eval: OOS directional IC vs all baselines; agent loop | **GATE D:** IC beats baselines out-of-sample |
| 7 | Jul 20–26 | Ablations (sparsification/lag/raw-vs-residual/overnight); figures; draft | Results frozen; long-form draft |
| 8 | Jul 27–Aug 1 | Compress to 8-page ACM sigconf; advisor review; submit | Submission by Aug 2 |

## Decision gates

- **Gate A (end W2):** synthetic directed-SBM recovery. If the pipeline can't
  recover known structure, fix before touching real data.
- **Gate B (end W3, go/no-go):** within-community triangle density. Triangle-sparse
  → AFRC gap collapses (Fesser-Weber-Lambiotte). Options if it fails: switch to
  common-neighbor triangle convention, relax sparsification, or reframe away from
  L(G)/AFRC. This gate decides whether Aug 2 ICAIF is realistic.
- **Gate C (end W5):** structural distinctness (Spearman<0.8, low Jaccard, |z|>2,
  residual signal survives residualization). If not distinct, the methodological
  claim fails — pivot framing.
- **Gate D (end W6):** OOS IC vs baselines. Decides ICAIF push vs journal.

## Realistic read

8 weeks solo to a clean ICAIF submission is aggressive. Lock the **285J floor**
(working pipeline + cascade + IC on real data) by ~W5–6; everything after is
upside. If gates slip, target the journal version (Quantitative Finance / JFDS /
Applied Network Science) with the full multi-frequency study.

## External dependencies / risks

- **WRDS access** is the critical path for *real-data* results (not for building
  or for the synthetic validation). Confirm institutional login + the `wrds`
  Python package early. Free-data fallback (daily) keeps development unblocked.
- **AlphaMark** schema only matters if the optional PnL appendix is pursued.
- **Directed L(G) / directed AFRC gap** are open-theory items — flagged, not
  assumed; undirected reduction is the honest baseline.
