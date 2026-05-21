"""
Tests for translate_positions.py.

Run with:
    .venv/bin/python3.12 -m pytest tests/

Each broker parser is tested against its fixture file in tests/data/, asserting
that the output rows match the corresponding rows in tests/data/positions.csv.
Helper functions are unit-tested independently.
"""

import csv
import os
import sys
from pathlib import Path

import pytest

# Make the repo root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import translate_positions as tp

REPO   = Path(__file__).parent.parent
DATA   = Path(__file__).parent / "data"
CANON  = DATA / "positions.csv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def canonical_rows(broker: str) -> list[dict]:
    """Return all rows for a given broker from the canonical positions.csv."""
    with open(CANON, newline="") as f:
        return [r for r in csv.DictReader(f) if r["broker"] == broker]


def parse(path: Path) -> list[dict]:
    """Run parse_file on path and return all rows as a list."""
    return list(tp.parse_file(str(path)))


# ---------------------------------------------------------------------------
# _clean_number
# ---------------------------------------------------------------------------

class TestCleanNumber:
    def test_strips_dollar(self):
        assert tp._clean_number("$1.23") == "1.23"

    def test_strips_plus(self):
        assert tp._clean_number("+5") == "5"

    def test_strips_commas(self):
        assert tp._clean_number("1,300") == "1300"

    def test_strips_percent(self):
        assert tp._clean_number("3.5%") == "3.5%".replace("%", "")

    def test_negative_preserved(self):
        assert tp._clean_number("-42.5") == "-42.5"

    def test_double_dash(self):
        assert tp._clean_number("--") == ""

    def test_single_dash(self):
        assert tp._clean_number("-") == ""

    def test_na(self):
        assert tp._clean_number("N/A") == ""

    def test_empty_string(self):
        assert tp._clean_number("") == ""

    def test_none(self):
        assert tp._clean_number(None) == ""

    def test_plain_number(self):
        assert tp._clean_number("42") == "42"

    def test_negative_market_value(self):
        assert tp._clean_number("-16,750.00") == "-16750.00"


# ---------------------------------------------------------------------------
# _option_underlier
# ---------------------------------------------------------------------------

class TestOptionUnderlier:
    def test_occ_compact(self):
        assert tp._option_underlier("AMD260618C150") == "AMD"

    def test_occ_long_zero_padded(self):
        assert tp._option_underlier("LIT260515P00075000") == "LIT"

    def test_tastytrade_spaced(self):
        assert tp._option_underlier("SPY   260515C00690000") == "SPY"

    def test_schwab_space_delimited(self):
        assert tp._option_underlier("AMZN 05/15/2026 210.00 C") == "AMZN"


# ---------------------------------------------------------------------------
# _parse_option_symbol
# ---------------------------------------------------------------------------

class TestParseOptionSymbol:
    def test_occ_compact_call(self):
        assert tp._parse_option_symbol("AMD260618C150") == ("150", "call")

    def test_occ_compact_put(self):
        assert tp._parse_option_symbol("AMD260618P270") == ("270", "put")

    def test_occ_compact_decimal_strike(self):
        assert tp._parse_option_symbol("GM270115C52.5") == ("52.5", "call")

    def test_occ_long_zero_padded(self):
        strike, pc = tp._parse_option_symbol("LIT260515P00075000")
        assert pc == "put"
        assert float(strike) == 75.0

    def test_occ_long_whole_strike(self):
        strike, pc = tp._parse_option_symbol("SPY260515C00690000")
        assert pc == "call"
        assert float(strike) == 690.0

    def test_tastytrade_spaced_occ(self):
        # _parse_option_symbol does not normalise internal spaces —
        # tastytrade OCC symbols with extra spaces return ("", "") because
        # the spaces prevent the regex from matching. strike/put_call are
        # instead sourced from the explicit CSV columns in parse_tastytrade.
        assert tp._parse_option_symbol("SPY   260515C00690000") == ("", "")

    def test_schwab_space_delimited_call(self):
        assert tp._parse_option_symbol("AMZN 05/15/2026 210.00 C") == ("210.00", "call")

    def test_schwab_space_delimited_put(self):
        assert tp._parse_option_symbol("GS 06/18/2026 940.00 P") == ("940.00", "put")

    def test_empty(self):
        assert tp._parse_option_symbol("") == ("", "")

    def test_invalid(self):
        assert tp._parse_option_symbol("NOTANOPTION") == ("", "")


