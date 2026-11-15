"""AviTrend PH: entry point. Run from the repo root:  streamlit run app/streamlit_app.py"""

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
for p in (APP_DIR, ROOT / "src"):  # src/ holds trends.py
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

# Data status: a green dot when a data group is fully real, yellow when a backup file is standing in.
DOTS = {"real": ("ok", "Real data loaded"), "backup": ("warn", "Using backup data")}
rows = []
for group in ld.GROUPS:
    tone, tip = DOTS[ld.group_status(group)]
    rows.append(f'<div class="av-status"><span>{group}</span>'
                f'<span class="av-dot {tone}" role="img" aria-label="{tip}" title="{tip}"></span></div>')
with st.sidebar:
    st.divider()
    ui.section("Data status")
    st.markdown("".join(rows), unsafe_allow_html=True)
    st.markdown('<div class="av-gloss"><span class="av-dot ok"></span> real data &nbsp; '
                '<span class="av-dot warn"></span> backup data</div>', unsafe_allow_html=True)
