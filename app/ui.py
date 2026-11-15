"""Shared look and feel: tokens, cards, badges, legends.

Design rules follow Hallmark (github.com/Nutlope/hallmark), app-screen scope:
every colour is a :root token, labels are sentence case and untracked, one
accent marks state, numbers use tabular numerals, no gradients, no emoji
icons, no middle-dot meta strings. Palette from the team's AviLight dashboard.
All text passed in is HTML-escaped.
"""

from __future__ import annotations

from html import escape

import streamlit as st

from config import APP_NAME

# Python-side mirror of the tokens below, for Plotly (which cannot read CSS variables).
PALETTE = {
    "paper": "#0f1117", "paper2": "#1a1d23", "paper3": "#21252d", "rule": "#2c313b",
    "ink": "#e8eaef", "ink2": "#b4b9c5", "muted": "#7d8394",
    "accent": "#4f8ff7", "accent_soft": "#8db6fa", "accent_faint": "#2a4a7f",
    "warn": "#e0b54a", "danger": "#e5726a", "ok": "#5fbf86",
    "gap": "#c8c8c8",
}
# Bird groups: the argued series (sensitive) wears the accent; the reference series is muted.
GROUP_COLORS = {"Sensitive": PALETTE["accent"], "Tolerant": PALETTE["muted"]}

