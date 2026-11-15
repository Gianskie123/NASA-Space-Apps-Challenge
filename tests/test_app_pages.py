"""Smoke tests: every page of the app runs on the real data without an exception.

Needs streamlit (skipped otherwise). Run from the project root:  python -m pytest tests -q
"""
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")
PAGES = ["views/overview.py", "views/trend_explorer.py", "views/birds_and_light.py", "views/about.py"]


def run(page: str) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    if page != PAGES[0]:
        at.switch_page(page)
        at.run()
    return at


@pytest.mark.parametrize("page", PAGES)
def test_page_runs(page):
    at = run(page)
    assert not at.exception, [e.value for e in at.exception]


def test_overview_shows_findings():
    at = run(PAGES[0])
    html = " ".join(m.value for m in at.markdown)
    assert "provinces got brighter at night" in html
    assert "Around Manila" in html
    assert "less likely" in html
    assert "What this means for DENR-BMB" in html


@pytest.mark.parametrize("var", ["alan", "ndvi", "rain_mm", "urban_frac", "forest_frac", "lst_day"])
def test_every_variable_gives_a_verdict(var):
    at = run(PAGES[1])
    at.selectbox(key="te_var").set_value(var).run()
    assert not at.exception, [e.value for e in at.exception]
    assert any("av-verdict" in m.value for m in at.markdown)


def test_short_window_says_not_enough_years():
    at = run(PAGES[1])
    at.select_slider(key="te_years").set_value((2020, 2021)).run()
    assert not at.exception
    assert any("Not enough years" in m.value for m in at.markdown)


def test_scientist_panel_switches_test():
    at = run(PAGES[1])
    at.radio(key="te_freq").set_value("annual").run()
    assert not at.exception
    assert any("Hamed" in m.value for m in at.markdown)


@pytest.mark.parametrize("mode", ["Where people birdwatched", "How often birds were recorded", "Satellite values"])
def test_bird_explorer_modes(mode):
    at = run(PAGES[2])
    at.segmented_control(key="bl_mode").set_value(mode).run()
    assert not at.exception, [e.value for e in at.exception]
