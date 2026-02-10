# Walk-Forward Validation Report

**Date:** 2026-02-11 09:42  
**Data:** BTCUSD 1H, 26,279 bars  
**Period:** 2023-02-08 → 2026-02-07  
**Base cost:** 0.1%  |  **Stress cost:** 0.15%

---


## H004: Volatility-Adjusted Trend Following

Research ID: R007  |  Timeframe: 4H  |  Bars: 6,571

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.40 |
| Sharpe Ratio | 1.18 |
| Total Trades | 87 |
| Win Rate | 44.8% |
| Net P&L | $51,799.23 |
| Gross P&L | $57,817.51 |
| Total Costs | $6,018.28 |
| Max Drawdown | $19,596.77 |
| Max DD Duration | 251 days |
| Avg Trade Duration | 165.7h |
| Expectancy | $595.39/trade |
| Sortino | 5.94 |
| Buy & Hold | $47,039.94 (202.7%) |

**Live Readiness: 4/7**

- [PASS] profit_factor: 1.4 (target: >= 1.3)
- [FAIL] win_rate: 44.8% (target: >= 50%)
- [PASS] sharpe_ratio: 1.18 (target: >= 1.0)
- [FAIL] total_trades: 87 (target: >= 100)
- [PASS] expectancy_positive: 595.39 (target: > 0)
- [PASS] beats_buy_hold: $51,799 vs $47,040 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 251 days (target: < 30 days)

### 2. Walk-Forward Validation (1095 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-10      12 33.3%   1.12    0.41 $  1,111.36
2023-08-10 → 2024-02-08      16 62.5%   2.84    3.16 $ 16,886.02
2024-02-08 → 2024-08-09      13 38.5%   0.97    0.19 $   -747.71
2024-08-09 → 2025-02-07      13 53.8%   2.56    2.45 $ 28,402.98
2025-02-07 → 2025-08-09      14 42.9%   1.28    0.92 $  7,864.02
2025-08-09 → 2026-02-07      13 30.8%   0.74   -0.80 $ -7,614.75
------------------------------------------------------------
Windows: 6  |  Profitable: 4/6  |  Total Net: $45,901.93
PF consistency: mean=1.58, std=0.88
```

- Profitable windows: 4/6
- Mean PF across windows: 1.58
- Worst window PF: 0.74
- **Walk-forward verdict: PASS**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                              4,599         1,972
Total Trades                         58            28
Win Rate                         48.3%        39.3%
Profit Factor                      1.75          1.09
Sharpe Ratio                       1.54          0.42
Net P&L                   $  50,332.09 $   5,090.75
Max Drawdown              $  19,023.70 $  19,596.77
Avg Duration                     184.8h        124.3h
-------------------------------------------------------
PF change in-sample → out-of-sample: -37.9%
WARNING: >30% PF degradation suggests overfitting
```

- OOS Profit Factor: 1.09
- PF degradation: -37.9%
- **OOS verdict: FAIL** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| ma_period | 24 | 1.38 | 87 | 1.14 | 44.8% | $50,271 |
| ma_period | 30 **BASE** | 1.40 | 87 | 1.18 | 44.8% | $51,799 |
| ma_period | 36 | 1.24 | 91 | 0.90 | 40.7% | $33,680 |
| atr_period | 16 | 1.14 | 82 | 0.70 | 41.5% | $19,265 |
| atr_period | 20 **BASE** | 1.40 | 87 | 1.18 | 44.8% | $51,799 |
| atr_period | 24 | 1.27 | 81 | 0.75 | 40.7% | $33,826 |
| stop_atr_mult | 2.5 | 1.26 | 101 | 0.82 | 37.6% | $36,837 |
| stop_atr_mult | 3.0 **BASE** | 1.40 | 87 | 1.18 | 44.8% | $51,799 |
| stop_atr_mult | 3.5 | 1.43 | 74 | 1.22 | 50.0% | $52,312 |
| target_atr_mult | 5.0 | 1.23 | 100 | 0.90 | 45.0% | $34,278 |
| target_atr_mult | 6.0 **BASE** | 1.40 | 87 | 1.18 | 44.8% | $51,799 |
| target_atr_mult | 7.0 | 1.17 | 72 | 0.74 | 38.9% | $20,860 |
| trend_filter_period | 60 | 1.03 | 90 | 0.45 | 40.0% | $5,413 |
| trend_filter_period | 80 **BASE** | 1.40 | 87 | 1.18 | 44.8% | $51,799 |
| trend_filter_period | 100 | 1.44 | 83 | 1.28 | 44.6% | $50,537 |

