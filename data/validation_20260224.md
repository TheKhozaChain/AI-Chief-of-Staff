# Walk-Forward Validation Report (Queue)

**Date:** 2026-02-24 17:52  
**Data:** BTCUSD 1H, 26,279 bars  
**Period:** 2023-02-08 → 2026-02-07  
**Base cost:** 0.1%  |  **Stress cost:** 0.15%

---


## H017: Range Compression Expansion (RCE)

Research ID: R021  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 2.20 |
| Sharpe Ratio | 1.49 |
| Total Trades | 50 |
| Win Rate | 44.0% |
| Net P&L | $46,225.67 |
| Gross P&L | $49,494.37 |
| Total Costs | $3,268.70 |
| Max Drawdown | $12,486.42 |
| Max DD Duration | 231 days |
| Avg Trade Duration | 99.1h |
| Expectancy | $924.51/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 3/7**

- [PASS] profit_factor: 2.2 (target: >= 1.3)
- [FAIL] win_rate: 44.0% (target: >= 50%)
- [PASS] sharpe_ratio: 1.49 (target: >= 1.0)
- [FAIL] total_trades: 50 (target: >= 100)
- [PASS] expectancy_positive: 924.51 (target: > 0)
- [FAIL] beats_buy_hold: $46,226 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 231 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10      11 45.5%   1.88    1.58 $  3,160.98
2023-08-10 → 2024-02-08       3 100.0%    inf   10.27 $  5,431.98
2024-02-08 → 2024-08-09       8 12.5%   0.33   -1.86 $ -6,667.46
2024-08-09 → 2025-02-07       9 44.4%   2.17    1.67 $  8,735.58
2025-02-07 → 2025-08-09       8 62.5%   3.73    2.64 $ 17,783.48
2025-08-09 → 2026-02-07       8 37.5%   1.73    0.99 $  7,174.64
------------------------------------------------------------
Windows: 6  |  Profitable: 5/6  |  Total Net: $35,619.21
PF consistency: mean=inf, std=nan
```

- Profitable windows: 5/6
- Mean PF across windows: inf
- Worst window PF: 0.33
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         34            14
Win Rate                         41.2%        50.0%
Profit Factor                      1.70          2.86
Sharpe Ratio                       1.32          1.94
Net P&L                   $  15,546.40 $  27,013.58
Max Drawdown              $  12,486.42 $   3,724.48
Avg Duration                      72.7h        144.0h
-------------------------------------------------------
PF change in-sample → out-of-sample: +67.7%
Out-of-sample PF >= 1.2 — edge appears robust
```

- OOS Profit Factor: 2.86
- PF degradation: +67.7%
- **OOS verdict: PASS** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| atr_period | 16 | 1.95 | 48 | 1.29 | 41.7% | $37,514 |
| atr_period | 20 **BASE** | 2.20 | 50 | 1.49 | 44.0% | $46,226 |
| atr_period | 24 | 1.94 | 49 | 1.06 | 38.8% | $37,908 |
| atr_lookback | 48 | 1.98 | 52 | 1.39 | 42.3% | $42,005 |
| atr_lookback | 60 **BASE** | 2.20 | 50 | 1.49 | 44.0% | $46,226 |
| atr_lookback | 72 | 2.09 | 47 | 1.50 | 44.7% | $40,607 |
| compression_percentile | 8 | 2.28 | 49 | 1.55 | 44.9% | $47,549 |
| compression_percentile | 10 **BASE** | 2.20 | 50 | 1.49 | 44.0% | $46,226 |
| compression_percentile | 12 | 2.20 | 50 | 1.49 | 44.0% | $46,226 |
| breakout_atr_mult | 1.2 | 1.88 | 62 | 1.34 | 40.3% | $45,691 |
| breakout_atr_mult | 1.5 **BASE** | 2.20 | 50 | 1.49 | 44.0% | $46,226 |
| breakout_atr_mult | 1.8 | 1.84 | 42 | 0.94 | 38.1% | $30,848 |
| stop_pct | 1.6 | 2.03 | 52 | 1.25 | 36.5% | $37,100 |
| stop_pct | 2.0 **BASE** | 2.20 | 50 | 1.49 | 44.0% | $46,226 |
| stop_pct | 2.4 | 1.85 | 50 | 1.20 | 44.0% | $38,894 |
| target_pct | 4.8 | 2.05 | 57 | 1.47 | 47.4% | $43,999 |
| target_pct | 6.0 **BASE** | 2.20 | 50 | 1.49 | 44.0% | $46,226 |
| target_pct | 7.2 | 2.20 | 47 | 1.45 | 40.4% | $48,019 |

