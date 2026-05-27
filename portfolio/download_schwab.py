"""
Download positions for all Schwab accounts and write a CSV to sample-data/.

Requires a token file at schwab_token.json (created by setup_schwab_auth.py).
The token is refreshed automatically when needed — no browser interaction required.

Credentials are read from a .env file in the same directory as this script:

    SCHWAB_APP_KEY=...
    SCHWAB_APP_SECRET=...

Output file:
    sample-data/schwab_All-Accounts-Positions-<YYYY-MM-DD>-<HHMMSS>.csv

The file format matches a manual Schwab export exactly, so parse_schwab in
translate_positions.py works without any changes.

Requires: schwab-py  (not stdlib — install into .venv)
"""

import csv
import os
import sys
from datetime import datetime
from io import StringIO
from pathlib import Path

import schwab
from schwab.auth import client_from_token_file


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

APP_KEY    = os.environ.get("SCHWAB_APP_KEY", "")
APP_SECRET = os.environ.get("SCHWAB_APP_SECRET", "")
TOKEN_PATH = str(Path(__file__).parent / "schwab_token.json")

if not APP_KEY or not APP_SECRET:
    print(
        "Error: SCHWAB_APP_KEY and SCHWAB_APP_SECRET must be set in .env or environment.",
        file=sys.stderr,
    )
    sys.exit(1)

if not Path(TOKEN_PATH).exists():
    print(
        f"Error: {TOKEN_PATH} not found. Run setup_schwab_auth.py first.",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# CSV formatting helpers — match the exact format of a manual Schwab export
# ---------------------------------------------------------------------------

# Column order exactly as in a manual export
CSV_COLUMNS = [
    "Symbol", "Description", "Qty (Quantity)", "Price",
    "Price Chng $ (Price Change $)", "Price Chng % (Price Change %)",
    "Mkt Val (Market Value)", "Day Chng $ (Day Change $)", "Day Chng % (Day Change %)",
    "Cost Basis", "Gain $ (Gain/Loss $)", "Gain % (Gain/Loss %)",
    "Ratings", "Reinvest?", "Reinvest Capital Gains?",
    "% of Acct (% of Account)", "Asset Type",
]

# Instrument type values from the API mapped to the Asset Type column values
# that parse_schwab recognises.
_ASSET_TYPE_MAP = {
    "EQUITY":                  "Equity",
    "ETF":                     "ETFs & Closed End Funds",
    "COLLECTIVE_INVESTMENT":   "ETFs & Closed End Funds",
    "OPTION":                  "Option",
    "MUTUAL_FUND":             "Mutual Fund",
    "FIXED_INCOME":            "Fixed Income",
    "CASH_EQUIVALENT":         "Cash and Money Market",
    "CURRENCY":                "Cash and Money Market",
}


def _asset_type(instrument: dict) -> str:
    raw = instrument.get("assetType", "")
    return _ASSET_TYPE_MAP.get(raw, raw.capitalize())


def _fmt(value, default="--") -> str:
    """Return a plain string or '--' if absent."""
    if value is None:
        return default
    return str(value)


def _position_rows(account_number: str, positions: list[dict]) -> list[dict]:
    """Convert API position objects to CSV row dicts."""
    rows = []
    for pos in positions:
        instrument = pos.get("instrument", {})
        symbol      = instrument.get("symbol", "")
        description = instrument.get("description", "")
        asset_type  = _asset_type(instrument)

        quantity    = _fmt(pos.get("longQuantity") or -pos.get("shortQuantity", 0) or None)
        market_val  = _fmt(pos.get("marketValue"))
        avg_price   = _fmt(pos.get("averagePrice"))
        cost_basis  = _fmt(pos.get("costBasis") or pos.get("averageLongPrice"))

        rows.append({
            "Symbol":                          symbol,
            "Description":                     description,
            "Qty (Quantity)":                  quantity,
            "Price":                           avg_price,
            "Price Chng $ (Price Change $)":   "--",
            "Price Chng % (Price Change %)":   "--",
            "Mkt Val (Market Value)":          market_val,
            "Day Chng $ (Day Change $)":       "--",
            "Day Chng % (Day Change %)":       "--",
            "Cost Basis":                      cost_basis,
            "Gain $ (Gain/Loss $)":            "--",
            "Gain % (Gain/Loss %)":            "--",
            "Ratings":                         "--",
            "Reinvest?":                       "--",
            "Reinvest Capital Gains?":         "--",
            "% of Acct (% of Account)":        "--",
            "Asset Type":                      asset_type,
        })

    return rows


def _cash_row(cash_balance: float) -> dict:
    return {
        "Symbol":                          "Cash & Cash Investments",
        "Description":                     "--",
        "Qty (Quantity)":                  "--",
        "Price":                           "--",
        "Price Chng $ (Price Change $)":   "--",
        "Price Chng % (Price Change %)":   "--",
        "Mkt Val (Market Value)":          str(cash_balance),
        "Day Chng $ (Day Change $)":       "--",
        "Day Chng % (Day Change %)":       "--",
        "Cost Basis":                      "--",
        "Gain $ (Gain/Loss $)":            "--",
        "Gain % (Gain/Loss %)":            "--",
        "Ratings":                         "--",
        "Reinvest?":                       "--",
        "Reinvest Capital Gains?":         "--",
        "% of Acct (% of Account)":        "--",
        "Asset Type":                      "Cash and Money Market",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    client = client_from_token_file(
        token_path=TOKEN_PATH,
        api_key=APP_KEY,
        app_secret=APP_SECRET,
    )

    resp = client.get_accounts(fields=[schwab.client.Client.Account.Fields.POSITIONS])
    if resp.status_code != 200:
        print(f"Error fetching accounts: {resp.status_code} {resp.text}", file=sys.stderr)
        sys.exit(1)

    accounts = resp.json()
    if not accounts:
        print("No accounts returned.", file=sys.stderr)
        sys.exit(1)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H%M%S")
    out_path = f"sample-data/schwab_All-Accounts-Positions-{date_str}-{time_str}.csv"

    # Build the CSV in memory using StringIO so we can write it with
    # Unix line endings (lineterminator="\n") matching the rest of the repo.
    buf = StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=CSV_COLUMNS,
        lineterminator="\n",
        quoting=csv.QUOTE_ALL,
    )

    for entry in accounts:
        account_info = entry.get("securitiesAccount", entry)
        account_number = account_info.get("accountNumber", "unknown")
        positions = account_info.get("positions", [])
        balances  = account_info.get("currentBalances", {})

        # Account name line (e.g. "crmills100 ...783")
        buf.write(f"{account_number}\n")

        # Header row
        writer.writeheader()

        # Position rows
        for row in _position_rows(account_number, positions):
            writer.writerow(row)

        # Cash row
        cash = balances.get("cashBalance", balances.get("liquidationValue", 0))
        writer.writerow(_cash_row(cash))

        buf.write("\n\n")

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(buf.getvalue())

    print(f"wrote {out_path}")
    print("Done.")


if __name__ == "__main__":
    main()