- Variants with PF > 1.0: 10/10
- Worst variant PF: 1.03
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.40 | 1.37 |
| Net P&L | $51,799 | $48,790 |
| Sharpe | 1.18 | 1.13 |
| Costs | $6,018 | $9,027 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | PASS |
| out_of_sample | FAIL |
| sensitivity | PASS |
| cost_stress | PASS |

**H004 VALIDATED (3/4 tests passed)**

**Recommendation:** Proceed to paper trading evaluation.

---


## H005: Donchian Channel Breakout

Research ID: R009  |  Timeframe: 4H  |  Bars: 6,571

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
| channel_period | 15 | 1.10 | 161 | 0.76 | 31.1% | $16,292 |
| channel_period | 20 **BASE** | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| channel_period | 25 | 1.17 | 123 | 0.97 | 33.3% | $21,056 |
| stop_pct | 1.5 | 1.17 | 148 | 0.70 | 25.7% | $19,889 |
| stop_pct | 2.0 **BASE** | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| stop_pct | 2.5 | 1.12 | 132 | 0.70 | 35.6% | $18,191 |
| target_pct | 5.0 | 1.30 | 148 | 1.23 | 38.5% | $40,544 |
| target_pct | 6.0 **BASE** | 1.23 | 134 | 1.04 | 33.6% | $30,033 |
| target_pct | 7.0 | 0.98 | 126 | 0.65 | 27.8% | $-2,665 |

- Variants with PF > 1.0: 5/6
- Worst variant PF: 0.98
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

**H005 FAILED VALIDATION (2/4 tests passed)**

**Recommendation:** Archive or refine. Edge not robust enough for live deployment.

---


## H006: Daily Timeframe Trend

Research ID: R011  |  Timeframe: 24H  |  Bars: 1,096

### 1. Full-Sample Baseline (0.1% costs)

| Metric | Value |
|--------|-------|
| Profit Factor | 1.86 |
| Sharpe Ratio | 0.79 |
| Total Trades | 20 |
| Win Rate | 35.0% |
| Net P&L | $41,993.58 |
| Gross P&L | $43,172.41 |
| Total Costs | $1,178.82 |
| Max Drawdown | $20,559.74 |
| Max DD Duration | 256 days |
| Avg Trade Duration | 877.2h |
| Expectancy | $2,099.68/trade |
| Sortino | 99.00 |
| Buy & Hold | $47,122.46 (203.8%) |

**Live Readiness: 2/7**

- [PASS] profit_factor: 1.86 (target: >= 1.3)
- [FAIL] win_rate: 35.0% (target: >= 50%)
- [FAIL] sharpe_ratio: 0.79 (target: >= 1.0)
- [FAIL] total_trades: 20 (target: >= 100)
- [PASS] expectancy_positive: 2099.68 (target: > 0)
- [FAIL] beats_buy_hold: $41,994 vs $47,122 (target: strategy > buy & hold)
- [FAIL] max_drawdown_duration: 256 days (target: < 30 days)

### 2. Walk-Forward Validation (182 bars/window)

```
Walk-Forward Validation
============================================================
Period                       Trades     WR     PF  Sharpe      Net P&L
------------------------------------------------------------
2023-02-08 → 2023-08-08       3  0.0%   0.00   -7.86 $ -4,360.45
2023-08-09 → 2024-02-06       5 40.0%   2.65    1.63 $  9,192.22
2024-02-07 → 2024-08-06       4  0.0%   0.00 -4547617503095680.00 $-16,169.68
2024-08-07 → 2025-02-04       3 100.0%    inf    6.07 $ 39,977.14
2025-02-05 → 2025-08-05       2 100.0%    inf    4.41 $ 30,507.04
2025-08-06 → 2026-02-03       2  0.0%   0.00    0.00 $-12,692.53
------------------------------------------------------------
Windows: 6  |  Profitable: 3/6  |  Total Net: $46,453.74
PF consistency: mean=inf, std=nan
```