- Variants with PF > 1.0: 12/12
- Worst variant PF: 1.84
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 2.20 | 2.13 |
| Net P&L | $46,226 | $44,591 |
| Sharpe | 1.49 | 1.44 |
| Costs | $3,269 | $4,903 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | PASS |
| sensitivity | PASS |
| cost_stress | PASS |

**H017 VALIDATED (4/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## H018: Momentum Exhaustion Reversal to Trend (MERT)

Research ID: R022  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.30 |
| Sharpe Ratio | 0.16 |
| Total Trades | 28 |
| Win Rate | 28.6% |
| Net P&L | $8,185.96 |
| Gross P&L | $10,070.40 |
| Total Costs | $1,884.44 |
| Max Drawdown | $11,322.64 |
| Max DD Duration | 662 days |
| Avg Trade Duration | 46.6h |
| Expectancy | $292.36/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 2/7**

- [PASS] profit_factor: 1.3 (target: >= 1.3)
- [FAIL] win_rate: 28.6% (target: >= 50%)
- [FAIL] sharpe_ratio: 0.16 (target: >= 1.0)
- [FAIL] total_trades: 28 (target: >= 100)
- [PASS] expectancy_positive: 292.36 (target: > 0)
- [FAIL] beats_buy_hold: $8,186 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 662 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10       5  0.0%   0.00 -2633252562813185.00 $ -2,899.90
2023-08-10 → 2024-02-08       2 50.0%   2.51    2.43 $  1,322.15
2024-02-08 → 2024-08-09       7  0.0%   0.00 -1433337598870346.75 $ -9,744.89
2024-08-09 → 2025-02-07       8 50.0%   2.83    1.99 $ 12,408.87
2025-02-07 → 2025-08-09       0  0.0%   0.00    0.00 $      0.00
2025-08-09 → 2026-02-07       5 40.0%   1.54    1.09 $  3,666.15
------------------------------------------------------------
Windows: 6  |  Profitable: 3/6  |  Total Net: $4,752.39
PF consistency: mean=1.38, std=1.34
```

- Profitable windows: 3/6
- Mean PF across windows: 1.38
- Worst window PF: 0.00
- **Walk-forward verdict: FAIL**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         23             5
Win Rate                         26.1%        40.0%
Profit Factor                      1.22          1.54
Sharpe Ratio                      -0.01          1.09
Net P&L                   $   4,519.80 $   3,666.15
Max Drawdown              $  11,322.64 $   6,744.09
Avg Duration                      49.7h         32.0h
-------------------------------------------------------
PF change in-sample → out-of-sample: +26.2%
Out-of-sample PF >= 1.2 — edge appears robust
```

- OOS Profit Factor: 1.54
- PF degradation: +26.2%
- **OOS verdict: PASS** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| ma_period | 40 | 0.99 | 23 | -0.30 | 21.7% | $-348 |
| ma_period | 50 **BASE** | 1.30 | 28 | 0.16 | 28.6% | $8,186 |
| ma_period | 60 | 1.54 | 29 | 0.54 | 34.5% | $15,037 |
| rsi_period | 11 | 1.12 | 35 | -0.04 | 25.7% | $4,438 |
| rsi_period | 14 **BASE** | 1.30 | 28 | 0.16 | 28.6% | $8,186 |
| rsi_period | 17 | 1.47 | 18 | 0.37 | 33.3% | $7,698 |
| rsi_threshold | 24 | 1.26 | 14 | 0.11 | 28.6% | $3,586 |
| rsi_threshold | 30 **BASE** | 1.30 | 28 | 0.16 | 28.6% | $8,186 |
| rsi_threshold | 36 | 1.33 | 43 | 0.51 | 32.6% | $13,564 |
| bounce_min_pct | 0.8 | 1.56 | 37 | 0.47 | 32.4% | $19,744 |
| bounce_min_pct | 1.0 **BASE** | 1.30 | 28 | 0.16 | 28.6% | $8,186 |
| bounce_min_pct | 1.2 | 0.58 | 24 | -0.74 | 16.7% | $-11,413 |
| stop_pct | 1.6 | 1.36 | 28 | 0.19 | 25.0% | $8,269 |
| stop_pct | 2.0 **BASE** | 1.30 | 28 | 0.16 | 28.6% | $8,186 |
| stop_pct | 2.4 | 1.09 | 28 | -0.08 | 28.6% | $3,036 |
| target_pct | 4.8 | 1.21 | 28 | 0.08 | 32.1% | $5,451 |
| target_pct | 6.0 **BASE** | 1.30 | 28 | 0.16 | 28.6% | $8,186 |
| target_pct | 7.2 | 1.20 | 28 | 0.15 | 25.0% | $5,944 |

- Variants with PF > 1.0: 10/12
- Worst variant PF: 0.58
- **Sensitivity verdict: FAIL**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.30 | 1.26 |
| Net P&L | $8,186 | $7,244 |
| Sharpe | 0.16 | 0.11 |
| Costs | $1,884 | $2,827 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | FAIL |
| out_of_sample | PASS |
| sensitivity | FAIL |
| cost_stress | PASS |

**H018 FAILED VALIDATION (2/4 tests passed)**

**Recommendation:** Archive or refine. Edge not robust enough for live deployment.

---


## H019: Volatility Breakout with Momentum Confirmation (VBMC)

Research ID: R027  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.19 |
| Sharpe Ratio | 1.08 |
| Total Trades | 126 |
| Win Rate | 34.1% |
| Net P&L | $24,230.88 |
| Gross P&L | $32,726.92 |
| Total Costs | $8,496.04 |
| Max Drawdown | $22,092.97 |
| Max DD Duration | 256 days |
| Avg Trade Duration | 76.6h |
| Expectancy | $192.31/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 3/7**

- [FAIL] profit_factor: 1.19 (target: >= 1.3)
- [FAIL] win_rate: 34.1% (target: >= 50%)
- [PASS] sharpe_ratio: 1.08 (target: >= 1.0)
- [PASS] total_trades: 126 (target: >= 100)
- [PASS] expectancy_positive: 192.31 (target: > 0)
- [FAIL] beats_buy_hold: $24,231 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 256 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10      19 42.1%   1.73    1.58 $  4,646.92
2023-08-10 → 2024-02-08      22 50.0%   2.89    3.38 $ 14,608.90
2024-02-08 → 2024-08-09      22 22.7%   0.71   -0.57 $ -6,929.31
2024-08-09 → 2025-02-07      24 41.7%   1.85    2.24 $ 21,021.16
2025-02-07 → 2025-08-09      19 26.3%   1.08    0.20 $  2,023.75
2025-08-09 → 2026-02-07      17 11.8%   0.37   -2.65 $-20,634.42
------------------------------------------------------------
Windows: 6  |  Profitable: 4/6  |  Total Net: $14,737.00
PF consistency: mean=1.44, std=0.91
```

- Profitable windows: 4/6
- Mean PF across windows: 1.44
- Worst window PF: 0.37
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         93            32
Win Rate                         37.6%        25.0%
Profit Factor                      1.45          0.92
Sharpe Ratio                       1.59         -0.17
Net P&L                   $  31,455.31 $  -4,160.71
Max Drawdown              $  20,520.93 $  22,092.97
Avg Duration                      70.7h         94.2h
-------------------------------------------------------
PF change in-sample → out-of-sample: -36.5%
WARNING: >30% PF degradation suggests overfitting
```

- OOS Profit Factor: 0.92
- PF degradation: -36.5%
- **OOS verdict: FAIL** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| channel_period | 16 | 1.15 | 132 | 1.00 | 33.3% | $19,841 |
| channel_period | 20 **BASE** | 1.19 | 126 | 1.08 | 34.1% | $24,231 |
| channel_period | 24 | 1.21 | 122 | 1.10 | 34.4% | $26,023 |
| roc_fast | 4 | 1.19 | 126 | 1.08 | 34.1% | $24,231 |
| roc_fast | 5 **BASE** | 1.19 | 126 | 1.08 | 34.1% | $24,231 |
| roc_fast | 6 | 1.19 | 126 | 1.08 | 34.1% | $24,231 |
| roc_med | 12 | 1.19 | 126 | 1.08 | 34.1% | $24,231 |
| roc_med | 15 **BASE** | 1.19 | 126 | 1.08 | 34.1% | $24,231 |
| roc_med | 18 | 1.19 | 126 | 1.08 | 34.1% | $24,231 |
| roc_slow | 24 | 1.20 | 130 | 1.06 | 33.8% | $25,757 |
| roc_slow | 30 **BASE** | 1.19 | 126 | 1.08 | 34.1% | $24,231 |
| roc_slow | 36 | 1.20 | 119 | 0.99 | 33.6% | $23,710 |
| stop_pct | 1.6 | 1.23 | 137 | 0.92 | 28.5% | $26,018 |
| stop_pct | 2.0 **BASE** | 1.19 | 126 | 1.08 | 34.1% | $24,231 |
| stop_pct | 2.4 | 1.15 | 124 | 0.88 | 36.3% | $20,760 |
| target_pct | 4.8 | 1.27 | 146 | 1.27 | 39.7% | $35,943 |
| target_pct | 6.0 **BASE** | 1.19 | 126 | 1.08 | 34.1% | $24,231 |
| target_pct | 7.2 | 1.05 | 119 | 0.80 | 28.6% | $6,577 |

- Variants with PF > 1.0: 12/12
- Worst variant PF: 1.05
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.19 | 1.16 |
| Net P&L | $24,231 | $19,983 |
| Sharpe | 1.08 | 1.00 |
| Costs | $8,496 | $12,744 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | FAIL |
| sensitivity | PASS |
| cost_stress | PASS |

**H019 VALIDATED (3/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## H020: High ATR Regime Trend Following (HARTF)

Research ID: R029  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.31 |
| Sharpe Ratio | 1.01 |
| Total Trades | 68 |
| Win Rate | 32.4% |
| Net P&L | $34,755.08 |
| Gross P&L | $39,229.20 |
| Total Costs | $4,474.12 |
| Max Drawdown | $35,999.62 |
| Max DD Duration | 245 days |
| Avg Trade Duration | 229.5h |
| Expectancy | $511.10/trade |
| Sortino | 9.10 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 3/7**

- [PASS] profit_factor: 1.31 (target: >= 1.3)
- [FAIL] win_rate: 32.4% (target: >= 50%)
- [PASS] sharpe_ratio: 1.01 (target: >= 1.0)
- [FAIL] total_trades: 68 (target: >= 100)
- [PASS] expectancy_positive: 511.1 (target: > 0)
- [FAIL] beats_buy_hold: $34,755 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 245 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10      12 25.0%   1.19    0.58 $  1,476.97
2023-08-10 → 2024-02-08       9 66.7%   4.25    3.30 $ 16,969.65
2024-02-08 → 2024-08-09      15 20.0%   0.74   -0.46 $ -7,635.69
2024-08-09 → 2025-02-07      10 50.0%   3.35    2.88 $ 31,145.03
2025-02-07 → 2025-08-09       9 33.3%   1.54    1.06 $ 11,884.30
2025-08-09 → 2026-02-07       8 12.5%   0.54   -1.11 $-11,230.95
------------------------------------------------------------
Windows: 6  |  Profitable: 4/6  |  Total Net: $42,609.32
PF consistency: mean=1.94, std=1.51
```

- Profitable windows: 4/6
- Mean PF across windows: 1.94
- Worst window PF: 0.54
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         52            16
Win Rate                         36.5%        18.8%
Profit Factor                      1.69          0.77
Sharpe Ratio                       1.46         -0.23
Net P&L                   $  46,093.19 $ -10,283.53
Max Drawdown              $  26,647.92 $  35,999.62
Avg Duration                     204.6h        275.0h
-------------------------------------------------------
PF change in-sample → out-of-sample: -54.6%
WARNING: >30% PF degradation suggests overfitting
```

- OOS Profit Factor: 0.77
- PF degradation: -54.6%
- **OOS verdict: FAIL** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| ma_period | 16 | 1.23 | 76 | 0.93 | 30.3% | $28,256 |
| ma_period | 20 **BASE** | 1.31 | 68 | 1.01 | 32.4% | $34,755 |
| ma_period | 24 | 1.22 | 76 | 0.77 | 30.3% | $28,297 |
| atr_period | 11 | 1.34 | 67 | 1.03 | 32.8% | $37,260 |
| atr_period | 14 **BASE** | 1.31 | 68 | 1.01 | 32.4% | $34,755 |
| atr_period | 17 | 1.31 | 69 | 1.02 | 31.9% | $34,609 |
| atr_history | 96 | 1.35 | 67 | 1.05 | 32.8% | $37,913 |
| atr_history | 120 **BASE** | 1.31 | 68 | 1.01 | 32.4% | $34,755 |
| atr_history | 144 | 1.36 | 67 | 1.06 | 32.8% | $38,523 |
| base_stop_pct | 2.4 | 1.13 | 81 | 0.80 | 25.9% | $15,952 |
| base_stop_pct | 3.0 **BASE** | 1.31 | 68 | 1.01 | 32.4% | $34,755 |
| base_stop_pct | 3.6 | 1.18 | 66 | 0.82 | 33.3% | $22,002 |
| base_target_pct | 9.6 | 1.31 | 81 | 1.03 | 37.0% | $37,675 |
| base_target_pct | 12.0 **BASE** | 1.31 | 68 | 1.01 | 32.4% | $34,755 |
| base_target_pct | 14.4 | 1.14 | 66 | 0.62 | 25.8% | $16,172 |
| trend_filter_period | 64 | 1.23 | 76 | 0.86 | 30.3% | $29,617 |
| trend_filter_period | 80 **BASE** | 1.31 | 68 | 1.01 | 32.4% | $34,755 |
| trend_filter_period | 96 | 1.15 | 74 | 0.85 | 29.7% | $18,438 |

- Variants with PF > 1.0: 12/12
- Worst variant PF: 1.13
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.31 | 1.29 |
| Net P&L | $34,755 | $32,518 |
| Sharpe | 1.01 | 0.97 |
| Costs | $4,474 | $6,711 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | FAIL |
| sensitivity | PASS |
| cost_stress | PASS |

**H020 VALIDATED (3/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## H021: Trending Strength Continuation (TSC)

Research ID: R035  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.42 |
| Sharpe Ratio | 1.26 |
| Total Trades | 104 |
| Win Rate | 36.5% |
| Net P&L | $42,233.56 |
| Gross P&L | $49,384.09 |
| Total Costs | $7,150.53 |
| Max Drawdown | $14,909.58 |
| Max DD Duration | 256 days |
| Avg Trade Duration | 80.7h |
| Expectancy | $406.09/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 4/7**

- [PASS] profit_factor: 1.42 (target: >= 1.3)
- [FAIL] win_rate: 36.5% (target: >= 50%)
- [PASS] sharpe_ratio: 1.26 (target: >= 1.0)
- [PASS] total_trades: 104 (target: >= 100)
- [PASS] expectancy_positive: 406.09 (target: > 0)
- [FAIL] beats_buy_hold: $42,234 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 256 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10      14 35.7%   1.56    1.14 $  2,755.09
2023-08-10 → 2024-02-08      18 50.0%   2.83    3.08 $ 11,818.90
2024-02-08 → 2024-08-09      19 26.3%   0.87    0.01 $ -2,561.70
2024-08-09 → 2025-02-07      21 42.9%   1.93    2.26 $ 20,056.73
2025-02-07 → 2025-08-09      16 31.2%   1.35    0.79 $  7,585.65
2025-08-09 → 2026-02-07      14 21.4%   0.79   -0.62 $ -4,994.57
------------------------------------------------------------
Windows: 6  |  Profitable: 4/6  |  Total Net: $34,660.09
PF consistency: mean=1.56, std=0.76
```

- Profitable windows: 4/6
- Mean PF across windows: 1.56
- Worst window PF: 0.79
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         76            28
Win Rate                         38.2%        32.1%
Profit Factor                      1.48          1.34
Sharpe Ratio                       1.48          0.71
Net P&L                   $  28,236.48 $  13,997.07
Max Drawdown              $  14,909.58 $  12,614.81
Avg Duration                      75.7h         94.1h
-------------------------------------------------------
PF change in-sample → out-of-sample: -9.3%
Out-of-sample PF >= 1.2 — edge appears robust
```

- OOS Profit Factor: 1.34
- PF degradation: -9.3%
- **OOS verdict: PASS** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| channel_period | 16 | 1.31 | 111 | 1.24 | 36.0% | $34,292 |
| channel_period | 20 **BASE** | 1.42 | 104 | 1.26 | 36.5% | $42,234 |
| channel_period | 24 | 1.41 | 98 | 1.25 | 36.7% | $38,957 |
| adx_period | 11 | 1.24 | 113 | 0.96 | 33.6% | $26,455 |
| adx_period | 14 **BASE** | 1.42 | 104 | 1.26 | 36.5% | $42,234 |
| adx_period | 17 | 1.10 | 102 | 0.53 | 30.4% | $10,724 |
| adx_threshold | 20 | 1.35 | 111 | 1.14 | 35.1% | $37,621 |
| adx_threshold | 25 **BASE** | 1.42 | 104 | 1.26 | 36.5% | $42,234 |
| adx_threshold | 30 | 1.29 | 100 | 1.06 | 35.0% | $28,604 |
| stop_pct | 1.6 | 1.51 | 112 | 1.28 | 32.1% | $45,327 |
| stop_pct | 2.0 **BASE** | 1.42 | 104 | 1.26 | 36.5% | $42,234 |
| stop_pct | 2.4 | 1.42 | 103 | 1.32 | 40.8% | $46,799 |
| target_pct | 4.8 | 1.31 | 119 | 1.22 | 40.3% | $32,955 |
| target_pct | 6.0 **BASE** | 1.42 | 104 | 1.26 | 36.5% | $42,234 |
| target_pct | 7.2 | 1.11 | 98 | 0.73 | 28.6% | $11,634 |

- Variants with PF > 1.0: 10/10
- Worst variant PF: 1.10
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.42 | 1.38 |
| Net P&L | $42,234 | $38,658 |
| Sharpe | 1.26 | 1.19 |
| Costs | $7,151 | $10,726 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | PASS |
| sensitivity | PASS |
| cost_stress | PASS |

**H021 VALIDATED (4/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## H022: Acceleration Breakout With Volume Confirmation (ABVC)

Research ID: R037  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.29 |
| Sharpe Ratio | 1.19 |
| Total Trades | 129 |
| Win Rate | 34.9% |
| Net P&L | $35,731.79 |
| Gross P&L | $44,390.81 |
| Total Costs | $8,659.02 |
| Max Drawdown | $24,349.46 |
| Max DD Duration | 285 days |
| Avg Trade Duration | 71.6h |
| Expectancy | $276.99/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 3/7**

- [FAIL] profit_factor: 1.29 (target: >= 1.3)
- [FAIL] win_rate: 34.9% (target: >= 50%)
- [PASS] sharpe_ratio: 1.19 (target: >= 1.0)
- [PASS] total_trades: 129 (target: >= 100)
- [PASS] expectancy_positive: 276.99 (target: > 0)
- [FAIL] beats_buy_hold: $35,732 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 285 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10      20 40.0%   1.52    1.38 $  3,644.52
2023-08-10 → 2024-02-08      21 57.1%   3.36    3.76 $ 15,815.72
2024-02-08 → 2024-08-09      24 29.2%   1.05    0.45 $  1,182.63
2024-08-09 → 2025-02-07      28 28.6%   1.02    0.40 $    616.99
2025-02-07 → 2025-08-09      19 26.3%   1.10    0.20 $  2,600.35
2025-08-09 → 2026-02-07      16 25.0%   1.02   -0.17 $    612.82
------------------------------------------------------------
Windows: 6  |  Profitable: 6/6  |  Total Net: $24,473.04
PF consistency: mean=1.51, std=0.93
```

- Profitable windows: 6/6
- Mean PF across windows: 1.51
- Worst window PF: 1.02
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         97            32
Win Rate                         36.1%        31.2%
Profit Factor                      1.27          1.35
Sharpe Ratio                       1.42          0.65
Net P&L                   $  21,116.06 $  15,887.02
Max Drawdown              $  15,965.51 $  17,085.41
Avg Duration                      65.0h         91.0h
-------------------------------------------------------
PF change in-sample → out-of-sample: +6.0%
Out-of-sample PF >= 1.2 — edge appears robust
```

- OOS Profit Factor: 1.35
- PF degradation: +6.0%
- **OOS verdict: PASS** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| channel_period | 12 | 1.27 | 133 | 1.17 | 34.6% | $34,810 |
| channel_period | 15 **BASE** | 1.29 | 129 | 1.19 | 34.9% | $35,732 |
| channel_period | 18 | 1.35 | 117 | 1.27 | 35.9% | $39,134 |
| vol_period | 16 | 1.19 | 136 | 0.99 | 33.1% | $26,288 |
| vol_period | 20 **BASE** | 1.29 | 129 | 1.19 | 34.9% | $35,732 |
| vol_period | 24 | 1.31 | 125 | 1.21 | 35.2% | $36,952 |
| vol_mult | 1.2 | 1.20 | 147 | 1.06 | 33.3% | $29,363 |
| vol_mult | 1.5 **BASE** | 1.29 | 129 | 1.19 | 34.9% | $35,732 |
| vol_mult | 1.8 | 1.29 | 111 | 1.14 | 35.1% | $30,817 |
| stop_pct | 1.6 | 1.32 | 138 | 1.19 | 30.4% | $36,017 |
| stop_pct | 2.0 **BASE** | 1.29 | 129 | 1.19 | 34.9% | $35,732 |
| stop_pct | 2.4 | 1.25 | 125 | 1.05 | 37.6% | $33,814 |
| target_pct | 4.8 | 1.31 | 145 | 1.30 | 40.0% | $40,185 |
| target_pct | 6.0 **BASE** | 1.29 | 129 | 1.19 | 34.9% | $35,732 |
| target_pct | 7.2 | 1.34 | 113 | 1.30 | 32.7% | $38,749 |

- Variants with PF > 1.0: 10/10
- Worst variant PF: 1.19
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.29 | 1.25 |
| Net P&L | $35,732 | $31,402 |
| Sharpe | 1.19 | 1.11 |
| Costs | $8,659 | $12,989 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | PASS |
| sensitivity | PASS |
| cost_stress | PASS |

**H022 VALIDATED (4/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## Summary

| Strategy | Baseline PF | OOS PF | Walk-Fwd | OOS | Sensitivity | Cost Stress | **Verdict** |
|----------|------------|--------|----------|-----|-------------|-------------|-------------|
| H017 | 2.20 | 2.86 | PASS | PASS | PASS | PASS | **VALIDATED** |
| H018 | 1.30 | 1.54 | FAIL | PASS | FAIL | PASS | **FAILED** |
| H019 | 1.19 | 0.92 | PASS | FAIL | PASS | PASS | **VALIDATED** |
| H020 | 1.31 | 0.77 | PASS | FAIL | PASS | PASS | **VALIDATED** |
| H021 | 1.42 | 1.34 | PASS | PASS | PASS | PASS | **VALIDATED** |
| H022 | 1.29 | 1.35 | PASS | PASS | PASS | PASS | **VALIDATED** |
