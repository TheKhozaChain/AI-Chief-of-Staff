# Walk-Forward Validation Report (Queue)

**Date:** 2026-02-12 13:26  
**Data:** BTCUSD 1H, 26,279 bars  
**Period:** 2023-02-08 → 2026-02-07  
**Base cost:** 0.1%  |  **Stress cost:** 0.15%

---


## H007: Multi-Asset Momentum

Research ID: R010  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.53 |
| Sharpe Ratio | 1.15 |
| Total Trades | 82 |
| Win Rate | 24.4% |
| Net P&L | $47,329.35 |
| Gross P&L | $52,715.89 |
| Total Costs | $5,386.54 |
| Max Drawdown | $17,737.36 |
| Max DD Duration | 199 days |
| Avg Trade Duration | 134.4h |
| Expectancy | $577.19/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 4/7**

- [PASS] profit_factor: 1.53 (target: >= 1.3)
- [FAIL] win_rate: 24.4% (target: >= 50%)
- [PASS] sharpe_ratio: 1.15 (target: >= 1.0)
- [FAIL] total_trades: 82 (target: >= 100)
- [PASS] expectancy_positive: 577.19 (target: > 0)
- [PASS] beats_buy_hold: $47,329 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 199 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10      12 25.0%   1.73    1.14 $  3,867.38
2023-08-10 → 2024-02-08      15 33.3%   2.48    1.80 $ 10,775.81
2024-02-08 → 2024-08-09      16 31.2%   2.20    2.02 $ 18,796.56
2024-08-09 → 2025-02-07      15 26.7%   1.88    1.51 $ 17,073.18
2025-02-07 → 2025-08-09      14 21.4%   1.60    0.89 $ 13,038.21
2025-08-09 → 2026-02-07       7  0.0%   0.00 -1664862760005527.75 $-15,255.92
------------------------------------------------------------
Windows: 6  |  Profitable: 5/6  |  Total Net: $48,295.22
PF consistency: mean=1.65, std=0.87
```

- Profitable windows: 5/6
- Mean PF across windows: 1.65
- Worst window PF: 0.00
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         63            19
Win Rate                         27.0%        15.8%
Profit Factor                      1.82          1.04
Sharpe Ratio                       1.48          0.10
Net P&L                   $  45,863.73 $   1,465.62
Max Drawdown              $  12,489.48 $  17,737.36
Avg Duration                     121.2h        178.1h
-------------------------------------------------------
PF change in-sample → out-of-sample: -42.7%
WARNING: >30% PF degradation suggests overfitting
```

- OOS Profit Factor: 1.04
- PF degradation: -42.7%
- **OOS verdict: FAIL** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| roc_period | 24 | 1.23 | 89 | 0.57 | 19.1% | $22,378 |
| roc_period | 30 **BASE** | 1.53 | 82 | 1.15 | 24.4% | $47,329 |
| roc_period | 36 | 1.59 | 80 | 1.21 | 25.0% | $51,283 |
| min_roc | 0.8 | 1.42 | 86 | 1.05 | 23.3% | $40,458 |
| min_roc | 1.0 **BASE** | 1.53 | 82 | 1.15 | 24.4% | $47,329 |
| min_roc | 1.2 | 1.62 | 77 | 1.27 | 26.0% | $52,115 |
| stop_pct | 1.6 | 1.39 | 98 | 0.88 | 18.4% | $34,620 |
| stop_pct | 2.0 **BASE** | 1.53 | 82 | 1.15 | 24.4% | $47,329 |
| stop_pct | 2.4 | 1.35 | 79 | 0.94 | 25.3% | $35,388 |
| target_pct | 9.6 | 1.36 | 93 | 0.99 | 25.8% | $34,720 |
| target_pct | 12.0 **BASE** | 1.53 | 82 | 1.15 | 24.4% | $47,329 |
| target_pct | 14.4 | 1.36 | 81 | 0.77 | 18.5% | $32,554 |
| aux_timeframe_hours | 3 | 1.06 | 107 | 0.29 | 16.8% | $7,061 |
| aux_timeframe_hours | 4 **BASE** | 1.53 | 82 | 1.15 | 24.4% | $47,329 |
| aux_timeframe_hours | 5 | 1.16 | 76 | 0.45 | 18.4% | $13,379 |

- Variants with PF > 1.0: 10/10
- Worst variant PF: 1.06
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.53 | 1.49 |
| Net P&L | $47,329 | $44,636 |
| Sharpe | 1.15 | 1.10 |
| Costs | $5,387 | $8,080 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | FAIL |
| sensitivity | PASS |
| cost_stress | PASS |

