#!/usr/bin/env python3
"""
Translate broker position exports into a standard CSV format.

Standard output columns:
    broker, account, symbol, description, quantity, last_price, market_value, asset_type, option_symbol

Usage:
    python translate_positions.py <input_file> [<input_file> ...]
    python translate_positions.py sample-data/fidelity_Portfolio_Positions_May-05-2026.csv
    python translate_positions.py sample-data/*.csv sample-data/*.json

The broker name is taken from the filename prefix before the first underscore.
Output is written to stdout as CSV (header included).
"""

import csv
import json
import os
import re
import sys
from datetime import datetime
from io import StringIO
from typing import Iterator

OUTPUT_FIELDS = [
    "broker",
    "account",
    "symbol",
    "description",
    "quantity",
    "last_price",
    "market_value",
    "asset_type",
    "option_symbol",
    "option_strike",
    "option_put_call",
    "position_date",
]

Row = dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_number(value: str) -> str:
    """Strip $, +, commas, and % from a numeric string. Return '' if empty."""
    if value is None:
        return ""
    v = value.strip().lstrip("+").replace("$", "").replace(",", "").replace("%", "")
    return v if v not in ("--", "-", "N/A", "") else ""


def _broker_from_filename(path: str) -> str:
    basename = os.path.basename(path)
    return basename.split("_")[0]


# Ordered list of (regex, strptime_format) pairs tried against the filename stem.
# The regex must capture the date portion as group 1.
# Patterns are tried in order; first match wins.
_DATE_PATTERNS: list[tuple[str, str]] = [
    # webull:      ..._2026-05-21_...   ISO date anywhere in stem
    (r'(\d{4}-\d{2}-\d{2})',            "%Y-%m-%d"),
    # manual/etc:  same, also catches fidelity after transformation
    # fidelity:    ..._May-05-2026      month-name at end (last segment of stem)
    (r'([A-Za-z]+-\d{2}-\d{4})$',      "%b-%d-%Y"),
    # schwab:      ...-2026-05-05-HHMMSS  date followed by 6-digit time
    (r'(\d{4}-\d{2}-\d{2})-\d{6}',     "%Y-%m-%d"),
    # robinhood:   ..._20260511         8-digit compact date
    (r'(\d{8})$',                       "%Y%m%d"),
    # tastytrade:  ..._260511           6-digit compact date (YYMMDD)
    (r'(\d{6})$',                       "%y%m%d"),
]


