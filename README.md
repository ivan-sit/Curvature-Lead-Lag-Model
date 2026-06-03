# Curvature Lead-Lag Model

Discrete **Forman-Ricci curvature on directed lead-lag networks** of US equities,
for selecting statistical-arbitrage pairs that are *structurally distinct* from
those surfaced by correlation-based methods.

UCLA Math 285J project (advisor: Prof. Mihai Cucuringu), engineered toward an
**ICAIF 2026** submission (deadline Aug 2, 2026). Full specification, exact
mathematics, data sources, and risks are in [`CLAUDE.md`](./CLAUDE.md).

## Core hypothesis

> Negatively-curved edges in the *directed* lead-lag network mark structurally
> isolated pairs — bridges between separated market regions — that correlation
> and undirected-curvature methods overlook.

## Two deliverables (kept separate)

1. **Structural distinctness** — a validation cascade proving curvature is not a
   re-skin of correlation/degree (Spearman < 0.8, low top-K Jaccard,
   configuration-model null z-scores, residual orthogonalization, AFRC gap).
2. **Performance** — mean-reversion trading on selected pairs, benchmarked via
   **AlphaMark** vs. correlation-distance / correlation-clustering / cointegration
   / random baselines, *plus a return-correlation diversification test*.

## Build order (de-risked — kill-switches first)

| Phase | What | Status |
|---|---|---|
| 0 | Scaffold & git | ✅ in progress |
| 1 | WRDS/CRSP data ingest (point-in-time, survivorship) | ⬜ |
| 2 | Lead-lag network (BCR signed statistic, walk-forward) | ⬜ |
| 3 | **Kill-switch A**: planted directed-SBM sanity of full pipeline | ⬜ |
| 4 | **Kill-switch B**: within-sector triangle density (decision gate) | ⬜ |
| 5 | Curvature module — weighted directed `F` + augmented `F#` | ⬜ |
| 6 | Line graph `L(G)` + AFRC clustering | ⬜ |
| 7 | Validation cascade + threshold sweep (operating point on held-out) | ⬜ |
| 8 | AlphaMark integration + baselines + diversification test | ⬜ |
| 9 | Critic/orchestrator wrapper (thin) | ⬜ |
| 10 | Write-up → 8-page ACM `sigconf` | ⬜ |

## Key risks (see `CLAUDE.md` §10)

1. **Triangle sparsity** — may collapse the AFRC curvature gap and the whole
   `L(G)` thesis. Diagnosed before building the stack (Phase 4 gate).
2. **Directed line graph** — Tian-Lubberts-Weber framework is undirected; a
   directed construction is an open problem / possible theory contribution.
3. **Directed AFRC gap** — SBM recovery guarantees are undirected-only.
