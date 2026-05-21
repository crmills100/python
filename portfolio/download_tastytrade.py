"""
Download positions and balances for all Tastytrade accounts and write them to sample-data/.

Credentials are read from a .env file in the same directory as this script:

    TT_SECRET=<your OAuth provider secret>
    TT_REFRESH=<your refresh token>

TT_SECRET is the client secret from your Tastytrade developer application.
TT_REFRESH is a long-lived refresh token obtained from the Tastytrade API.

To get a refresh token for the first time, use the Tastytrade API directly:

    curl -X POST https://api.tastytrade.com/oauth/token \\
      -H "Content-Type: application/json" \\
      -d '{"grant_type": "password", "username": "YOUR_EMAIL", "password": "YOUR_PASSWORD", "client_id": "YOUR_CLIENT_ID"}'

The response includes a "refresh_token" field. Store it in .env as TT_REFRESH.
The refresh token is long-lived; the script will use it to obtain short-lived access tokens.

Output files (one pair per account):
    sample-data/tastytrade_positions_<account>_<YYMMDD>.csv
    sample-data/tastytrade_balance_<account>_<YYMMDD>.csv

Requires: tastytrade  (not stdlib — install into .venv)
"""

import asyncio
import csv
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from tastytrade.account import Account
from tastytrade.order import InstrumentType
from tastytrade.session import Session


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

PROVIDER_SECRET = os.environ.get("TT_SECRET", "")
REFRESH_TOKEN   = os.environ.get("TT_REFRESH", "")

if not PROVIDER_SECRET or not REFRESH_TOKEN:
    print(
        "Error: TT_SECRET and TT_REFRESH must be set in .env or environment.",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _today() -> str:
    """Return today's date as YYMMDD (matches existing tastytrade filename convention)."""
    return datetime.now().strftime("%y%m%d")


def _fmt_exp_date(dt: datetime | None) -> str:
    """Format expiry datetime as 'Jun 18, 2026' (the format parse_tastytrade expects)."""
    if dt is None:
        return ""
    return dt.strftime("%b %-d, %Y")


def _dec(value: Decimal | None) -> str:
    """Convert a Decimal to a plain string, or empty string if None."""
    if value is None:
        return ""
    return str(value)


# ---------------------------------------------------------------------------
# Per-account download
# ---------------------------------------------------------------------------

async def download_account(session: Session, account: Account, date: str) -> None:
    account_number = account.account_number
    print(f"Account {account_number}")

    # --- positions ---
    positions = await account.get_positions(session, include_marks=True)
    pos_path = f"sample-data/tastytrade_positions_{account_number}_{date}.csv"
    pos_fields = [
        "Account", "Symbol", "Type", "Quantity",
        "Exp Date", "DTE", "Strike Price", "Call/Put",
        "Underlying Last Price", "P/L Day", "Delta", "P/L Open",
        "Bid (Sell)", "Ask (Buy)", "Trade Price", "D's Opn",
        "Days To Expiration", "Net Liq",
    ]
    with open(pos_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=pos_fields, lineterminator="\n")
        writer.writeheader()
        for pos in positions:
            is_option = pos.instrument_type in (
                InstrumentType.EQUITY_OPTION,
                InstrumentType.FUTURE_OPTION,
            )
            pos_type = "OPTION" if is_option else "STOCK"

            # mark_price is the mid-market price from the exchange.
            # The parser computes option last_price as (Bid + Ask) / 2,
            # so writing mark_price into both columns yields mark_price as the result.
            mark = _dec(pos.mark_price)

            writer.writerow({
                "Account":               account_number,
                "Symbol":                pos.symbol,
                "Type":                  pos_type,
                "Quantity":              _dec(pos.quantity),
                "Exp Date":              _fmt_exp_date(pos.expires_at),
                "DTE":                   "",
                "Strike Price":          "",   # not available on CurrentPosition
                "Call/Put":              "",   # not available on CurrentPosition
                "Underlying Last Price": _dec(pos.close_price),
                "P/L Day":               "",
                "Delta":                 "",
                "P/L Open":              "",
                "Bid (Sell)":            mark,
                "Ask (Buy)":             mark,
                "Trade Price":           "",
                "D's Opn":               "",
                "Days To Expiration":    "",
                "Net Liq":               _dec(pos.mark),
            })
    print(f"  wrote {pos_path}")

    # --- balance ---
    balance = await account.get_balances(session)
    bal_path = f"sample-data/tastytrade_balance_{account_number}_{date}.csv"
    with open(bal_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["Account", "Symbol", "Net Liq"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerow({
            "Account": account_number,
            "Symbol":  "Cash",
            "Net Liq": _dec(balance.cash_balance),
        })
    print(f"  wrote {bal_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main_async() -> None:
    async with Session(
        provider_secret=PROVIDER_SECRET,
        refresh_token=REFRESH_TOKEN,
    ) as session:
        accounts = await Account.get(session)
        if not accounts:
            print("No accounts returned.", file=sys.stderr)
            sys.exit(1)

        date = _today()
        for account in accounts:
            await download_account(session, account, date)

    print("Done.")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