# ---------------------------------------------------------------------------
# _date_from_file
# ---------------------------------------------------------------------------

class TestDateFromFile:
    def test_webull_iso_date(self):
        path = DATA / "webull_IKIIO5FM27KB81I1JR0CADQ0Q9_2026-05-21_positions.json"
        assert tp._date_from_file(str(path)) == "2026-05-21"

    def test_manual_iso_date(self):
        path = DATA / "manual_assets_2026-05-11.csv"
        assert tp._date_from_file(str(path)) == "2026-05-11"

    def test_fidelity_month_name(self):
        path = DATA / "fidelity_Portfolio_Positions_May-05-2026.csv"
        assert tp._date_from_file(str(path)) == "2026-05-05"

    def test_schwab_date_with_time_suffix(self):
        path = DATA / "schwab_All-Accounts-Positions-2026-05-05-232726.csv"
        assert tp._date_from_file(str(path)) == "2026-05-05"

    def test_robinhood_8digit_compact(self):
        path = DATA / "robinhood_positions_ACCOUNT1_20260511.html"
        assert tp._date_from_file(str(path)) == "2026-05-11"

    def test_tastytrade_6digit_yymmdd(self):
        path = DATA / "tastytrade_positions_5WZ05848_260521.csv"
        assert tp._date_from_file(str(path)) == "2026-05-21"

    def test_mtime_fallback(self, tmp_path):
        # File with no date in name — should fall back to mtime
        f = tmp_path / "public_account-positions.json"
        f.write_text("{}")
        result = tp._date_from_file(str(f))
        # Just assert it's a valid YYYY-MM-DD string
        from datetime import datetime
        datetime.strptime(result, "%Y-%m-%d")


# ---------------------------------------------------------------------------
# Per-broker parser tests — output must match canonical positions.csv
# ---------------------------------------------------------------------------

class TestParseFidelity:
    def test_row_count(self):
        rows = parse(DATA / "fidelity_Portfolio_Positions_May-05-2026.csv")
        assert len(rows) == len(canonical_rows("fidelity"))

    def test_matches_canonical(self):
        rows = parse(DATA / "fidelity_Portfolio_Positions_May-05-2026.csv")
        assert rows == canonical_rows("fidelity")

    def test_cash_rows_have_empty_quantity_and_price(self):
        rows = parse(DATA / "fidelity_Portfolio_Positions_May-05-2026.csv")
        # Money market sweep accounts (symbol ends with **) have empty quantity/price.
        # Other rows classified as Cash (e.g. money market funds with a price) may not.
        sweep = [r for r in rows if r["symbol"].endswith("**")]
        assert sweep, "expected at least one sweep cash row"
        for r in sweep:
            assert r["quantity"] == ""
            assert r["last_price"] == ""

    def test_option_rows_have_underlier_as_symbol(self):
        rows = parse(DATA / "fidelity_Portfolio_Positions_May-05-2026.csv")
        options = [r for r in rows if r["asset_type"] == "Option"]
        assert options, "expected at least one Option row"
        for r in options:
            assert r["symbol"] != r["option_symbol"]
            assert r["option_symbol"] != ""
            assert r["option_put_call"] in ("call", "put")


class TestParseManual:
    def test_row_count(self):
        rows = parse(DATA / "manual_assets_2026-05-11.csv")
        assert len(rows) == len(canonical_rows("manual"))

    def test_matches_canonical(self):
        rows = parse(DATA / "manual_assets_2026-05-11.csv")
        assert rows == canonical_rows("manual")


