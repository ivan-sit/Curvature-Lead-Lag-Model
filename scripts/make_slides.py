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
from pptx.enum.shapes import MSO_SHAPE
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


def content_slide(prs, idx, section, title, bullets, lead=None, closer=None):
    """bullets: list of str (level 0) or (str, level) tuples.

    ``closer`` (optional): a highlighted call-out box near the bottom — used to
    land a research question or a one-line punch.
    """
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
    _, bf = _box(s, ML, top, CW, Inches(3.0 if closer else 4.0))
    for i, b in enumerate(bullets):
        text, level = (b if isinstance(b, tuple) else (b, 0))
        p = bf.paragraphs[0] if i == 0 else bf.add_paragraph()
        p.level = level
        p.space_after = Pt(12 if level == 0 else 6)
        bullet = "•  " if level == 0 else "–  "
        r = p.add_run(); r.text = bullet + text
        _set(r, 21 if level == 0 else 18, BODY if level == 0 else MUTE,
             bold=False)
    if closer:
        from pptx.enum.shapes import MSO_SHAPE
        box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, ML, Inches(5.45),
                                 CW, Inches(1.15))
        box.fill.solid(); box.fill.fore_color.rgb = PALE
        box.line.color.rgb = ACCENT; box.line.width = Pt(1.25)
        box.shadow.inherit = False
        ctf = box.text_frame; ctf.word_wrap = True
        ctf.vertical_anchor = MSO_ANCHOR.MIDDLE
        ctf.margin_left = Inches(0.25); ctf.margin_right = Inches(0.25)
        cp = ctf.paragraphs[0]
        lbl = cp.add_run(); lbl.text = "Research question   "
        _set(lbl, 14, ACCENT, bold=True)
        rr = cp.add_run(); rr.text = closer
        _set(rr, 18, INK, bold=True)
    _footer(s, idx, section)
    return s


def _fill_cell(cell, val, size, color, bold, align):
    """Write possibly multi-line text into a table cell (split on '\\n')."""
    tf = cell.text_frame
    for k, line in enumerate(str(val).split("\n")):
        para = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        para.alignment = align
        run = para.add_run(); run.text = line
        _set(run, size, color, bold=bold)


def table_slide(prs, idx, section, title, headers, rows, note=None, lead=None,
                col_widths=None, highlight_rows=(), align=None):
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
    amap = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}
    aligns = [amap[a] for a in align] if align else \
        [PP_ALIGN.LEFT] + [PP_ALIGN.CENTER] * (nc - 1)
    # header
    for j, h in enumerate(headers):
        c = gtbl.cell(0, j)
        c.fill.solid(); c.fill.fore_color.rgb = ACCENT
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        _fill_cell(c, h, 15, WHITE, True, aligns[j])
    # body
    for i, row in enumerate(rows, start=1):
        hl = (i - 1) in highlight_rows
        for j, val in enumerate(row):
            c = gtbl.cell(i, j)
            c.fill.solid()
            c.fill.fore_color.rgb = PALE if (hl or i % 2 == 0) else WHITE
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            _fill_cell(c, val, 14, INK if hl else BODY, hl, aligns[j])
    if note:
        _, nf = _box(s, ML, Inches(6.25), CW, Inches(0.7))
        pp = nf.paragraphs[0]
        rr = pp.add_run(); rr.text = note
        _set(rr, 14, MUTE, italic=True)
    _footer(s, idx, section)
    return s


def _flowbox(slide, x, y, w, h, title, sub=None, accent=False):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    shp.fill.solid(); shp.fill.fore_color.rgb = ACCENT if accent else PALE
    shp.line.color.rgb = ACCENT; shp.line.width = Pt(1.25)
    shp.shadow.inherit = False
    tf = shp.text_frame; tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.08); tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.03); tf.margin_bottom = Inches(0.03)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = title
    _set(r, 14, WHITE if accent else INK, bold=True)
    if sub:
        p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER; p2.space_before = Pt(2)
        r2 = p2.add_run(); r2.text = sub
        _set(r2, 10, RGBColor(0xE5, 0xED, 0xFF) if accent else MUTE)


