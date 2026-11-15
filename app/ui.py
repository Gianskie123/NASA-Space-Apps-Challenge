"""Shared look and feel: tokens, cards, legends.

Light theme for projectors, printouts and government readers. Every colour is a :root token; labels are
sentence case; one accent marks state; numbers use tabular numerals; no gradients, no emoji icons.
Plain words lead; specialist terms live inside "For scientists" panels. All text passed in is HTML-escaped.
"""

from __future__ import annotations

from html import escape

import streamlit as st

from config import APP_NAME, TAGLINE

# Python-side mirror of the tokens below, for Plotly (which cannot read CSS variables).
PALETTE = {
    "paper": "#f6f6f3", "paper2": "#ffffff", "paper3": "#efefea", "rule": "#e1e1da",
    "ink": "#1b2230", "ink2": "#454d5b", "muted": "#6b7280",
    "accent": "#1f5fbf", "accent_soft": "#6f9ad8", "accent_faint": "#dbe6f6",
    "warn": "#9a6400", "danger": "#b3372b", "ok": "#2c7a4b",
    "gap": "#b9bcc2", "neutral": "#c9ccd2",
}
# Bird groups: birds that need darkness wear the accent; the reference group is muted.
GROUP_COLORS = {"Sensitive": "#1f5fbf", "Tolerant": "#8a909b"}

