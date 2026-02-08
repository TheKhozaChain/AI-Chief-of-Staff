"""
4H Volatility Contraction Breakout Strategy (HYPOTHESIS_003)

Detects Bollinger Band squeezes on BTCUSD 4H and enters on breakout.
Wider targets (4%) make transaction costs negligible relative to edge.

Status: Quick screen
See strategies/HYPOTHESIS_003.md for full thesis.

Usage:
    python vol_contraction.py ../../data/BTCUSD_1h.csv
    python vol_contraction.py ../../data/BTCUSD_1h.csv --validate
"""

import sys
import statistics
from typing import Dict, List, Optional
from data_loader import load_csv, resample_to_4h
from engine import (
    Backtest,
    walk_forward, walk_forward_summary,
    run_in_out_of_sample, in_out_of_sample_summary,
)


# ---------------------------------------------------------------------------
# Strategy parameters (from HYPOTHESIS_003.md)
# ---------------------------------------------------------------------------
BB_PERIOD = 20           # 20 bars = 80 hours (~3.3 days) lookback
BB_STD = 2.0             # Standard Bollinger Band multiplier
SQUEEZE_LOOKBACK = 50    # Bars of bandwidth history for percentile
SQUEEZE_PERCENTILE = 20  # Bandwidth below this percentile = squeeze
MIN_SQUEEZE_BARS = 3     # Consecutive squeeze bars before arming
STOP_PCT = 1.5           # Stop loss: 1.5% beyond entry
TAKE_PROFIT_PCT = 4.0    # Take profit: 4.0% from entry
COST_PCT = 0.1           # Round-trip transaction cost


class VolContractionStrategy:
    """Bollinger Band squeeze breakout on 4H BTCUSD.

    Signal logic:
        1. Compute BB (20-period, 2 std dev) and bandwidth for each bar.
        2. If bandwidth is in the bottom 20th percentile for 3+ consecutive
           bars, the market is in a "squeeze" (compressed volatility).
        3. When price closes beyond the BB while squeeze is active → entry.
           - Close > upper band → long
           - Close < lower band → short
        4. Stop at 1.5%, target at 4.0% (2.67:1 R:R).

    All state is computed from prev_bars on each call (no carried state),
    so gaps from position holds don't affect signal accuracy.
    """

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        needed = BB_PERIOD + SQUEEZE_LOOKBACK  # 70 bars warmup
        if len(prev_bars) < needed:
            return None

        # Current Bollinger Bands (from last BB_PERIOD bars before current bar)
        recent_closes = [b['close'] for b in prev_bars[-BB_PERIOD:]]
        ma = statistics.mean(recent_closes)
        std = statistics.stdev(recent_closes)
        if std == 0 or ma == 0:
            return None

        upper = ma + BB_STD * std
        lower = ma - BB_STD * std

        # Compute bandwidth at each of the last SQUEEZE_LOOKBACK+1 positions
        # to build a history for percentile calculation and squeeze counting.
        bandwidths = []
        for end_idx in range(len(prev_bars) - SQUEEZE_LOOKBACK, len(prev_bars) + 1):
            start_idx = end_idx - BB_PERIOD
            if start_idx < 0:
                continue
            window = [b['close'] for b in prev_bars[start_idx:end_idx]]
            if len(window) < BB_PERIOD:
                continue
            w_ma = statistics.mean(window)
            w_std = statistics.stdev(window) if len(window) > 1 else 0
            if w_ma > 0 and w_std > 0:
                bw = (2 * BB_STD * w_std) / w_ma * 100
                bandwidths.append(bw)

        if len(bandwidths) < 10:
            return None

        # Squeeze threshold: 20th percentile of recent bandwidth
        sorted_bw = sorted(bandwidths)
        thresh_idx = max(0, int(len(sorted_bw) * SQUEEZE_PERCENTILE / 100))
        squeeze_thresh = sorted_bw[min(thresh_idx, len(sorted_bw) - 1)]

        # Count consecutive squeeze bars from most recent
        squeeze_count = 0
        for bw in reversed(bandwidths):
            if bw <= squeeze_thresh:
                squeeze_count += 1
            else:
                break

        # Signal: armed (squeeze long enough) AND breakout beyond band
        if squeeze_count >= MIN_SQUEEZE_BARS:
            price = bar['close']
            if price > upper:
                return {
                    'action': 'buy',
                    'stop_loss': price * (1 - STOP_PCT / 100),
                    'take_profit': price * (1 + TAKE_PROFIT_PCT / 100),
                }
            elif price < lower:
                return {
                    'action': 'sell',
                    'stop_loss': price * (1 + STOP_PCT / 100),
                    'take_profit': price * (1 - TAKE_PROFIT_PCT / 100),
                }

        return None


