# What can curvature signify? — exhaustive implication search (honest log)

We tested whether curvature on the equity network signifies anything useful, across
~12 distinct targets, on 25 years of daily data (fixed 195-name universe, 63-day
rolling windows). **Every forward/cross-sectional test uses a partial control** (for
current volatility or current correlation), so a result only counts if curvature
adds signal *beyond* plain correlation/volatility.

## The one survivor
| Test | Result | Verdict |
|---|---|---|
| Aggregate curvature vs **market volatility** (contemporaneous) | Spearman **−0.78** | ✓ strong — reproduces Sandhu/Samal |

Curvature is a genuine **real-time fragility thermometer**: it drops hard when the
market is volatile. But density (+0.78) and mean-correlation (+0.75) carry the same
information — so it is **equivalent to the correlation level**, not a value-add.

## Everything unique / predictive — discarded (all partial |corr| ≤ 0.16)
| Hypothesis | Partial (vs control) | Verdict |
|---|---|---|
| Curvature **leads** volatility | +0.07 | null |
| Node curvature ranks **stock risk** | IC +0.01 | null |
| Curvature predicts **drawdowns** beyond vol | −0.11 (sign-flipped) | null |
| Δcurvature / dispersion / leadership concentration | ≤ 0.14 | null |
| Future market **return** (timing) | −0.04 | null |
| Future **skew / kurtosis** (tail risk) | −0.00 / −0.04 | null |
| **Contagion** (future correlation) | +0.11 | null |
| **EPS / earnings risk** (fundamentals) | −0.16 | null |
| **Directed** version beats correlation | no | — |

## Honest conclusion
On equity networks, curvature is a **valid but redundant fragility indicator** — it
confirms market stress in real time (matching the literature) but, across a wide net
of targets including fundamentals, **adds no independent predictive power over plain
correlation/volatility**, and the **directed lead-lag version does not beat the
correlation version**. This is consistent with the project's spine: structure yes
(H1), prediction no (H2) — and now, fragility-tracking yes, but not uniquely.

Further searching past this point would be p-hacking; the negative is the result.

## Round 4 — diversification (risk application) + the unifying reason

| Portfolio (OOS, equal-weight, monthly) | vol all | dd all | vol crisis | dd crisis |
|---|---|---|---|---|
| correlation (min-corr) | 0.160 | -0.040 | 0.620 | -0.161 |
| structural (lead-lag communities) | 0.166 | -0.041 | 0.667 | -0.168 |
| random | 0.169 | -0.043 | 0.578 | -0.142 |

Structural diversification is slightly WORSE than correlation diversification, overall
and in crises. Null.

**The unifying reason (why all 13 tests are null):** portfolio risk / diversification
is the covariance matrix, which *is* correlation; return prediction isn't topology.
Every standard financial objective is covariance- or return-determined, and curvature's
unique information is *topological* — orthogonal to those objectives. So curvature
cannot beat correlation at any of them by construction.

## Final conclusion
Curvature's value is **descriptive / structural, not optimization**: mapping hidden
cross-sector wiring, flagging specific critical links for stress-testing, detecting
structural regime change. It is a market-structure microscope, not an alpha or risk
engine. (Tested across 13 targets; topology ⟂ covariance.) Stop here — more is p-hacking.

## Round 5 — shock propagation + VIX (the professor's idea)
- **Directed shock propagation** (does a big move in source s propagate to its laggers at t+1,
  beyond correlation?): IC +0.002 even conditioning on 536k shock events. Null.