_CSS = """
<style>
:root{
  --color-paper:#f6f6f3; --color-paper-2:#ffffff; --color-paper-3:#efefea; --color-rule:#e1e1da;
  --color-ink:#1b2230; --color-ink-2:#454d5b; --color-muted:#6b7280; --color-field-edge:#8b919c;
  --color-accent:#1f5fbf; --color-accent-wash:#1f5fbf12; --color-accent-line:#1f5fbf66;
  --color-warn:#9a6400; --color-warn-wash:#f5b5001f; --color-warn-line:#c9930066;
  --color-danger:#b3372b; --color-danger-wash:#b3372b14; --color-danger-line:#b3372b55;
  --color-ok:#2c7a4b; --color-neutral-wash:#6b72800f; --color-neutral-line:#6b728055;
  --color-focus:#1f5fbf;
  --space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px; --space-5:20px; --space-6:24px; --space-7:32px;
  --radius-1:12px; --radius-2:8px; --radius-pill:999px;
  --step--1:0.86rem; --step-0:1rem; --step-1:1.15rem; --step-2:1.35rem; --step-3:1.9rem; --step-4:2.4rem;
}
html,body{overflow-x:clip;}
.block-container{padding-top:4.4rem; max-width:1240px; margin-inline:auto;}
a:focus-visible,button:focus-visible,[tabindex]:focus-visible{outline:2px solid var(--color-focus); outline-offset:2px;}
[data-testid="stMarkdownContainer"] a,.av-link{color:var(--color-accent);}
.stSelectbox div:has(> input),[data-baseweb="select"] > div{border-color:var(--color-field-edge);}

/* brand line + page header */
.av-brand{font-size:var(--step--1); color:var(--color-muted); margin:0 0 var(--space-2) 0;}
.av-brand b{color:var(--color-accent); font-weight:700;}
.av-page-title{font-size:var(--step-3); font-weight:750; color:var(--color-ink); margin:0 0 var(--space-2) 0; line-height:1.2;
  max-width:28ch; text-wrap:balance;}
.av-page-title.hero{font-size:var(--step-4); max-width:30ch;}
.av-page-sub{color:var(--color-ink-2); font-size:var(--step-1); margin:0 0 var(--space-6) 0; max-width:64ch; line-height:1.5;}

/* section heading */
.av-section{font-size:var(--step-2); font-weight:700; color:var(--color-ink); margin:var(--space-7) 0 var(--space-1) 0; line-height:1.3;}
.av-section-sub{display:block; font-weight:400; color:var(--color-ink-2); font-size:var(--step-0); margin:var(--space-1) 0 var(--space-3) 0; max-width:70ch;}
.av-gloss{font-size:var(--step--1); color:var(--color-muted); line-height:1.55; margin:var(--space-1) 0 var(--space-3) 0; max-width:78ch;}
.av-gloss b{color:var(--color-ink-2); font-weight:600;}

/* finding cards (Overview) */
.av-cards{display:grid; grid-template-columns:repeat(auto-fit,minmax(min(260px,100%),1fr)); gap:var(--space-4); margin:0 0 var(--space-4) 0;}
.av-card{background:var(--color-paper-2); border:1px solid var(--color-rule); border-radius:var(--radius-1); padding:var(--space-5);
  border-top:4px solid var(--card-color, var(--color-accent));}
.av-card-kicker{font-size:var(--step--1); font-weight:650; color:var(--card-color, var(--color-accent)); margin-bottom:var(--space-2);}
.av-card-big{font-size:2.1rem; font-weight:800; color:var(--color-ink); line-height:1.1; font-variant-numeric:tabular-nums;}
.av-card-text{font-size:var(--step-0); color:var(--color-ink-2); line-height:1.5; margin-top:var(--space-2);}

/* verdict (the answer for a selection) */
.av-verdict{background:var(--color-paper-2); border:1px solid var(--color-rule); border-left:6px solid var(--verdict-color, var(--color-neutral-line));
  border-radius:var(--radius-1); padding:var(--space-5) var(--space-6); margin:var(--space-2) 0 var(--space-4) 0;}
.av-verdict-q{font-size:var(--step-0); color:var(--color-ink-2);}
.av-verdict-a{font-size:2.2rem; font-weight:800; color:var(--verdict-color, var(--color-ink)); line-height:1.15; margin:var(--space-1) 0 var(--space-2) 0;}
.av-verdict-line{font-size:var(--step-1); color:var(--color-ink); line-height:1.5;}
.av-verdict-line.muted{color:var(--color-ink-2); font-size:var(--step-0);}

/* the headline sentence */
.av-insight{background:var(--color-paper-2); border:1px solid var(--color-rule); border-left:6px solid var(--color-accent);
  border-radius:var(--radius-1); padding:var(--space-5) var(--space-6); margin-bottom:var(--space-4);}
.av-insight-text{font-size:var(--step-2); font-weight:650; color:var(--color-ink); line-height:1.45; font-variant-numeric:tabular-nums;}
.av-insight-meta{font-size:var(--step--1); color:var(--color-muted); margin-top:var(--space-3);}

/* numbered recommendations and checklists */
.av-list{background:var(--color-paper-2); border:1px solid var(--color-rule); border-radius:var(--radius-1); padding:var(--space-2) var(--space-5); margin-bottom:var(--space-4);}
.av-item{display:flex; gap:var(--space-4); align-items:flex-start; padding:var(--space-3) 0; border-bottom:1px solid var(--color-rule);}
.av-item:last-child{border-bottom:none;}
.av-item-num{width:30px; height:30px; border-radius:50%; background:var(--color-accent-wash); color:var(--color-accent);
  font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0; font-variant-numeric:tabular-nums;}
.av-item-title{font-weight:650; color:var(--color-ink);}
.av-item-body{color:var(--color-ink-2); line-height:1.55; max-width:75ch;}

/* places list */
.av-place{display:flex; justify-content:space-between; gap:var(--space-3); padding:var(--space-2) 0; border-bottom:1px solid var(--color-rule); font-size:0.95rem;}
.av-place:last-child{border-bottom:none;}
.av-place-name{color:var(--color-ink); min-width:0; overflow-wrap:anywhere;}
.av-place-val{color:var(--color-warn); font-weight:700; white-space:nowrap; font-variant-numeric:tabular-nums;}

/* figure tiles (scientist panels) */
.av-stats{display:grid; grid-template-columns:repeat(auto-fit,minmax(min(190px,100%),1fr)); gap:var(--space-3); margin-bottom:var(--space-3);}
.av-stat{background:var(--color-paper-2); border:1px solid var(--color-rule); border-radius:var(--radius-2); padding:var(--space-4); min-width:0;}
.av-stat.accent{border-color:var(--color-accent-line);}
.av-stat-label{font-size:var(--step--1); color:var(--color-ink-2); margin-bottom:var(--space-2);}
.av-stat-value{font-size:1.5rem; font-weight:700; color:var(--color-ink); line-height:1.15; font-variant-numeric:tabular-nums; overflow-wrap:break-word;}
.av-stat-value.compact{font-size:var(--step-1); line-height:1.3;}
.av-stat-aside{font-size:var(--step--1); color:var(--color-ink-2); margin-left:var(--space-2);}
.av-stat-desc{font-size:var(--step--1); color:var(--color-muted); margin-top:var(--space-2); line-height:1.45;}

/* notices */
.av-alert{border-radius:var(--radius-2); padding:var(--space-3) var(--space-4); margin:0 0 var(--space-3) 0; font-size:0.95rem; line-height:1.5; color:var(--color-ink);}
.av-alert.info{background:var(--color-accent-wash); border:1px solid var(--color-accent-line);}
.av-alert.warn{background:var(--color-warn-wash); border:1px solid var(--color-warn-line);}
.av-alert.danger{background:var(--color-danger-wash); border:1px solid var(--color-danger-line);}
.av-alert.pending{background:var(--color-neutral-wash); border:1px dashed var(--color-neutral-line); color:var(--color-ink-2);}

/* legend */
.av-legend{background:var(--color-paper-2); border:1px solid var(--color-rule); border-radius:var(--radius-1); padding:var(--space-3) var(--space-4); margin-bottom:var(--space-3);}
.av-legend-title{font-size:var(--step--1); font-weight:650; color:var(--color-ink); margin-bottom:var(--space-2);}
.av-legend-item{display:flex; align-items:flex-start; gap:var(--space-3); margin:var(--space-2) 0; font-size:0.92rem; color:var(--color-ink);}
.av-legend-swatch{width:var(--space-4); height:var(--space-4); border-radius:50%; flex-shrink:0; margin-top:2px;}
.av-legend-swatch.ring{background:transparent; border:2px solid var(--color-ink);}
.av-legend-note{font-size:var(--step--1); color:var(--color-muted); line-height:1.4;}

/* dataset list and method steps (How we know) */
.av-ds{padding:var(--space-3) 0; border-bottom:1px solid var(--color-rule);}
.av-ds:last-child{border-bottom:none;}
.av-ds-name{font-weight:650; color:var(--color-ink);}
.av-ds-by{color:var(--color-muted); font-size:var(--step--1);}
.av-ds-use{color:var(--color-ink-2); font-size:0.95rem; line-height:1.5; margin-top:2px;}

/* gradient legend under maps */
.av-grad{display:flex; flex-wrap:wrap; align-items:center; gap:var(--space-2) var(--space-4); font-size:0.9rem; color:var(--color-ink-2); margin:var(--space-2) 0 var(--space-3) 0;}
.av-grad-bar{display:flex; align-items:center; gap:var(--space-2);}
.av-grad-strip{width:160px; height:12px; border-radius:6px;}
.av-grad-dot{display:inline-block; width:12px; height:12px; border-radius:50%; vertical-align:-1px; margin-right:6px;}

/* page links as cards */
[data-testid="stPageLink"] a{background:var(--color-paper-2); border:1px solid var(--color-rule); border-radius:var(--radius-1); padding:var(--space-3) var(--space-4);}
[data-testid="stPageLink"] a:hover{border-color:var(--color-accent-line);}
[data-testid="stPageLink"] p{font-size:var(--step-0); font-weight:600;}

/* charts sit on cards */
[data-testid="stPlotlyChart"]{background:var(--color-paper-2); border:1px solid var(--color-rule); border-radius:var(--radius-1); padding:var(--space-2);}
[data-testid="stExpander"] details{background:var(--color-paper-2); border-radius:var(--radius-1);}
[data-testid="stExpander"] summary p{font-weight:600;}

.st-key-mnav{display:none !important;}
@media (max-width: 640px){
  .st-key-mnav{display:flex !important; flex-wrap:wrap; gap:6px;}
  .st-key-mnav [data-testid="stPageLink"] a{padding:6px 10px;}
  .block-container{padding-left:var(--space-4); padding-right:var(--space-4); padding-top:4rem;}
  .av-page-title,.av-page-title.hero{font-size:1.55rem;}
  .av-verdict-a{font-size:1.7rem;}
  .av-card-big{font-size:1.8rem;}
  .av-insight-text{font-size:var(--step-1);}
}
@media (prefers-reduced-motion: reduce){ *{animation:none!important; transition:none!important;} }
</style>
"""