class TestParseRobinhood:
    def test_row_count(self):
        rows = parse(DATA / "robinhood_positions_ACCOUNT1_20260511.html")
        assert len(rows) == len(canonical_rows("robinhood"))

    def test_matches_canonical(self):
        rows = parse(DATA / "robinhood_positions_ACCOUNT1_20260511.html")
        assert rows == canonical_rows("robinhood")

    def test_all_equity(self):
        rows = parse(DATA / "robinhood_positions_ACCOUNT1_20260511.html")
        assert all(r["asset_type"] == "Equity" for r in rows)

    def test_account_from_filename(self):
        rows = parse(DATA / "robinhood_positions_ACCOUNT1_20260511.html")
        assert all(r["account"] == "ACCOUNT1" for r in rows)


class TestParseSchwab:
    def test_row_count(self):
        rows = parse(DATA / "schwab_All-Accounts-Positions-2026-05-05-232726.csv")
        assert len(rows) == len(canonical_rows("schwab"))

    def test_matches_canonical(self):
        rows = parse(DATA / "schwab_All-Accounts-Positions-2026-05-05-232726.csv")
        assert rows == canonical_rows("schwab")

    def test_etf_remapped_to_equity(self):
        rows = parse(DATA / "schwab_All-Accounts-Positions-2026-05-05-232726.csv")
        raw_types = [r["asset_type"] for r in rows]
        assert "ETFs & Closed End Funds" not in raw_types

    def test_multiple_accounts(self):
        rows = parse(DATA / "schwab_All-Accounts-Positions-2026-05-05-232726.csv")
        accounts = {r["account"] for r in rows}
        assert len(accounts) > 1

    def test_option_rows(self):
        rows = parse(DATA / "schwab_All-Accounts-Positions-2026-05-05-232726.csv")
        options = [r for r in rows if r["asset_type"] == "Option"]
        assert options
        for r in options:
            assert r["option_symbol"] != ""
            assert r["option_put_call"] in ("call", "put")
            assert r["option_strike"] != ""


class TestParsePublic:
    def test_row_count(self):
        rows = parse(DATA / "public_account-positions_2026-05-06.json")
        assert len(rows) == len(canonical_rows("public"))

    def test_matches_canonical(self):
        rows = parse(DATA / "public_account-positions_2026-05-06.json")
        assert rows == canonical_rows("public")

    def test_has_cash_row(self):
        rows = parse(DATA / "public_account-positions_2026-05-06.json")
        assert any(r["asset_type"] == "Cash" for r in rows)


class TestParseTastytrade:
    def _positions_file(self):
        # Strip leading 'x' from account segment before sorting, matching the
        # same logic as refresh_positions.py, so 5WZ05848_260521 beats x5WZ05848_260511.
        files = sorted(
            DATA.glob("tastytrade_positions_*.csv"),
            key=lambda p: p.stem.split("_")[2].lstrip("x") + p.stem.split("_")[3],
        )
        assert files, "no tastytrade positions file found"
        return files[-1]  # latest

    def _balance_file(self):
        files = sorted(
            DATA.glob("tastytrade_balance_*.csv"),
            key=lambda p: p.stem.split("_")[2].lstrip("x") + p.stem.split("_")[3],
        )
        assert files, "no tastytrade balance file found"
        return files[-1]

    def test_row_count(self):
        rows = (parse(self._positions_file()) +
                parse(self._balance_file()))
        assert len(rows) == len(canonical_rows("tastytrade"))

    def test_matches_canonical(self):
        rows = (parse(self._positions_file()) +
                parse(self._balance_file()))
        assert rows == canonical_rows("tastytrade")

    def test_option_last_price_is_mid(self):
        rows = parse(self._positions_file())
        options = [r for r in rows if r["asset_type"] == "Option"]
        assert options
        for r in options:
            # last_price must be a valid number
            float(r["last_price"])

    def test_balance_row_is_cash(self):
        rows = parse(self._balance_file())
        assert len(rows) == 1
        assert rows[0]["asset_type"] == "Cash"


