"""
Regime detection and coverage analysis for strategy screening.

Classifies market bars into bull/bear/sideways regimes using a 200-bar SMA
and its slope, then runs sub-backtests per regime to check strategy coverage.

A strategy that only works in bull markets is dangerous for live deployment.
This module catches that gap at screening time.

Usage:
    from regime import split_by_regime, run_regime_coverage_check

    regimes = split_by_regime(bars)
    coverage = run_regime_coverage_check(bars, strategy_factory, cost_pct=0.1)
    if not coverage['pass']:
        print(f"Failed regimes: {coverage['failed_regimes']}")
"""

import statistics
from typing import Dict, List, Optional, Callable

from engine import Backtest


SMA_PERIOD = 200
SLOPE_PERIOD = 10


def classify_bar_regime(bar: Dict, prev_bars: List[Dict]) -> Optional[str]:
    """Classify a single bar's regime based on 200-bar SMA and its slope.

    Bull:     price > SMA AND SMA rising (10-bar slope > 0)
    Bear:     price < SMA AND SMA falling (10-bar slope < 0)
    Sideways: everything else

    Returns 'bull', 'bear', 'sideways', or None if insufficient data.
    """
    if len(prev_bars) < SMA_PERIOD:
        return None

    closes = [b['close'] for b in prev_bars[-SMA_PERIOD:]]
    sma = statistics.mean(closes)
    price = bar['close']

    # SMA slope: compare current SMA to SMA from SLOPE_PERIOD bars ago
    if len(prev_bars) < SMA_PERIOD + SLOPE_PERIOD:
        # Not enough data for slope — can still classify by price vs SMA
        if price > sma:
            return 'bull'
        elif price < sma:
            return 'bear'
        return 'sideways'

    older_closes = [b['close'] for b in prev_bars[-(SMA_PERIOD + SLOPE_PERIOD):-SLOPE_PERIOD]]
    sma_prev = statistics.mean(older_closes)
    sma_rising = sma > sma_prev
    sma_falling = sma < sma_prev

    if price > sma and sma_rising:
        return 'bull'
    elif price < sma and sma_falling:
        return 'bear'
    else:
        return 'sideways'


def split_by_regime(bars: List[Dict]) -> Dict[str, List[Dict]]:
    """Classify each bar and group into regime buckets.

    Returns {'bull': [...], 'bear': [...], 'sideways': [...]}.
    Each bucket contains full bar dicts. Bars with insufficient lookback
    for classification are excluded.
    """
    regimes = {'bull': [], 'bear': [], 'sideways': []}

    for i, bar in enumerate(bars):
        prev = bars[max(0, i - (SMA_PERIOD + SLOPE_PERIOD)):i]
        regime = classify_bar_regime(bar, prev)
        if regime:
            regimes[regime].append(bar)

    return regimes


def run_regime_coverage_check(
    bars: List[Dict],
    strategy_factory: Callable,
    cost_pct: float = 0.1,
    min_trades_per_regime: int = 10,
    min_bars_per_regime: int = 50,
) -> Dict:
    """Run sub-backtests per regime and check trade coverage.

    Args:
        bars: Full OHLCV bar list (already resampled to target timeframe).
        strategy_factory: Callable returning a fresh strategy instance.
        cost_pct: Transaction cost percentage.
        min_trades_per_regime: Required trades in each non-skipped regime.
        min_bars_per_regime: Regimes with fewer bars are skipped (not penalized).

    Returns:
        Dict with keys:
            pass: bool (True if all non-skipped regimes have enough trades)
            regimes: {regime_name: {bars, trades, pf, skipped}}
            failed_regimes: list of regime names that failed
            reason: human-readable explanation
    """
    regime_labels = _label_bars(bars)
    result = {
        'pass': True,
        'regimes': {},
        'failed_regimes': [],
        'reason': '',
    }

    for regime_name in ('bull', 'bear', 'sideways'):
        regime_bars = [bars[i] for i, label in enumerate(regime_labels) if label == regime_name]
        n_bars = len(regime_bars)

        if n_bars < min_bars_per_regime:
            result['regimes'][regime_name] = {
                'bars': n_bars,
                'trades': 0,
                'pf': 0.0,
                'skipped': True,
                'reason': f'Only {n_bars} bars (need {min_bars_per_regime})',
            }
            continue

        # Run backtest on regime subset
        strategy = strategy_factory()
        bt = Backtest(regime_bars, cost_pct=cost_pct)
        bt.run(strategy)
        trades = bt.result.total_trades
        pf = bt.result.profit_factor

        passed = trades >= min_trades_per_regime
        regime_info = {
            'bars': n_bars,
            'trades': trades,
            'pf': round(pf, 2),
            'skipped': False,
            'passed': passed,
        }

        if not passed:
            regime_info['reason'] = f'{trades} trades (need {min_trades_per_regime})'
            result['failed_regimes'].append(regime_name)
            result['pass'] = False

        result['regimes'][regime_name] = regime_info

    if result['failed_regimes']:
        result['reason'] = (
            f"Insufficient trade coverage in: {', '.join(result['failed_regimes'])}. "
            f"Strategy may only work in specific market conditions."
        )
    else:
        result['reason'] = 'All non-skipped regimes have sufficient trades.'

    return result


def _label_bars(bars: List[Dict]) -> List[Optional[str]]:
    """Label each bar with its regime. Returns list parallel to bars."""
    labels = []
    for i, bar in enumerate(bars):
        prev = bars[max(0, i - (SMA_PERIOD + SLOPE_PERIOD)):i]
        labels.append(classify_bar_regime(bar, prev))
    return labels