**H007 VALIDATED (3/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## H008: Adaptive Momentum Burst (AMB)

Research ID: R012  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.56 |
| Sharpe Ratio | 0.65 |
| Total Trades | 35 |
| Win Rate | 22.9% |
| Net P&L | $23,321.80 |
| Gross P&L | $25,833.69 |
| Total Costs | $2,511.89 |
| Max Drawdown | $12,399.97 |
| Max DD Duration | 194 days |
| Avg Trade Duration | 148.0h |
| Expectancy | $666.34/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 2/7**

- [PASS] profit_factor: 1.56 (target: >= 1.3)
- [FAIL] win_rate: 22.9% (target: >= 50%)
- [FAIL] sharpe_ratio: 0.65 (target: >= 1.0)
- [FAIL] total_trades: 35 (target: >= 100)
- [PASS] expectancy_positive: 666.34 (target: > 0)
- [FAIL] beats_buy_hold: $23,322 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 194 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10       4 25.0%   1.67    0.73 $  1,243.85
2023-08-10 → 2024-02-08       4 25.0%   1.96    0.71 $  2,017.16
2024-02-08 → 2024-08-09       6 33.3%   2.32    1.38 $  7,653.13
2024-08-09 → 2025-02-07       7 28.6%   2.47    1.31 $ 12,144.56
2025-02-07 → 2025-08-09       7 28.6%   1.57    0.72 $  5,874.61
2025-08-09 → 2026-02-07       6  0.0%   0.00 -2184735479690122.25 $-12,399.97
------------------------------------------------------------
Windows: 6  |  Profitable: 5/6  |  Total Net: $16,533.33
PF consistency: mean=1.67, std=0.89
```

- Profitable windows: 5/6
- Mean PF across windows: 1.67
- Worst window PF: 0.00
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         22            12
Win Rate                         27.3%        16.7%
Profit Factor                      2.20          1.13
Sharpe Ratio                       0.94          0.17
Net P&L                   $  22,439.46 $   2,658.39
Max Drawdown              $   5,805.42 $  12,399.97
Avg Duration                     124.9h        183.0h
-------------------------------------------------------
PF change in-sample → out-of-sample: -48.8%
WARNING: >30% PF degradation suggests overfitting
```

- OOS Profit Factor: 1.13
- PF degradation: -48.8%
- **OOS verdict: FAIL** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| bb_period | 16 | 1.24 | 38 | 0.32 | 18.4% | $11,301 |
| bb_period | 20 **BASE** | 1.56 | 35 | 0.65 | 22.9% | $23,322 |
| bb_period | 24 | 1.10 | 31 | 0.36 | 19.4% | $3,940 |
| bb_std | 1.6 | 1.26 | 40 | 0.46 | 20.0% | $13,271 |
| bb_std | 2.0 **BASE** | 1.56 | 35 | 0.65 | 22.9% | $23,322 |
| bb_std | 2.4 | 2.07 | 28 | 0.92 | 28.6% | $33,418 |
| squeeze_lookback | 40 | 1.00 | 36 | 0.16 | 16.7% | $-128 |
| squeeze_lookback | 50 **BASE** | 1.56 | 35 | 0.65 | 22.9% | $23,322 |
| squeeze_lookback | 60 | 1.12 | 37 | 0.36 | 18.9% | $5,655 |
| squeeze_pct | 16 | 0.97 | 31 | -0.20 | 12.9% | $-1,078 |
| squeeze_pct | 20 **BASE** | 1.56 | 35 | 0.65 | 22.9% | $23,322 |
| squeeze_pct | 24 | 1.48 | 38 | 0.74 | 23.7% | $21,582 |
| min_squeeze_bars | 2 | 1.48 | 39 | 0.70 | 23.1% | $21,926 |
| min_squeeze_bars | 3 **BASE** | 1.56 | 35 | 0.65 | 22.9% | $23,322 |
| min_squeeze_bars | 4 | 1.25 | 31 | 0.36 | 19.4% | $9,674 |
| ma_period | 40 | 1.48 | 34 | 0.47 | 20.6% | $18,929 |
| ma_period | 50 **BASE** | 1.56 | 35 | 0.65 | 22.9% | $23,322 |
| ma_period | 60 | 1.22 | 34 | 0.24 | 17.6% | $9,079 |
| ma_slope_bars | 4 | 1.41 | 34 | 0.47 | 20.6% | $16,969 |
| ma_slope_bars | 5 **BASE** | 1.56 | 35 | 0.65 | 22.9% | $23,322 |
| ma_slope_bars | 6 | 1.41 | 34 | 0.47 | 20.6% | $16,968 |
| stop_pct | 1.6 | 1.30 | 39 | 0.52 | 17.9% | $12,515 |
| stop_pct | 2.0 **BASE** | 1.56 | 35 | 0.65 | 22.9% | $23,322 |
| stop_pct | 2.4 | 1.38 | 34 | 0.49 | 23.5% | $17,677 |
| target_pct | 9.6 | 1.35 | 38 | 0.47 | 23.7% | $15,492 |
| target_pct | 12.0 **BASE** | 1.56 | 35 | 0.65 | 22.9% | $23,322 |
| target_pct | 14.4 | 1.07 | 35 | 0.40 | 17.1% | $3,024 |

- Variants with PF > 1.0: 16/18
- Worst variant PF: 0.97
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.56 | 1.52 |
| Net P&L | $23,322 | $22,066 |
| Sharpe | 0.65 | 0.62 |
| Costs | $2,512 | $3,768 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | FAIL |
| sensitivity | PASS |
| cost_stress | PASS |

**H008 VALIDATED (3/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## H009: Acceleration Breakout Filter (ABF)

Research ID: R013  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 2.21 |
| Sharpe Ratio | 0.87 |
| Total Trades | 35 |
| Win Rate | 25.7% |
| Net P&L | $37,839.18 |
| Gross P&L | $39,907.74 |
| Total Costs | $2,068.56 |
| Max Drawdown | $9,368.43 |
| Max DD Duration | 202 days |
| Avg Trade Duration | 92.0h |
| Expectancy | $1,081.12/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 2/7**

- [PASS] profit_factor: 2.21 (target: >= 1.3)
- [FAIL] win_rate: 25.7% (target: >= 50%)
- [FAIL] sharpe_ratio: 0.87 (target: >= 1.0)
- [FAIL] total_trades: 35 (target: >= 100)
- [PASS] expectancy_positive: 1081.12 (target: > 0)
- [FAIL] beats_buy_hold: $37,839 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 202 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10       6 16.7%   1.02    0.17 $     55.79
2023-08-10 → 2024-02-08      10 10.0%   0.59   -0.57 $ -2,274.95
2024-02-08 → 2024-08-09       6 33.3%   2.84    1.31 $  9,544.04
2024-08-09 → 2025-02-07       5 40.0%   4.13    1.58 $ 14,503.59
2025-02-07 → 2025-08-09       4 50.0%   6.55    2.11 $ 19,831.91
2025-08-09 → 2026-02-07       4  0.0%   0.00 -2076581011216646.25 $ -9,368.43
------------------------------------------------------------
Windows: 6  |  Profitable: 4/6  |  Total Net: $32,291.95
PF consistency: mean=2.52, std=2.50
```

- Profitable windows: 4/6
- Mean PF across windows: 2.52
- Worst window PF: 0.00
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         28             6
Win Rate                         25.0%        33.3%
Profit Factor                      2.43          2.50
Sharpe Ratio                       0.89          1.10
Net P&L                   $  26,866.45 $  14,036.45
Max Drawdown              $   4,114.36 $   9,368.43
Avg Duration                      85.9h        126.0h
-------------------------------------------------------
PF change in-sample → out-of-sample: +2.9%
Out-of-sample PF >= 1.2 — edge appears robust
```

- OOS Profit Factor: 2.50
- PF degradation: +2.9%
- **OOS verdict: PASS** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| channel_period | 24 | 2.08 | 41 | 1.01 | 26.8% | $42,622 |
| channel_period | 30 **BASE** | 2.21 | 35 | 0.87 | 25.7% | $37,839 |
| channel_period | 36 | 2.19 | 29 | 0.92 | 27.6% | $31,340 |
| roc_short | 4 | 1.55 | 34 | 0.70 | 23.5% | $20,397 |
| roc_short | 5 **BASE** | 2.21 | 35 | 0.87 | 25.7% | $37,839 |
| roc_short | 6 | 1.42 | 35 | 0.44 | 20.0% | $15,071 |
| roc_long | 12 | 1.91 | 42 | 0.99 | 26.2% | $37,415 |
| roc_long | 15 **BASE** | 2.21 | 35 | 0.87 | 25.7% | $37,839 |
| roc_long | 18 | 1.30 | 33 | 0.28 | 18.2% | $11,098 |
| stop_pct | 1.6 | 2.39 | 36 | 0.84 | 22.2% | $38,494 |
| stop_pct | 2.0 **BASE** | 2.21 | 35 | 0.87 | 25.7% | $37,839 |
| stop_pct | 2.4 | 2.38 | 33 | 1.17 | 33.3% | $45,983 |
| target_pct | 9.6 | 1.69 | 36 | 0.57 | 25.0% | $22,444 |
| target_pct | 12.0 **BASE** | 2.21 | 35 | 0.87 | 25.7% | $37,839 |
| target_pct | 14.4 | 2.33 | 31 | 0.78 | 22.6% | $34,323 |

- Variants with PF > 1.0: 10/10
- Worst variant PF: 1.30
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 2.21 | 2.15 |
| Net P&L | $37,839 | $36,805 |
| Sharpe | 0.87 | 0.84 |
| Costs | $2,069 | $3,103 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | PASS |
| sensitivity | PASS |
| cost_stress | PASS |

**H009 VALIDATED (4/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## H010: Multi-Timeframe Breakout Confluence (MTBC)

Research ID: R014  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.33 |
| Sharpe Ratio | 1.16 |
| Total Trades | 107 |
| Win Rate | 50.5% |
| Net P&L | $50,327.36 |
| Gross P&L | $57,403.43 |
| Total Costs | $7,076.06 |
| Max Drawdown | $26,970.89 |
| Max DD Duration | 360 days |
| Avg Trade Duration | 128.7h |
| Expectancy | $470.35/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 6/7**

- [PASS] profit_factor: 1.33 (target: >= 1.3)
- [PASS] win_rate: 50.5% (target: >= 50%)
- [PASS] sharpe_ratio: 1.16 (target: >= 1.0)
- [PASS] total_trades: 107 (target: >= 100)
- [PASS] expectancy_positive: 470.35 (target: > 0)
- [PASS] beats_buy_hold: $50,327 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 360 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10      17 35.3%   0.76   -0.53 $ -2,899.86
2023-08-10 → 2024-02-08      21 61.9%   2.57    3.23 $ 16,615.55
2024-02-08 → 2024-08-09      16 43.8%   0.99    0.33 $   -234.97
2024-08-09 → 2025-02-07      23 56.5%   1.74    2.20 $ 26,216.91
2025-02-07 → 2025-08-09      16 37.5%   0.92   -0.12 $ -3,080.25
2025-08-09 → 2026-02-07       9 44.4%   1.23    0.32 $  4,502.96
------------------------------------------------------------
Windows: 6  |  Profitable: 3/6  |  Total Net: $41,120.34
PF consistency: mean=1.37, std=0.68
```

- Profitable windows: 3/6
- Mean PF across windows: 1.37
- Worst window PF: 0.76
- **Walk-forward verdict: FAIL**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         82            24
Win Rate                         52.4%        45.8%
Profit Factor                      1.47          1.19
Sharpe Ratio                       1.47          0.52
Net P&L                   $  43,164.42 $  10,662.45
Max Drawdown              $  18,435.56 $  15,948.17
Avg Duration                     118.5h        158.7h
-------------------------------------------------------
PF change in-sample → out-of-sample: -18.9%
```

- OOS Profit Factor: 1.19
- PF degradation: -18.9%
- **OOS verdict: FAIL** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| channel_period | 12 | 1.28 | 112 | 1.01 | 49.1% | $44,630 |
| channel_period | 15 **BASE** | 1.33 | 107 | 1.16 | 50.5% | $50,327 |
| channel_period | 18 | 1.43 | 101 | 1.36 | 52.5% | $58,468 |
| trend_ma_period | 72 | 1.24 | 108 | 0.99 | 49.1% | $37,277 |
| trend_ma_period | 90 **BASE** | 1.33 | 107 | 1.16 | 50.5% | $50,327 |
| trend_ma_period | 108 | 1.25 | 99 | 1.00 | 49.5% | $35,822 |
| stop_pct | 3.2 | 1.15 | 115 | 0.75 | 41.7% | $22,949 |
| stop_pct | 4.0 **BASE** | 1.33 | 107 | 1.16 | 50.5% | $50,327 |
| stop_pct | 4.8 | 1.33 | 100 | 1.14 | 55.0% | $49,994 |
| target_pct | 4.8 | 1.08 | 127 | 0.61 | 51.2% | $14,720 |
| target_pct | 6.0 **BASE** | 1.33 | 107 | 1.16 | 50.5% | $50,327 |
| target_pct | 7.2 | 1.29 | 91 | 1.07 | 46.2% | $39,373 |

- Variants with PF > 1.0: 8/8
- Worst variant PF: 1.08
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.33 | 1.31 |
| Net P&L | $50,327 | $46,789 |
| Sharpe | 1.16 | 1.09 |
| Costs | $7,076 | $10,614 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | FAIL |
| out_of_sample | FAIL |
| sensitivity | PASS |
| cost_stress | PASS |

**H010 FAILED VALIDATION (2/4 tests passed)**

**Recommendation:** Archive or refine. Edge not robust enough for live deployment.

---


## Summary

| Strategy | Baseline PF | OOS PF | Walk-Fwd | OOS | Sensitivity | Cost Stress | **Verdict** |
|----------|------------|--------|----------|-----|-------------|-------------|-------------|
| H007 | 1.53 | 1.04 | PASS | FAIL | PASS | PASS | **VALIDATED** |
| H008 | 1.56 | 1.13 | PASS | FAIL | PASS | PASS | **VALIDATED** |
| H009 | 2.21 | 2.50 | PASS | PASS | PASS | PASS | **VALIDATED** |
| H010 | 1.33 | 1.19 | FAIL | FAIL | PASS | PASS | **FAILED** |
