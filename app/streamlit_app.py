"""AviTrend PH: entry point. Run from the repo root:  streamlit run app/streamlit_app.py"""

import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
for p in (APP_DIR, ROOT / "src"):  # src/ holds trends.py, plain.py
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import ui  # noqa: E402
from config import APP_NAME  # noqa: E402

st.set_page_config(page_title=APP_NAME, page_icon=":material/satellite_alt:", layout="wide",
                   initial_sidebar_state="collapsed")
ui.inject_css()

pages = [
    st.Page("views/overview.py", title="Overview", icon=":material/home:", default=True),
    st.Page("views/trend_explorer.py", title="What's changing", icon=":material/insights:"),
    st.Page("views/birds_and_light.py", title="What it means for birds", icon=":material/flutter_dash:"),
    st.Page("views/about.py", title="How we know", icon=":material/menu_book:"),
]
st.navigation(pages, position="top").run()
