"""
Data loader and resampling for backtesting.

Supports CSV files and arbitrary timeframe resampling.
No external dependencies — stdlib only.

Resampling:
    resample(data, hours=4)  → 4H bars
    resample(data, hours=1)  → 1H bars (passthrough if already 1H)
    resample(data, hours=24) → daily bars
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


def load_csv(
    filepath: str,
    date_col: str = "datetime",
    date_format: str = "%Y-%m-%d %H:%M:%S",
) -> List[Dict]:
    """Load OHLCV data from CSV file.

    Expected columns: datetime, open, high, low, close, volume (optional)

    Args:
        filepath: Path to CSV file.
        date_col: Name of the datetime column.
        date_format: strptime format string for parsing dates.

    Returns:
        Sorted list of bar dicts with keys: datetime, open, high, low, close, volume.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    data = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bar = {
                "datetime": datetime.strptime(row[date_col], date_format),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row.get("volume", 0)),
            }
            data.append(bar)

    data.sort(key=lambda x: x["datetime"])
    return data


def filter_by_date(
    data: List[Dict],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[Dict]:
    """Filter data to a date range (inclusive)."""
    filtered = data
    if start:
        filtered = [d for d in filtered if d["datetime"] >= start]
    if end:
        filtered = [d for d in filtered if d["datetime"] <= end]
    return filtered


# ---------------------------------------------------------------------------
# Generic resampling
# ---------------------------------------------------------------------------

def resample(data: List[Dict], hours: int) -> List[Dict]:
    """Resample OHLCV data to a higher timeframe.

    Aligns bars to clean boundaries (e.g., 4H aligns to 00:00, 04:00, 08:00...).
    Aggregates: open=first, high=max, low=min, close=last, volume=sum.

    Args:
        data: List of OHLCV bar dicts (must be sorted by datetime).
        hours: Target bar size in hours. Must be >= 1.
              Common values: 1, 2, 3, 4, 6, 8, 12, 24.

    Returns:
        Sorted list of resampled bar dicts.

    Example:
        data_4h = resample(data_15m, hours=4)
        data_1h = resample(data_15m, hours=1)
        data_daily = resample(data_15m, hours=24)
    """
    if hours < 1:
        raise ValueError(f"Resample hours must be >= 1, got {hours}")
    if not data:
        return []

    buckets: Dict = {}
    for bar in data:
        dt = bar["datetime"]

        if hours >= 24:
            # Daily or longer: align to midnight
            bucket_key = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Sub-daily: align to nearest multiple of hours
            aligned_hour = (dt.hour // hours) * hours
            bucket_key = dt.replace(hour=aligned_hour, minute=0, second=0, microsecond=0)

        if bucket_key not in buckets:
            buckets[bucket_key] = {
                "datetime": bucket_key,
                "open": bar["open"],
                "high": bar["high"],
                "low": bar["low"],
                "close": bar["close"],
                "volume": bar["volume"],
            }
        else:
            buckets[bucket_key]["high"] = max(buckets[bucket_key]["high"], bar["high"])
            buckets[bucket_key]["low"] = min(buckets[bucket_key]["low"], bar["low"])
            buckets[bucket_key]["close"] = bar["close"]
            buckets[bucket_key]["volume"] += bar["volume"]

    return sorted(buckets.values(), key=lambda x: x["datetime"])


# ---------------------------------------------------------------------------
# Convenience wrappers (for readability in strategy code)
# ---------------------------------------------------------------------------

def resample_to_1h(data: List[Dict]) -> List[Dict]:
    """Resample to 1-hour bars."""
    return resample(data, hours=1)


def resample_to_2h(data: List[Dict]) -> List[Dict]:
    """Resample to 2-hour bars."""
    return resample(data, hours=2)


def resample_to_3h(data: List[Dict]) -> List[Dict]:
    """Resample to 3-hour bars."""
    return resample(data, hours=3)


def resample_to_4h(data: List[Dict]) -> List[Dict]:
    """Resample to 4-hour bars."""
    return resample(data, hours=4)


def resample_to_daily(data: List[Dict]) -> List[Dict]:
    """Resample to daily bars."""
    return resample(data, hours=24)


if __name__ == "__main__":
    print("Data loader ready.")
    print()
    print("Load:     load_csv('path/to/data.csv')")
    print("Resample: resample(data, hours=4)  # any integer >= 1")
    print("Filter:   filter_by_date(data, start=datetime(2025, 1, 1))")
    print()
    print("Expected CSV columns: datetime, open, high, low, close, volume")
