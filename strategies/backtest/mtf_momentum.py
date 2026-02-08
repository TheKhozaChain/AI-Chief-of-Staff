"""
Multi-Timeframe Momentum Quick Screen (R004)

Aligns daily trend direction with 4H entry timing.
Long only when daily MA is rising + 4H pullback to support.
Short only when daily MA is falling + 4H rally to resistance.

This is a quick screen — kill in 30 min or promote to full hypothesis.

Usage:
    python mtf_momentum.py ../../data/BTCUSD_1h.csv
"""

import sys
import statistics
from typing import Dict, List, Optional
from data_loader import load_csv, resample_to_4h, resample_to_daily
from engine import Backtest


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
DAILY_MA_PERIOD = 20       # 20-day MA for trend direction
FOUR_H_MA_FAST = 10       # 10-bar fast MA on 4H (~40 hours)
FOUR_H_MA_SLOW = 30       # 30-bar slow MA on 4H (~120 hours / 5 days)
STOP_PCT = 2.0             # Stop: 2% beyond entry
TAKE_PROFIT_PCT = 6.0      # Target: 6% (3:1 R:R)
COST_PCT = 0.1


class MTFMomentumStrategy:
    """Multi-timeframe momentum: daily trend + 4H entry.

    Logic:
        - Compute 20-day MA direction from daily bars (rising/falling).
        - On 4H bars, use fast/slow MA crossover for timing.
        - Long: daily MA rising AND 4H fast MA crosses above slow MA.
        - Short: daily MA falling AND 4H fast MA crosses below slow MA.
        - Stop 2%, target 6% (3:1 R:R).

    The daily trend acts as a directional filter — only trade with the trend.
    """

    def __init__(self, daily_data: List[Dict]):
        # Pre-compute daily MA for lookup
        self.daily_trend = {}  # date -> 'up' | 'down' | None
        closes = []
        prev_ma = None
        for bar in daily_data:
            closes.append(bar['close'])
            if len(closes) >= DAILY_MA_PERIOD:
                ma = statistics.mean(closes[-DAILY_MA_PERIOD:])
                if prev_ma is not None:
                    if ma > prev_ma:
                        self.daily_trend[bar['datetime'].date()] = 'up'
                    elif ma < prev_ma:
                        self.daily_trend[bar['datetime'].date()] = 'down'
                    else:
                        self.daily_trend[bar['datetime'].date()] = None
                prev_ma = ma

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        if len(prev_bars) < FOUR_H_MA_SLOW + 1:
            return None

        # Get daily trend for this bar's date
        bar_date = bar['datetime'].date()
        trend = self.daily_trend.get(bar_date)
        if trend is None:
            return None

        # Compute 4H fast and slow MAs
        closes = [b['close'] for b in prev_bars]
        fast_ma = statistics.mean(closes[-FOUR_H_MA_FAST:])
        slow_ma = statistics.mean(closes[-FOUR_H_MA_SLOW:])

        # Previous bar's MAs for crossover detection
        prev_closes = closes[:-1]
        if len(prev_closes) < FOUR_H_MA_SLOW:
            return None
        prev_fast = statistics.mean(prev_closes[-FOUR_H_MA_FAST:])
        prev_slow = statistics.mean(prev_closes[-FOUR_H_MA_SLOW:])

        price = bar['close']

        # Long: daily uptrend + 4H fast crosses above slow
        if trend == 'up' and prev_fast <= prev_slow and fast_ma > slow_ma:
            return {
                'action': 'buy',
                'stop_loss': price * (1 - STOP_PCT / 100),
                'take_profit': price * (1 + TAKE_PROFIT_PCT / 100),
            }

        # Short: daily downtrend + 4H fast crosses below slow
        if trend == 'down' and prev_fast >= prev_slow and fast_ma < slow_ma:
            return {
                'action': 'sell',
                'stop_loss': price * (1 + STOP_PCT / 100),
                'take_profit': price * (1 - TAKE_PROFIT_PCT / 100),
            }

        return None


def run_backtest(data_file: str, cost_pct: float = COST_PCT):
    """Quick screen: load, resample, run."""
    print(f"Loading data from {data_file}...")
    raw_data = load_csv(data_file)
    print(f"Loaded {len(raw_data)} bars")

    print("Resampling...")
    data_4h = resample_to_4h(raw_data)
    data_daily = resample_to_daily(raw_data)
    print(f"4H bars: {len(data_4h)}, Daily bars: {len(data_daily)}")
    print(f"Period: {data_4h[0]['datetime']} → {data_4h[-1]['datetime']}")
    print()

    # Factory needs daily data for trend computation
    def strategy_factory():
        return MTFMomentumStrategy(data_daily)

    strategy = strategy_factory()

    # Gross
    print("=" * 60)
    print("GROSS (0% costs)")
    print("=" * 60)
    bt_gross = Backtest(data_4h, cost_pct=0.0)
    bt_gross.run(strategy)
    print(bt_gross.result.summary())

    # Net
    strategy = strategy_factory()
    print("=" * 60)
    print(f"NET ({cost_pct}% costs)")
    print("=" * 60)
    bt_net = Backtest(data_4h, cost_pct=cost_pct)
    bt_net.run(strategy)
    print(bt_net.result.summary())

    return bt_gross.result, bt_net.result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mtf_momentum.py <data_file.csv>")
        sys.exit(1)
    run_backtest(sys.argv[1])
