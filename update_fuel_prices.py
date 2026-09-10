#!/usr/bin/env python3
"""
update_fuel_prices.py
----------------------
Refreshes the RON95/RON97/Diesel rows on the "Fuels" sheet of
Malaysia_Highway_Cost_Estimator_v3_EV_fixed.xlsx with the current week's
official price, pulled from data.gov.my (Ministry of Finance open data,
CC BY 4.0). Everything else in the workbook — formulas, other sheets,
formatting — is left untouched.

This is the actual "automation" for this workbook: Excel's own Power Query
feature can also pull this data (see README_fuel_price_automation.md for
that route), but Power Query only refreshes while the file is open in
Excel. This script can be run any time from a terminal, or handed to
Windows Task Scheduler / cron / macOS launchd to run completely unattended
on a schedule (e.g. every Wednesday evening, when MOF announces the new
week's prices) -- no Excel needed to perform the update itself.

Requirements:
    pip install openpyxl

Usage:
    python update_fuel_prices.py
    python update_fuel_prices.py --file "path\\to\\your.xlsx"

Exit code is non-zero if the update could not be completed (no internet,
API unreachable, or unexpected response shape) so a scheduler can flag a
failed run -- the workbook is left untouched in that case.
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import date, timedelta

try:
    import openpyxl
except ImportError:
    sys.exit("Missing dependency. Install it first with:  pip install openpyxl")

API_URL = (
    "https://api.data.gov.my/data-catalogue"
    "?id=fuelprice&date_start={since}@date&limit=60"
)
DATAGOVMY_SOURCE = "https://data.gov.my/data-catalogue/fuelprice"
DEFAULT_FILE = "Malaysia_Highway_Cost_Estimator_v3_EV_fixed.xlsx"


def fetch_latest_prices():
    """Return the most recent {date, ron95, ron97, diesel} row from data.gov.my."""
    since = (date.today() - timedelta(days=60)).isoformat()
    url = API_URL.format(since=since)

    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            rows = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as e:
        raise RuntimeError(f"Could not reach data.gov.my: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Unexpected response from data.gov.my: {e}") from e

    if not rows:
        raise RuntimeError("data.gov.my returned no rows for the last 60 days.")

    # The dataset mixes real price "level" rows with week-on-week "change" rows (small
    # +/- deltas) under the same field names -- only "level" rows are actual prices.
    # Grabbing a "change" row by mistake is what previously showed up as a negative price.
    rows = [r for r in rows if r.get("series_type") in ("level", None)]
    if not rows:
        raise RuntimeError("No level-series (actual price) rows found in the last 60 days.")

    # Don't trust server-side ordering -- sort client-side and take the newest.
    rows.sort(key=lambda r: r["date"])
    latest = rows[-1]

    ron95 = latest.get("ron95_budi95") or latest.get("ron95")
    ron95_market = latest.get("ron95")
    ron97 = latest.get("ron97")
    diesel = latest.get("diesel")

    def is_sane(v):
        return isinstance(v, (int, float)) and 0.5 < v < 10  # plausible RM/L range

    if not all(is_sane(v) for v in (ron95, ron95_market, ron97, diesel)):
        raise RuntimeError(f"Latest row failed the sanity check (looked like a delta, not a price): {latest}")

    return latest["date"], ron95, ron95_market, ron97, diesel


def update_workbook(path, price_date, ron95, ron95_market, ron97, diesel):
    wb = openpyxl.load_workbook(path)
    ws = wb["Fuels"]

    # Row 2 = RON95 (Subsidised/BUDI95), row 3 = RON97, row 4 = Diesel (Peninsular).
    # Column B = what you pay, Column F = unsubsidised market value (for the subsidy figure).
    # This matches the sheet's existing layout -- change these coordinates if you ever
    # reorder the table or its columns.
    ws["B2"], ws["E2"], ws["F2"] = ron95, price_date, ron95_market
    ws["B3"], ws["E3"], ws["F3"] = ron97, price_date, ron97
    ws["B4"], ws["E4"], ws["F4"] = diesel, price_date, diesel
    for cell in ("D2", "D3", "D4"):
        ws[cell] = DATAGOVMY_SOURCE

    wb.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file", default=DEFAULT_FILE,
        help=f"Path to the workbook (default: {DEFAULT_FILE}, same folder as this script)",
    )
    args = parser.parse_args()

    try:
        price_date, ron95, ron95_market, ron97, diesel = fetch_latest_prices()
        update_workbook(args.file, price_date, ron95, ron95_market, ron97, diesel)
    except RuntimeError as e:
        print(f"UPDATE FAILED: {e}", file=sys.stderr)
        print("The workbook was left unchanged.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"UPDATE FAILED: couldn't find '{args.file}'.", file=sys.stderr)
        print("Pass its path with --file, or run this script from the same folder.", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"UPDATE FAILED: '{args.file}' is open in Excel (or otherwise locked).", file=sys.stderr)
        print("Close the file and run this again.", file=sys.stderr)
        sys.exit(1)

    print(f"Updated {args.file}:")
    print(f"  week of {price_date}")
    print(f"  RON95 (subsidised/BUDI95): RM{ron95:.2f}/L  (market value: RM{ron95_market:.2f}/L, "
          f"subsidy RM{ron95_market - ron95:.2f}/L)")
    print(f"  RON97:                     RM{ron97:.2f}/L")
    print(f"  Diesel (Peninsular):       RM{diesel:.2f}/L")
    print("Note: formulas will show the new totals next time the file is opened in Excel.")


if __name__ == "__main__":
    main()
