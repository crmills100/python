# AGENTS.md

## What this repo is

A single Python script (`translate_positions.py`) that converts broker position exports into a standard CSV format. No dependencies beyond the Python 3 stdlib.

## Running the script

```bash
python3 translate_positions.py <file> [<file> ...]
```

Output is written to stdout. Redirect to save:

```bash
python3 translate_positions.py sample-data/*.csv sample-data/*.json > positions.csv
```

## Verifying output

`positions.csv` in the repo root is the canonical expected output for all sample files. Re-run the command above and diff against it to verify correctness.

There are no automated tests, no lint config, and no CI.

## Standard output schema

```
broker, account, symbol, description, quantity, last_price, market_value, asset_type, option_symbol, option_strike, option_put_call
```

- `quantity`, `last_price`, `market_value`: plain numbers — no `$`, `+`, `,`; negative for short positions
- `_clean_number` also treats `"--"`, `"-"`, and `"N/A"` as empty strings
- Cash-only rows (money market, sweep accounts): `quantity` and `last_price` are empty strings
- CSV writer uses Unix line endings (`lineterminator="\n"`)
- `option_symbol`: for `Option` rows, holds the broker's raw option symbol; `symbol` is set to the underlier ticker. For non-option rows, `option_symbol` is empty. The underlier is extracted by `_option_underlier()`: takes the leading alpha characters for OCC/compact formats, or the first space-delimited token for Schwab's format. For webull, the symbol is already the underlier so `symbol == option_symbol`.
- `option_strike`: strike price as a plain number string (e.g. `"150"`, `"52.5"`, `"210.00"`); empty for non-option rows. Source varies by broker: explicit column for tastytrade and webull; parsed from `option_symbol` via `_parse_option_symbol()` for fidelity, schwab, and public.
- `option_put_call`: `"call"` or `"put"` (lowercase); empty for non-option rows. Same sourcing as `option_strike`. `_parse_option_symbol()` handles OCC compact (`AMD260618C150`), OCC long zero-padded (`LIT260515P00075000`, `SPY   260515C00690000`), and Schwab space-delimited (`AMZN 05/15/2026 210.00 C`).

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

## analyze_exposure.py

A secondary script that reads `positions.csv` (or any path passed as the first argument) and produces a per-symbol / per-broker / per-asset-type exposure summary. Writes `exposure_summary.csv` by default. Requires `openpyxl` for the `.xlsx` variant. Not part of the core translate pipeline.

## Adding a new broker

1. Add `def parse_<broker>(path: str) -> Iterator[Row]` — yield `_make_row(...)` for each position.
2. Register it in `PARSERS` at the bottom of the file.
3. Name input files `<broker>_anything.csv` (or `.json`).

## webapi_download.py

A separate script (`webapi_download.py`) downloads positions from Webull via the `webull-trade-sdk` third-party package (not stdlib). It writes JSON files to `sample-data/` named `webull_<account_id>_<date>_positions.json` and `webull_<account_id>_<date>_balance.json`.

**Caution:** The script has hardcoded API credentials (`ApiClient(...)`) and hardcoded account index assumptions (`my_json[0]`, `my_json[1]`). It is not a general-purpose tool — update credentials and account iteration before running in a new environment.

Webull positions JSON format:
- Positions file: a JSON array of position objects.
- Each object has: `symbol`, `instrument_type` (`OPTION`/`EQUITY`), `quantity` (string, negative = short), `last_price`, `market_value`, `cost_price`.
- `option_strategy` may be `COVERED_STOCK`: emitted as **two rows** (equity leg + option leg). Legs are in a `legs[]` array on the position object. Both are computed from the top-level `quantity` (number of contracts):
  - Equity leg: `quantity = top_qty * 100`, `market_value = equity_leg.last_price * top_qty * 100`, `asset_type = "Equity"`
  - Option leg: `quantity = -top_qty`, `market_value = -(option_leg.last_price * top_qty * 100)`, `asset_type = "Option"`. Description from `option_type`, `option_expire_date`, `option_exercise_price` leg fields.
- Balance file: a single JSON object; cash comes from `total_cash_balance`.
- One account may have an empty positions array (`[]`) with balance only.

## Sample data

`sample-data/` contains files for all six brokers: `fidelity`, `robinhood`, `schwab`, `public`, `tastytrade`, and `webull` (two files per webull account: `_positions.json` and `_balance.json`), plus one `manual_assets_*.csv` for non-broker assets.

The canonical expected output for all sources is `positions.csv` in the repo root:

```bash
python3 translate_positions.py sample-data/fidelity_*.csv sample-data/manual_*.csv sample-data/robinhood_*.html sample-data/schwab_*.csv sample-data/public_*.json sample-data/tastytrade_*.csv sample-data/webull_*.json > /tmp/positions_check.csv
diff positions.csv /tmp/positions_check.csv  # empty = correct
```
