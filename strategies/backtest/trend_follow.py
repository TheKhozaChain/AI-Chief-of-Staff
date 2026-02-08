"""
Trend Following (Long Bias) Quick Screen (R006)

Simple trend-following on 4H BTCUSD. Long-only.
Enter long when price is above a rising MA, exit when it crosses below.
Don't fight the structural BTC uptrend.

Usage:
    python trend_follow.py ../../data/BTCUSD_1h.csv
"""

import sys
import statistics
from typing import Dict, List, Optional
from data_loader import load_csv, resample_to_4h
from engine import Backtest


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
MA_PERIOD = 20             # 20-bar MA on 4H (~3.3 days)
TREND_MA_PERIOD = 80       # 80-bar MA on 4H (~13.3 days) for trend filter
STOP_PCT = 4.0             # Stop: 4% below entry (wider to reduce whipsaws)
TAKE_PROFIT_PCT = 12.0     # Target: 12% (3:1 R:R)
COST_PCT = 0.1


class TrendFollowStrategy:
    """Simple trend following, long only.

    Logic:
        - Compute 50-bar and 200-bar MAs on 4H.
        - Long entry: price closes above 50 MA AND 50 MA > 200 MA (golden cross regime).
        - No shorts — ride the BTC structural uptrend.
        - Stop: 3% below entry. Target: 9%.
    """

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        if len(prev_bars) < TREND_MA_PERIOD:
            return None

        closes = [b['close'] for b in prev_bars]
        ma_fast = statistics.mean(closes[-MA_PERIOD:])
        ma_slow = statistics.mean(closes[-TREND_MA_PERIOD:])

        price = bar['close']

        # Long only: price above fast MA, fast MA above slow MA
        if price > ma_fast and ma_fast > ma_slow:
            return {
                'action': 'buy',
                'stop_loss': price * (1 - STOP_PCT / 100),
                'take_profit': price * (1 + TAKE_PROFIT_PCT / 100),
            }

        return None


def run_backtest(data_file: str, cost_pct: float = COST_PCT):
    """Quick screen."""
    print(f"Loading data from {data_file}...")
    raw_data = load_csv(data_file)
    print(f"Loaded {len(raw_data)} bars")

    print("Resampling to 4H...")
    data = resample_to_4h(raw_data)
    print(f"Resampled to {len(data)} 4H bars")
    print(f"Period: {data[0]['datetime']} → {data[-1]['datetime']}")
    print()

    # Gross
    print("=" * 60)
    print("GROSS (0% costs)")
    print("=" * 60)
    bt_gross = Backtest(data, cost_pct=0.0)
    bt_gross.run(TrendFollowStrategy())
    print(bt_gross.result.summary())

    # Net
    print("=" * 60)
    print(f"NET ({cost_pct}% costs)")
    print("=" * 60)
    bt_net = Backtest(data, cost_pct=cost_pct)
    bt_net.run(TrendFollowStrategy())
    print(bt_net.result.summary())

    return bt_gross.result, bt_net.result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python trend_follow.py <data_file.csv>")
        sys.exit(1)
    run_backtest(sys.argv[1])
