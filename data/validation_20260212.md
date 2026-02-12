# Walk-Forward Validation Report (Queue)

**Date:** 2026-02-12 13:54  
**Data:** BTCUSD 1H, 26,279 bars  
**Period:** 2023-02-08 → 2026-02-07  
**Base cost:** 0.1%  |  **Stress cost:** 0.15%

---


## H011: Volume-Confirmed Breakout (VCB)

Research ID: R015  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.33 |
| Sharpe Ratio | 0.83 |
| Total Trades | 90 |
| Win Rate | 21.1% |
| Net P&L | $34,484.41 |
| Gross P&L | $40,583.11 |
| Total Costs | $6,098.70 |
| Max Drawdown | $17,266.25 |
| Max DD Duration | 251 days |
| Avg Trade Duration | 105.8h |
| Expectancy | $383.16/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 2/7**

- [PASS] profit_factor: 1.33 (target: >= 1.3)
- [FAIL] win_rate: 21.1% (target: >= 50%)
- [FAIL] sharpe_ratio: 0.83 (target: >= 1.0)
- [FAIL] total_trades: 90 (target: >= 100)
- [PASS] expectancy_positive: 383.16 (target: > 0)
- [FAIL] beats_buy_hold: $34,484 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 251 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10      13 23.1%   1.08    0.25 $    447.96
2023-08-10 → 2024-02-08      16 31.2%   2.11    1.88 $  9,522.06
2024-02-08 → 2024-08-09      18 16.7%   1.02    0.27 $    409.84
2024-08-09 → 2025-02-07      17 23.5%   1.69    1.24 $ 15,284.85
2025-02-07 → 2025-08-09      15 20.0%   1.56    0.83 $ 12,611.08
2025-08-09 → 2026-02-07      11  9.1%   0.60   -1.01 $ -8,747.12
------------------------------------------------------------
Windows: 6  |  Profitable: 5/6  |  Total Net: $29,528.67
PF consistency: mean=1.34, std=0.54
```

- Profitable windows: 5/6
- Mean PF across windows: 1.34
- Worst window PF: 0.60
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         67            23
Win Rate                         22.4%        17.4%
Profit Factor                      1.47          1.18
Sharpe Ratio                       1.02          0.32
Net P&L                   $  28,549.10 $   7,206.59
Max Drawdown              $  10,548.21 $  17,266.25
Avg Duration                      97.8h        128.2h
-------------------------------------------------------
PF change in-sample → out-of-sample: -19.8%
```

- OOS Profit Factor: 1.18
- PF degradation: -19.8%
- **OOS verdict: FAIL** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| channel_period | 16 | 1.33 | 94 | 0.99 | 22.3% | $36,094 |
| channel_period | 20 **BASE** | 1.33 | 90 | 0.83 | 21.1% | $34,484 |
| channel_period | 24 | 1.29 | 84 | 0.83 | 21.4% | $28,041 |
| vol_period | 16 | 1.18 | 98 | 0.64 | 19.4% | $21,375 |
| vol_period | 20 **BASE** | 1.33 | 90 | 0.83 | 21.1% | $34,484 |
| vol_period | 24 | 1.36 | 89 | 0.85 | 21.3% | $36,482 |
| vol_mult | 1.2 | 1.18 | 101 | 0.70 | 19.8% | $21,436 |
| vol_mult | 1.5 **BASE** | 1.33 | 90 | 0.83 | 21.1% | $34,484 |
| vol_mult | 1.8 | 1.33 | 81 | 0.77 | 21.0% | $30,472 |
| stop_pct | 1.6 | 1.56 | 95 | 1.06 | 20.0% | $49,933 |
| stop_pct | 2.0 **BASE** | 1.33 | 90 | 0.83 | 21.1% | $34,484 |
| stop_pct | 2.4 | 1.32 | 84 | 0.94 | 25.0% | $35,793 |
| target_pct | 9.6 | 1.13 | 93 | 0.73 | 23.7% | $13,491 |
| target_pct | 12.0 **BASE** | 1.33 | 90 | 0.83 | 21.1% | $34,484 |
| target_pct | 14.4 | 1.35 | 73 | 0.80 | 19.2% | $28,210 |

