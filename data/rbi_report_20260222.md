# RBI Pipeline Report — 2026-02-22


RBI Pipeline Summary — 2026-02-22
============================================================
Screened: 18 ideas
Promoted: 7 (R027, R029, R033, R035, R037, R038, R041)
Killed: 4 (R028, R031, R034, R039)
Parked: 7 (R025, R030, R032, R036, R040, R042, R043)

PROMOTED IDEAS (ready for full hypothesis):
  R027 — Volatility Breakout with Momentum Confirmation (VBMC)
    PF: 1.37 gross | Trades: 126 | Sharpe: 1.2
    Params: {'channel_period': 20, 'roc_fast': 5, 'roc_med': 15, 'roc_slow': 30, 'stop_pct': 2.0, 'target_pct': 6.0}

  R029 — High ATR Regime Trend Following (HARTF)
    PF: 1.31 gross | Trades: 72 | Sharpe: 0.84
    Params: {'ma_period': 20, 'atr_period': 14, 'atr_history': 120, 'base_stop_pct': 3.0, 'base_target_pct': 12.0, 'trend_filter_period': 80}

  R033 — Multi-Day Consolidation Breakout (MDCB)
    PF: 2.49 gross | Trades: 48 | Sharpe: 1.44
    Params: {'atr_period': 20, 'atr_lookback': 60, 'compression_percentile': 10, 'breakout_atr_mult': 1.5, 'confirmation_bars': 2, 'stop_pct': 2.0, 'target_pct': 6.0, 'long_only': True}

  R035 — Trending Strength Continuation (TSC)
    PF: 1.56 gross | Trades: 103 | Sharpe: 1.3
    Params: {'channel_period': 20, 'adx_period': 14, 'adx_threshold': 25, 'stop_pct': 2.0, 'target_pct': 6.0}

  R037 — Acceleration Breakout With Volume Confirmation (ABVC)
    PF: 1.32 gross | Trades: 129 | Sharpe: 1.0
    Params: {'channel_period': 15, 'vol_period': 20, 'vol_mult': 1.5, 'stop_pct': 2.0, 'target_pct': 6.0}

  R038 — Adaptive Volatility Regime Trend (AVRT)
    PF: 1.31 gross | Trades: 72 | Sharpe: 0.84
    Params: {'ma_period': 20, 'atr_period': 14, 'atr_history': 120, 'base_stop_pct': 3.0, 'base_target_pct': 12.0, 'trend_filter_period': 80}

  R041 — ATR Percentile Expansion Breakout
    PF: 1.31 gross | Trades: 72 | Sharpe: 0.84
    Params: {'ma_period': 20, 'atr_period': 14, 'atr_history': 120, 'base_stop_pct': 3.0, 'base_target_pct': 12.0, 'trend_filter_period': 80}

KILLED IDEAS:
  R028 — Trend Acceleration Breakout (TAB): PF 1.08
  R031 — Acceleration Surge After Consolidation (ASAC): PF 1.08
  R034 — Momentum Divergence Acceleration (MDA): PF 1.08
  R039 — Volatility Breakout with Momentum Confirmation: PF 1.08


## New Research Ideas (LLM-sourced)
- **R044** — Volatility Regime Shift Breakout (VRSB): BTC exhibits extended periods of low volatility consolidation followed by sustained high-volatility trending moves; entering at the REGIME transition (not just individual compression) captures the first leg of major moves before they become obvious.
- **R045** — Momentum Persistence Stacking (MPS): Requiring multiple independent momentum confirmations across price, rate-of-change, and trend strength filters out weak breakouts and isolates only high-conviction momentum regimes where follow-through is likely.
- **R046** — Post-Pullback Acceleration Surge (PPAS): Pullbacks in strong trends create compressed coils where late sellers capitulate and early buyers accumulate; the subsequent acceleration breakout above the pullback high confirms the trend resumption with renewed conviction and attracts momentum followers.