- **VIX (implied vol; WRDS cboe.cboe, matches CBOE exactly):** curvature tracks VIX at -0.52
  (worse than realized vol's +0.81), does NOT lead VIX controlling current VIX (partial ~0); a
  faint sub-threshold hint (~0.10) at 10-21d after controlling VIX+rvol. Null/borderline — fits
  topology ⟂ covariance (VIX is expectation/covariance-determined).

Total: ~14 targets, one survivor (vol-tracking, = correlation). Conclusion unchanged.

## Round 6 — THE POSITIVE RESULT: curvature recovers real economic links
Curvature's cross-sector bridges (most-negative augmented Forman, residualized lead-lag) are
ENRICHED for real customer-supplier links (comp.wrds_seg_customer), 221-name universe, 131 links:
  top-300 bridges: 6 economic links vs 1.6 expected = 3.7x, **p=0.006 (significant)**
  top-500 bridges: 7 vs 2.7 = 2.6x, p=0.019 (significant)
  top-correlation pairs: 0x (correlation captures NO cross-sector economic links).

**Reconciliation / the thesis:** topology ⟂ covariance => curvature can't beat correlation at
risk/return (covariance objectives). BUT curvature's TOPOLOGY recovers ECONOMIC structure
(supply-chain links) that correlation misses entirely (it picks within-sector co-movers; the real
links are cross-sector, where the bridges live). Curvature is a structural-DISCOVERY tool, not a
risk/return optimizer. This is the positive, non-covariance, ICAIF-anchor result.
Caveat: absolute counts modest, name-matching coarse (undercounts links); enrichment direction is
robust and significant at top-300/500.

## Round 7 — alpha path (closed)
Cohen-Frazzini link momentum (monthly, raw returns, 221-name universe):
  (1) REAL customer-supplier links: +2.5%/yr, t=1.22 (weak — effect lives in small-caps, not large)
  (2) curvature-discovered bridges: +0.5%/yr, t=0.30 (diluted)
  (3) all cross-sector edges:       +0.0%/yr, t=0.03
=> No tradeable alpha: the underlying momentum is weak in large-caps AND curvature's discovery is
too sparse to isolate it. Curvature's contribution = structural DISCOVERY (significant link
recovery, p=0.006), NOT alpha. Final, consistent.

## Round 8 — small/mid-cap retest: the discovery does NOT replicate
Broad small/mid-cap universe (1290 names, 1182 real customer-supplier links):
  enrichment: top-300 2.3x p=0.35, top-500 1.4x p=0.51, top-1000 0.7x p=0.76 (1 hit total) -- NULL
  momentum: REAL links -0.2%/yr t=-0.14; curvature bridges -0.4%/yr t=-0.12 -- NULL
=> The large-cap enrichment (3.7x, p=0.006, ~6 hits) is LARGE-CAP SPECIFIC and FRAGILE; it does not
generalize. No link-momentum alpha (even on real links, because this universe is the most-liquid
small/mid-caps, not the under-covered micro-caps where Cohen-Frazzini lives). HONEST status: the
economic-link discovery is a SUGGESTIVE large-cap observation, not a robust result. Robust findings
remain: H1 distinctness + topology ⟂ covariance.

## Round 9 — FALSE POSITIVE: clean resolved links kill the enrichment
Re-ran with RESOLVED supply-chain IDs (wrdsapps_link_supplychain.seglink: gvkey->cgvkey, no fuzzy
name matching):
  LARGE-CAP (103 clean links): curvature top-300/500 = 0 links, 0x, p=1 (top-1000 0.4x). corr also 0x.
  SMALL-CAP (309 clean links): curvature top-300/500 = 0 links, 0x, p=1. corr also 0x.
=> The earlier 3.7x/p=0.006 was a FUZZY-NAME-MATCHING ARTIFACT. With clean IDs there is NO enrichment;
neither curvature nor correlation price-networks recover disclosed supply-chain links. Economic-link
DISCOVERY is dead. Lesson: entity-resolution matters; the clean test (motivated by non-replication)
caught a false positive before publication.

## FINAL STANDING (after 18+ tests)
Robust: (1) H1 structural distinctness (curvature != correlation/degree/undirected; cross-sector),
(2) topology ⟂ covariance — no edge across 14 covariance/return objectives. Everything else null,
incl. the economic-link discovery (false positive). Curvature is a structural lens distinct from
correlation but orthogonal to financial objectives. Honest, complete.

## Round 10 — Sandhu extension on RAW returns (the fragility angle, done right)
Undirected correlation curvature tracks vol at -0.76 (reproduces Sandhu/Samal). But the DIRECTED
lead-lag curvature: tracks weaker (+0.42), does NOT lead the undirected curvature (partial -0.05 to
-0.08), does NOT predict forward vol beyond vol+undirected (+0.01). => The directed/novel angle adds
NOTHING to Sandhu's existing undirected result. The positive (curvature->fragility) is Sandhu's; our
directed extension does not improve it. 19 tests; no novel positive from directedness.
