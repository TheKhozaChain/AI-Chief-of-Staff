"""
Parameterized strategy archetypes for rapid screening.

Each archetype is a configurable strategy class that can be instantiated
with different parameters. This eliminates writing boilerplate strategy
files for each new idea — just pick an archetype and set params.

Archetypes:
    MACrossover       — Trend following with fast/slow MA crossover
    DonchianBreakout  — Enter on N-bar high/low breakout
    VolAdjustedTrend  — MA trend with ATR-scaled position sizing
    DailyTrend        — Longer-hold trend following on daily bars
    BollingerBreakout — Bollinger Band squeeze breakout (generalized)

All archetypes implement __call__(bar, prev_bars, position) -> Optional[Dict]
compatible with engine.Backtest.run().
"""

import statistics
from typing import Dict, List, Optional


class MACrossover:
    """Trend following via moving average crossover.

    Long when fast MA > slow MA and price > fast MA.
    Short when fast MA < slow MA and price < fast MA (if allow_short=True).

    Params:
        fast_period: Fast MA lookback (bars)
        slow_period: Slow MA lookback (bars)
        stop_pct: Stop loss percentage
        target_pct: Take profit percentage
        long_only: If True, only take long signals
    """

    def __init__(self, fast_period=20, slow_period=80, stop_pct=4.0,
                 target_pct=12.0, long_only=True):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.stop_pct = stop_pct
        self.target_pct = target_pct
        self.long_only = long_only

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        if len(prev_bars) < self.slow_period:
            return None

        closes = [b['close'] for b in prev_bars]
        ma_fast = statistics.mean(closes[-self.fast_period:])
        ma_slow = statistics.mean(closes[-self.slow_period:])
        price = bar['close']

        if price > ma_fast and ma_fast > ma_slow:
            return {
                'action': 'buy',
                'stop_loss': price * (1 - self.stop_pct / 100),
                'take_profit': price * (1 + self.target_pct / 100),
            }

        if not self.long_only and price < ma_fast and ma_fast < ma_slow:
            return {
                'action': 'sell',
                'stop_loss': price * (1 + self.stop_pct / 100),
                'take_profit': price * (1 - self.target_pct / 100),
            }

        return None


class DonchianBreakout:
    """Donchian channel breakout strategy.

    Long when price breaks above the N-bar high.
    Short when price breaks below the N-bar low (if allow_short=True).

    Params:
        channel_period: Lookback for channel high/low (bars)
        stop_pct: Stop loss percentage
        target_pct: Take profit percentage
        long_only: If True, only take long breakouts
    """

    def __init__(self, channel_period=20, stop_pct=3.0, target_pct=9.0,
                 long_only=True):
        self.channel_period = channel_period
        self.stop_pct = stop_pct
        self.target_pct = target_pct
        self.long_only = long_only

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        if len(prev_bars) < self.channel_period:
            return None

        lookback = prev_bars[-self.channel_period:]
        channel_high = max(b['high'] for b in lookback)
        channel_low = min(b['low'] for b in lookback)
        price = bar['close']

        if price > channel_high:
            return {
                'action': 'buy',
                'stop_loss': price * (1 - self.stop_pct / 100),
                'take_profit': price * (1 + self.target_pct / 100),
            }

        if not self.long_only and price < channel_low:
            return {
                'action': 'sell',
                'stop_loss': price * (1 + self.stop_pct / 100),
                'take_profit': price * (1 - self.target_pct / 100),
            }

        return None


class VolAdjustedTrend:
    """Trend following with volatility-adjusted stops/targets.

    Uses ATR (average true range) to set stop and target distances,
    so the strategy adapts to market conditions.

    Params:
        ma_period: Trend MA lookback (bars)
        atr_period: ATR lookback (bars)
        stop_atr_mult: Stop = entry - stop_atr_mult * ATR
        target_atr_mult: Target = entry + target_atr_mult * ATR
        trend_filter_period: Slow MA for trend confirmation
        long_only: If True, only take long signals
    """

    def __init__(self, ma_period=20, atr_period=14, stop_atr_mult=2.0,
                 target_atr_mult=6.0, trend_filter_period=80, long_only=True):
        self.ma_period = ma_period
        self.atr_period = atr_period
        self.stop_atr_mult = stop_atr_mult
        self.target_atr_mult = target_atr_mult
        self.trend_filter_period = trend_filter_period
        self.long_only = long_only

    def _calc_atr(self, bars: List[Dict]) -> float:
        """Calculate Average True Range from bars."""
        if len(bars) < 2:
            return 0.0
        trs = []
        for i in range(1, len(bars)):
            high = bars[i]['high']
            low = bars[i]['low']
            prev_close = bars[i - 1]['close']
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            trs.append(tr)
        return statistics.mean(trs[-self.atr_period:]) if trs else 0.0

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        needed = max(self.ma_period, self.atr_period, self.trend_filter_period)
        if len(prev_bars) < needed:
            return None

        closes = [b['close'] for b in prev_bars]
        ma = statistics.mean(closes[-self.ma_period:])
        trend_ma = statistics.mean(closes[-self.trend_filter_period:])
        atr = self._calc_atr(prev_bars[-self.atr_period - 1:])

        if atr == 0:
            return None

        price = bar['close']

        if price > ma and ma > trend_ma:
            return {
                'action': 'buy',
                'stop_loss': price - self.stop_atr_mult * atr,
                'take_profit': price + self.target_atr_mult * atr,
            }

        if not self.long_only and price < ma and ma < trend_ma:
            return {
                'action': 'sell',
                'stop_loss': price + self.stop_atr_mult * atr,
                'take_profit': price - self.target_atr_mult * atr,
            }

        return None


