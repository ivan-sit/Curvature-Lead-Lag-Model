# Orchestrator findings — propose → test → reject log

Proposed **12** candidate signals · accepted **6** · rejected **6**.

| cand | residualize | thr | curvature | verdict | spearman | jaccard | R²(deg) | reason |
|---|---|---|---|---|---|---|---|---|
| cand000 | market | 0.9 | F_plain | ❌ reject | 0.23 | 0.00 | 1.00 | R2-on-degree 1.00 >= 0.95 (~degree, no higher-order) |
| cand001 | market | 0.9 | F_augmented | ✅ accept | 0.27 | 0.00 | 0.53 |  |
| cand002 | market | 0.95 | F_plain | ❌ reject | 0.16 | 0.03 | 1.00 | R2-on-degree 1.00 >= 0.95 (~degree, no higher-order) |
| cand003 | market | 0.95 | F_augmented | ✅ accept | 0.21 | 0.00 | 0.67 |  |
| cand004 | market_sector | 0.9 | F_plain | ❌ reject | 0.14 | 0.00 | 1.00 | R2-on-degree 1.00 >= 0.95 (~degree, no higher-order) |
| cand005 | market_sector | 0.9 | F_augmented | ✅ accept | 0.21 | 0.00 | 0.51 |  |
| cand006 | market_sector | 0.95 | F_plain | ❌ reject | 0.12 | 0.00 | 1.00 | R2-on-degree 1.00 >= 0.95 (~degree, no higher-order) |
| cand007 | market_sector | 0.95 | F_augmented | ✅ accept | 0.17 | 0.03 | 0.66 |  |
| cand008 | pca | 0.9 | F_plain | ❌ reject | 0.24 | 0.00 | 1.00 | R2-on-degree 1.00 >= 0.95 (~degree, no higher-order) |
| cand009 | pca | 0.9 | F_augmented | ✅ accept | 0.18 | 0.00 | 0.45 |  |
| cand010 | pca | 0.95 | F_plain | ❌ reject | 0.25 | 0.05 | 1.00 | R2-on-degree 1.00 >= 0.95 (~degree, no higher-order) |
| cand011 | pca | 0.95 | F_augmented | ✅ accept | 0.19 | 0.03 | 0.64 |  |
