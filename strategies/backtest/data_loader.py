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
