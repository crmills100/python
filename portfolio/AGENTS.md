# AGENTS.md

## What this repo is

A single Python script (`translate_positions.py`) that converts broker position exports into a standard CSV format. No dependencies beyond the Python 3 stdlib.

## Running the script

```bash
python3 translate_positions.py <file> [<file> ...]
```

Output is written to stdout. Pass explicit file paths; the script does no file selection itself.

## Rebuilding positions.csv

`refresh_positions.py` selects the latest snapshot per account from `sample-data/` and writes `positions.csv`:

```bash
python3 refresh_positions.py
```

For brokers with download scripts (webull, and later tastytrade/schwab), multiple dated snapshots may accumulate in `sample-data/`. `refresh_positions.py` picks only the newest file per account using lexicographic date sorting. For brokers without download scripts, all matching files are included as-is.

To verify the output is correct:

```bash
python3 refresh_positions.py && diff positions.csv <(python3 refresh_positions.py 2>/dev/null)
```

Or compare against the canonical file directly after any change:

```bash
python3 refresh_positions.py
diff positions.csv /tmp/positions_check.csv  # if you saved a known-good copy there
```

There are no lint config and no CI.

## Tests

```bash
.venv/bin/python3.12 -m pytest tests/
```

`tests/test_translate.py` covers:
- `_clean_number`, `_option_underlier`, `_parse_option_symbol`, `_date_from_file` — unit tests
- Each broker parser against its sample file, asserting output matches `positions.csv`
- Full pipeline integration test replicating `refresh_positions.py` file selection

After any change to `translate_positions.py`, run `python3 refresh_positions.py` to rebuild `positions.csv` if the output legitimately changes, then run the tests to confirm everything passes.

Test fixtures live in `tests/data/` — a fixed snapshot of the broker input files and the expected `positions.csv` output derived from them. These are independent of `sample-data/` and do not change when new downloads are run. The `public` fixture is named `public_account-positions_2026-05-06.json` (date embedded) so `_date_from_file` doesn't fall back to mtime.

## Standard output schema

```
broker, account, symbol, description, quantity, last_price, market_value, asset_type, option_symbol, option_strike, option_put_call, position_date
```

- `quantity`, `last_price`, `market_value`: plain numbers — no `$`, `+`, `,`; negative for short positions
- `_clean_number` also treats `"--"`, `"-"`, and `"N/A"` as empty strings
- Cash-only rows (money market, sweep accounts): `quantity` and `last_price` are empty strings
- CSV writer uses Unix line endings (`lineterminator="\n"`)
- `option_symbol`: for `Option` rows, holds the broker's raw option symbol; `symbol` is set to the underlier ticker. For non-option rows, `option_symbol` is empty. The underlier is extracted by `_option_underlier()`: takes the leading alpha characters for OCC/compact formats, or the first space-delimited token for Schwab's format. For webull, the symbol is already the underlier so `symbol == option_symbol`.
- `option_strike`: strike price as a plain number string (e.g. `"150"`, `"52.5"`, `"210.00"`); empty for non-option rows. Source varies by broker: explicit column for tastytrade and webull; parsed from `option_symbol` via `_parse_option_symbol()` for fidelity, schwab, and public.
- `option_put_call`: `"call"` or `"put"` (lowercase); empty for non-option rows. Same sourcing as `option_strike`. `_parse_option_symbol()` handles OCC compact (`AMD260618C150`), OCC long zero-padded (`LIT260515P00075000`, `SPY   260515C00690000`), and Schwab space-delimited (`AMZN 05/15/2026 210.00 C`).
- `position_date`: `YYYY-MM-DD` date the positions were captured. Extracted from the filename by `_date_from_file()` using a sequence of regex patterns (ISO date, month-name date, compact 8-digit, compact 6-digit YYMMDD). Falls back to the file's modification time if no pattern matches. The date is injected into every row in `parse_file()`, not in the individual broker parsers.

## Broker detection

The broker name is the filename prefix **before the first `_`**, lowercased. The prefix must match a key in the `PARSERS` dict. File names that don't match a known broker cause an immediate error **before any output is written** (two-pass design: all files are validated first, then the header is emitted).

## Supported brokers and format quirks

### fidelity — CSV
- UTF-8 BOM (`utf-8-sig`). One header row at top.
- Trailing disclaimer lines (starting with `"`) and the blank line before them must be ignored — the parser stops at the first blank or quoted line.
- Short option symbols have a leading space and dash: ` -AMD260618C150` → strip to `AMD260618C150`.
- Cash positions (money market, sweep): symbol ends with `**`; no quantity or price.
- `Type` column holds account margin type (`Cash`, `Margin`, `Financing`), **not** asset class. Asset type classification priority:
  1. Symbol ends with `**` → `"Cash"`
  2. Symbol starts with `"-"` **or** description contains `CALL`/`PUT` (regex, case-insensitive) → `"Option"`
  3. `Type` is `"Margin"` or `"Financing"` → `"Equity"`
  4. Else use raw `Type` column value if non-empty
  5. Else `"Equity"`
