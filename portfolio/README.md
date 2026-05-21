# Portfolio Position Translator

Converts broker position export files into a single standard CSV (`positions.csv`).

## Requirements

- Python 3 (stdlib only for core scripts)
- Third-party packages for download scripts: `webull-trade-sdk`, `tastytrade`, `schwab-py`

Install into the virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python3.12 -m pip install webull-trade-sdk tastytrade schwab-py pytest
```

## Setup

Create a `.env` file in the repo root with credentials for each broker you want
to download automatically:

```
# Webull
WEBULL_APP_KEY=
WEBULL_APP_SECRET=
WEBULL_REGION=us

# Tastytrade
TT_SECRET=
TT_REFRESH=

# Schwab
SCHWAB_APP_KEY=
SCHWAB_APP_SECRET=
SCHWAB_CALLBACK_URL=https://127.0.0.1:8182
```

- **Webull:** `WEBULL_APP_KEY` and `WEBULL_APP_SECRET` come from the Webull developer portal.
- **Tastytrade:** `TT_SECRET` is the OAuth client secret from the Tastytrade developer portal. `TT_REFRESH` is a long-lived refresh token — obtain it via the Tastytrade developer portal and set it manually.
- **Schwab:** `SCHWAB_APP_KEY` and `SCHWAB_APP_SECRET` come from the Schwab developer portal. Register `https://127.0.0.1:8182` as the redirect URI in your Schwab app, then run `setup_schwab_auth.py` once to complete the browser login before using `download_schwab.py`.

## Downloading positions

Run the download script for each broker you want to update:

```bash
python3 download_webull.py
python3 download_tastytrade.py
python3 download_schwab.py
```

Each script writes dated snapshot files to `sample-data/`, e.g.:

```
sample-data/webull_<account>_2026-05-21_positions.json
sample-data/tastytrade_positions_<account>_260521.csv
```

For brokers without a download script (Fidelity, Robinhood, Public),
export the file manually from the broker's website and place it in `sample-data/`.
The filename must start with the broker name followed by an underscore:

| Broker | Format | Export path |
|---|---|---|
| Fidelity | CSV | Portfolio → Positions → Download |
| Robinhood | HTML | Save the Positions page from the web app |
| Public | JSON | Account → Export positions |

## Rebuilding positions.csv

```bash
python3 refresh_positions.py
```

This selects the latest snapshot per account from `sample-data/` and writes
`positions.csv`. Run this after downloading or manually adding any new files.

## Output format

`positions.csv` contains one row per position across all brokers and accounts:

| Column | Description |
|---|---|
| `broker` | Source broker (`fidelity`, `schwab`, `webull`, etc.) |
| `account` | Account number / name |
| `symbol` | Ticker symbol (underlier for options) |
| `description` | Human-readable position name |
| `quantity` | Shares or contracts (negative = short) |
| `last_price` | Last trade price |
| `market_value` | Current market value (negative = short) |
| `asset_type` | `Equity`, `Option`, `Cash`, `Futures`, etc. |
| `option_symbol` | Raw broker option symbol (options only) |
| `option_strike` | Strike price (options only) |
| `option_put_call` | `call` or `put` (options only) |
| `position_date` | Date the snapshot was captured (`YYYY-MM-DD`) |

Numbers contain no `$`, `+`, or `,`. Cash rows have empty `quantity` and `last_price`.

## Translating files directly

`translate_positions.py` can be called directly if you want to translate specific
files without rebuilding `positions.csv`:

```bash
python3 translate_positions.py sample-data/fidelity_*.csv
```

Output is written to stdout.

## Running the tests

```bash
.venv/bin/python3.12 -m pytest tests/
```

Tests use fixed fixtures in `tests/data/` and do not depend on `sample-data/`.
After any change to `translate_positions.py` that legitimately alters the output,
rebuild the canonical file and update the fixtures:

```bash
python3 refresh_positions.py
# then update tests/data/ as needed and re-run the tests
```

## Adding a new broker

1. Add `def parse_<broker>(path: str) -> Iterator[Row]` in `translate_positions.py`.
2. Register it in the `PARSERS` dict at the bottom of the file.
3. Name input files `<broker>_anything.<ext>`.
