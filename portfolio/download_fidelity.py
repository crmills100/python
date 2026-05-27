"""
Download positions for all Fidelity accounts and write a CSV to sample-data/.

Fidelity has no retail API. This script connects to an already-running Chrome
browser via the Chrome DevTools Protocol (CDP) and automates the download.

Usage
-----
1. Launch Chrome with the remote debugging port (do this once, keep it running):

       google-chrome --remote-debugging-port=9222 \\
           --user-data-dir=/tmp/chrome-debug-profile \\
           --ozone-platform=x11 --no-first-run

2. Log into Fidelity in that browser if not already logged in.

3. Run this script:

       python3 download_fidelity.py

The script will navigate to the Positions page, click Download, and save the
file to sample-data/fidelity_Portfolio_Positions_<date>.csv.

If the session has expired and login is required, credentials are read from
.env in the repo root:

    FIDELITY_USERNAME=...
    FIDELITY_PASSWORD=...

The downloaded file format matches the manual Fidelity export exactly, so
parse_fidelity in translate_positions.py works without any changes.

Requires: playwright  (not stdlib — install into .venv)
    .venv/bin/python3.12 -m pip install playwright
    .venv/bin/playwright install chromium
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Config / credentials
# ---------------------------------------------------------------------------

CDP_URL = "http://127.0.0.1:9222"


def _load_dotenv(path: Path) -> None:
    """Parse a simple KEY=VALUE .env file into os.environ (no third-party needed)."""
    if not path.exists():
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv(Path(__file__).parent / ".env")

USERNAME = os.environ.get("FIDELITY_USERNAME", "")
PASSWORD = os.environ.get("FIDELITY_PASSWORD", "")


# ---------------------------------------------------------------------------
# URLs and selectors
# ---------------------------------------------------------------------------

POSITIONS_URL = "https://digital.fidelity.com/ftgw/digital/portfolio/positions"

# Verified selectors as of May 2026 — update if Fidelity changes their Angular app.
SEL_USERNAME  = "#dom-username-input"
SEL_PASSWORD  = "#dom-pswd-input"
SEL_LOGIN_BTN = "#dom-login-button"
SEL_OTP_INPUT = "#dom-otp-code-input"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print(
            "Error: playwright is not installed.\n"
            "  .venv/bin/python3.12 -m pip install playwright\n"
            "  .venv/bin/playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(1)

    dest_dir = Path(__file__).parent / "sample-data"
    dest_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        # Connect to the already-running Chrome instance.
        print(f"Connecting to Chrome on {CDP_URL}…")
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print(
                f"Error: could not connect to Chrome ({e}).\n"
                "Make sure Chrome is running with:\n"
                "  google-chrome --remote-debugging-port=9222 \\\n"
                "      --user-data-dir=/tmp/chrome-debug-profile \\\n"
                "      --ozone-platform=x11 --no-first-run",
                file=sys.stderr,
            )
            sys.exit(1)

        ctx = browser.contexts[0]
        ctx.set_default_timeout(30_000)

        # Use the first existing page or open a new one.
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        print(f"Connected. Current URL: {page.url}")

        # ----------------------------------------------------------------
        # Step 1: Navigate to Positions page
        # ----------------------------------------------------------------
        print("Navigating to Positions page…")
        page.goto(POSITIONS_URL, wait_until="domcontentloaded", timeout=30_000)
        print(f"URL: {page.url}")

        # ----------------------------------------------------------------
        # Step 2: Log in if session has expired
        # ----------------------------------------------------------------
        if "login" in page.url or "signin" in page.url:
            if not USERNAME or not PASSWORD:
                print(
                    "Error: session expired and FIDELITY_USERNAME/FIDELITY_PASSWORD "
                    "are not set in .env.",
                    file=sys.stderr,
                )
                sys.exit(1)

            print("Session expired — logging in…")

            # Dismiss cookie consent banner before interacting with the form.
            try:
                page.locator("#ensSave").click(timeout=3_000)
                print("Dismissed cookie banner.")
                page.wait_for_timeout(500)
            except PWTimeout:
                pass

            page.locator(SEL_USERNAME).wait_for(state="visible", timeout=30_000)
            page.locator(SEL_USERNAME).fill(USERNAME)
            page.locator(SEL_PASSWORD).fill(PASSWORD)
            page.locator(SEL_LOGIN_BTN).click()

            # 2FA — prompt for SMS code if required.
            try:
                page.locator(SEL_OTP_INPUT).wait_for(state="visible", timeout=15_000)
                otp = input("Enter your Fidelity 2FA code: ").strip()
                page.locator(SEL_OTP_INPUT).fill(otp)
                page.locator("button[type=submit]").click()
                print("2FA code submitted.")
            except PWTimeout:
                pass

            # Wait for login to complete.
            try:
                page.wait_for_url(
                    lambda url: "login" not in url and "signin" not in url,
                    timeout=60_000,
                )
                print("Logged in.")
            except PWTimeout:
                page.screenshot(path="/tmp/fidelity_login_failed.png")
                print(
                    f"Error: login did not complete (url: {page.url}).\n"
                    "Screenshot saved to /tmp/fidelity_login_failed.png",
                    file=sys.stderr,
                )
                sys.exit(1)

            page.goto(POSITIONS_URL, wait_until="domcontentloaded", timeout=30_000)

        # ----------------------------------------------------------------
        # Step 3: Click Download
        # ----------------------------------------------------------------
        print(f"Positions page loaded ({page.url}). Waiting for positions table to render…")

        # Wait for the kebab menu trigger to appear — confirms positions have rendered.
        try:
            page.locator("#posweb-grid_top-kebab_popover-button").wait_for(state="visible", timeout=30_000)
            print("Positions table rendered. Opening kebab menu…")
            page.locator("#posweb-grid_top-kebab_popover-button").click()
            page.locator("#kebabmenuitem-download").wait_for(state="visible", timeout=5_000)
            print("Kebab menu opened.")
        except PWTimeout:
            print("Warning: could not open kebab menu.")

        # Dismiss cookie consent banner if present.
        try:
            page.locator("#ensSave").click(timeout=3_000)
            print("Dismissed cookie banner.")
        except PWTimeout:
            pass

        # Click the Download menu item (menu should already be open).
        clicked = False
        with page.expect_download(timeout=60_000) as dl_info:
            try:
                page.locator("#kebabmenuitem-download").click(timeout=10_000)
                clicked = True
            except PWTimeout:
                # Try force-clicking as last resort.
                try:
                    page.locator("#kebabmenuitem-download").click(force=True, timeout=5_000)
                    clicked = True
                except Exception as e:
                    print(f"Could not click Download menu item: {e}", file=sys.stderr)

        if not clicked:
            page.screenshot(path="/tmp/fidelity_positions.png")
            with open("/tmp/fidelity_positions.html", "w") as f:
                f.write(page.content())
            print(
                "Error: could not find a Download button.\n"
                "Saved debug snapshot to /tmp/fidelity_positions.png and .html",
                file=sys.stderr,
            )
            sys.exit(1)

        download = dl_info.value
        original_name = download.suggested_filename  # e.g. Portfolio_Positions_May-07-2026.csv

        # Rename to include the fidelity_ prefix so translate_positions.py detects the broker.
        dest_path = dest_dir / f"fidelity_{original_name}"
        download.save_as(dest_path)
        print(f"Saved: {dest_path}")

    print("Done.")


if __name__ == "__main__":
    main()