def _arrow(slide, kind, x, y, w, h):
    shp = slide.shapes.add_shape(kind, x, y, w, h)
    shp.fill.solid(); shp.fill.fore_color.rgb = ACCENT
    shp.line.fill.background(); shp.shadow.inherit = False


def pipeline_slide(prs, idx, section, title, stages, lead=None):
    """Six-stage pipeline as a snake flow chart (3 top L->R, 3 bottom R->L)."""
    s = _blank(prs)
    _, tf = _box(s, ML, TITLE_TOP, CW, Inches(0.9))
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = title
    _set(r, 30, INK, bold=True)
    _rule(s, Inches(1.55))
    if lead:
        _, lf = _box(s, ML, Inches(1.75), CW, Inches(0.6))
        rr = lf.paragraphs[0].add_run(); rr.text = lead
        _set(rr, 18, ACCENT, italic=True)
    bw, bh = Inches(3.3), Inches(1.1)
    xs = [ML, Inches(4.6), Inches(8.35)]
    ytop, ybot = Inches(2.55), Inches(4.75)
    ah = Inches(0.34)
    # top row, left -> right
    for k in range(3):
        _flowbox(s, xs[k], ytop, bw, bh, stages[k][0], stages[k][1])
    _arrow(s, MSO_SHAPE.RIGHT_ARROW, Inches(4.18), ytop + Inches(0.38), Inches(0.42), ah)
    _arrow(s, MSO_SHAPE.RIGHT_ARROW, Inches(7.93), ytop + Inches(0.38), Inches(0.42), ah)
    # down on the right
    _arrow(s, MSO_SHAPE.DOWN_ARROW, Inches(9.83), Inches(3.7), ah, Inches(1.0))
    # bottom row, right -> left (so the flow continues 4 -> 5 -> 6)
    bottom_x = [Inches(8.35), Inches(4.6), ML]
    for k in range(3):
        _flowbox(s, bottom_x[k], ybot, bw, bh, stages[3 + k][0], stages[3 + k][1],
                 accent=(3 + k == 5))
    _arrow(s, MSO_SHAPE.LEFT_ARROW, Inches(7.93), ybot + Inches(0.38), Inches(0.42), ah)
    _arrow(s, MSO_SHAPE.LEFT_ARROW, Inches(4.18), ybot + Inches(0.38), Inches(0.42), ah)
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

    # 4 — the one opening -> research question
    content_slide(
        prs, nx(), "Motivation", "The opening they left",
        ["Sandhu et al. built the network on an undirected correlation graph.",
         "But markets have direction — some names lead, others lag.",
         ("The symmetric correlation graph erases that asymmetry by construction.", 1)],
        lead="One thing their construction could not see: direction.",
        closer="Does Ricci curvature on the directed, residualized lead-lag network reveal "
               "structure the undirected correlation view cannot?",
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

    # 6 — what I did, overview (flow chart)
    pipeline_slide(
        prs, nx(), "What I did", "The pipeline",
        [("Residualize returns", "remove market + sector"),
         ("Directed lead-lag network", "BCR signed statistic"),
         ("Four curvature objects", "plain → weighted aug. directed"),
         ("Line graph  L(G)", "curvature pair-communities"),
         ("Validation cascade", "curvature ≠ corr / degree?"),
         ("Structurally isolated pairs", "the structural output")],
        lead="Six stages, fully automated.",
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

    # 8 — four objects (with plain-language "what it measures")
    table_slide(
        prs, nx(), "What I did", "Step 2 — Four curvature objects",
        ["Object", "What it measures", "Role"],
        [["Plain directed Forman\n4 − deg_in − deg_out",
          "only the two endpoints' link counts — pure connectivity",
          "Degree BASELINE\n(no higher-order signal)"],
         ["Triangle-augmented\nF# = F + 3m",
          "+3 for every triangle the edge sits inside",
          "Higher-order:\nisolates the 3m term"],
         ["Weighted augmented\ndirected Forman",
          "lead-lag strength + triangles + edge direction",
          "MAIN object"],
         ["Ollivier-Ricci\n(optimal transport)",
          "cost to morph one node's neighborhood into the other's",
          "Robustness / contrast\n(Sandhu's)"]],
        lead="One ablation, from pure degree to full directed curvature.",
        note="Plain Forman is an exact function of endpoint degrees — the baseline the rest must beat.",
        col_widths=[Inches(3.6), Inches(4.7), Inches(3.3)],
        align=["l", "l", "l"],
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

    # 10 — data (what each source is FOR)
    table_slide(
        prs, nx(), "What I did", "Data — all institutional (WRDS)",
        ["Source", "What it is", "What it's for"],
        [["CRSP", "daily S&P 500 returns, 2000–2024\n(survivorship-correct)",
          "daily-frequency robustness check"],
         ["Compustat", "GICS sector classifications",
          "residualize returns; sector-boundary tests"],
         ["TAQ", "30-min intraday bars, full-year 2019\n(~155 large-caps)",
          "the HEADLINE network — where lead-lag lives"]],
        lead="Every network is built on factor-residualized returns.",
        note="Intraday is the main result; daily is the robustness check.",
        col_widths=[Inches(2.0), Inches(5.4), Inches(4.2)],
        align=["l", "l", "l"],
        highlight_rows=(2,),
    )

    # 11 — section: structural results
    section_slide(prs, nx(), "RESULTS", "The structural result holds.")

    # 12 — result 1
    table_slide(
        prs, nx(), "Results", "Curvature is not correlation",
        ["Test", "Value", "What it means"],
        [["Top-K Jaccard vs correlation", "≈ 0.0", "the two methods pick almost no pairs in common"],
         ["Spearman(F, |ρ|)", "0.18", "curvature rank barely tracks correlation (≪ 0.8)"]],
        lead="The pairs curvature flags are not the pairs correlation flags.",
        note="Significance: curvature is not a re-skin of correlation — it surfaces genuinely "
             "different structure. This distinctness IS the headline result.",
        col_widths=[Inches(4.4), Inches(1.9), Inches(5.3)],
        align=["l", "c", "l"],
        highlight_rows=(0, 1),
    )

    # 13 — result 2
    table_slide(
        prs, nx(), "Results", "A clean degree ablation",
        ["Object", "R² on degree", "What it means"],
        [["Plain Forman", "1.00", "100% explained by degree — pure baseline, by design"],
         ["Augmented Forman", "0.56", "~44% is NOT degree → genuinely higher-order signal"]],
        lead="Does the curvature carry anything beyond node connectivity?",
        note="Significance: plain Forman = pure degree (proves the test is calibrated); the "
             "augmented object adds real higher-order structure the +3m triangle term captures.",
        col_widths=[Inches(3.8), Inches(2.4), Inches(5.4)],
        align=["l", "c", "l"],
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

    # 15 — implications
    content_slide(
        prs, nx(), "Implications", "What it means",
        ["A new structural lens: directed, residualized curvature surfaces pair structure "
         "correlation / degree / undirected methods miss.",
         "Directedness changes the geometry — the directed graph is provably distinct "
         "from its symmetrized version.",
         "Triangle sparsity is a first-class constraint for curvature methods in finance.",
         "This is a structural study — we make no predictive claim (Sandhu's precedent: "
         "structural-only is publishable)."],
    )

    # 17 — outlook
    content_slide(
        prs, nx(), "Outlook", "Where this could go",
        ["Maybe not lead-lag at all — apply the same directed-curvature tools to "
         "other market graphs and relations.",
         "Directed line-graph & directed AFRC-gap theory (open problems).",
         "Multi-frequency replication; curvature dynamics through 2020 stress.",
         "Write-up → 8-page ACM sigconf for ICAIF 2026."],
        lead="The structural toolkit is not tied to one construction.",
    )

    out = Path("slides"); out.mkdir(exist_ok=True)
    path = out / "Ricci_Curvature_LeadLag.pptx"
    prs.save(str(path))
    print(f"saved {path}  ({n} slides)")


if __name__ == "__main__":
    build()