def inject_css() -> None:
    st.html(_CSS)


def _md(html: str, container=None) -> None:
    (container or st).markdown(html, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", hero: bool = False) -> None:
    """Brand line, page title and a one-sentence purpose."""
    sub = f'<p class="av-page-sub">{escape(subtitle)}</p>' if subtitle else ""
    cls = "av-page-title hero" if hero else "av-page-title"
    _md(f'<div class="av-brand"><b>{escape(APP_NAME)}</b>&ensp;{escape(TAGLINE)}</div>'
        f'<h1 class="{cls}">{escape(title)}</h1>{sub}')


def section(title: str, sub: str | None = None, container=None) -> None:
    s = f'<span class="av-section-sub">{escape(sub)}</span>' if sub else ""
    _md(f'<div class="av-section">{escape(title)}{s}</div>', container)


def cards(items: list[tuple[str, str, str, str]], container=None) -> None:
    """Finding cards: (kicker, big figure, sentence, colour)."""
    html = "".join(
        f'<div class="av-card" style="--card-color:{escape(c)}"><div class="av-card-kicker">{escape(k)}</div>'
        f'<div class="av-card-big">{escape(b)}</div><div class="av-card-text">{escape(t)}</div></div>'
        for k, b, t, c in items)
    _md(f'<div class="av-cards">{html}</div>', container)


def verdict(question: str, answer: str, lines: list[str], color: str | None = None, muted_last: bool = False,
            container=None) -> None:
    """The answer for one selection: the question, a one- or two-word verdict, and plain lines under it."""
    style = f' style="--verdict-color:{escape(color)}"' if color else ""
    body = "".join(
        f'<div class="av-verdict-line{" muted" if muted_last and i == len(lines) - 1 else ""}">{escape(x)}</div>'
        for i, x in enumerate(lines) if x)
    _md(f'<div class="av-verdict"{style}><div class="av-verdict-q">{escape(question)}</div>'
        f'<div class="av-verdict-a">{escape(answer)}</div>{body}</div>', container)


def numbered(items: list[tuple[str, str]], container=None) -> None:
    """Numbered list of (title, body)."""
    html = "".join(f'<div class="av-item"><div class="av-item-num">{i}</div><div><div class="av-item-title">'
                   f'{escape(t)}</div><div class="av-item-body">{escape(b)}</div></div></div>'
                   for i, (t, b) in enumerate(items, 1))
    _md(f'<div class="av-list">{html}</div>', container)


def places(title: str, rows: list[tuple[str, str]], note: str | None = None, container=None) -> None:
    """A short list of (place name, value)."""
    body = "".join(f'<div class="av-place"><span class="av-place-name">{escape(n)}</span>'
                   f'<span class="av-place-val">{escape(v)}</span></div>' for n, v in rows)
    nt = f'<div class="av-legend-note" style="margin-top:8px">{escape(note)}</div>' if note else ""
    _md(f'<div class="av-legend"><div class="av-legend-title">{escape(title)}</div>{body}{nt}</div>', container)


def gradient_legend(low: str, high: str, colors: list[str], extras: list[tuple[str, str]] | None = None,
                    container=None) -> None:
    """A colour strip with words at both ends, plus optional (colour, label) dots, for under a map."""
    strip = f'linear-gradient(90deg, {", ".join(escape(c) for c in colors)})'
    dots = "".join(f'<span><span class="av-grad-dot" style="background:{escape(c)}"></span>{escape(t)}</span>'
                   for c, t in (extras or []))
    _md(f'<div class="av-grad"><span class="av-grad-bar">{escape(low)}<span class="av-grad-strip" '
        f'style="background:{strip}"></span>{escape(high)}</span>{dots}</div>', container)


def stat_html(label: str, value: str, aside: str | None = None, desc: str | None = None, accent: bool = False,
              compact: bool = False) -> str:
    a = f'<span class="av-stat-aside">{escape(aside)}</span>' if aside else ""
    d = f'<div class="av-stat-desc">{escape(desc)}</div>' if desc else ""
    cls = "av-stat accent" if accent else "av-stat"
    return (f'<div class="{cls}"><div class="av-stat-label">{escape(label)}</div>'
            f'<div><span class="av-stat-value{" compact" if compact else ""}">{escape(value)}</span>{a}</div>{d}</div>')


def stats_row(tiles: list[str], container=None) -> None:
    _md(f'<div class="av-stats">{"".join(tiles)}</div>', container)


def insight(text: str, meta: str | None = None, container=None) -> None:
    m = f'<div class="av-insight-meta">{escape(meta)}</div>' if meta else ""
    _md(f'<div class="av-insight"><div class="av-insight-text">{escape(text)}</div>{m}</div>', container)


def alert(text: str, kind: str = "info", container=None, html: bool = False) -> None:
    """kind: info | warn | danger | pending (an empty state: the data is not available)."""
    _md(f'<div class="av-alert {kind}">{text if html else escape(text)}</div>', container)


def gloss(html_text: str, container=None) -> None:
    """A short explanatory line. Caller passes trusted, escaped HTML."""
    _md(f'<p class="av-gloss">{html_text}</p>', container)


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


def style_fig(fig, height: int | None = None, legend_bottom: bool = True):
    """Charts on white cards: transparent ground, light grid, text in ink tones."""
    p = PALETTE
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=p["ink2"], size=13),
        hoverlabel=dict(bgcolor=p["paper2"], bordercolor=p["rule"], font_color=p["ink"], font_size=13),
        modebar=dict(bgcolor="rgba(0,0,0,0)", color=p["muted"], activecolor=p["ink"]),
    )
    if legend_bottom:
        fig.update_layout(legend=dict(orientation="h", y=-0.2, x=0, bgcolor="rgba(0,0,0,0)", font=dict(color=p["ink2"])))
    if height:
        fig.update_layout(height=height)
    fig.update_xaxes(gridcolor=p["rule"], zerolinecolor=p["rule"], linecolor=p["rule"], showgrid=False,
                     tickfont=dict(color=p["muted"]))
    fig.update_yaxes(gridcolor=p["rule"], zerolinecolor=p["rule"], nticks=5, tickfont=dict(color=p["muted"]))
    return fig


# Maps never hijack page scrolling (use the +/- buttons or drag to move); no toolbar clutter.
MAP_CONFIG = {"scrollZoom": False, "displaylogo": False, "displayModeBar": False}
CHART_CONFIG = {"displaylogo": False, "displayModeBar": False}