- Skip symbols in `FIDELITY_SKIP_SYMBOLS` set (currently empty). Symbols in `FIDELITY_CASH_SYMBOLS` (currently: `"Pending activity"`) are emitted as Cash summary rows with empty symbol, quantity, and last_price.

### robinhood — HTML
- Scraped HTML from the Robinhood web portfolio page (`.html` extension).
- Account is the third underscore-delimited filename segment (e.g. `robinhood_positions_ACCOUNT1_date.html` → `ACCOUNT1`).
- Each position is an `<a href="/stocks/SYMBOL">` block. Within each block, `<span>` text nodes appear in fixed order: `[0]` description, `[1]` symbol, `[2]` quantity, `[3]` last_price, `[4]` avg_cost (unused), `[5]` total_return (unused), `[6]` market_value.
- All positions are `Equity`; no options or cash rows in this export.
- CSS class names are obfuscated — parse by span position, not class.

### schwab — CSV
- UTF-8 BOM (`utf-8-sig`). Multiple account sections in one file.
- Account name detection heuristic: a parsed line with **fewer than 4 CSV columns** (and not in `SCHWAB_SKIP_SYMBOLS` or `SCHWAB_SUMMARY_ASSET_TYPES`) is treated as an account name. The name is committed when the next header row (`Symbol,...`) is encountered.
- Exact column names: `Qty (Quantity)`, `Price`, `Mkt Val (Market Value)`, `Asset Type`.
- Skip rows where `Symbol` is in `SCHWAB_SKIP_SYMBOLS`: `Positions Total` only.
- `Cash & Cash Investments`, `Futures Cash`, and `Futures Positions Market Value` are **not** skipped — they are emitted as summary rows with empty symbol (the symbol string becomes the description), empty quantity/last_price, and overridden `asset_type`: `"Cash"` for cash, `"Futures"` for both futures rows. This mapping lives in `SCHWAB_SUMMARY_ASSET_TYPES`.
- Quantities use comma formatting (`"1,300"`) — stripped by `_clean_number`.
- `Asset Type` column values used as-is except `"ETFs & Closed End Funds"` → `"Equity"`.
- Option symbols use Schwab's space-delimited format (`AMZN 05/15/2026 210.00 C`), not OCC format.

### manual — CSV
- UTF-8, no BOM. One header row. One file for all non-broker assets.
- Columns map directly to the output schema: `account`, `symbol`, `description`, `quantity`, `last_price`, `market_value`, `asset_type`.
- `symbol` should be empty for unique assets (e.g. a specific property); use a short code for fungible assets (e.g. `GOLD`).
- `quantity` and `last_price` are optional — set `market_value` directly and leave them empty for assets without a per-unit price.
- `asset_type` is free-form (e.g. `RealEstate`, `Commodity`, `PrivateEquity`).
- Multiple accounts and asset types can be mixed in one file; the `account` column separates them.

### public — JSON
- Single JSON object with `accountId` and `positions[]` array.
- Fields used: `instrument.symbol`, `instrument.name`, `instrument.type`, `quantity`, `currentValue`, `lastPrice.lastPrice` (nested dict — guarded with `isinstance` check; absent or non-dict → `""`).
- `instrument.type` values: `EQUITY` → `Equity`, `OPTION` → `Option`; unknown types fall back to `raw_type.capitalize()`.
- `quantity` is a string and can be negative (`"-4"` for short options).
- Option symbols use OCC long format (e.g. `LIT260515P00075000`).
- Cash balance is **not** in `positions[]` — it comes from `equity[]` where `type == "CASH"`. Emitted as a row with empty symbol, description `"Cash"`, empty quantity/last_price, and `asset_type` `"Cash"`.

### tastytrade — CSV
- UTF-8, no BOM. One header row.
- Filename: `tastytrade_positions_<account>_<date>.csv`. Account is read from the `Account` column (not the filename — the filename has a spurious `x` prefix on the account segment).
- Columns used: `Account`, `Symbol`, `Type`, `Quantity`, `Exp Date`, `Strike Price`, `Call/Put`, `Underlying Last Price`, `Net Liq`.
- `Type` values: `STOCK` → `"Equity"`, `OPTION` → `"Option"`.
- Option symbols use OCC-style with extra internal spaces (e.g. `SPY   260515C00690000`) — preserved as-is.
- `last_price`: for `STOCK`, `Underlying Last Price`; for `OPTION`, the mid of `Bid (Sell)` and `Ask (Buy)`, rounded to 4 decimal places.
- `market_value`: `Net Liq` — comma-formatted, can be negative in quotes (e.g. `"-16,750.00"`), handled by `_clean_number`.
- Description: empty for stocks; `"CALL/PUT Exp Strike"` for options (e.g. `"Put Jun 18, 2026 940"`).
- Balance file: `tastytrade_balance_<account>_<date>.csv`. Columns: `Account`, `Symbol`, `Net Liq`. Standard 3-column CSV; `Net Liq` is a plain number read via `csv.DictReader`.

