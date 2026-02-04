"""
Fetch BTCUSD historical data from Yahoo Finance.

Usage:
    python fetch_btc_data.py

Outputs: data/BTCUSD_15m.csv
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import json


def fetch_binance_klines(symbol: str = "BTCUSDT", interval: str = "15m", days: int = 180) -> list:
    """
    Fetch historical klines from Binance public API.
    No API key required for public endpoints.
    
    Returns list of [timestamp, open, high, low, close, volume, ...]
    """
    base_url = "https://api.binance.com/api/v3/klines"
    all_data = []
    
    # Binance returns max 1000 candles per request
    # 15m = 96 candles/day, so ~10 days per request
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    
    current_start = start_time
    
    print(f"Fetching {days} days of {interval} data for {symbol}...")
    
    while current_start < end_time:
        url = f"{base_url}?symbol={symbol}&interval={interval}&startTime={current_start}&limit=1000"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())
                
                if not data:
                    break
                    
                all_data.extend(data)
                
                # Move to next batch
                last_timestamp = data[-1][0]
                current_start = last_timestamp + 1
                
                print(f"  Fetched {len(all_data)} candles...")
                
        except Exception as e:
            print(f"Error fetching data: {e}")
            break
    
    return all_data


def save_to_csv(data: list, filepath: str):
    """Save kline data to CSV format expected by data_loader."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['datetime', 'open', 'high', 'low', 'close', 'volume'])
        
        for candle in data:
            # Binance kline format: [open_time, open, high, low, close, volume, close_time, ...]
            timestamp = datetime.fromtimestamp(candle[0] / 1000)
            dt_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            writer.writerow([
                dt_str,
                candle[1],  # open
                candle[2],  # high
                candle[3],  # low
                candle[4],  # close
                candle[5]   # volume
            ])
    
    print(f"Saved {len(data)} candles to {filepath}")


def main():
    # Fetch 6 months of 15-minute BTCUSD data
    data = fetch_binance_klines(symbol="BTCUSDT", interval="15m", days=180)
    
    if data:
        # Save to data directory
        output_path = Path(__file__).parent.parent.parent / "data" / "BTCUSD_15m.csv"
        save_to_csv(data, str(output_path))
        
        # Print summary
        first_dt = datetime.fromtimestamp(data[0][0] / 1000)
        last_dt = datetime.fromtimestamp(data[-1][0] / 1000)
        print(f"\nData range: {first_dt} to {last_dt}")
        print(f"Total candles: {len(data)}")
    else:
        print("No data fetched!")


if __name__ == "__main__":
    main()
