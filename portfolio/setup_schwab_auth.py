"""
Perform the one-time Schwab OAuth login and save the token to schwab_token.json.

Run this once before using download_schwab.py. It opens a browser, completes
the OAuth flow, and writes schwab_token.json to the repo root. Subsequent runs
of download_schwab.py load and refresh the token automatically without a browser.

Credentials are read from a .env file in the same directory as this script:

    SCHWAB_APP_KEY=...
    SCHWAB_APP_SECRET=...
    SCHWAB_CALLBACK_URL=https://127.0.0.1:8182  # optional, this is the default

Register https://127.0.0.1:8182 as the redirect URI in your Schwab developer
app before running this script. Your browser will show a self-signed certificate
warning on the redirect — this is expected; accept it to complete the flow.

Requires: schwab-py  (not stdlib — install into .venv)
"""

import os
import sys
from pathlib import Path

from schwab.auth import client_from_login_flow


# ---------------------------------------------------------------------------
# Config / credentials
# ---------------------------------------------------------------------------

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

APP_KEY      = os.environ.get("SCHWAB_APP_KEY", "")
APP_SECRET   = os.environ.get("SCHWAB_APP_SECRET", "")
CALLBACK_URL = os.environ.get("SCHWAB_CALLBACK_URL", "https://127.0.0.1:8182")
TOKEN_PATH   = str(Path(__file__).parent / "schwab_token.json")

if not APP_KEY or not APP_SECRET:
    print(
        "Error: SCHWAB_APP_KEY and SCHWAB_APP_SECRET must be set in .env or environment.",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Token will be saved to: {TOKEN_PATH}")
    client_from_login_flow(
        api_key=APP_KEY,
        app_secret=APP_SECRET,
        callback_url=CALLBACK_URL,
        token_path=TOKEN_PATH,
    )
    print("Authentication complete. You can now run download_schwab.py.")


if __name__ == "__main__":
    main()
