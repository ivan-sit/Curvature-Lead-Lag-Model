"""cllm — Curvature Lead-Lag Model.

Weighted augmented directed Forman-Ricci curvature on factor-residualized
lead-lag networks of US equities, for selecting pairs whose directed
predictability is structurally distinct from correlation/degree/undirected
methods.

See CLAUDE.md for the full specification and docs/PLAN.md for the execution plan.

Module map
----------
synthetic    : planted directed-SBM graphs + factor/lead-lag return generators
network      : Bennett-Cucuringu-Reinert lead-lag estimation + directed graph build
residualize  : factor/sector residualization of returns (do BEFORE graph build)
curvature    : the four curvature objects (plain / augmented / weighted / Ollivier)
linegraph    : L(G) construction, AFRC community detection, curvature gap
validation   : structural validation cascade (the methodological contribution)
evaluation   : out-of-sample directional IC (primary) + baselines
diagnostics  : kill-switch A (synthetic recovery) + kill-switch B (triangle density)
pipeline     : end-to-end orchestration
"""

__version__ = "0.1.0"