### webull — JSON
- Two file types per account, detected from the last `_`-segment before `.json`: `positions` or `balance`.
- Account ID from second `_`-segment of filename via `_webull_account_from_filename()`.
- Balance file: single JSON object; cash from `total_cash_balance`.
- `COVERED_STOCK` strategy: emits **two rows** from `legs[]` array:
  - Equity leg: `quantity = top_qty * 100`, `market_value = float(lp) * eq_qty` rounded to 2 dp
  - Option leg: `quantity = -top_qty`, `market_value = -(float(lp) * top_qty * 100)` rounded to 2 dp; description from `option_type`, `option_expire_date`, `option_exercise_price` leg fields
- For webull options, `option_symbol` is set to `symbol` (the underlier) because webull already uses underlier as symbol.
- Non-covered positions use top-level `quantity`/`last_price`/`market_value` directly; option leg metadata still read from `legs[0]` for description/strike/put_call.

## analyze_exposure.py

A secondary script that reads `positions.csv` (or any path passed as the first argument) and produces a per-symbol / per-broker / per-asset-type exposure summary. Writes `exposure_summary.csv` by default. Requires `openpyxl` for the `.xlsx` variant. Not part of the core translate pipeline.

## Adding a new broker

1. Add `def parse_<broker>(path: str) -> Iterator[Row]` — yield `_make_row(...)` for each position.
2. Register it in `PARSERS` at the bottom of the file.
3. Name input files `<broker>_anything.csv` (or `.json`).

## Download scripts

Credentials for all download scripts are read from a `.env` file (gitignored) in the repo root. Run any script with:

```bash
python3 download_<broker>.py
```

Each script iterates all accounts returned by the API (no hardcoded indices) and writes dated snapshot files to `sample-data/`. `refresh_positions.py` then picks the latest snapshot per account.

### download_webull.py

Replaces the old `webapi_download.py`. Requires `webull-trade-sdk` (install into `.venv`).

```
WEBULL_APP_KEY=...
WEBULL_APP_SECRET=...
WEBULL_REGION=us   # optional, defaults to "us"
```

### download_tastytrade.py

Requires `tastytrade` (install into `.venv`). Uses OAuth refresh-token flow — no browser required.

```
TT_SECRET=...    # OAuth provider secret from your Tastytrade developer application
TT_REFRESH=...   # long-lived refresh token
```

The `grant_type=password` flow is **not supported** by Tastytrade. Obtain a refresh token via the Tastytrade developer portal and set it in `.env` manually.

The script writes positions using the same CSV columns as a manual export. Option `last_price` is sourced from `mark_price` (written into both `Bid (Sell)` and `Ask (Buy)` so the parser's mid calculation yields the mark). `Strike Price` and `Call/Put` are left empty — the parser derives them from the OCC option symbol instead.

### download_schwab.py

Requires `schwab-py` (install into `.venv`). Uses OAuth2 authorization code flow. On first run it opens a browser for a one-time login; subsequent runs load the saved token from `schwab_token.json` (gitignored) and refresh it automatically.

```
SCHWAB_APP_KEY=...
SCHWAB_APP_SECRET=...
SCHWAB_CALLBACK_URL=https://127.0.0.1:8182   # optional, this is the default
```

Register `https://127.0.0.1:8182` as the redirect URI in your Schwab developer app before running for the first time. The browser will show a self-signed certificate warning on the redirect — this is expected; accept it to complete the flow.

Run `setup_schwab_auth.py` once to complete the browser login and create `schwab_token.json`. After that, `download_schwab.py` loads the token file directly and fails fast if it is missing.

The script writes a single multi-account CSV matching the manual export format exactly, so `parse_schwab` works unchanged.

## Sample data

`sample-data/` contains files for all seven brokers: `fidelity`, `manual`, `robinhood`, `schwab`, `public`, `tastytrade`, and `webull` (two files per webull account: `_positions.json` and `_balance.json`). Multiple webull accounts and date snapshots are present; the glob `webull_*.json` picks them all up correctly.

The canonical expected output for all sources is `positions.csv` in the repo root. Use `refresh_positions.py` to rebuild it:

```bash
python3 refresh_positions.py
diff positions.csv <(python3 refresh_positions.py 2>/dev/null)  # empty = correct
```
