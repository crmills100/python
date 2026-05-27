"""
Rebuild positions.csv from the latest snapshot files in sample-data/.

For brokers with download scripts (fidelity, webull, tastytrade, schwab), multiple
dated snapshots may exist in sample-data/. This script selects only the newest file
per account before passing the full file list to translate_positions.py.

For brokers without download scripts (manual, robinhood, public),
all matching files are included as-is — there is typically only one per broker.

Usage:
    python3 refresh_positions.py
"""

import csv
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


def _latest_per_account(pattern: str, account_segment: int, date_segment: int,
                        strip_leading: str = "") -> list[str]:
    """
    From files matching pattern, return only the newest file per account.

    Account and date are identified by their position in the underscore-split
    filename (zero-indexed, excluding the extension). Date segments must be
    lexicographically sortable (YYYY-MM-DD or YYMMDD both work).

    strip_leading: if set, strip this prefix from the account segment before
    grouping. Used for tastytrade where old files had a spurious 'x' prefix
    on the account segment that the download script no longer writes.

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
        if strip_leading and account.startswith(strip_leading):
            account = account[len(strip_leading):]
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
    fidelity_files = sorted(glob.glob("sample-data/fidelity_*.csv"))
    if fidelity_files:
        files.append(fidelity_files[-1])
    files += _all("sample-data/manual_*.csv")
    files += _all("sample-data/robinhood_*.html")
    files += _all("sample-data/public_*.json")

    # Schwab: single multi-account file per run; pick the latest by filename sort.
    # Filename: schwab_All-Accounts-Positions-<YYYY-MM-DD>-<HHMMSS>.csv
    schwab_files = sorted(glob.glob("sample-data/schwab_*.csv"))
    if schwab_files:
        files.append(schwab_files[-1])

    # Tastytrade: tastytrade_<type>_<account>_<YYMMDD>.csv  (account=2, date=3)
    # strip_leading="x": old manual exports had a spurious 'x' prefix on the account segment
    files += _latest_per_account("sample-data/tastytrade_positions_*.csv", account_segment=2, date_segment=3, strip_leading="x")
    files += _latest_per_account("sample-data/tastytrade_balance_*.csv",   account_segment=2, date_segment=3, strip_leading="x")

    # Webull: webull_<account>_<YYYY-MM-DD>_<type>.json  (account=1, date=2)
    files += _latest_per_account("sample-data/webull_*_positions.json", account_segment=1, date_segment=2)
    files += _latest_per_account("sample-data/webull_*_balance.json",   account_segment=1, date_segment=2)

    return files


# ---------------------------------------------------------------------------
# Accounts to exclude from the Positions and Summary sheets.
# Rows for these accounts are moved to a separate Excluded sheet in the ODS.
# ---------------------------------------------------------------------------

EXCLUDED_ACCOUNTS = {
    "603728018",  # 529 account — excluded from summary
}


# ---------------------------------------------------------------------------
# ODS export
# ---------------------------------------------------------------------------

def _write_ods(csv_path: str, ods_path: str) -> None:
    """Write an ODS spreadsheet with Positions, Summary, and Excluded sheets."""
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.style import Style, TextProperties
    from odf.table import Table, TableRow, TableCell
    from odf.text import P

    doc = OpenDocumentSpreadsheet()

    header_style = Style(name="HeaderCell", family="table-cell")
    header_style.addElement(TextProperties(fontweight="bold"))
    doc.automaticstyles.addElement(header_style)

    def _header_row(sheet, values):
        tr = TableRow()
        sheet.addElement(tr)
        for v in values:
            tc = TableCell(stylename="HeaderCell")
            tc.addElement(P(text=v))
            tr.addElement(tc)

    def _data_row(sheet, values):
        tr = TableRow()
        sheet.addElement(tr)
        for v in values:
            try:
                num = float(v)
                tc = TableCell(valuetype="float", value=str(num))
                tc.addElement(P(text=v))
            except (ValueError, TypeError):
                tc = TableCell()
                tc.addElement(P(text=v))
            tr.addElement(tc)

    def _is_excluded(row: dict) -> bool:
        account = row.get("account", "")
        return any(excl in account for excl in EXCLUDED_ACCOUNTS)

    # Load all rows and split into included/excluded.
    all_rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_rows.append(row)

    included = [r for r in all_rows if not _is_excluded(r)]
    excluded = [r for r in all_rows if _is_excluded(r)]

    # --- Positions sheet (excluded accounts omitted) ---
    positions_sheet = Table(name="Positions")
    doc.spreadsheet.addElement(positions_sheet)
    if included:
        _header_row(positions_sheet, list(included[0].keys()))
        for row in included:
            _data_row(positions_sheet, list(row.values()))

    # --- Summary sheet: total market_value by (broker, account, position_date) ---
    summary: dict[tuple, float] = {}
    for row in included:
        mv_str = row.get("market_value", "")
        try:
            mv = float(mv_str)
        except (ValueError, TypeError):
            mv = 0.0
        key = (row["broker"], row["account"], row["position_date"])
        summary[key] = summary.get(key, 0.0) + mv

    summary_sheet = Table(name="Summary")
    doc.spreadsheet.addElement(summary_sheet)
    _header_row(summary_sheet, ["broker", "account", "market_value", "position_date"])
    for (broker, account, position_date), total in summary.items():
        _data_row(summary_sheet, [broker, account, f"{total:.2f}", position_date])

    # --- Excluded sheet ---
    excluded_sheet = Table(name="Excluded")
    doc.spreadsheet.addElement(excluded_sheet)
    if excluded:
        _header_row(excluded_sheet, list(excluded[0].keys()))
        for row in excluded:
            _data_row(excluded_sheet, list(row.values()))

    doc.save(ods_path)

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

    ods_path = "positions.ods"
    _write_ods(output_path, ods_path)
    print(f"Written to {ods_path}.")


if __name__ == "__main__":
    main()
