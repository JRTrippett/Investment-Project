"""
capture_prices.py
-----------------
Pulls the 3:55 PM ET 1-minute bar for each ticker and appends it to
data/prices_3pm55.csv.

Runs inside GitHub Actions (see .github/workflows/price_capture.yml).
Can also be run locally for testing — will report "no 15:55 bar" if
the market isn't open right now, which is the correct behavior.
"""

import os
import sys
from datetime import date, datetime
import pandas as pd
import pytz
import yfinance as yf

# ── Tickers — must match TICKERS list in the notebook ─────────────────────────
TICKERS = [
    # Technology
    "AAPL", "MSFT", "NVDA", "GOOGL", "META", "ORCL",
    # Healthcare
    "JNJ",  "UNH",  "ABBV", "PFE",  "MRK",  "LLY",
    # Financials
    "JPM",  "BAC",  "GS",   "MS",   "WFC",  "BLK",
    # Energy
    "XOM",  "CVX",  "COP",  "SLB",  "EOG",  "PSX",
    # Consumer Staples
    "PG",   "KO",   "PEP",  "WMT",  "COST", "CL",
]

CSV_PATH  = "data/prices_3pm55.csv"
MARKET_TZ = pytz.timezone("US/Eastern")
TARGET_H  = 15
TARGET_M  = 55


def is_market_holiday():
    """
    Lightweight holiday check — skips obvious US market holidays.
    yfinance will return empty data anyway, but this gives a cleaner log message.
    NYSE holidays 2025-2026 (add years as needed).
    """
    holidays = {
        # 2025
        "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18",
        "2025-05-26", "2025-06-19", "2025-07-04", "2025-09-01",
        "2025-11-27", "2025-12-25",
        # 2026
        "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
        "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07",
        "2026-11-26", "2026-12-25",
    }
    return date.today().isoformat() in holidays


def main():
    today_str = date.today().isoformat()
    now_utc   = datetime.utcnow()
    print(f"=== Price Capture | {today_str} | {now_utc.strftime('%H:%M UTC')} ===")
    print(f"    Tickers: {len(TICKERS)}")

    # ── Skip weekends ──────────────────────────────────────────────────────────
    if date.today().weekday() >= 5:
        print("Weekend — skipping.")
        sys.exit(0)

    # ── Skip holidays ──────────────────────────────────────────────────────────
    if is_market_holiday():
        print(f"Market holiday ({today_str}) — skipping.")
        sys.exit(0)

    # ── Skip if today already captured ────────────────────────────────────────
    if os.path.exists(CSV_PATH):
        existing = pd.read_csv(CSV_PATH, index_col=0)
        if today_str in existing.index:
            print(f"Already captured for {today_str} — nothing to do.")
            sys.exit(0)

    # ── Pull 1-minute data ────────────────────────────────────────────────────
    print(f"Downloading 1-min bars for {len(TICKERS)} tickers...")
    raw = yf.download(
        TICKERS,
        period="2d",        # last 2 days guarantees today is included
        interval="1m",
        auto_adjust=True,
        progress=False,
        group_by="ticker",
    )

    # Flatten MultiIndex to Close-only DataFrame
    try:
        close = raw.xs("Close", axis=1, level=1)
    except KeyError:
        close = raw["Close"]

    # Check for missing tickers
    missing = [t for t in TICKERS if t not in close.columns]
    if missing:
        print(f"WARNING: Missing tickers in download: {missing}")

    # ── Localize index to ET ───────────────────────────────────────────────────
    if close.index.tz is None:
        close.index = close.index.tz_localize("UTC")
    close.index = close.index.tz_convert(MARKET_TZ)

    # ── Filter for 15:55 bar, today only ──────────────────────────────────────
    mask = (
        (close.index.date  == date.today()) &
        (close.index.hour  == TARGET_H)     &
        (close.index.minute == TARGET_M)
    )

    if mask.sum() == 0:
        print(
            f"No {TARGET_H}:{TARGET_M:02d} ET bar found for {today_str}. "
            "Market may be closed or data is delayed. No row written."
        )
        sys.exit(0)

    bar = close[mask].iloc[-1]  # last match in case of rare duplicate timestamps

    # ── Build output row ───────────────────────────────────────────────────────
    available = [t for t in TICKERS if t in bar.index]
    row = pd.DataFrame(
        [bar[available].values],
        index=[today_str],
        columns=available,
    )

    # ── Append to CSV ──────────────────────────────────────────────────────────
    os.makedirs("data", exist_ok=True)
    if os.path.exists(CSV_PATH):
        row.to_csv(CSV_PATH, mode="a", header=False)
    else:
        row.to_csv(CSV_PATH)

    print(f"Appended row for {today_str}:")
    for t in available:
        print(f"  {t:6s}  ${bar[t]:.2f}")
    print(f"Done. {len(available)}/{len(TICKERS)} tickers captured.")


if __name__ == "__main__":
    main()
