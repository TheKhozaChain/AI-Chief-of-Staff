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


class MultiAssetMomentum:
    """Cross-asset momentum rotation — BTC filter via relative strength.

    Compares rate-of-change (ROC) across BTC, ETH, and SOL.
    Only goes long BTC when BTC has the strongest momentum among
    all available assets AND exceeds a minimum threshold.

    This is a momentum filter, not a full rotation strategy.
    The engine trades BTC; ETH/SOL data is used purely for ranking.

    Params:
        roc_period: Lookback for rate of change (bars)
        min_roc: Minimum BTC ROC to take a trade (%)
        stop_pct: Stop loss percentage
        target_pct: Take profit percentage
        aux_data_dir: Directory containing ETHUSD_1h.csv and SOLUSD_1h.csv
        aux_timeframe_hours: Resample aux data to this timeframe (must match main)
        long_only: Only long signals (always True for this strategy)
    """

    def __init__(self, roc_period=20, min_roc=2.0, stop_pct=3.0, target_pct=8.0,
                 aux_data_dir='', aux_timeframe_hours=4, long_only=True):
        self.roc_period = roc_period
        self.min_roc = min_roc
        self.stop_pct = stop_pct
        self.target_pct = target_pct
        self.long_only = long_only

        self._eth = self._load_aux(aux_data_dir, 'ETHUSD_1h.csv', aux_timeframe_hours)
        self._sol = self._load_aux(aux_data_dir, 'SOLUSD_1h.csv', aux_timeframe_hours)

    @staticmethod
    def _load_aux(data_dir, filename, tf_hours):
        """Load auxiliary asset data and build datetime-indexed lookup."""
        import os
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            return None

        from data_loader import load_csv, resample
        raw = load_csv(filepath)
        bars = resample(raw, hours=tf_hours) if tf_hours > 1 else raw

        lookup = {}
        closes = []
        for i, bar in enumerate(bars):
            lookup[bar['datetime']] = i
            closes.append(bar['close'])
        return {'lookup': lookup, 'closes': closes}

    def _get_roc(self, asset_data, dt):
        """Get ROC for an auxiliary asset at a given datetime."""
        if asset_data is None:
            return None
        idx = asset_data['lookup'].get(dt)
        if idx is None or idx < self.roc_period:
            return None
        current = asset_data['closes'][idx]
        past = asset_data['closes'][idx - self.roc_period]
        if past == 0:
            return None
        return ((current - past) / past) * 100

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        if len(prev_bars) < self.roc_period:
            return None

        # BTC momentum
        btc_current = bar['close']
        btc_past = prev_bars[-self.roc_period]['close']
        if btc_past == 0:
            return None
        btc_roc = ((btc_current - btc_past) / btc_past) * 100

        # Aux asset momentum at the same point in time
        dt = bar['datetime']
        eth_roc = self._get_roc(self._eth, dt)
        sol_roc = self._get_roc(self._sol, dt)

        # Collect all valid ROCs for ranking
        rocs = {'BTC': btc_roc}
        if eth_roc is not None:
            rocs['ETH'] = eth_roc
        if sol_roc is not None:
            rocs['SOL'] = sol_roc

        # Need at least 2 assets to make a meaningful comparison
        if len(rocs) < 2:
            return None

        # BTC must be the strongest AND above minimum threshold
        strongest = max(rocs, key=rocs.get)
        if strongest != 'BTC':
            return None
        if btc_roc < self.min_roc:
            return None

        return {
            'action': 'buy',
            'stop_loss': btc_current * (1 - self.stop_pct / 100),
            'take_profit': btc_current * (1 + self.target_pct / 100),
        }


class AdaptiveMomentumBurst:
    """Squeeze breakout with trend confirmation.

    Enters when price breaks out of a volatility compression zone
    AND price is above a rising medium-term MA. Combines the squeeze
    detection of BollingerBreakout with directional trend filtering.

    Research idea R012.

    Params:
        bb_period: Bollinger Band lookback (bars)
        bb_std: Standard deviation multiplier for bands
        squeeze_lookback: Bars of bandwidth history for percentile calc
        squeeze_pct: Bandwidth below this percentile = squeeze
        min_squeeze_bars: Consecutive squeeze bars required to arm
        ma_period: Trend MA period (price must be above this)
        ma_slope_bars: Number of bars to measure MA slope (must be rising)
        stop_pct: Stop loss percentage
        target_pct: Take profit percentage
    """

    def __init__(self, bb_period=20, bb_std=2.0, squeeze_lookback=50,
                 squeeze_pct=20, min_squeeze_bars=3, ma_period=50,
                 ma_slope_bars=5, stop_pct=3.0, target_pct=8.0):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.squeeze_lookback = squeeze_lookback
        self.squeeze_pct = squeeze_pct
        self.min_squeeze_bars = min_squeeze_bars
        self.ma_period = ma_period
        self.ma_slope_bars = ma_slope_bars
        self.stop_pct = stop_pct
        self.target_pct = target_pct

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        needed = max(self.bb_period + self.squeeze_lookback, self.ma_period + self.ma_slope_bars)
        if len(prev_bars) < needed:
            return None

        closes = [b['close'] for b in prev_bars]
        price = bar['close']

        # Trend filter: MA must be rising and price above it
        ma_now = statistics.mean(closes[-self.ma_period:])
        ma_prev = statistics.mean(closes[-(self.ma_period + self.ma_slope_bars):-self.ma_slope_bars])
        if price <= ma_now or ma_now <= ma_prev:
            return None

        # Bollinger Band squeeze detection
        recent = closes[-self.bb_period:]
        bb_ma = statistics.mean(recent)
        bb_std = statistics.stdev(recent)
        if bb_std == 0 or bb_ma == 0:
            return None
        upper = bb_ma + self.bb_std * bb_std

        # Compute bandwidth history
        bandwidths = []
        for end_idx in range(len(prev_bars) - self.squeeze_lookback, len(prev_bars) + 1):
            start_idx = end_idx - self.bb_period
            if start_idx < 0:
                continue
            window = closes[start_idx:end_idx]
            if len(window) < self.bb_period:
                continue
            w_ma = statistics.mean(window)
            w_std = statistics.stdev(window) if len(window) > 1 else 0
            if w_ma > 0 and w_std > 0:
                bandwidths.append((2 * self.bb_std * w_std) / w_ma * 100)

        if len(bandwidths) < 10:
            return None

        sorted_bw = sorted(bandwidths)
        thresh_idx = max(0, int(len(sorted_bw) * self.squeeze_pct / 100))
        squeeze_thresh = sorted_bw[min(thresh_idx, len(sorted_bw) - 1)]

        squeeze_count = 0
        for bw in reversed(bandwidths):
            if bw <= squeeze_thresh:
                squeeze_count += 1
            else:
                break

        # Entry: squeeze armed + breakout above upper band + trend confirmed
        if squeeze_count >= self.min_squeeze_bars and price > upper:
            return {
                'action': 'buy',
                'stop_loss': price * (1 - self.stop_pct / 100),
                'take_profit': price * (1 + self.target_pct / 100),
            }

        return None