- Profitable windows: 3/6
- Mean PF across windows: inf
- Worst window PF: 0.00
- **Walk-forward verdict: FAIL**

### 3. In-Sample vs Out-of-Sample (70/30 split)

```
In-Sample vs Out-of-Sample
=======================================================
Metric                        In-Sample Out-of-Sample
-------------------------------------------------------
Bars                                767           329
Total Trades                         17             4
Win Rate                         35.3%        25.0%
Profit Factor                      1.92          1.13
Sharpe Ratio                       0.90          0.22
Net P&L                   $  33,810.92 $   2,662.70
Max Drawdown              $  20,559.74 $  19,898.91
Avg Duration                     710.1h        996.0h
-------------------------------------------------------
PF change in-sample → out-of-sample: -41.0%
WARNING: >30% PF degradation suggests overfitting
```

- OOS Profit Factor: 1.13
- PF degradation: -41.0%
- **OOS verdict: FAIL** (need PF >= 1.2, decay < 30%)

### 4. Parameter Sensitivity

| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |
|-----------|-------|----|--------|--------|----|---------|
| fast_period | 3 | 1.60 | 22 | 0.67 | 31.8% | $34,266 |
| fast_period | 5 **BASE** | 1.86 | 20 | 0.79 | 35.0% | $41,994 |
| fast_period | 7 | 1.16 | 25 | 0.50 | 28.0% | $12,551 |
| slow_period | 30 | 1.62 | 21 | 0.73 | 33.3% | $34,598 |
| slow_period | 40 **BASE** | 1.86 | 20 | 0.79 | 35.0% | $41,994 |
| slow_period | 50 | 1.08 | 26 | 0.44 | 26.9% | $6,777 |
| stop_pct | 5.0 | 1.52 | 27 | 0.58 | 25.9% | $31,102 |
| stop_pct | 6.0 **BASE** | 1.86 | 20 | 0.79 | 35.0% | $41,994 |
| stop_pct | 7.0 | 1.66 | 19 | 0.73 | 36.8% | $36,021 |
| target_pct | 20.0 | 1.82 | 23 | 0.89 | 39.1% | $50,512 |
| target_pct | 24.0 **BASE** | 1.86 | 20 | 0.79 | 35.0% | $41,994 |
| target_pct | 28.0 | 1.22 | 26 | 0.60 | 26.9% | $18,903 |

- Variants with PF > 1.0: 8/8
- Worst variant PF: 1.08
- **Sensitivity verdict: PASS**

### 5. Cost Stress Test (0.15% vs 0.1%)

| Metric | Base (0.1%) | Stress (0.15%) |
|--------|------------|----------------|
| Profit Factor | 1.86 | 1.84 |
| Net P&L | $41,994 | $41,404 |
| Sharpe | 0.79 | 0.79 |
| Costs | $1,179 | $1,768 |

- **Cost stress verdict: PASS** (need PF >= 1.15 at 0.15% costs)

### Overall Verdict

| Test | Result |
|------|--------|
| walk_forward | FAIL |
| out_of_sample | FAIL |
| sensitivity | PASS |
| cost_stress | PASS |

**H006 FAILED VALIDATION (2/4 tests passed)**

**Recommendation:** Archive or refine. Edge not robust enough for live deployment.

---


## Summary

| Strategy | Baseline PF | OOS PF | Walk-Fwd | OOS | Sensitivity | Cost Stress | **Verdict** |
|----------|------------|--------|----------|-----|-------------|-------------|-------------|
| H004 | 1.40 | 1.09 | PASS | FAIL | PASS | PASS | **VALIDATED** |
| H005 | 1.23 | 1.07 | FAIL | FAIL | PASS | PASS | **FAILED** |
| H006 | 1.86 | 1.13 | FAIL | FAIL | PASS | PASS | **FAILED** |

### Validated (1)
- **H004**: Ready for paper trading. Baseline PF 1.40, OOS PF 1.09

### Failed Validation (2)
- **H005**: 2/4 tests. Archive or refine.
- **H006**: 2/4 tests. Archive or refine.
