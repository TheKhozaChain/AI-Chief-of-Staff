"""
Data loader for backtesting.

Supports CSV files and can be extended for API sources.
Keeps things simple - no heavy dependencies.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


def load_csv(
    filepath: str,
    date_col: str = "datetime",
    date_format: str = "%Y-%m-%d %H:%M:%S"
) -> List[Dict]:
    """
    Load OHLCV data from CSV file.
    
    Expected columns: datetime, open, high, low, close, volume (optional)
    
    Returns list of dicts with parsed data.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    data = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bar = {
                'datetime': datetime.strptime(row[date_col], date_format),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row.get('volume', 0))
            }
            data.append(bar)
    
    # Sort by datetime
    data.sort(key=lambda x: x['datetime'])
    return data


def filter_by_date(
    data: List[Dict],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None
) -> List[Dict]:
    """Filter data to date range."""
    filtered = data
    if start:
        filtered = [d for d in filtered if d['datetime'] >= start]
    if end:
        filtered = [d for d in filtered if d['datetime'] <= end]
    return filtered


def resample_to_4h(data: List[Dict]) -> List[Dict]:
    """
    Resample 15-minute data to 4-hour OHLCV bars.

    Aligns to standard 4H boundaries: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC.
    Each 4H bar aggregates up to 16 × 15m bars.

    Returns sorted list of 4H bar dicts.
    """
    if not data:
        return []

    buckets: Dict = {}
    for bar in data:
        dt = bar['datetime']
        # Align to 4H boundary: floor hour to nearest multiple of 4
        aligned_hour = (dt.hour // 4) * 4
        bucket_key = dt.replace(hour=aligned_hour, minute=0, second=0, microsecond=0)

        if bucket_key not in buckets:
            buckets[bucket_key] = {
                'datetime': bucket_key,
                'open': bar['open'],
                'high': bar['high'],
                'low': bar['low'],
                'close': bar['close'],
                'volume': bar['volume'],
            }
        else:
            buckets[bucket_key]['high'] = max(buckets[bucket_key]['high'], bar['high'])
            buckets[bucket_key]['low'] = min(buckets[bucket_key]['low'], bar['low'])
            buckets[bucket_key]['close'] = bar['close']
            buckets[bucket_key]['volume'] += bar['volume']

    return sorted(buckets.values(), key=lambda x: x['datetime'])


def resample_to_daily(data: List[Dict]) -> List[Dict]:
    """
    Resample intraday data to daily OHLC.
    Useful for higher-timeframe analysis.
    """
    if not data:
        return []
    
    daily = {}
    for bar in data:
        date_key = bar['datetime'].date()
        if date_key not in daily:
            daily[date_key] = {
                'datetime': datetime.combine(date_key, datetime.min.time()),
                'open': bar['open'],
                'high': bar['high'],
                'low': bar['low'],
                'close': bar['close'],
                'volume': bar['volume']
            }
        else:
            daily[date_key]['high'] = max(daily[date_key]['high'], bar['high'])
            daily[date_key]['low'] = min(daily[date_key]['low'], bar['low'])
            daily[date_key]['close'] = bar['close']
            daily[date_key]['volume'] += bar['volume']
    
    return sorted(daily.values(), key=lambda x: x['datetime'])


if __name__ == "__main__":
    print("Data loader ready.")
    print("Usage: load_csv('path/to/data.csv')")
    print("Expected columns: datetime, open, high, low, close, volume")