- Variants with PF > 1.0: 10/10
- Worst variant PF: 1.13
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.33 | 1.30 |
| Net P&L | $34,484 | $31,435 |
| Sharpe | 0.83 | 0.78 |
| Costs | $6,099 | $9,148 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | FAIL |
| sensitivity | PASS |
| cost_stress | PASS |

**H011 VALIDATED (3/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## H012: Dual Momentum Consensus (DMC)

Research ID: R016  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.23 |
| Sharpe Ratio | 1.04 |
| Total Trades | 134 |
| Win Rate | 33.6% |
| Net P&L | $30,033.29 |
| Gross P&L | $39,112.01 |
| Total Costs | $9,078.73 |
| Max Drawdown | $21,670.86 |
| Max DD Duration | 323 days |
| Avg Trade Duration | 72.5h |
| Expectancy | $224.13/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 3/7**

- [FAIL] profit_factor: 1.23 (target: >= 1.3)
- [FAIL] win_rate: 33.6% (target: >= 50%)
- [PASS] sharpe_ratio: 1.04 (target: >= 1.0)
- [PASS] total_trades: 134 (target: >= 100)
- [PASS] expectancy_positive: 224.13 (target: > 0)
- [FAIL] beats_buy_hold: $30,033 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 323 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10      20 40.0%   1.59    1.38 $  4,072.87
2023-08-10 → 2024-02-08      23 52.2%   2.68    3.26 $ 14,158.17
2024-02-08 → 2024-08-09      25 24.0%   0.80   -0.21 $ -4,951.94
2024-08-09 → 2025-02-07      26 38.5%   1.67    1.87 $ 18,340.59
2025-02-07 → 2025-08-09      21 23.8%   0.94   -0.19 $ -1,885.01
2025-08-09 → 2026-02-07      19 21.1%   0.79   -0.80 $ -6,697.21
------------------------------------------------------------
Windows: 6  |  Profitable: 3/6  |  Total Net: $23,037.48
PF consistency: mean=1.41, std=0.73
```

- Profitable windows: 3/6
- Mean PF across windows: 1.41
- Worst window PF: 0.79
- **Walk-forward verdict: FAIL**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         97            37
Win Rate                         36.1%        27.0%
Profit Factor                      1.37          1.07
Sharpe Ratio                       1.42          0.11
Net P&L                   $  27,231.83 $   4,072.74
Max Drawdown              $  21,670.86 $  20,749.13
Avg Duration                      68.1h         83.4h
-------------------------------------------------------
PF change in-sample → out-of-sample: -21.6%
```

- OOS Profit Factor: 1.07
- PF degradation: -21.6%
- **OOS verdict: FAIL** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| channel_period | 16 | 1.12 | 144 | 0.85 | 31.9% | $17,453 |
| channel_period | 20 **BASE** | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| channel_period | 24 | 1.14 | 126 | 0.98 | 33.3% | $18,219 |
| roc_fast | 2 | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| roc_fast | 3 **BASE** | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| roc_fast | 4 | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| roc_med | 8 | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| roc_med | 10 **BASE** | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| roc_med | 12 | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| roc_slow | 16 | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| roc_slow | 20 **BASE** | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| roc_slow | 24 | 1.20 | 130 | 1.06 | 33.8% | $25,757 |
| stop_pct | 1.6 | 1.17 | 147 | 0.77 | 27.2% | $21,132 |
| stop_pct | 2.0 **BASE** | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| stop_pct | 2.4 | 1.16 | 132 | 0.81 | 35.6% | $24,162 |
| target_pct | 4.8 | 1.22 | 156 | 1.13 | 38.5% | $31,832 |
| target_pct | 6.0 **BASE** | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| target_pct | 7.2 | 1.03 | 124 | 0.77 | 28.2% | $4,313 |

- Variants with PF > 1.0: 12/12
- Worst variant PF: 1.03
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.23 | 1.19 |
| Net P&L | $30,033 | $25,494 |
| Sharpe | 1.04 | 0.95 |
| Costs | $9,079 | $13,618 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | FAIL |
| out_of_sample | FAIL |
| sensitivity | PASS |
| cost_stress | PASS |

**H012 FAILED VALIDATION (2/4 tests passed)**

**Recommendation:** Archive or refine. Edge not robust enough for live deployment.

---


## H013: Trend Strength Breakout (TSB)

Research ID: R017  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.50 |
| Sharpe Ratio | 1.12 |
| Total Trades | 67 |
| Win Rate | 29.9% |
| Net P&L | $34,596.12 |
| Gross P&L | $39,080.07 |
| Total Costs | $4,483.95 |
| Max Drawdown | $16,542.81 |
| Max DD Duration | 243 days |
| Avg Trade Duration | 118.6h |
| Expectancy | $516.36/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 3/7**

- [PASS] profit_factor: 1.5 (target: >= 1.3)
- [FAIL] win_rate: 29.9% (target: >= 50%)
- [PASS] sharpe_ratio: 1.12 (target: >= 1.0)
- [FAIL] total_trades: 67 (target: >= 100)
- [PASS] expectancy_positive: 516.36 (target: > 0)
- [FAIL] beats_buy_hold: $34,596 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 243 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10       8 37.5%   2.34    1.49 $  3,992.10
2023-08-10 → 2024-02-08      13 30.8%   1.64    1.32 $  4,581.70
2024-02-08 → 2024-08-09      14 28.6%   1.52    1.12 $  7,262.41
2024-08-09 → 2025-02-07      14 28.6%   1.37    1.24 $  6,840.44
2025-02-07 → 2025-08-09       9 33.3%   2.17    1.44 $ 13,355.04
2025-08-09 → 2026-02-07       7 14.3%   0.73   -0.51 $ -3,749.16
------------------------------------------------------------
Windows: 6  |  Profitable: 5/6  |  Total Net: $32,282.53
PF consistency: mean=1.63, std=0.58
```

- Profitable windows: 5/6
- Mean PF across windows: 1.63
- Worst window PF: 0.73
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         53            14
Win Rate                         30.2%        28.6%
Profit Factor                      1.47          1.54
Sharpe Ratio                       1.23          0.83
Net P&L                   $  22,284.67 $  12,311.45
Max Drawdown              $  14,693.60 $  11,859.91
Avg Duration                     100.7h        186.3h
-------------------------------------------------------
PF change in-sample → out-of-sample: +4.7%
Out-of-sample PF >= 1.2 — edge appears robust
```

- OOS Profit Factor: 1.54
- PF degradation: +4.7%
- **OOS verdict: PASS** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| channel_period | 24 | 1.41 | 69 | 1.05 | 29.0% | $30,036 |
| channel_period | 30 **BASE** | 1.50 | 67 | 1.12 | 29.9% | $34,596 |
| channel_period | 36 | 1.57 | 64 | 1.22 | 31.2% | $37,716 |
| adx_period | 16 | 1.43 | 72 | 0.95 | 27.8% | $32,158 |
| adx_period | 20 **BASE** | 1.50 | 67 | 1.12 | 29.9% | $34,596 |
| adx_period | 24 | 1.32 | 60 | 0.92 | 28.3% | $20,638 |
| adx_threshold | 24 | 1.38 | 72 | 0.95 | 27.8% | $28,462 |
| adx_threshold | 30 **BASE** | 1.50 | 67 | 1.12 | 29.9% | $34,596 |
| adx_threshold | 36 | 1.51 | 62 | 1.00 | 29.0% | $32,776 |
| stop_pct | 1.6 | 1.54 | 72 | 1.02 | 25.0% | $33,054 |
| stop_pct | 2.0 **BASE** | 1.50 | 67 | 1.12 | 29.9% | $34,596 |
| stop_pct | 2.4 | 1.42 | 63 | 1.11 | 33.3% | $31,098 |
| target_pct | 7.2 | 1.36 | 71 | 1.00 | 32.4% | $25,422 |
| target_pct | 9.0 **BASE** | 1.50 | 67 | 1.12 | 29.9% | $34,596 |
| target_pct | 10.8 | 1.39 | 63 | 1.10 | 27.0% | $27,113 |

- Variants with PF > 1.0: 10/10
- Worst variant PF: 1.32
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.50 | 1.45 |
| Net P&L | $34,596 | $32,354 |
| Sharpe | 1.12 | 1.07 |
| Costs | $4,484 | $6,726 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | PASS |
| sensitivity | PASS |
| cost_stress | PASS |

**H013 VALIDATED (4/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## H014: Trend Pullback Entry (TPE)

Research ID: R018  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 2.49 |
| Sharpe Ratio | 1.20 |
| Total Trades | 26 |
| Win Rate | 46.2% |
| Net P&L | $29,597.08 |
| Gross P&L | $31,385.02 |
| Total Costs | $1,787.94 |
| Max Drawdown | $6,203.15 |
| Max DD Duration | 224 days |
| Avg Trade Duration | 61.8h |
| Expectancy | $1,138.35/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 3/7**

- [PASS] profit_factor: 2.49 (target: >= 1.3)
- [FAIL] win_rate: 46.2% (target: >= 50%)
- [PASS] sharpe_ratio: 1.2 (target: >= 1.0)
- [FAIL] total_trades: 26 (target: >= 100)
- [PASS] expectancy_positive: 1138.35 (target: > 0)
- [FAIL] beats_buy_hold: $29,597 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 224 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10       3 66.7%   5.74    2.81 $  2,709.71
2023-08-10 → 2024-02-08       4 25.0%   0.62   -0.10 $   -975.22
2024-02-08 → 2024-08-09       5 20.0%   0.53   -0.58 $ -2,742.70
2024-08-09 → 2025-02-07       8 50.0%   2.79    2.23 $ 12,577.72
2025-02-07 → 2025-08-09       4 50.0%   1.62    0.39 $  2,471.13
2025-08-09 → 2026-02-07       1 100.0%    inf    0.00 $  5,207.08
------------------------------------------------------------
Windows: 6  |  Profitable: 4/6  |  Total Net: $19,247.72
PF consistency: mean=inf, std=nan
```

- Profitable windows: 4/6
- Mean PF across windows: inf
- Worst window PF: 0.53
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         21             5
Win Rate                         42.9%        60.0%
Profit Factor                      1.95          4.61
Sharpe Ratio                       1.10          1.58
Net P&L                   $  15,105.26 $  14,491.82
Max Drawdown              $   5,781.88 $   4,015.07
Avg Duration                      56.8h         83.2h
-------------------------------------------------------
PF change in-sample → out-of-sample: +136.4%
Out-of-sample PF >= 1.2 — edge appears robust
```

- OOS Profit Factor: 4.61
- PF degradation: +136.4%
- **OOS verdict: PASS** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| ma_period | 64 | 1.19 | 28 | -0.09 | 25.0% | $5,258 |
| ma_period | 80 **BASE** | 2.49 | 26 | 1.20 | 46.2% | $29,597 |
| ma_period | 96 | 1.08 | 25 | 0.12 | 28.0% | $1,802 |
| ma_slope_bars | 4 | 2.17 | 30 | 1.11 | 43.3% | $28,105 |
| ma_slope_bars | 5 **BASE** | 2.49 | 26 | 1.20 | 46.2% | $29,597 |
| ma_slope_bars | 6 | 2.29 | 24 | 1.13 | 45.8% | $24,062 |
| pullback_pct | 0.8 | 2.16 | 25 | 1.05 | 44.0% | $23,170 |
| pullback_pct | 1.0 **BASE** | 2.49 | 26 | 1.20 | 46.2% | $29,597 |
| pullback_pct | 1.2 | 2.43 | 29 | 1.19 | 44.8% | $31,310 |
| roc_period | 4 | 1.60 | 26 | 0.98 | 42.3% | $14,340 |
| roc_period | 5 **BASE** | 2.49 | 26 | 1.20 | 46.2% | $29,597 |
| roc_period | 6 | 1.83 | 28 | 1.05 | 42.9% | $20,514 |
| min_roc | 0.8 | 2.25 | 34 | 1.24 | 44.1% | $35,061 |
| min_roc | 1.0 **BASE** | 2.49 | 26 | 1.20 | 46.2% | $29,597 |
| min_roc | 1.2 | 1.96 | 24 | 0.90 | 41.7% | $19,197 |
| stop_pct | 1.6 | 2.89 | 26 | 1.21 | 42.3% | $31,368 |
| stop_pct | 2.0 **BASE** | 2.49 | 26 | 1.20 | 46.2% | $29,597 |
| stop_pct | 2.4 | 2.81 | 26 | 1.45 | 53.8% | $36,986 |
| target_pct | 4.8 | 2.31 | 26 | 1.15 | 50.0% | $24,245 |
| target_pct | 6.0 **BASE** | 2.49 | 26 | 1.20 | 46.2% | $29,597 |
| target_pct | 7.2 | 2.20 | 25 | 1.03 | 40.0% | $26,938 |

- Variants with PF > 1.0: 14/14
- Worst variant PF: 1.08
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 2.49 | 2.41 |
| Net P&L | $29,597 | $28,703 |
| Sharpe | 1.20 | 1.16 |
| Costs | $1,788 | $2,682 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | PASS |
| sensitivity | PASS |
| cost_stress | PASS |

**H014 VALIDATED (4/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## H015: ATR Regime Adaptive (ARA)

Research ID: R019  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.33 |
| Sharpe Ratio | 1.04 |
| Total Trades | 69 |
| Win Rate | 31.9% |
| Net P&L | $36,071.12 |
| Gross P&L | $40,568.67 |
| Total Costs | $4,497.54 |
| Max Drawdown | $37,502.65 |
| Max DD Duration | 245 days |
| Avg Trade Duration | 222.0h |
| Expectancy | $522.77/trade |
| Sortino | 8.82 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 3/7**

- [PASS] profit_factor: 1.33 (target: >= 1.3)
- [FAIL] win_rate: 31.9% (target: >= 50%)
- [PASS] sharpe_ratio: 1.04 (target: >= 1.0)
- [FAIL] total_trades: 69 (target: >= 100)
- [PASS] expectancy_positive: 522.77 (target: > 0)
- [FAIL] beats_buy_hold: $36,071 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 245 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10      12 25.0%   1.26    0.69 $  1,909.82
2023-08-10 → 2024-02-08       9 66.7%   4.43    3.39 $ 17,181.97
2024-02-08 → 2024-08-09      15 26.7%   1.01    0.39 $    316.56
2024-08-09 → 2025-02-07      11 45.5%   2.83    2.38 $ 28,710.02
2025-02-07 → 2025-08-09       8 37.5%   1.68    1.17 $ 13,667.64
2025-08-09 → 2026-02-07       8  0.0%   0.00  -16.90 $-23,138.70
------------------------------------------------------------
Windows: 6  |  Profitable: 5/6  |  Total Net: $38,647.33
PF consistency: mean=1.87, std=1.56
```

- Profitable windows: 5/6
- Mean PF across windows: 1.87
- Worst window PF: 0.00
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         52            17
Win Rate                         36.5%        17.6%
Profit Factor                      1.76          0.76
Sharpe Ratio                       1.54         -0.30
Net P&L                   $  48,707.22 $ -10,972.04
Max Drawdown              $  23,935.60 $  37,502.65
Avg Duration                     200.6h        245.9h
-------------------------------------------------------
PF change in-sample → out-of-sample: -57.0%
WARNING: >30% PF degradation suggests overfitting
```

- OOS Profit Factor: 0.76
- PF degradation: -57.0%
- **OOS verdict: FAIL** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| ma_period | 16 | 1.42 | 75 | 1.10 | 32.0% | $48,842 |
| ma_period | 20 **BASE** | 1.33 | 69 | 1.04 | 31.9% | $36,071 |
| ma_period | 24 | 1.24 | 76 | 0.81 | 30.3% | $30,131 |
| atr_period | 16 | 1.31 | 69 | 1.02 | 31.9% | $34,424 |
| atr_period | 20 **BASE** | 1.33 | 69 | 1.04 | 31.9% | $36,071 |
| atr_period | 24 | 1.36 | 68 | 1.08 | 32.4% | $38,724 |
| atr_history | 72 | 1.29 | 71 | 0.96 | 31.0% | $32,675 |
| atr_history | 90 **BASE** | 1.33 | 69 | 1.04 | 31.9% | $36,071 |
| atr_history | 108 | 1.32 | 69 | 1.03 | 31.9% | $35,533 |
| base_stop_pct | 2.4 | 1.18 | 81 | 0.84 | 25.9% | $20,438 |
| base_stop_pct | 3.0 **BASE** | 1.33 | 69 | 1.04 | 31.9% | $36,071 |
| base_stop_pct | 3.6 | 1.23 | 65 | 0.88 | 33.8% | $27,835 |
| base_target_pct | 9.6 | 1.30 | 84 | 1.02 | 35.7% | $36,603 |
| base_target_pct | 12.0 **BASE** | 1.33 | 69 | 1.04 | 31.9% | $36,071 |
| base_target_pct | 14.4 | 1.10 | 69 | 0.58 | 24.6% | $12,195 |
| trend_filter_period | 64 | 1.20 | 78 | 0.84 | 29.5% | $27,034 |
| trend_filter_period | 80 **BASE** | 1.33 | 69 | 1.04 | 31.9% | $36,071 |
| trend_filter_period | 96 | 1.18 | 73 | 0.90 | 30.1% | $22,607 |

- Variants with PF > 1.0: 12/12
- Worst variant PF: 1.10
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.33 | 1.30 |
| Net P&L | $36,071 | $33,822 |
| Sharpe | 1.04 | 1.00 |
| Costs | $4,498 | $6,746 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | FAIL |
| sensitivity | PASS |
| cost_stress | PASS |

**H015 VALIDATED (3/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## H016: Consecutive Momentum Filter (CMF)

Research ID: R020  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.64 |
| Sharpe Ratio | 0.77 |
| Total Trades | 48 |
| Win Rate | 22.9% |
| Net P&L | $36,495.62 |
| Gross P&L | $39,991.95 |
| Total Costs | $3,496.33 |
| Max Drawdown | $9,887.27 |
| Max DD Duration | 232 days |
| Avg Trade Duration | 140.7h |
| Expectancy | $760.33/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 2/7**

- [PASS] profit_factor: 1.64 (target: >= 1.3)
- [FAIL] win_rate: 22.9% (target: >= 50%)
- [FAIL] sharpe_ratio: 0.77 (target: >= 1.0)
- [FAIL] total_trades: 48 (target: >= 100)
- [PASS] expectancy_positive: 760.33 (target: > 0)
- [FAIL] beats_buy_hold: $36,496 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 232 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10       5 40.0%   2.33    0.92 $  2,210.66
2023-08-10 → 2024-02-08       7 28.6%   0.86    0.27 $   -598.67
2024-02-08 → 2024-08-09       8 25.0%   1.69    0.90 $  5,825.43
2024-08-09 → 2025-02-07      10 20.0%   1.44    0.59 $  5,915.04
2025-02-07 → 2025-08-09      10 30.0%   2.51    1.63 $ 20,941.38
2025-08-09 → 2026-02-07       8 12.5%   0.90   -0.32 $ -1,484.42
------------------------------------------------------------
Windows: 6  |  Profitable: 4/6  |  Total Net: $32,809.40
PF consistency: mean=1.62, std=0.70
```

- Profitable windows: 4/6
- Mean PF across windows: 1.62
- Worst window PF: 0.86
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         32            16
Win Rate                         21.9%        25.0%
Profit Factor                      1.47          1.94
Sharpe Ratio                       0.69          1.00
Net P&L                   $  14,494.45 $  23,272.45
Max Drawdown              $   9,784.93 $   9,887.27
Avg Duration                     142.0h        136.8h
-------------------------------------------------------
PF change in-sample → out-of-sample: +31.6%
Out-of-sample PF >= 1.2 — edge appears robust
```

- OOS Profit Factor: 1.94
- PF degradation: +31.6%
- **OOS verdict: PASS** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| channel_period | 16 | 1.53 | 50 | 0.70 | 22.0% | $32,069 |
| channel_period | 20 **BASE** | 1.64 | 48 | 0.77 | 22.9% | $36,496 |
| channel_period | 24 | 1.41 | 46 | 0.65 | 21.7% | $23,374 |
| consec_bars | 3 | 1.35 | 73 | 0.84 | 21.9% | $30,172 |
| consec_bars | 4 **BASE** | 1.64 | 48 | 0.77 | 22.9% | $36,496 |
| consec_bars | 5 | 1.43 | 25 | 0.38 | 20.0% | $14,374 |
| stop_pct | 1.6 | 1.47 | 50 | 0.60 | 18.0% | $24,871 |
| stop_pct | 2.0 **BASE** | 1.64 | 48 | 0.77 | 22.9% | $36,496 |
| stop_pct | 2.4 | 1.44 | 47 | 0.57 | 23.4% | $28,346 |
| target_pct | 9.6 | 1.38 | 51 | 0.71 | 25.5% | $22,785 |
| target_pct | 12.0 **BASE** | 1.64 | 48 | 0.77 | 22.9% | $36,496 |
| target_pct | 14.4 | 1.05 | 43 | 0.36 | 16.3% | $2,658 |

- Variants with PF > 1.0: 8/8
- Worst variant PF: 1.05
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.64 | 1.60 |
| Net P&L | $36,496 | $34,747 |
| Sharpe | 0.77 | 0.73 |
| Costs | $3,496 | $5,245 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | PASS |
| sensitivity | PASS |
| cost_stress | PASS |

**H016 VALIDATED (4/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## Summary

| Strategy | Baseline PF | OOS PF | Walk-Fwd | OOS | Sensitivity | Cost Stress | **Verdict** |
|----------|------------|--------|----------|-----|-------------|-------------|-------------|
| H011 | 1.33 | 1.18 | PASS | FAIL | PASS | PASS | **VALIDATED** |
| H012 | 1.23 | 1.07 | FAIL | FAIL | PASS | PASS | **FAILED** |
| H013 | 1.50 | 1.54 | PASS | PASS | PASS | PASS | **VALIDATED** |
| H014 | 2.49 | 4.61 | PASS | PASS | PASS | PASS | **VALIDATED** |
| H015 | 1.33 | 0.76 | PASS | FAIL | PASS | PASS | **VALIDATED** |
| H016 | 1.64 | 1.94 | PASS | PASS | PASS | PASS | **VALIDATED** |
