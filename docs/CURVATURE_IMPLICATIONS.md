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