class DailyTrend:
    """Longer-hold trend following designed for daily bars.

    Same logic as MACrossover but with parameters calibrated for
    daily timeframes (hold for weeks, not hours).

    Params:
        fast_period: Fast MA lookback (days)
        slow_period: Slow MA lookback (days)
        stop_pct: Stop loss percentage (wider for daily)
        target_pct: Take profit percentage (wider for daily)
        long_only: If True, only take long signals
    """

    def __init__(self, fast_period=10, slow_period=40, stop_pct=6.0,
                 target_pct=18.0, long_only=True):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.stop_pct = stop_pct
        self.target_pct = target_pct
        self.long_only = long_only

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        if len(prev_bars) < self.slow_period:
            return None

        closes = [b['close'] for b in prev_bars]
        ma_fast = statistics.mean(closes[-self.fast_period:])
        ma_slow = statistics.mean(closes[-self.slow_period:])
        price = bar['close']

        if price > ma_fast and ma_fast > ma_slow:
            return {
                'action': 'buy',
                'stop_loss': price * (1 - self.stop_pct / 100),
                'take_profit': price * (1 + self.target_pct / 100),
            }

        if not self.long_only and price < ma_fast and ma_fast < ma_slow:
            return {
                'action': 'sell',
                'stop_loss': price * (1 + self.stop_pct / 100),
                'take_profit': price * (1 - self.target_pct / 100),
            }

        return None


class BollingerBreakout:
    """Generalized Bollinger Band squeeze breakout.

    Detects low-volatility squeezes and enters on band breakout.
    Parameterized version of the vol_contraction strategy.

    Params:
        bb_period: Bollinger Band lookback (bars)
        bb_std: Standard deviation multiplier
        squeeze_lookback: Bars of bandwidth history for percentile
        squeeze_percentile: Bandwidth below this = squeeze
        min_squeeze_bars: Consecutive squeeze bars to arm
        stop_pct: Stop loss percentage
        target_pct: Take profit percentage
    """

    def __init__(self, bb_period=20, bb_std=2.0, squeeze_lookback=50,
                 squeeze_percentile=20, min_squeeze_bars=3,
                 stop_pct=1.5, target_pct=4.0):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.squeeze_lookback = squeeze_lookback
        self.squeeze_percentile = squeeze_percentile
        self.min_squeeze_bars = min_squeeze_bars
        self.stop_pct = stop_pct
        self.target_pct = target_pct

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        needed = self.bb_period + self.squeeze_lookback
        if len(prev_bars) < needed:
            return None

        recent_closes = [b['close'] for b in prev_bars[-self.bb_period:]]
        ma = statistics.mean(recent_closes)
        std = statistics.stdev(recent_closes)
        if std == 0 or ma == 0:
            return None

        upper = ma + self.bb_std * std
        lower = ma - self.bb_std * std

        bandwidths = []
        for end_idx in range(len(prev_bars) - self.squeeze_lookback, len(prev_bars) + 1):
            start_idx = end_idx - self.bb_period
            if start_idx < 0:
                continue
            window = [b['close'] for b in prev_bars[start_idx:end_idx]]
            if len(window) < self.bb_period:
                continue
            w_ma = statistics.mean(window)
            w_std = statistics.stdev(window) if len(window) > 1 else 0
            if w_ma > 0 and w_std > 0:
                bw = (2 * self.bb_std * w_std) / w_ma * 100
                bandwidths.append(bw)

        if len(bandwidths) < 10:
            return None

        sorted_bw = sorted(bandwidths)
        thresh_idx = max(0, int(len(sorted_bw) * self.squeeze_percentile / 100))
        squeeze_thresh = sorted_bw[min(thresh_idx, len(sorted_bw) - 1)]

        squeeze_count = 0
        for bw in reversed(bandwidths):
            if bw <= squeeze_thresh:
                squeeze_count += 1
            else:
                break

        if squeeze_count >= self.min_squeeze_bars:
            price = bar['close']
            if price > upper:
                return {
                    'action': 'buy',
                    'stop_loss': price * (1 - self.stop_pct / 100),
                    'take_profit': price * (1 + self.target_pct / 100),
                }
            elif price < lower:
                return {
                    'action': 'sell',
                    'stop_loss': price * (1 + self.stop_pct / 100),
                    'take_profit': price * (1 - self.target_pct / 100),
                }

        return None


# Registry: maps archetype name to class for dynamic instantiation
ARCHETYPES = {
    'ma_crossover': MACrossover,
    'donchian_breakout': DonchianBreakout,
    'vol_adjusted_trend': VolAdjustedTrend,
    'daily_trend': DailyTrend,
    'bollinger_breakout': BollingerBreakout,
}