class AccelerationBreakoutFilter:
    """Donchian breakout filtered by momentum acceleration.

    Only enters Donchian channel breakouts when the rate of change (ROC)
    is accelerating — i.e., short-term ROC exceeds long-term ROC,
    indicating genuine momentum thrust rather than a slow grind.

    Research idea R013.

    Params:
        channel_period: Donchian channel lookback (bars)
        roc_short: Short ROC lookback (bars)
        roc_long: Long ROC lookback (bars)
        stop_pct: Stop loss percentage
        target_pct: Take profit percentage
    """

    def __init__(self, channel_period=20, roc_short=5, roc_long=20,
                 stop_pct=3.0, target_pct=9.0):
        self.channel_period = channel_period
        self.roc_short = roc_short
        self.roc_long = roc_long
        self.stop_pct = stop_pct
        self.target_pct = target_pct

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        needed = max(self.channel_period, self.roc_long)
        if len(prev_bars) < needed:
            return None

        price = bar['close']
        closes = [b['close'] for b in prev_bars]

        # Donchian breakout check
        channel_high = max(b['high'] for b in prev_bars[-self.channel_period:])
        if price <= channel_high:
            return None

        # ROC acceleration filter
        if closes[-self.roc_short] == 0 or closes[-self.roc_long] == 0:
            return None
        roc_s = ((price - closes[-self.roc_short]) / closes[-self.roc_short]) * 100
        roc_l = ((price - closes[-self.roc_long]) / closes[-self.roc_long]) * 100

        # Short ROC must exceed long ROC (acceleration) and both must be positive
        if roc_s <= roc_l or roc_s <= 0:
            return None

        return {
            'action': 'buy',
            'stop_loss': price * (1 - self.stop_pct / 100),
            'take_profit': price * (1 + self.target_pct / 100),
        }


class MultiTimeframeBreakout:
    """Donchian breakout with daily trend confirmation.

    Enters on a shorter-period Donchian channel breakout ONLY when the
    longer-term trend is bullish (price above a slow MA that approximates
    the daily timeframe trend).

    Run on 4H data: a 120-bar MA ≈ 20-day moving average.

    Research idea R014.

    Params:
        channel_period: Donchian breakout lookback (bars, shorter)
        trend_ma_period: Slow MA for daily trend proxy (bars, longer)
        stop_pct: Stop loss percentage
        target_pct: Take profit percentage
    """

    def __init__(self, channel_period=15, trend_ma_period=120,
                 stop_pct=3.0, target_pct=9.0):
        self.channel_period = channel_period
        self.trend_ma_period = trend_ma_period
        self.stop_pct = stop_pct
        self.target_pct = target_pct

    def __call__(self, bar: Dict, prev_bars: List[Dict], position) -> Optional[Dict]:
        needed = max(self.channel_period, self.trend_ma_period)
        if len(prev_bars) < needed:
            return None

        price = bar['close']
        closes = [b['close'] for b in prev_bars]

        # Daily trend filter: price must be above slow MA
        trend_ma = statistics.mean(closes[-self.trend_ma_period:])
        if price <= trend_ma:
            return None

        # Donchian breakout
        channel_high = max(b['high'] for b in prev_bars[-self.channel_period:])
        if price <= channel_high:
            return None

        return {
            'action': 'buy',
            'stop_loss': price * (1 - self.stop_pct / 100),
            'take_profit': price * (1 + self.target_pct / 100),
        }


# Registry: maps strategy name to class for dynamic instantiation
ARCHETYPES = {
    'ma_crossover': MACrossover,
    'donchian_breakout': DonchianBreakout,
    'vol_adjusted_trend': VolAdjustedTrend,
    'daily_trend': DailyTrend,
    'bollinger_breakout': BollingerBreakout,
    'multi_asset_momentum': MultiAssetMomentum,
    'adaptive_momentum_burst': AdaptiveMomentumBurst,
    'acceleration_breakout': AccelerationBreakoutFilter,
    'mtf_breakout': MultiTimeframeBreakout,
}
