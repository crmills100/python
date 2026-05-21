# Portfolio Position Translator

Converts broker position export files into a single standard CSV format.

## Requirements

Python 3 — no third-party packages needed.

## Usage

```bash
python3 translate_positions.py <file> [<file> ...]
```

Pass one or more broker export files. Output is written to stdout.

**Save to a file:**

```bash
python3 translate_positions.py sample-data/*.csv sample-data/*.json > positions.csv
```

**Single broker:**

```bash
python3 translate_positions.py sample-data/fidelity_Portfolio_Positions_May-05-2026.csv
```

## Output format

The output is a CSV with the following columns:

| Column | Description |
|---|---|
| `broker` | Source broker (`fidelity`, `schwab`, `public`) |
| `account` | Account number / name |
| `symbol` | Ticker symbol |
| `description` | Human-readable position name |
| `quantity` | Number of shares or contracts (negative = short) |
| `last_price` | Last trade price |
| `market_value` | Current market value (negative = short) |
| `asset_type` | `Equity`, `Option`, `ETFs & Closed End Funds`, `Cash`, etc. |

Numbers contain no `$`, `+`, or `,`. Cash rows (money market, sweep accounts) have empty `quantity` and `last_price`.

## Supported brokers

| Broker | File format | How to export |
|---|---|---|
| Fidelity | CSV | Portfolio → Positions → Download |
| Schwab | CSV | Accounts → Positions → Export |
| Public | JSON | Account → Export positions |

File names must start with the broker name followed by an underscore, e.g. `fidelity_export.csv` or `schwab_2026-05-05.csv`.

## Adding a new broker

1. Add a parser function `parse_<broker>(path: str) -> Iterator[Row]` in `translate_positions.py`.
2. Register it in the `PARSERS` dict at the bottom of the file.
3. Name input files `<broker>_anything.<ext>`.
