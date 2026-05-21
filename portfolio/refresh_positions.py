"""
Rebuild positions.csv from the latest snapshot files in sample-data/.

For brokers with download scripts (webull, and later tastytrade/schwab), multiple
dated snapshots may exist in sample-data/. This script selects only the newest file
per account before passing the full file list to translate_positions.py.

For brokers without download scripts (fidelity, manual, robinhood, schwab, public),
all matching files are included as-is — there is typically only one per broker.

Usage:
    python3 refresh_positions.py
"""

import glob
import os
import subprocess
import sys


# ---------------------------------------------------------------------------
# File selection helpers
# ---------------------------------------------------------------------------

def _all(pattern: str) -> list[str]:
    """Return all files matching a glob pattern, sorted for determinism."""
    return sorted(glob.glob(pattern))


def _latest_per_account(pattern: str, account_segment: int, date_segment: int) -> list[str]:
    """
    From files matching pattern, return only the newest file per account.

    Account and date are identified by their position in the underscore-split
    filename (zero-indexed, excluding the extension). Date segments must be
    lexicographically sortable (YYYY-MM-DD or YYMMDD both work).

    Example — webull_<account>_<YYYY-MM-DD>_positions.json:
        account_segment=1, date_segment=2
    Example — tastytrade_positions_<account>_<YYMMDD>.csv:
        account_segment=2, date_segment=3
    """
    by_account: dict[str, str] = {}
    for path in glob.glob(pattern):
        stem = os.path.basename(path).rsplit(".", 1)[0]
        parts = stem.split("_")
        try:
            account = parts[account_segment]
            date    = parts[date_segment]
        except IndexError:
            continue
        prev = by_account.get(account)
        if prev is None or date > prev.rsplit(".", 1)[0].split("_")[date_segment]:
            by_account[account] = path
    return sorted(by_account.values())


# ---------------------------------------------------------------------------
# File list
# ---------------------------------------------------------------------------

def collect_files() -> list[str]:
    files: list[str] = []

    # Brokers with a single file (no date-selection needed)
    files += _all("sample-data/fidelity_*.csv")
    files += _all("sample-data/manual_*.csv")
    files += _all("sample-data/robinhood_*.html")
    files += _all("sample-data/schwab_*.csv")
    files += _all("sample-data/public_*.json")

    # Tastytrade: tastytrade_<type>_<account>_<YYMMDD>.csv  (account=2, date=3)
    files += _latest_per_account("sample-data/tastytrade_positions_*.csv", account_segment=2, date_segment=3)
    files += _latest_per_account("sample-data/tastytrade_balance_*.csv",   account_segment=2, date_segment=3)

    # Webull: webull_<account>_<YYYY-MM-DD>_<type>.json  (account=1, date=2)
    files += _latest_per_account("sample-data/webull_*_positions.json", account_segment=1, date_segment=2)
    files += _latest_per_account("sample-data/webull_*_balance.json",   account_segment=1, date_segment=2)

    return files


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    files = collect_files()
    if not files:
        print("No input files found in sample-data/.", file=sys.stderr)
        sys.exit(1)

    print("Input files:")
    for f in files:
        print(f"  {f}")

    output_path = "positions.csv"
    with open(output_path, "w") as out:
        subprocess.run(
            [sys.executable, "translate_positions.py"] + files,
            stdout=out,
            check=True,
        )

    print(f"Written to {output_path}.")


if __name__ == "__main__":
    main()
