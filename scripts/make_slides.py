#!/usr/bin/env python3
"""Generate the ~20-minute talk deck (PPTX) for the Ricci-curvature lead-lag study.

Clean, concise slides — few points each — following the arc:
  why Ricci curvature  ->  hypothesis  ->  what I did  ->  structural results  ->  implications

Run:  python scripts/make_slides.py
Out:  slides/Ricci_Curvature_LeadLag.pptx
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

# ---- palette -------------------------------------------------------------- #
INK = RGBColor(0x1F, 0x29, 0x37)      # near-black slate (titles)
BODY = RGBColor(0x37, 0x41, 0x51)     # dark gray (body text)
ACCENT = RGBColor(0x25, 0x63, 0xEB)   # blue (rules, accents)
MUTE = RGBColor(0x9C, 0xA3, 0xAF)     # light gray (footer)
PALE = RGBColor(0xEF, 0xF2, 0xFB)     # pale blue (table zebra)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Calibri"

# ---- geometry (16:9) ------------------------------------------------------ #
SW, SH = Inches(13.333), Inches(7.5)
ML = Inches(0.85)             # left margin
CW = Inches(11.6)             # content width
TITLE_TOP = Inches(0.7)


def _set(run, size, color, bold=False, italic=False, font=FONT):
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font


def _box(slide, left, top, width, height):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    return tb, tf


def _blank(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])  # blank layout


def _rule(slide, top, left=ML, width=Inches(2.0), color=ACCENT, h=Pt(3)):
    from pptx.enum.shapes import MSO_SHAPE
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, h)
    shp.fill.solid(); shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def _footer(slide, idx, section):
    _, tf = _box(slide, ML, Inches(6.95), CW, Inches(0.4))
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = f"{section}"
    _set(r, 11, MUTE)
    # page number right-aligned
    _, tf2 = _box(slide, Inches(11.8), Inches(6.95), Inches(1.4), Inches(0.4))
    p2 = tf2.paragraphs[0]; p2.alignment = PP_ALIGN.RIGHT
    r2 = p2.add_run(); r2.text = str(idx)
    _set(r2, 11, MUTE)


def title_slide(prs, title, subtitle, meta):
    s = _blank(prs)
    _rule(s, Inches(2.55), left=ML, width=Inches(2.4), color=ACCENT, h=Pt(4))
    _, tf = _box(s, ML, Inches(2.75), CW, Inches(2.2))
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = title
    _set(r, 40, INK, bold=True)
    p2 = tf.add_paragraph(); p2.space_before = Pt(14)
    r2 = p2.add_run(); r2.text = subtitle
    _set(r2, 22, ACCENT, italic=True)
    _, tf3 = _box(s, ML, Inches(5.35), CW, Inches(1.2))
    for i, line in enumerate(meta):
        p = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
        r = p.add_run(); r.text = line
        _set(r, 15, BODY)
    return s


def content_slide(prs, idx, section, title, bullets, lead=None):
    """bullets: list of str (level 0) or (str, level) tuples."""
    s = _blank(prs)
    _, tf = _box(s, ML, TITLE_TOP, CW, Inches(0.9))
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = title
    _set(r, 30, INK, bold=True)
    _rule(s, Inches(1.55))
    top = Inches(1.95)
    if lead:
        _, lf = _box(s, ML, top, CW, Inches(0.8))
        pp = lf.paragraphs[0]
        rr = pp.add_run(); rr.text = lead
        _set(rr, 19, ACCENT, italic=True)
        top = Inches(2.75)
    _, bf = _box(s, ML, top, CW, Inches(4.0))
    for i, b in enumerate(bullets):
        text, level = (b if isinstance(b, tuple) else (b, 0))
        p = bf.paragraphs[0] if i == 0 else bf.add_paragraph()
        p.level = level
        p.space_after = Pt(12 if level == 0 else 6)
        bullet = "•  " if level == 0 else "–  "
        r = p.add_run(); r.text = bullet + text
        _set(r, 21 if level == 0 else 18, BODY if level == 0 else MUTE,
             bold=False)
    _footer(s, idx, section)
    return s


def table_slide(prs, idx, section, title, headers, rows, note=None, lead=None,
                col_widths=None, highlight_rows=()):
    s = _blank(prs)
    _, tf = _box(s, ML, TITLE_TOP, CW, Inches(0.9))
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = title
    _set(r, 30, INK, bold=True)
    _rule(s, Inches(1.55))
    top = Inches(1.95)
    if lead:
        _, lf = _box(s, ML, top, CW, Inches(0.7))
        pp = lf.paragraphs[0]
        rr = pp.add_run(); rr.text = lead
        _set(rr, 18, ACCENT, italic=True)
        top = Inches(2.6)
    nr, nc = len(rows) + 1, len(headers)
    gtbl = s.shapes.add_table(nr, nc, ML, top, CW, Inches(0.5 * nr)).table
    if col_widths:
        for j, w in enumerate(col_widths):
            gtbl.columns[j].width = w
    # header
    for j, h in enumerate(headers):
        c = gtbl.cell(0, j)
        c.fill.solid(); c.fill.fore_color.rgb = ACCENT
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        para = c.text_frame.paragraphs[0]
        para.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
        run = para.add_run(); run.text = h
        _set(run, 15, WHITE, bold=True)
    # body
    for i, row in enumerate(rows, start=1):
        hl = (i - 1) in highlight_rows
        for j, val in enumerate(row):
            c = gtbl.cell(i, j)
            c.fill.solid()
            c.fill.fore_color.rgb = PALE if (hl or i % 2 == 0) else WHITE
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            para = c.text_frame.paragraphs[0]
            para.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            run = para.add_run(); run.text = val
            _set(run, 14, INK if hl else BODY, bold=hl)
    if note:
        _, nf = _box(s, ML, Inches(6.25), CW, Inches(0.7))
        pp = nf.paragraphs[0]
        rr = pp.add_run(); rr.text = note
        _set(rr, 14, MUTE, italic=True)
    _footer(s, idx, section)
    return s


def section_slide(prs, idx, kicker, big):
    s = _blank(prs)
    _rule(s, Inches(3.0), left=ML, width=Inches(1.8), color=ACCENT, h=Pt(4))
    _, tf = _box(s, ML, Inches(3.2), CW, Inches(1.6))
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = kicker
    _set(r, 16, ACCENT, bold=True)
    p2 = tf.add_paragraph(); p2.space_before = Pt(6)
    r2 = p2.add_run(); r2.text = big
    _set(r2, 34, INK, bold=True)
    return s


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = SW, SH
    n = 0

    def nx():
        nonlocal n; n += 1; return n

    # 1 — title
    title_slide(
        prs,
        "Ricci Curvature on Directed Lead-Lag Networks",
        "A structural study of factor-residualized information flow in US equities",
        ["Ivan Sit", "UCLA Math 285J — Agentic AI for Autonomous Research in Quant Finance",
         "Advisor: Prof. Mihai Cucuringu   ·   Target: ICAIF 2026"],
    )

    # 2 — what is curvature
    content_slide(
        prs, nx(), "Motivation", "Curvature, on a graph",
        ["Ricci curvature measures how a space bends — and how diffusion flows through it.",
         "On a graph it lives on each edge and has one intuitive meaning:",
         ("Negative = a bridge: connects separated regions, structurally isolated.", 1),
         ("Positive = an interior link: sits inside a dense cluster, many paths route around it.", 1),
         "A parameter-free, local number with a global meaning."],
        lead="Is this relationship a fragile bridge, or a redundant interior link?",
    )

    # 3 — why I got into it
    content_slide(
        prs, nx(), "Motivation", "Why I got into Ricci curvature",
        ["Sandhu, Georgiou & Tannenbaum (Science Advances, 2016):",
         ("Ollivier-Ricci curvature on equity correlation networks rises before crashes.", 1),
         ("Curvature as a systemic-fragility signal — geometry, not statistics.", 1),
         "It reframes a market as a shape whose bottlenecks you can measure.",
         "That raised the question this project asks."],
    )

    # 4 — the gap
    table_slide(
        prs, nx(), "Motivation", "The opening they left",
        ["Sandhu et al. (2016)", "This work"],
        [["Undirected correlation graph", "Directed lead-lag graph"],
         ["Correlation edges", "BCR signed lead-lag, residualized"],
         ["Ollivier-Ricci only", "Forman-Ricci (cheap, directed) + Ollivier"],
         ["Structural validation only", "Structural cascade + (exploratory) test"]],
        note="Markets have direction. The symmetric correlation matrix destroys it by construction.",
        col_widths=[Inches(5.8), Inches(5.8)],
    )

    # 5 — hypothesis
    content_slide(
        prs, nx(), "Hypothesis", "The hypothesis",
        ["Negatively-curved edges in the directed, factor-residualized lead-lag network "
         "mark structurally isolated pairs —",
         ("bridges between otherwise separated regions of the market —", 1),
         ("that correlation-, degree-, and undirected-curvature methods do not recover.", 1),
         "Lead-lag asymmetry encodes structure the symmetric correlation graph destroys."],
        lead="The claim is structural and falsifiable.",
    )

    # 6 — what I did, overview
    content_slide(
        prs, nx(), "What I did", "An autonomous pipeline, six stages",
        ["Residualize returns — remove market + sector first.",
         "Build the directed lead-lag network (BCR signed statistic).",
         "Compute four curvature objects.",
         "Line graph L(G) + curvature-based pair-communities.",
         "Structural validation cascade  →  curvature ≠ correlation/degree?",
         "Exploratory: out-of-sample directional IC vs baselines."],
    )

    # 7 — residualized lead-lag
    content_slide(
        prs, nx(), "What I did", "Step 1 — Residualized, directed network",
        ["Residualize first: on raw returns, market + sector dominate the graph —",
         ("otherwise curvature just rediscovers GICS sectors (instructor requirement).", 1),
         "Edge weight = BCR signed lead-lag:  w(i→j) = ρ_ij(τ*) − ρ_ji(τ*).",
         ("Antisymmetric → each pair is a directed edge in the sign direction.", 1),
         "Intraday: within-day estimator (lag pairs never cross the overnight gap)."],
    )

    # 8 — four objects
    table_slide(
        prs, nx(), "What I did", "Step 2 — Four curvature objects",
        ["Object", "Role"],
        [["Plain directed Forman  (4 − deg − deg)", "Degree BASELINE (signal ≡ 0 by design)"],
         ["Triangle-augmented  F# = F + 3m", "Higher-order: isolates 3m"],
         ["Weighted augmented directed Forman", "MAIN object"],
         ["Ollivier-Ricci  (optimal transport)", "Robustness / contrast (Sandhu's)"]],
        note="Plain Forman is an exact function of endpoint degrees — the baseline the rest must beat.",
        col_widths=[Inches(6.4), Inches(5.2)],
        highlight_rows=(2,),
    )

    # 9 — cascade
    content_slide(
        prs, nx(), "What I did", "Step 3 — The validation cascade",
        ["Goal: prove curvature is not a re-skin of correlation, degree, or sector.",
         "Spearman(F, |ρ|) — must be small.",
         "Top-K Jaccard vs correlation-ranked pairs — must be small.",
         "Degree-preserving configuration-model null (z-scores).",
         "Residual orthogonalization — regress out degree & |ρ|, keep the rest.",
         "Benjamini–Hochberg + strict train / validate / test split."],
        lead="This cascade is the methodological core.",
    )

    # 10 — data
    content_slide(
        prs, nx(), "What I did", "Data — all institutional (WRDS)",
        ["CRSP daily S&P 500, 2000–2024 — survivorship-correct, delisting-adjusted.",
         "Compustat GICS sectors — residualization & community-boundary tests.",
         "TAQ 30-min intraday — full-year 2019, ~155 large-caps (where lead-lag lives).",
         "Every network is built on factor-residualized returns."],
    )

    # 11 — section: structural results
    section_slide(prs, nx(), "RESULTS", "The structural result holds.")

    # 12 — result 1
    table_slide(
        prs, nx(), "Results", "Curvature is not correlation",
        ["Test", "Value", "Reading"],
        [["Top-K Jaccard vs correlation", "≈ 0.0", "near-disjoint pair sets"],
         ["Spearman(F, |ρ|)", "0.18", "weak (≪ 0.8 threshold)"]],
        lead="The pairs curvature flags are not the pairs correlation flags.",
        note="The directed graph carries lead-lag asymmetry the symmetric correlation graph cannot.",
        col_widths=[Inches(5.0), Inches(2.4), Inches(4.2)],
        highlight_rows=(0, 1),
    )

    # 13 — result 2
    table_slide(
        prs, nx(), "Results", "A clean degree ablation",
        ["Object", "R² on degree", "Reading"],
        [["Plain Forman", "1.00", "exact degree identity (calibration ✓)"],
         ["Augmented Forman", "0.56", "≈ 44% is NEW higher-order signal"]],
        lead="The +3m triangle term is genuinely not explained by degree.",
        note="Plain Forman is rightly a baseline; the augmented object earns its place.",
        col_widths=[Inches(4.2), Inches(3.0), Inches(4.4)],
        highlight_rows=(1,),
    )

    # 14 — result 3 triangle sparsity
    content_slide(
        prs, nx(), "Results", "The network is triangle-sparse",
        ["Most edges have few common-neighbor triangles; strict cyclic triangles ≈ 0.",
         "Only ~1% of triangles fall within a GICS sector.",
         "Two honest consequences:",
         ("AFRC community separability is intrinsically limited (Fesser–Weber–Lambiotte).", 1),
         ("The structure curvature surfaces is cross-sector — not aligned with GICS.", 1)],
        lead="A finding, not a bug.",
    )

    # 15 — predictive null
    table_slide(
        prs, nx(), "Results", "The predictive question — an honest null",
        ["Method", "Mean IC", "95% CI"],
        [["Undirected Forman", "+0.013", "[−0.016, +0.040]"],
         ["Curvature (aug, directed)", "+0.005", "[−0.016, +0.026]"],
         ["Correlation", "−0.003", "[−0.027, +0.024]"],
         ["Random", "−0.015", "[−0.031, +0.006]"]],
        lead="Out-of-sample directional IC (full-year 2019, within-day horizon).",
        note="Forman leads — but every CI spans zero, ranking flips across samples, "
             "and undirected ties directed. No significant predictive edge.",
        col_widths=[Inches(5.0), Inches(2.6), Inches(4.0)],
        highlight_rows=(0, 1),
    )

    # 16 — implications
    content_slide(
        prs, nx(), "Implications", "What it means",
        ["A new structural lens: directed residualized curvature surfaces pair structure "
         "correlation / degree / undirected methods miss.",
         "Directedness is structurally informative even where it is not predictive.",
         "Triangle sparsity is a first-class constraint for curvature methods in finance.",
         "An honest predictive null is a result — Sandhu's precedent: structural-only is publishable."],
    )

    # 17 — next / thanks
    content_slide(
        prs, nx(), "Close", "Next steps & thanks",
        ["Directed line-graph & directed AFRC-gap theory (possible Weber collaboration).",
         "Multi-frequency replication and curvature dynamics through 2020 stress.",
         "Write-up → 8-page ACM sigconf for ICAIF 2026.",
         "Thanks to Prof. Mihai Cucuringu and the 285J group."],
        lead="The paper stands on the structural result.",
    )

    out = Path("slides"); out.mkdir(exist_ok=True)
    path = out / "Ricci_Curvature_LeadLag.pptx"
    prs.save(str(path))
    print(f"saved {path}  ({n} slides)")


if __name__ == "__main__":
    build()
