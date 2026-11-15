"""Keep the public Streamlit app awake (Member 4; run by .github/workflows/keep-alive.yml).

Free Streamlit Community Cloud apps go to sleep without visitors, and the next visitor then sees a
"get this app back up" button. This script opens the app in a headless browser like a real visitor, clicks
that button if it is there, and waits until the app's own page title appears. It exits with an error if the
app never loads, so a failed run shows up in the Actions log.

Usage:  APP_URL=https://<your-app>.streamlit.app python scripts/keep_alive.py
Optional: CHROME_PATH=<path to a Chromium/Chrome binary> to use an existing browser instead of Playwright's.
"""

from __future__ import annotations

import os
import sys
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

WAKE_BUTTON = "get this app back up"  # text on Streamlit Cloud's sleep page button
APP_MARKER = "Trend Explorer"          # the app's first page title
LOAD_TIMEOUT_MS = 180_000              # a cold start can take a couple of minutes


def app_loaded(page) -> bool:
    """True when the app's page title is visible in the page or in any frame (Cloud wraps apps in an iframe)."""
    for frame in page.frames:
        try:
            visible = frame.get_by_text(APP_MARKER, exact=True).first.is_visible()
        except PlaywrightError:  # a frame can detach while the app loads; check the others
            visible = False
        if visible:
            return True
    return False


def main() -> int:
    url = os.environ.get("APP_URL", "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        print("APP_URL is not set to a valid http(s) URL.", file=sys.stderr)
        return 2
    with sync_playwright() as pw:
        launch = {"headless": True}
        if os.environ.get("CHROME_PATH"):
            launch["executable_path"] = os.environ["CHROME_PATH"]
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)

        woke = False
        try:
            button = page.get_by_role("button", name=WAKE_BUTTON, exact=False)
            button.wait_for(state="visible", timeout=15_000)
            button.click()
            woke = True
            print("App was asleep; clicked the wake-up button.")
        except PlaywrightTimeout:
            print("No wake-up button: the app was already awake.")

        deadline_steps = LOAD_TIMEOUT_MS // 5_000
        for _ in range(deadline_steps):
            if app_loaded(page):
                print("App loaded" + (" after waking." if woke else "."))
                browser.close()
                return 0
            page.wait_for_timeout(5_000)
        browser.close()
    print(f"The app did not show '{APP_MARKER}' within {LOAD_TIMEOUT_MS // 1000} s.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