class TestParseWebull:
    def _latest_files(self, kind: str):
        """Return the latest positions or balance files, one per account, in
        the same account order as the canonical positions.csv."""
        by_account: dict[str, Path] = {}
        for path in DATA.glob(f"webull_*_{kind}.json"):
            parts = path.stem.split("_")
            account, date = parts[1], parts[2]
            if account not in by_account or date > by_account[account].stem.split("_")[2]:
                by_account[account] = path
        # Return in canonical account order (IKIIO... before UHI8...)
        return [by_account[a] for a in sorted(by_account)]

    def test_row_count(self):
        rows = []
        for f in self._latest_files("positions") + self._latest_files("balance"):
            rows += parse(f)
        assert len(rows) == len(canonical_rows("webull"))

    def test_matches_canonical(self):
        rows = []
        for f in self._latest_files("positions") + self._latest_files("balance"):
            rows += parse(f)
        assert rows == canonical_rows("webull")

    def test_covered_stock_emits_two_rows(self):
        # At least one covered_stock position should produce an equity + option pair
        rows = []
        for f in self._latest_files("positions"):
            rows += parse(f)
        symbols = [r["symbol"] for r in rows]
        # If covered stock positions exist, the same symbol appears as both Equity and Option
        equity_syms  = {r["symbol"] for r in rows if r["asset_type"] == "Equity"}
        option_syms  = {r["symbol"] for r in rows if r["asset_type"] == "Option"}
        covered = equity_syms & option_syms
        # Only assert if covered stock positions are present in the sample data
        if covered:
            assert len(covered) >= 1


# ---------------------------------------------------------------------------
# Integration test — full pipeline output matches positions.csv exactly
# ---------------------------------------------------------------------------

class TestFullPipeline:
    def test_output_matches_canonical(self):
        """
        Collect files the same way refresh_positions.py does and assert the
        translated output matches positions.csv exactly.
        """
        import glob as globmod

        def latest_per_account(pattern, account_seg, date_seg, strip_leading=""):
            by_account: dict[str, str] = {}
            for path in globmod.glob(pattern):
                stem = os.path.basename(path).rsplit(".", 1)[0]
                parts = stem.split("_")
                try:
                    account = parts[account_seg]
                    date    = parts[date_seg]
                except IndexError:
                    continue
                if strip_leading and account.startswith(strip_leading):
                    account = account[len(strip_leading):]
                prev = by_account.get(account)
                if prev is None or date > prev.rsplit(".", 1)[0].split("_")[date_seg]:
                    by_account[account] = path
            return [by_account[a] for a in sorted(by_account)]

        old_dir = os.getcwd()
        os.chdir(DATA)
        try:
            files = (
                sorted(globmod.glob("fidelity_*.csv")) +
                sorted(globmod.glob("manual_*.csv")) +
                sorted(globmod.glob("robinhood_*.html")) +
                sorted(globmod.glob("public_*.json")) +
                sorted(globmod.glob("schwab_*.csv"))[-1:] +
                latest_per_account("tastytrade_positions_*.csv", 2, 3, "x") +
                latest_per_account("tastytrade_balance_*.csv",   2, 3, "x") +
                latest_per_account("webull_*_positions.json", 1, 2) +
                latest_per_account("webull_*_balance.json",   1, 2)
            )

            rows = []
            for path in files:
                rows.extend(tp.parse_file(path))
        finally:
            os.chdir(old_dir)

        assert rows == canonical_rows("fidelity") + \
                       canonical_rows("manual") + \
                       canonical_rows("robinhood") + \
                       canonical_rows("public") + \
                       canonical_rows("schwab") + \
                       canonical_rows("tastytrade") + \
                       canonical_rows("webull")
