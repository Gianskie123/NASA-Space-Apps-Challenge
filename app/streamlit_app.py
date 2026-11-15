"""AviTrend PH: entry point. Run from the repo root:  streamlit run app/streamlit_app.py"""

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
for p in (APP_DIR, ROOT / "src"):  # src/ holds Member 3's trends.py
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import load_data as ld  # noqa: E402
import ui  # noqa: E402
from config import APP_NAME  # noqa: E402

st.set_page_config(page_title=APP_NAME, page_icon=":material/satellite_alt:", layout="wide", initial_sidebar_state="auto")
ui.inject_css()
ui.sidebar_brand()

pages = [
    st.Page("views/trend_explorer.py", title="Trend Explorer", icon=":material/insights:", default=True),
    st.Page("views/birds_and_light.py", title="Birds & Light", icon=":material/flutter_dash:"),
    st.Page("views/about.py", title="About the data", icon=":material/menu_book:"),
]
st.navigation(pages, position="top").run()

# Data status: which hand-offs are real, partly in, or still mock.
SOURCES = [
    ("eBird checklists", "Member 1"),
    ("NASA satellite tables", "Member 2"),
    ("Trends and bird model", "Member 3"),
]
BADGES = {"real": ("real", "ok"), "partial": ("partly in", "accent"), "mock": ("mock", "warn"), "missing": ("missing", "danger")}
rows = []
for label, owner in SOURCES:
    text, tone = BADGES[ld.member_status(owner)]
    rows.append(f'<div class="av-status"><span>{label}<br><small>from {owner}</small></span>{ui.badge(text, tone)}</div>')
with st.sidebar:
    st.divider()
    ui.section("Data status")
    st.markdown("".join(rows), unsafe_allow_html=True)
    st.caption("Mock data only stands in until a member delivers. Each section on a page also says where its numbers come from.")
