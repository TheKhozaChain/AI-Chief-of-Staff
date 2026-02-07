"""
Fetch BTCUSD historical OHLCV data from Binance public API.

Downloads candlestick data at specified intervals and durations.
No API key required — uses Binance public market data endpoints.

Usage:
    python fetch_btc_data.py                  # Fetch all standard datasets
    python fetch_btc_data.py --interval 1h --days 1095
    python fetch_btc_data.py --list           # Show what exists

Outputs to: data/BTCUSD_{interval}.csv
"""

import csv
import time
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import json
import sys


# ---------------------------------------------------------------------------
# Standard datasets to fetch — edit this to change what gets downloaded
# ---------------------------------------------------------------------------
STANDARD_DATASETS = [
    {"interval": "15m", "days": 1095, "desc": "3 years of 15m bars"},
    {"interval": "1h",  "days": 1095, "desc": "3 years of 1h bars"},
]


def fetch_binance_klines(
    symbol: str = "BTCUSDT",
    interval: str = "15m",
    days: int = 1095,
) -> list:
    """Fetch historical klines from Binance public API.

    Paginates automatically (1000 candles per request).
    Respects rate limits with a small sleep between requests.

    Args:
        symbol: Binance trading pair (default BTCUSDT).
        interval: Candle interval — 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 1w.
        days: How many days of history to fetch.

    Returns:
        List of raw kline arrays from Binance.
    """
    base_url = "https://api.binance.com/api/v3/klines"
    all_data = []

    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    current_start = start_time

    print(f"Fetching {days} days ({days/365:.1f}y) of {interval} data for {symbol}...")

    request_count = 0
    while current_start < end_time:
        url = (
            f"{base_url}?symbol={symbol}&interval={interval}"
            f"&startTime={current_start}&limit=1000"
        )

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())

                if not data:
                    break

                all_data.extend(data)
                last_timestamp = data[-1][0]
                current_start = last_timestamp + 1
                request_count += 1

                if request_count % 10 == 0:
                    print(f"  {len(all_data):,} candles fetched...")

                # Small delay to be respectful of rate limits
                if request_count % 50 == 0:
                    time.sleep(1)

        except Exception as e:
            print(f"Error at request {request_count}: {e}")
            print("  Retrying in 5 seconds...")
            time.sleep(5)
            continue

    print(f"  Done: {len(all_data):,} candles in {request_count} requests")
    return all_data


def save_to_csv(data: list, filepath: str):
    """Save kline data to CSV format expected by data_loader.

    Columns: datetime, open, high, low, close, volume
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["datetime", "open", "high", "low", "close", "volume"])

        for candle in data:
            timestamp = datetime.fromtimestamp(candle[0] / 1000)
            dt_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([
                dt_str,
                candle[1],  # open
                candle[2],  # high
                candle[3],  # low
                candle[4],  # close
                candle[5],  # volume
            ])

    print(f"Saved {len(data):,} candles to {filepath}")


def get_output_path(interval: str) -> Path:
    """Standard output path for a given interval."""
    return Path(__file__).parent.parent.parent / "data" / f"BTCUSD_{interval}.csv"


def fetch_and_save(interval: str, days: int):
    """Fetch data and save to standard location."""
    data = fetch_binance_klines(symbol="BTCUSDT", interval=interval, days=days)

    if not data:
        print(f"No data fetched for {interval}!")
        return None

    output_path = get_output_path(interval)
    save_to_csv(data, str(output_path))

    first_dt = datetime.fromtimestamp(data[0][0] / 1000)
    last_dt = datetime.fromtimestamp(data[-1][0] / 1000)
    print(f"  Range: {first_dt.date()} to {last_dt.date()}")
    print(f"  Candles: {len(data):,}")
    print()

    return output_path


def list_existing():
    """Show what data files already exist."""
    data_dir = Path(__file__).parent.parent.parent / "data"
    csv_files = sorted(data_dir.glob("BTCUSD_*.csv"))

    if not csv_files:
        print("No BTCUSD data files found.")
        return

    print("Existing data files:")
    for f in csv_files:
        size_mb = f.stat().st_size / (1024 * 1024)
        # Count lines (subtract header)
        with open(f) as fh:
            lines = sum(1 for _ in fh) - 1
        print(f"  {f.name}: {lines:,} candles, {size_mb:.1f} MB")


def main():
    """Fetch all standard datasets."""
    if "--list" in sys.argv:
        list_existing()
        return

    if "--interval" in sys.argv:
        # Custom fetch: --interval 1h --days 1095
        idx = sys.argv.index("--interval")
        interval = sys.argv[idx + 1]
        days = 1095
        if "--days" in sys.argv:
            days_idx = sys.argv.index("--days")
            days = int(sys.argv[days_idx + 1])
        fetch_and_save(interval, days)
        return

    # Default: fetch all standard datasets
    print("=" * 60)
    print("BTCUSD Data Fetch — Standard Datasets")
    print("=" * 60)
    print()

    for ds in STANDARD_DATASETS:
        print(f"--- {ds['desc']} ---")
        fetch_and_save(ds["interval"], ds["days"])

    print("=" * 60)
    list_existing()


if __name__ == "__main__":
    main()