def _date_from_file(path: str) -> str:
    """Return the position date as YYYY-MM-DD.

    Tries to parse a date from the filename stem using known patterns.
    Falls back to the file's modification time if nothing matches.
    """
    stem = os.path.basename(path).rsplit(".", 1)[0]
    for pattern, fmt in _DATE_PATTERNS:
        m = re.search(pattern, stem)
        if m:
            try:
                return datetime.strptime(m.group(1), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    # Fall back to file modification time
    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")


def _option_underlier(symbol: str) -> str:
    """Extract the underlier ticker from an option symbol.

    Handles three formats:
      - Schwab space-delimited: 'AMZN 05/15/2026 210.00 C' -> 'AMZN'
      - OCC compact:            'AMD260618C150'             -> 'AMD'
      - Tastytrade OCC spaced:  'SPY   260515C00690000'     -> 'SPY'
    """
    s = symbol.strip()
    if ' ' in s:
        return s.split()[0]
    m = re.match(r'([A-Z]+)', s)
    return m.group(1) if m else ""


def _parse_option_symbol(symbol: str) -> tuple[str, str]:
    """Return (strike, put_call) parsed from an option symbol string.

    Handles three formats:
      - Schwab space-delimited: 'AMZN 05/15/2026 210.00 C'  -> ('210.00', 'call')
      - OCC long zero-padded:   'LIT260515P00075000'         -> ('75.0', 'put')
        (also handles tastytrade OCC-spaced: 'SPY   260515C00690000')
      - OCC compact no-padding: 'AMD260618C150'              -> ('150', 'call')
        (strike has no leading zeros; may include a decimal, e.g. 'GM270115C52.5')

    Returns ('', '') if the symbol cannot be parsed.
    """
    s = symbol.strip()
    if not s:
        return "", ""

    # Schwab space-delimited: 4 tokens, last is C or P
    tokens = s.split()
    if len(tokens) == 4 and tokens[-1].upper() in ("C", "P"):
        put_call = "call" if tokens[-1].upper() == "C" else "put"
        return tokens[2], put_call

    # OCC formats (compact or long/zero-padded): leading alpha + 6-digit date + C/P + digits
    m = re.match(r'[A-Z]+(\d{6})([CP])(\d+(?:\.\d+)?)$', s)
    if m:
        _, cp, strike_raw = m.groups()
        put_call = "call" if cp == "C" else "put"
        # If 8+ digit integer with no decimal: OCC long format (3 implied decimal places)
        if re.match(r'^\d{8}$', strike_raw):
            strike = str(float(strike_raw) / 1000).rstrip('0').rstrip('.')
        else:
            strike = strike_raw
        return strike, put_call

    return "", ""


def _make_row(broker, account, symbol, description, quantity, last_price, market_value, asset_type, option_symbol="", option_strike="", option_put_call="", position_date="") -> Row:
    return {
        "broker": broker,
        "account": account,
        "symbol": symbol.strip(),
        "description": description.strip(),
        "quantity": _clean_number(quantity),
        "last_price": _clean_number(last_price),
        "market_value": _clean_number(market_value),
        "asset_type": asset_type.strip(),
        "option_symbol": option_symbol.strip(),
        "option_strike": option_strike.strip() if option_strike else "",
        "option_put_call": option_put_call.strip().lower() if option_put_call else "",
        "position_date": position_date,
    }


# ---------------------------------------------------------------------------
# Fidelity CSV parser
# ---------------------------------------------------------------------------
# Format notes:
#   - First row has a BOM; columns include Account Number, Account Name, Symbol,
#     Description, Quantity, Last Price, Current Value, Type.
#   - Rows with no symbol (cash / pending) are still included as Cash.
#   - Trailing disclaimer lines start with a quote character; stop there.
#   - Option symbols have a leading space in the raw data.

FIDELITY_SKIP_SYMBOLS: set[str] = set()

# Symbols emitted as Cash summary rows (empty symbol, quantity, last_price).
FIDELITY_CASH_SYMBOLS = {"Pending activity"}

def parse_fidelity(path: str) -> Iterator[Row]:
    broker = _broker_from_filename(path)

    with open(path, newline="", encoding="utf-8-sig") as fh:
        lines = fh.readlines()

    # Collect only the data lines (stop at blank/disclaimer lines after the data)
    data_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            break
        if stripped.startswith('"'):
            break
        data_lines.append(line)

    reader = csv.DictReader(StringIO("".join(data_lines)))

    for rec in reader:
        symbol = rec.get("Symbol", "").strip()
        if not symbol or symbol in FIDELITY_SKIP_SYMBOLS:
            continue

        account_num = rec.get("Account Number", "").strip()
        account_name = rec.get("Account Name", "").strip()
        account = f"{account_num} {account_name}".strip() if account_num else account_name

        market_value = rec.get("Current Value", "")

        # Cash summary rows: emit with empty symbol, quantity, last_price.
        if symbol in FIDELITY_CASH_SYMBOLS:
            yield _make_row(broker, account, "", symbol,
                            "", "", market_value, "Cash")
            continue

        quantity = rec.get("Quantity", "")
        last_price = rec.get("Last Price", "")
        description = rec.get("Description", "")
        asset_type_raw = rec.get("Type", "").strip()

        # Classify asset type
        if symbol.endswith("**"):
            asset_type = "Cash"
        elif symbol.startswith("-") or (description and re.search(r"\b(CALL|PUT)\b", description, re.I)):
            asset_type = "Option"
        elif asset_type_raw in ("Margin", "Financing"):
            asset_type = "Equity"
        elif asset_type_raw:
            asset_type = asset_type_raw
        else:
            asset_type = "Equity"

        # Clean option symbol: remove leading space/dash notation used by Fidelity
        # Fidelity short options look like " -AMD260618C150"
        clean_symbol = symbol.lstrip()
        if clean_symbol.startswith("-"):
            clean_symbol = clean_symbol[1:]

        underlier = _option_underlier(clean_symbol) if asset_type == "Option" else ""
        out_symbol = underlier if underlier else clean_symbol
        opt_strike, opt_put_call = _parse_option_symbol(clean_symbol) if asset_type == "Option" else ("", "")
        yield _make_row(broker, account, out_symbol, description,
                        quantity, last_price, market_value, asset_type,
                        clean_symbol if asset_type == "Option" else "",
                        opt_strike, opt_put_call)

# ---------------------------------------------------------------------------
# Schwab CSV parser
# ---------------------------------------------------------------------------
# Format notes:
#   - File has multiple account sections, each preceded by an account name line
#     and a fresh header row.
#   - Skip: "Positions Total", "Cash & Cash Investments", "Futures Cash",
#     "Futures Positions Market Value", any row where Symbol is empty.
#   - Quantities use comma formatting ("1,300").
#   - Asset type is in the last column "Asset Type".

SCHWAB_SKIP_SYMBOLS = {
    "Positions Total",
}

# Special summary rows: emitted as cash/futures rows with empty symbol,
# quantity, and last_price. asset_type is overridden by this map.
SCHWAB_SUMMARY_ASSET_TYPES = {
    "Cash & Cash Investments": "Cash",
    "Futures Cash": "Futures",
    "Futures Positions Market Value": "Futures",
}

SCHWAB_HEADER_FIRST_COL = "Symbol"

def parse_schwab(path: str) -> Iterator[Row]:
    broker = _broker_from_filename(path)

    with open(path, newline="", encoding="utf-8-sig") as fh:
        raw_lines = fh.readlines()

    current_account = "unknown"
    header: list[str] | None = None
    pending_account_name: str | None = None

    for line in raw_lines:
        stripped = line.strip()

        # Skip the very first summary line ("Positions for All-Accounts as of ...")
        if stripped.startswith('"Positions for'):
            continue

        # Blank lines reset account name candidates
        if not stripped:
            continue

        # Detect header rows (start with "Symbol")
        if stripped.startswith(f'"{SCHWAB_HEADER_FIRST_COL}"') or stripped.startswith(SCHWAB_HEADER_FIRST_COL):
            header = next(csv.reader([stripped]))
            # If we had a pending account name, commit it
            if pending_account_name is not None:
                current_account = pending_account_name
                pending_account_name = None
            continue

        # Try to parse as a CSV row
        try:
            cols = next(csv.reader([stripped]))
        except Exception:
            continue

        if not cols:
            continue

        first = cols[0].strip()

        # Account name lines appear between blank lines and the header row.
        # They are plain text, not quoted, and don't parse as data rows.
        # Heuristic: if there's no current header yet, or the line has very few
        # columns compared to the header, it's an account name.
        if header is None or (len(cols) < 4 and first and first not in SCHWAB_SKIP_SYMBOLS
                              and first not in SCHWAB_SUMMARY_ASSET_TYPES):
            pending_account_name = first
            continue

        # Map columns to dict
        rec = dict(zip(header, cols))
        symbol = rec.get("Symbol", "").strip()

        if not symbol or symbol in SCHWAB_SKIP_SYMBOLS:
            continue

        description = rec.get("Description", "")
        quantity = rec.get("Qty (Quantity)", "")
        last_price = rec.get("Price", "")
        market_value = rec.get("Mkt Val (Market Value)", "")
        asset_type = rec.get("Asset Type", "")
        if asset_type == "ETFs & Closed End Funds":
            asset_type = "Equity"

        # Cash & cash-equivalent summary rows: override symbol, description,
        # quantity, last_price, and asset_type.
        if symbol in SCHWAB_SUMMARY_ASSET_TYPES:
            asset_type = SCHWAB_SUMMARY_ASSET_TYPES[symbol]
            yield _make_row(broker, current_account, "", symbol,
                            "", "", market_value, asset_type)
            continue

        underlier = _option_underlier(symbol) if asset_type == "Option" else ""
        out_symbol = underlier if underlier else symbol
        opt_strike, opt_put_call = _parse_option_symbol(symbol) if asset_type == "Option" else ("", "")
        yield _make_row(broker, current_account, out_symbol, description,
                        quantity, last_price, market_value, asset_type,
                        symbol if asset_type == "Option" else "",
                        opt_strike, opt_put_call)


# ---------------------------------------------------------------------------
# Public JSON parser
# ---------------------------------------------------------------------------
# Format notes:
#   - Top-level object with accountId and positions array.
#   - Each position has instrument.symbol, instrument.name, instrument.type,
#     quantity (string, can be negative), currentValue, lastPrice.lastPrice.
#   - instrument.type values seen: EQUITY, OPTION.

def parse_public(path: str) -> Iterator[Row]:
    broker = _broker_from_filename(path)

    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    account = data.get("accountId", "unknown")
    positions = data.get("positions", [])

    for pos in positions:
        instrument = pos.get("instrument", {})
        symbol = instrument.get("symbol", "")
        description = instrument.get("name", "")
        raw_type = instrument.get("type", "")

        quantity = str(pos.get("quantity", ""))
        last_price_obj = pos.get("lastPrice", {})
        last_price = str(last_price_obj.get("lastPrice", "")) if isinstance(last_price_obj, dict) else ""
        market_value = str(pos.get("currentValue", ""))

        # Normalise asset type
        type_map = {
            "EQUITY": "Equity",
            "OPTION": "Option",
        }
        asset_type = type_map.get(raw_type.upper(), raw_type.capitalize())

        underlier = _option_underlier(symbol) if asset_type == "Option" else ""
        out_symbol = underlier if underlier else symbol
        opt_strike, opt_put_call = _parse_option_symbol(symbol) if asset_type == "Option" else ("", "")
        yield _make_row(broker, account, out_symbol, description,
                        quantity, last_price, market_value, asset_type,
                        symbol if asset_type == "Option" else "",
                        opt_strike, opt_put_call)

    # Emit cash balance from the equity breakdown array (not in positions[])
    for equity_entry in data.get("equity", []):
        if equity_entry.get("type", "").upper() == "CASH":
            yield _make_row(broker, account, "", "Cash",
                            "", "", str(equity_entry.get("value", "")), "Cash")


# ---------------------------------------------------------------------------
# Robinhood HTML parser
# ---------------------------------------------------------------------------
# Format notes:
#   - HTML scraped from the Robinhood web portfolio page.
#   - Filename: robinhood_positions_<account>_<date>.html; account is the
#     third underscore-delimited segment.
#   - Each position is an <a href="/stocks/SYMBOL"> block. Within each block,
#     <span> text nodes appear in fixed order:
#       [0] name (description)
#       [1] symbol
#       [2] shares (quantity)
#       [3] price (last_price, $ prefixed)
#       [4] average cost (unused)
#       [5] total return (unused)
#       [6] equity (market_value, $ prefixed and comma-formatted)
#   - All positions are equities; no options or cash rows in this export.

def parse_robinhood(path: str) -> Iterator[Row]:
    broker = _broker_from_filename(path)
    account = os.path.basename(path).split("_")[2]

    with open(path, encoding="utf-8") as fh:
        html = fh.read()

    for symbol, block in re.findall(r'href="/stocks/([^"]+)"(.*?)</a>', html, re.S):
        spans = re.findall(r'<span[^>]*>([^<]+)</span>', block)
        if len(spans) < 7:
            continue
        description = spans[0]
        quantity    = spans[2]
        last_price  = spans[3]
        market_value = spans[6]
        yield _make_row(broker, account, symbol, description,
                        quantity, last_price, market_value, "Equity")


# ---------------------------------------------------------------------------
# Tastytrade CSV parser
# ---------------------------------------------------------------------------
# Format notes:
#   - UTF-8, no BOM. One header row.
#   - Two file types, detected from the second underscore-delimited segment:
#     tastytrade_positions_<account>_<date>.csv — positions
#     tastytrade_balance_<account>_<date>.csv   — cash balance
#   - Positions columns used: Account, Symbol, Type, Quantity, Exp Date,
#     Strike Price, Call/Put, Underlying Last Price, Net Liq.
#   - Type values: STOCK → Equity, OPTION → Option.
#   - Option symbols use OCC-style with extra internal spaces
#     (e.g. "SPY   260515C00690000") — preserved as-is.
#   - last_price: for STOCK, Underlying Last Price; for OPTION, mid of
#     Bid (Sell) and Ask (Buy), rounded to 4 decimal places.
#   - market_value: Net Liq — comma-formatted, can be negative in quotes.
#   - description: empty for stocks; "CALL/PUT Exp Strike" for options.
#   - Balance file: columns Account, Symbol, Net Liq. Standard 3-column CSV;
#     Net Liq is a plain number read via csv.DictReader.
#   - Account is read from the Account column in both file types.

def parse_tastytrade(path: str) -> Iterator[Row]:
    broker = _broker_from_filename(path)
    file_type = os.path.basename(path).split("_")[1]  # "positions" or "balance"

    if file_type == "balance":
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for rec in reader:
                account = rec.get("Account", "").strip()
                market_value = rec.get("Net Liq", "")
                yield _make_row(broker, account, "", "Cash", "", "", market_value, "Cash")
        return

    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for rec in reader:
            raw_type = rec.get("Type", "").strip()
            if raw_type == "STOCK":
                asset_type = "Equity"
            elif raw_type == "OPTION":
                asset_type = "Option"
            else:
                asset_type = raw_type.capitalize()

            account = rec.get("Account", "").strip()
            symbol = rec.get("Symbol", "").strip()
            quantity = rec.get("Quantity", "")
            market_value = rec.get("Net Liq", "")

            if asset_type == "Option":
                # Use mid of Bid/Ask as the per-option last_price.
                bid = _clean_number(rec.get("Bid (Sell)", ""))
                ask = _clean_number(rec.get("Ask (Buy)", ""))
                try:
                    last_price = str(round((float(bid) + float(ask)) / 2, 4))
                except (ValueError, TypeError):
                    last_price = ""
            else:
                last_price = rec.get("Underlying Last Price", "")

            if asset_type == "Option":
                call_put = rec.get("Call/Put", "").strip()
                exp_date = rec.get("Exp Date", "").strip()
                strike = rec.get("Strike Price", "").strip()
                description = f"{call_put} {exp_date} {strike}" if (call_put and exp_date and strike) else ""
                option_put_call = call_put.lower() if call_put else ""
                option_strike = strike
            else:
                description = ""
                option_put_call = ""
                option_strike = ""

            underlier = _option_underlier(symbol) if asset_type == "Option" else ""
            out_symbol = underlier if underlier else symbol
            yield _make_row(broker, account, out_symbol, description,
                            quantity, last_price, market_value, asset_type,
                            symbol if asset_type == "Option" else "",
                            option_strike, option_put_call)


# ---------------------------------------------------------------------------
# Webull JSON parser
# ---------------------------------------------------------------------------
# Format notes:
#   - Two file types per account, distinguished by filename suffix before .json:
#     webull_<account>_<date>_positions.json  — JSON array of position objects
#     webull_<account>_<date>_balance.json    — single JSON object with cash totals
#   - Account ID is the second underscore-delimited segment of the filename.
#   - Positions: each object has symbol, instrument_type (OPTION/EQUITY),
#     quantity (string, negative = short), last_price, market_value, cost_price.
#   - option_strategy may be COVERED_STOCK: the top-level object represents the
#     combined position (e.g. long stock + short call). Use top-level fields
#     directly; do not iterate legs.
#   - Balance: emit one Cash row using total_cash_balance.

def _webull_account_from_filename(path: str) -> str:
    """Extract the account ID (second _ segment) from a webull filename."""
    parts = os.path.basename(path).split("_")
    return parts[1] if len(parts) > 1 else "unknown"


def parse_webull(path: str) -> Iterator[Row]:
    broker = _broker_from_filename(path)
    account = _webull_account_from_filename(path)
    basename = os.path.basename(path)

    # Detect file type from the segment immediately before ".json"
    name_no_ext = basename.rsplit(".", 1)[0]
    file_type = name_no_ext.split("_")[-1]  # "positions" or "balance"

    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    if file_type == "balance":
        cash = str(data.get("total_cash_balance", ""))
        yield _make_row(broker, account, "", "Cash", "", "", cash, "Cash")
        return

    # positions file — data is a JSON array
    type_map = {
        "EQUITY": "Equity",
        "OPTION": "Option",
    }

    for pos in data:
        symbol = pos.get("symbol", "")
        raw_type = pos.get("instrument_type", "")
        legs = pos.get("legs", [])

        if pos.get("option_strategy") == "COVERED_STOCK":
            # Emit two rows: one equity leg, one option leg.
            # The legs have no quantity or market_value; compute from top-level quantity.
            top_qty = int(pos.get("quantity", 0))
            equity_legs = [l for l in legs if l.get("instrument_type", "").upper() == "EQUITY"]
            option_legs = [l for l in legs if l.get("instrument_type", "").upper() == "OPTION"]

            if equity_legs:
                leg = equity_legs[0]
                lp = leg.get("last_price", "")
                eq_qty = top_qty * 100
                eq_mv = round(float(lp) * eq_qty, 2) if lp else ""
                yield _make_row(broker, account, symbol, "",
                                str(eq_qty), str(lp),
                                str(eq_mv) if eq_mv != "" else "", "Equity")

            if option_legs:
                leg = option_legs[0]
                lp = leg.get("last_price", "")
                opt_qty = -top_qty
                opt_mv = round(-(float(lp) * top_qty * 100), 2) if lp else ""
                opt_type = leg.get("option_type", "")
                expire = leg.get("option_expire_date", "")
                strike = leg.get("option_exercise_price", "")
                description = f"{opt_type} {expire} {strike}" if (opt_type and expire and strike) else ""
                yield _make_row(broker, account, symbol, description,
                                str(opt_qty), str(lp),
                                str(opt_mv) if opt_mv != "" else "", "Option",
                                symbol,  # symbol is already the underlier
                                strike, opt_type.lower() if opt_type else "")
            continue

        # Non-covered positions: use top-level fields directly.
        quantity = str(pos.get("quantity", ""))
        last_price = str(pos.get("last_price", ""))
        market_value = str(pos.get("market_value", ""))
        asset_type = type_map.get(raw_type.upper(), raw_type.capitalize())

        # Description: for single options include type, expiry, strike from leg
        description = ""
        opt_strike = ""
        opt_put_call = ""
        option_legs = [l for l in legs if l.get("instrument_type", "").upper() == "OPTION"]
        if option_legs:
            leg = option_legs[0]
            opt_type = leg.get("option_type", "")
            expire = leg.get("option_expire_date", "")
            strike = leg.get("option_exercise_price", "")
            if opt_type and expire and strike:
                description = f"{opt_type} {expire} {strike}"
            opt_strike = strike
            opt_put_call = opt_type.lower() if opt_type else ""

        yield _make_row(broker, account, symbol, description,
                        quantity, last_price, market_value, asset_type,
                        symbol if asset_type == "Option" else "",  # symbol is already the underlier
                        opt_strike, opt_put_call)


# ---------------------------------------------------------------------------
# Manual assets CSV parser
# ---------------------------------------------------------------------------
# Format notes:
#   - UTF-8, no BOM. One header row.
#   - Single file for all manual/non-broker assets.
#   - Columns: account, symbol, description, quantity, last_price,
#     market_value, asset_type — matching the output schema directly.
#   - All fields passed through as-is (numbers cleaned by _make_row).

def parse_manual(path: str) -> Iterator[Row]:
    broker = _broker_from_filename(path)

    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for rec in reader:
            yield _make_row(
                broker,
                rec.get("account", ""),
                rec.get("symbol", ""),
                rec.get("description", ""),
                rec.get("quantity", ""),
                rec.get("last_price", ""),
                rec.get("market_value", ""),
                rec.get("asset_type", ""),
            )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

PARSERS = {
    "fidelity": parse_fidelity,
    "manual": parse_manual,
    "robinhood": parse_robinhood,
    "schwab": parse_schwab,
    "public": parse_public,
    "tastytrade": parse_tastytrade,
    "webull": parse_webull,
}

def parse_file(path: str) -> Iterator[Row]:
    broker = _broker_from_filename(path).lower()
    parser = PARSERS.get(broker)
    if parser is None:
        raise ValueError(
            f"Unknown broker '{broker}' derived from filename '{os.path.basename(path)}'. "
            f"Supported brokers: {', '.join(PARSERS)}"
        )
    position_date = _date_from_file(path)
    for row in parser(path):
        row["position_date"] = position_date
        yield row


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    # Validate all files first so we don't emit a partial header-only CSV on error.
    for path in sys.argv[1:]:
        broker = _broker_from_filename(path).lower()
        if broker not in PARSERS:
            print(
                f"ERROR: Unknown broker '{broker}' derived from filename '{os.path.basename(path)}'. "
                f"Supported brokers: {', '.join(PARSERS)}",
                file=sys.stderr,
            )
            sys.exit(1)
        if not os.path.exists(path):
            print(f"ERROR: File not found: {path}", file=sys.stderr)
            sys.exit(1)

    writer = csv.DictWriter(sys.stdout, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
    writer.writeheader()

    for path in sys.argv[1:]:
        try:
            for row in parse_file(path):
                writer.writerow(row)
        except Exception as exc:
            print(f"ERROR processing {path}: {exc}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
