"""
Download positions and balances for all Webull accounts and write them to sample-data/.

Credentials are read from a .env file in the same directory as this script:

    WEBULL_APP_KEY=<your app key>
    WEBULL_APP_SECRET=<your app secret>
    WEBULL_REGION=us   # optional, defaults to "us"

Output files (one pair per account):
    sample-data/webull_<account_id>_<YYYY-MM-DD>_positions.json
    sample-data/webull_<account_id>_<YYYY-MM-DD>_balance.json

Requires: webull-trade-sdk  (not stdlib — install into .venv)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from webull.core.client import ApiClient
from webull.trade.trade_client import TradeClient


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

APP_KEY    = os.environ.get("WEBULL_APP_KEY", "")
APP_SECRET = os.environ.get("WEBULL_APP_SECRET", "")
REGION     = os.environ.get("WEBULL_REGION", "us")

if not APP_KEY or not APP_SECRET:
    print(
        "Error: WEBULL_APP_KEY and WEBULL_APP_SECRET must be set in .env or environment.",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _write(path: str, data: object, indent: int | None = None) -> None:
    with open(path, "w") as f:
        f.write(json.dumps(data, indent=indent))
    print(f"  wrote {path}")


def _check(response, label: str) -> object:
    """Assert HTTP 200 and return parsed JSON, or exit with an error message."""
    if response.status_code != 200:
        print(f"Error fetching {label}: {response.status_code} {response.text}", file=sys.stderr)
        sys.exit(1)
    return response.json()


# ---------------------------------------------------------------------------
# Per-account download
# ---------------------------------------------------------------------------

def download_account(trade_client: TradeClient, account_id: str, date: str) -> None:
    print(f"Account {account_id}")

    positions = _check(
        trade_client.account_v2.get_account_position(account_id),
        f"positions for {account_id}",
    )
    _write(
        f"sample-data/webull_{account_id}_{date}_positions.json",
        positions,
        indent=2,
    )

    balance = _check(
        trade_client.account_v2.get_account_balance(account_id),
        f"balance for {account_id}",
    )
    _write(
        f"sample-data/webull_{account_id}_{date}_balance.json",
        balance,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    api_client = ApiClient(APP_KEY, APP_SECRET, REGION)
    api_client.add_endpoint(REGION, "api.webull.com")
    trade_client = TradeClient(api_client)

    accounts = _check(trade_client.account_v2.get_account_list(), "account list")
    if not accounts:
        print("No accounts returned.", file=sys.stderr)
        sys.exit(1)

    date = _today()
    for account in accounts:
        download_account(trade_client, account["account_id"], date)

    print("Done.")


if __name__ == "__main__":
    main()
