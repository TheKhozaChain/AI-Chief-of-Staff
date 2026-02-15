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


def fetch_klines(
    symbol: str = "BTCUSDT",
    interval: str = "15m",
    days: int = 1095,
) -> list:
    """Fetch historical klines with Binance → CryptoCompare fallback.

    GitHub Actions runs in the US where Binance is geoblocked (HTTP 451).
    Falls back to CryptoCompare automatically.

    Args:
        symbol: Trading pair (default BTCUSDT).
        interval: Candle interval — 15m, 1h, 4h, 1d, etc.
        days: How many days of history to fetch.

    Returns:
        List of raw kline arrays [ts_ms, open, high, low, close, volume].
    """
    try:
        return _fetch_binance_klines(symbol, interval, days)
    except RuntimeError as e:
        print(f"  Binance failed ({e}). Falling back to CryptoCompare...")
        return _fetch_cryptocompare_klines(interval, days)


# Keep old name as alias for backwards compatibility
fetch_binance_klines = fetch_klines


def _fetch_binance_klines(symbol, interval, days):
    """Fetch from Binance. Raises RuntimeError on geoblock."""
    base_url = "https://api.binance.com/api/v3/klines"
    all_data = []

    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    current_start = start_time

    print(f"Fetching {days} days ({days/365:.1f}y) of {interval} data for {symbol}...")

    request_count = 0
    consecutive_errors = 0
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
                consecutive_errors = 0

                if request_count % 10 == 0:
                    print(f"  {len(all_data):,} candles fetched...")

                if request_count % 50 == 0:
                    time.sleep(1)

        except Exception as e:
            error_str = str(e)
            if "451" in error_str or "403" in error_str:
                raise RuntimeError(f"Binance geoblock: {e}")
            consecutive_errors += 1
            print(f"Error at request {request_count}: {e}")
            if consecutive_errors >= 5:
                raise RuntimeError(f"Binance failed after {consecutive_errors} errors: {e}")
            print("  Retrying in 5 seconds...")
            time.sleep(5)
            continue

    print(f"  Done: {len(all_data):,} candles in {request_count} requests")
    return all_data


def _fetch_cryptocompare_klines(interval, days):
    """Fetch from CryptoCompare. Works globally (no geoblock)."""
    # Map intervals to CryptoCompare endpoints
    interval_map = {
        "15m": ("histominute", 15),
        "1h": ("histohour", 1),
        "4h": ("histohour", 4),
        "1d": ("histoday", 1),
    }

    if interval not in interval_map:
        raise RuntimeError(f"CryptoCompare doesn't support interval '{interval}'. "
                          f"Supported: {list(interval_map.keys())}")

    endpoint, multiplier = interval_map[interval]
    all_data = []
    to_ts = int(datetime.now().timestamp())

    if endpoint == "histominute" and multiplier > 1:
        # For sub-hour intervals, fetch minute data and resample
        total_candles = days * 24 * (60 // multiplier)
        fetch_endpoint = "histominute"
    elif endpoint == "histohour" and multiplier > 1:
        # For multi-hour intervals, fetch hourly and resample later
        total_candles = days * 24
        fetch_endpoint = "histohour"
    else:
        total_candles = days * 24 if endpoint == "histohour" else days
        if endpoint == "histominute":
            total_candles = days * 24 * (60 // multiplier)
        fetch_endpoint = endpoint

    remaining = total_candles
    request_count = 0

    print(f"  [CryptoCompare] Fetching {days} days of {interval} BTCUSD...")

    while remaining > 0:
        limit = min(remaining, 2000)
        req_url = (
            f"https://min-api.cryptocompare.com/data/v2/{fetch_endpoint}"
            f"?fsym=BTC&tsym=USD&limit={limit}&toTs={to_ts}"
        )
        try:
            req = urllib.request.Request(req_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                candles = data.get("Data", {}).get("Data", [])
                if not candles:
                    break
                for c in candles:
                    ts_ms = c["time"] * 1000
                    all_data.append([
                        ts_ms,
                        str(c["open"]),
                        str(c["high"]),
                        str(c["low"]),
                        str(c["close"]),
                        str(c.get("volumefrom", 0)),
                    ])
                to_ts = candles[0]["time"] - 1
                remaining -= len(candles)
                request_count += 1
                if request_count % 5 == 0:
                    print(f"    {len(all_data):,} candles ({request_count} reqs)...")
                time.sleep(0.3)
        except Exception as e:
            raise RuntimeError(f"CryptoCompare failed: {e}")

    # Deduplicate and sort
    seen = set()
    deduped = []
    for candle in all_data:
        ts = candle[0]
        if ts not in seen:
            seen.add(ts)
            deduped.append(candle)
    deduped.sort(key=lambda c: c[0])

    print(f"  [CryptoCompare] Done: {len(deduped):,} candles in {request_count} requests")
    return deduped


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
    data = fetch_klines(symbol="BTCUSDT", interval=interval, days=days)

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