# ---------------------------------------------------------------------------
# Backtest runners
# ---------------------------------------------------------------------------

def run_backtest(data_file: str, cost_pct: float = COST_PCT):
    """Quick screen: load data, resample to 4H, run backtest."""
    print(f"Loading data from {data_file}...")
    raw_data = load_csv(data_file)
    print(f"Loaded {len(raw_data)} bars")

    print("Resampling to 4H...")
    data = resample_to_4h(raw_data)
    print(f"Resampled to {len(data)} 4H bars")
    print(f"Period: {data[0]['datetime']} → {data[-1]['datetime']}")
    print()

    # Gross edge (0% costs)
    print("=" * 60)
    print("GROSS (0% costs)")
    print("=" * 60)
    bt_gross = Backtest(data, cost_pct=0.0)
    bt_gross.run(VolContractionStrategy())
    print(bt_gross.result.summary())

    # Net edge (with transaction costs)
    print("=" * 60)
    print(f"NET ({cost_pct}% costs)")
    print("=" * 60)
    bt_net = Backtest(data, cost_pct=cost_pct)
    bt_net.run(VolContractionStrategy())
    print(bt_net.result.summary())

    return bt_gross.result, bt_net.result


def run_full_validation(data_file: str, cost_pct: float = COST_PCT):
    """Full validation: backtest + OOS + walk-forward."""
    print(f"Loading data from {data_file}...")
    raw_data = load_csv(data_file)
    print(f"Loaded {len(raw_data)} bars")

    print("Resampling to 4H...")
    data = resample_to_4h(raw_data)
    print(f"Resampled to {len(data)} 4H bars")
    print(f"Period: {data[0]['datetime']} → {data[-1]['datetime']}")
    print(f"Transaction cost: {cost_pct}% per trade (round-trip)")

    # 1. Full-sample backtest
    print("\n" + "=" * 60)
    print("1. FULL-SAMPLE BACKTEST")
    print("=" * 60)
    bt = Backtest(data, cost_pct=cost_pct)
    bt.run(VolContractionStrategy())
    print(bt.result.summary())

    # 2. In-sample vs out-of-sample (70/30 split)
    print("=" * 60)
    print("2. IN-SAMPLE vs OUT-OF-SAMPLE (70/30 split)")
    print("=" * 60)
    oos_results = run_in_out_of_sample(
        data, VolContractionStrategy, train_pct=0.7, cost_pct=cost_pct
    )
    print(in_out_of_sample_summary(oos_results))

    # 3. Walk-forward validation (~1300 bars per window for 5 windows)
    print("=" * 60)
    print("3. WALK-FORWARD VALIDATION (rolling windows)")
    print("=" * 60)
    wf_results = walk_forward(
        data, VolContractionStrategy, window_bars=1300, cost_pct=cost_pct
    )
    print(walk_forward_summary(wf_results))

    return bt.result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python vol_contraction.py <data_file.csv>              # quick screen")
        print("  python vol_contraction.py <data_file.csv> --validate   # full validation")
        print()
        print("Data should be 15m or 1h BTCUSD bars (will be resampled to 4H).")
        sys.exit(1)

    data_file = sys.argv[1]
    if "--validate" in sys.argv:
        run_full_validation(data_file)
    else:
        run_backtest(data_file)