_CSS = """
<style>
/* Hallmark v2.0.0 | shape: app screen | scope: app | genre: modern-minimal | theme: custom (AviLight navy) | modes: dark | data: sample until hand-off */
/* critique: one accent for state only; figures are tiles with worded qualifiers; gaps drawn as gaps, never zeros */
:root{
  --color-paper:#0f1117; --color-paper-2:#1a1d23; --color-paper-3:#21252d; --color-rule:#2c313b;
  --color-ink:#e8eaef; --color-ink-2:#b4b9c5; --color-muted:#7d8394; --color-field-edge:#6f7686;
  --color-accent:#4f8ff7; --color-accent-soft:#8db6fa; --color-accent-wash:#4f8ff724; --color-accent-line:#4f8ff7a6;
  --color-selection:#4f8ff74d;
  --color-warn:#e0b54a; --color-warn-wash:#e0b54a1f; --color-warn-line:#e0b54a52;
  --color-danger:#e5726a; --color-danger-wash:#e5726a1f; --color-danger-line:#e5726a4d;
  --color-ok:#5fbf86; --color-ok-wash:#5fbf862e;
  --color-neutral-wash:#7d83941f; --color-neutral-line:#7d839466;
  --color-ring:#e8eaef; --color-focus:#8db6fa; --color-focus-on-light:#0f1117;
  --space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px; --space-5:20px; --space-6:24px; --space-7:28px;
  --radius-1:10px; --radius-2:8px; --radius-pill:999px;
  --step--1:0.84rem; --step-0:1rem; --step-1:1.125rem; --step-2:1.27rem; --step-3:1.6rem;
}
html,body{overflow-x:clip;}
html{scrollbar-color:var(--color-rule) var(--color-paper);}
::selection{background:var(--color-selection); color:var(--color-ink);}
.block-container{padding-top:2.2rem; max-width:1440px; margin-inline:auto;}
a:focus-visible,button:focus-visible,[tabindex]:focus-visible{outline:2px solid var(--color-focus); outline-offset:2px; transition:none;}
/* links drawn over the light basemap get a dark ring */
.maplibregl-ctrl-attrib a:focus-visible{outline-color:var(--color-focus-on-light);}
/* the chart toolbar only shows on hover; keep it visible while it holds keyboard focus, ring inside the button */
.js-plotly-plot .modebar--hover:focus-within .modebar-group{opacity:1;}
.js-plotly-plot .plotly .modebar .modebar-btn:focus-visible{outline:2px solid var(--color-focus); outline-offset:-2px;}
.av-link,[data-testid="stMarkdownContainer"] a{color:var(--color-accent-soft);}
.av-link:hover,[data-testid="stMarkdownContainer"] a:hover{color:var(--color-ink);}
.av-link:active,[data-testid="stMarkdownContainer"] a:active{color:var(--color-accent);}
/* field edges at 3:1 against the surface */
.stSelectbox div:has(> input),.stTextInput div:has(> input),.stNumberInput div:has(> input),[data-baseweb="select"] > div{border-color:var(--color-field-edge);}

/* page header */
.av-page-title{font-size:var(--step-3); font-weight:700; color:var(--color-ink); margin:0 0 var(--space-1) 0; line-height:1.25;
  overflow-wrap:break-word; min-width:0;}
.av-page-sub{color:var(--color-ink-2); font-size:var(--step-0); margin:0 0 var(--space-5) 0; max-width:70ch;}

/* section heading: sentence case, untracked, body face */
.av-section{font-size:var(--step-1); font-weight:600; color:var(--color-ink); margin:var(--space-7) 0 var(--space-3) 0; line-height:1.3;}
.av-section-sub{font-weight:400; color:var(--color-muted); font-size:var(--step--1); margin-left:var(--space-2);}
.av-section-tag{margin-left:var(--space-2); font-weight:400;}
.av-section-tag .av-badge{vertical-align:2px;}
/* plain-language glossary line under a result */
.av-gloss{font-size:var(--step--1); color:var(--color-muted); line-height:1.5; margin:0 0 var(--space-3) 0; max-width:75ch;}
.av-gloss b{color:var(--color-ink-2); font-weight:600;}

/* figure tiles */
.av-stats{display:grid; grid-template-columns:repeat(auto-fit,minmax(min(190px,100%),1fr)); gap:var(--space-3); margin-bottom:var(--space-3);}
.av-stat{background:var(--color-paper-2); border:1px solid var(--color-rule); border-radius:var(--radius-1); padding:var(--space-4); min-width:0;}
.av-stat.accent{border-color:var(--color-accent-line);}
.av-stat-label{font-size:var(--step--1); color:var(--color-ink-2); margin-bottom:var(--space-2);}
.av-stat-value{font-size:1.7rem; font-weight:700; color:var(--color-ink); line-height:1.15; font-variant-numeric:tabular-nums;
  overflow-wrap:break-word;}
.av-stat-value.compact{font-size:var(--step-2); line-height:1.3;}
.av-stat-aside{font-size:var(--step--1); color:var(--color-ink-2); margin-left:var(--space-2); font-variant-numeric:tabular-nums;}
.av-stat-desc{font-size:var(--step--1); color:var(--color-muted); margin-top:var(--space-2); line-height:1.45;}

/* the answer */
.av-insight{background:var(--color-paper-2); border:1px solid var(--color-accent-line);
  border-radius:var(--radius-1); padding:var(--space-4) var(--space-5); margin-bottom:var(--space-4);}
.av-insight-text{font-size:var(--step-2); font-weight:600; color:var(--color-ink); line-height:1.45; font-variant-numeric:tabular-nums;}
.av-insight-meta{font-size:var(--step--1); color:var(--color-muted); margin-top:var(--space-2);}

/* notices */
.av-alert{border-radius:var(--radius-2); padding:var(--space-3) var(--space-4); margin:0 0 var(--space-3) 0; font-size:0.92rem; line-height:1.5; color:var(--color-ink);}
.av-alert.info{background:var(--color-accent-wash); border:1px solid var(--color-accent-line);}
.av-alert.warn{background:var(--color-warn-wash); border:1px solid var(--color-warn-line);}
.av-alert.danger{background:var(--color-danger-wash); border:1px solid var(--color-danger-line);}
.av-alert.pending{background:var(--color-neutral-wash); border:1px dashed var(--color-neutral-line); color:var(--color-ink-2);}
.av-alert b{color:var(--color-ink);}

/* tags: body face, a step smaller, lower case, untracked */
.av-badge{display:inline-block; font-size:var(--step--1); line-height:1; padding:var(--space-1) var(--space-2); border-radius:var(--radius-pill);
  white-space:nowrap; margin:2px var(--space-1) 2px 0; vertical-align:middle; border:1px solid var(--color-rule); color:var(--color-ink-2);
  background:var(--color-paper-3);}
.av-badge.accent{border-color:var(--color-accent-line); background:var(--color-accent-wash); color:var(--color-accent-soft);}
.av-badge.ok{border-color:var(--color-ok); color:var(--color-ok); background:var(--color-ok-wash);}
.av-badge.warn{border-color:var(--color-warn-line); color:var(--color-warn); background:var(--color-warn-wash);}
.av-badge.danger{border-color:var(--color-danger-line); color:var(--color-danger); background:var(--color-danger-wash);}

/* legend */
.av-legend{background:var(--color-paper-2); border:1px solid var(--color-rule); border-radius:var(--radius-1); padding:var(--space-3) var(--space-4); margin-bottom:var(--space-3);}
.av-legend-title{font-size:var(--step--1); font-weight:600; color:var(--color-ink); margin-bottom:var(--space-2);}
.av-legend-item{display:flex; align-items:flex-start; gap:var(--space-3); margin:var(--space-2) 0; font-size:0.9rem; color:var(--color-ink);}
.av-legend-swatch{width:var(--space-4); height:var(--space-4); border-radius:var(--space-1); flex-shrink:0; margin-top:2px;}
.av-legend-swatch.ring{background:transparent; border:2px solid var(--color-ring); border-radius:50%;}
.av-legend-note{font-size:var(--step--1); color:var(--color-muted); line-height:1.4;}

/* data status rows */
.av-status{display:flex; justify-content:space-between; align-items:center; gap:var(--space-2); margin:var(--space-2) 0; font-size:0.88rem; color:var(--color-ink);}
.av-status small{color:var(--color-muted); font-size:var(--step--1);}
.av-dot{display:inline-block; width:10px; height:10px; border-radius:50%; flex-shrink:0; vertical-align:middle;}
.av-dot.ok{background:var(--color-ok);} .av-dot.warn{background:var(--color-warn);}

/* sidebar wordmark */
.av-brand-name{font-size:var(--step-2); font-weight:700; color:var(--color-ink); line-height:1.1;}
.av-brand-name span{color:var(--color-accent);}
.av-brand-tag{font-size:var(--step--1); color:var(--color-muted); margin-top:2px;}

/* dataset list (About) */
.av-ds{padding:var(--space-3) 0; border-bottom:1px solid var(--color-rule);}
.av-ds:last-child{border-bottom:none;}
.av-ds-name{font-weight:600; color:var(--color-ink);}
.av-ds-by{color:var(--color-muted); font-size:var(--step--1);}
.av-ds-use{color:var(--color-ink-2); font-size:0.94rem; line-height:1.5; margin-top:2px;}

/* numbered method steps */
.av-step{display:flex; gap:var(--space-4); align-items:flex-start; padding:var(--space-3) 0; border-bottom:1px solid var(--color-rule);}
.av-step:last-child{border-bottom:none;}
.av-step-num{width:var(--space-7); height:var(--space-7); border-radius:50%; border:1px solid var(--color-accent-line); color:var(--color-accent-soft);
  font-weight:600; display:flex; align-items:center; justify-content:center; flex-shrink:0; font-size:0.9rem; font-variant-numeric:tabular-nums;}
.av-step-title{font-weight:600; color:var(--color-ink); margin-bottom:2px;}
.av-step-body{color:var(--color-ink-2); font-size:0.94rem; line-height:1.55; max-width:75ch;}

/* charts sit on the elevated surface */
[data-testid="stPlotlyChart"]{background:var(--color-paper-2); border:1px solid var(--color-rule); border-radius:var(--radius-1); padding:var(--space-2);}
[data-testid="stDataFrame"]{font-variant-numeric:tabular-nums;}

@media (max-width: 640px){
  .block-container{padding-left:var(--space-4); padding-right:var(--space-4); padding-top:var(--space-6);}
  .av-page-title{font-size:1.4rem;}
  .av-stat-value{font-size:1.45rem;}
  .av-insight-text{font-size:var(--step-1);}
}
@media (prefers-reduced-motion: reduce){ *{animation:none!important; transition:none!important;} }
</style>
"""


