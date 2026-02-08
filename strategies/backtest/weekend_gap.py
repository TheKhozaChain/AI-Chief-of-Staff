"""
Weekend Gap Fade Quick Screen (R005)

Hypothesis: Crypto weekend gaps tend to fill within 24-48 hours.
When Monday's open diverges significantly from Friday's close,
fade the gap expecting a return to Friday's level.

Usage:
    python weekend_gap.py ../../data/BTCUSD_1h.csv
"""

import sys
import statistics
from typing import Dict, List, Optional
from datetime import timedelta
from data_loader import load_csv, resample_to_4h
from engine import Backtest


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
GAP_THRESHOLD_PCT = 1.0    # Minimum gap size to trigger (1% of Friday close)
STOP_PCT = 2.0             # Stop: 2% beyond entry (gap extends)
TAKE_PROFIT_PCT = 1.5      # Target: gap fill (1.5% — partial fill + buffer)
COST_PCT = 0.1


class WeekendGapStrategy:
    """Fade weekend gaps on 4H BTCUSD.

    Logic:
        - Identify Friday's last 4H close and Monday's first 4H bar.
        - If Monday opens > Friday close + GAP_THRESHOLD → short (fade up-gap).
        - If Monday opens < Friday close - GAP_THRESHOLD → long (fade down-gap).
        - Target: partial gap fill. Stop: gap extends further.

    Note: Crypto trades 24/7 so "weekend gap" is really about
    low-liquidity weekend drift that reverts on Monday when volume returns.
    We detect this by looking for Friday-to-Monday price displacement.
    """

    def __init__(self):
        self.friday_close = None
        self.friday_date = None
        self.traded_this_week = False

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        if len(prev_bars) < 2:
            return None

        dt = bar['datetime']
        weekday = dt.weekday()  # 0=Mon, 4=Fri, 5=Sat, 6=Sun

        # Track Friday's close (last bar on Friday)
        if weekday == 4:  # Friday
            self.friday_close = bar['close']
            self.friday_date = dt.date()
            self.traded_this_week = False
            return None

        # Trade on Monday only, once per week
        if weekday != 0 or self.traded_this_week:
            return None

        if self.friday_close is None:
            return None

        # Check gap size
        price = bar['close']
        gap_pct = ((price - self.friday_close) / self.friday_close) * 100

        if abs(gap_pct) < GAP_THRESHOLD_PCT:
            return None

        self.traded_this_week = True

        # Fade the gap
        if gap_pct > 0:
            # Price gapped up → short, expect return to Friday close
            return {
                'action': 'sell',
                'stop_loss': price * (1 + STOP_PCT / 100),
                'take_profit': price * (1 - TAKE_PROFIT_PCT / 100),
            }
        else:
            # Price gapped down → long, expect return to Friday close
            return {
                'action': 'buy',
                'stop_loss': price * (1 - STOP_PCT / 100),
                'take_profit': price * (1 + TAKE_PROFIT_PCT / 100),
            }


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
    bt_gross.run(WeekendGapStrategy())
    print(bt_gross.result.summary())

    # Net
    print("=" * 60)
    print(f"NET ({cost_pct}% costs)")
    print("=" * 60)
    bt_net = Backtest(data, cost_pct=cost_pct)
    bt_net.run(WeekendGapStrategy())
    print(bt_net.result.summary())

    return bt_gross.result, bt_net.result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python weekend_gap.py <data_file.csv>")
        sys.exit(1)
    run_backtest(sys.argv[1])