def inject_css() -> None:
    st.html(_CSS)


def _md(html: str, container=None) -> None:
    (container or st).markdown(html, unsafe_allow_html=True)


def sidebar_brand(tagline: str = "NASA Earth data and birds in the Philippines") -> None:
    name = escape(APP_NAME)
    if " " in name:
        head, tail = name.rsplit(" ", 1)
        name = f"{head} <span>{tail}</span>"
    _md(f'<div class="av-brand-name">{name}</div><div class="av-brand-tag">{escape(tagline)}</div>', st.sidebar)


def page_header(title: str, subtitle: str = "") -> None:
    sub = f'<p class="av-page-sub">{escape(subtitle)}</p>' if subtitle else ""
    _md(f'<h1 class="av-page-title">{escape(title)}</h1>{sub}')


# Where a section's numbers come from, shown next to its heading when the real data is loaded.
SOURCES = {
    "satellite": ("NASA satellite data", "accent"),
    "observed": ("observed eBird data", "ok"),
    "model": ("model result", "accent"),
}


def source_tag(kind: str | None) -> str:
    if not kind or kind not in SOURCES:
        return ""
    text, tone = SOURCES[kind]
    return f'<span class="av-badge {tone}">{escape(text)}</span>'


def section(title: str, sub: str | None = None, container=None, source: str | None = None) -> None:
    s = f'<span class="av-section-sub">{escape(sub)}</span>' if sub else ""
    t = f' <span class="av-section-tag">{source_tag(source)}</span>' if source else ""
    _md(f'<div class="av-section">{escape(title)}{s}{t}</div>', container)


def stat_html(label: str, value: str, aside: str | None = None, desc: str | None = None, accent: bool = False,
              compact: bool = False) -> str:
    """A figure tile: label, figure, optional measured aside, worded qualifier. accent marks state."""
    a = f'<span class="av-stat-aside">{escape(aside)}</span>' if aside else ""
    d = f'<div class="av-stat-desc">{escape(desc)}</div>' if desc else ""
    cls = "av-stat accent" if accent else "av-stat"
    return (f'<div class="{cls}"><div class="av-stat-label">{escape(label)}</div>'
            f'<div><span class="av-stat-value{" compact" if compact else ""}">{escape(value)}</span>{a}</div>{d}</div>')


def stats_row(cards: list[str], container=None) -> None:
    _md(f'<div class="av-stats">{"".join(cards)}</div>', container)


def insight(text: str, kicker: str | None = None, meta: str | None = None, container=None) -> None:
    """The one sentence that answers the question. No eyebrow: `kicker` is folded into the meta line."""
    parts = [x for x in (kicker, meta) if x]
    m = f'<div class="av-insight-meta">{escape(", ".join(parts))}</div>' if parts else ""
    _md(f'<div class="av-insight"><div class="av-insight-text">{escape(text)}</div>{m}</div>', container)


def alert(text: str, kind: str = "info", container=None, html: bool = False) -> None:
    """kind: info | warn | danger | pending (an empty state: the data is not available)."""
    _md(f'<div class="av-alert {kind}">{text if html else escape(text)}</div>', container)


def gloss(html_text: str, container=None) -> None:
    """A short plain-language explanation of specialist terms. Caller passes trusted, escaped HTML."""
    _md(f'<p class="av-gloss">{html_text}</p>', container)


def badge(text: str, tone: str = "") -> str:
    return f'<span class="av-badge {tone}">{escape(text)}</span>'


def legend(title: str, items: list[tuple[str, str, str | None]], note: str | None = None, container=None) -> None:
    """items: (colour hex or 'ring', label, optional note)."""
    rows = []
    for color, label, sub in items:
        sw = '<span class="av-legend-swatch ring"></span>' if color == "ring" else \
            f'<span class="av-legend-swatch" style="background:{escape(color)}"></span>'
        sn = f'<div class="av-legend-note">{escape(sub)}</div>' if sub else ""
        rows.append(f'<div class="av-legend-item">{sw}<div>{escape(label)}{sn}</div></div>')
    nt = f'<div class="av-legend-note" style="margin-top:8px">{escape(note)}</div>' if note else ""
    _md(f'<div class="av-legend"><div class="av-legend-title">{escape(title)}</div>{"".join(rows)}{nt}</div>', container)


def dataset(name: str, url: str | None, by: str, use: str) -> str:
    n = f'<a class="av-link" href="{escape(url)}" target="_blank" rel="noopener">{escape(name)}</a>' if url else escape(name)
    return (f'<div class="av-ds"><div class="av-ds-name">{n} <span class="av-ds-by">{escape(by)}</span></div>'
            f'<div class="av-ds-use">{escape(use)}</div></div>')


def step(num: int, title: str, body: str) -> str:
    return (f'<div class="av-step"><div class="av-step-num">{num}</div><div>'
            f'<div class="av-step-title">{escape(title)}</div><div class="av-step-body">{escape(body)}</div></div></div>')


def style_fig(fig, height: int | None = None, legend_bottom: bool = True):
    """Charts on the elevated surface: transparent ground, hairline grid, text in ink tones, never series colours."""
    p = PALETTE
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=p["ink2"], size=12),
        title=dict(font=dict(color=p["ink"], size=14), x=0.01, xanchor="left"),
        hoverlabel=dict(bgcolor=p["paper3"], bordercolor=p["rule"], font_color=p["ink"]),
        # toolbar on its own dark chip, so the light focus ring reads even over light map tiles
        modebar=dict(bgcolor=p["paper2"], color=p["ink2"], activecolor=p["ink"]),
    )
    if legend_bottom:
        fig.update_layout(legend=dict(orientation="h", y=-0.18, x=0, bgcolor="rgba(0,0,0,0)", font=dict(color=p["ink2"])))
    if height:
        fig.update_layout(height=height)
    fig.update_xaxes(gridcolor=p["rule"], zerolinecolor=p["rule"], linecolor=p["rule"], showgrid=False, tickfont=dict(color=p["muted"]))
    fig.update_yaxes(gridcolor=p["rule"], zerolinecolor=p["rule"], nticks=5, tickfont=dict(color=p["muted"]))
    return fig


# Maps never hijack page scrolling (use the +/- buttons or drag to move).
MAP_CONFIG = {"scrollZoom": False, "displaylogo": False}
