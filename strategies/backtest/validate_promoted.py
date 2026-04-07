#!/usr/bin/env python3
"""
Walk-forward validation for promoted strategies H004, H005, H006.

Runs each strategy through:
1. Full-sample baseline (confirm screen results)
2. Walk-forward rolling windows (stability across regimes)
3. In-sample vs out-of-sample split (overfitting check)
4. Parameter sensitivity (robustness to param changes)
5. Cost stress test (0.15% instead of 0.1%)

Output: Markdown report saved to data/validation_YYYYMMDD.md
"""

import json
import sys
import os
import statistics
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import (
    Backtest, BacktestResult, walk_forward, walk_forward_summary,
    run_in_out_of_sample, in_out_of_sample_summary,
)
from archetypes import VolAdjustedTrend, DonchianBreakout, DailyTrend, ARCHETYPES
from data_loader import load_csv, resample

REPO_ROOT = Path(__file__).parent.parent.parent
DATA_FILE = str(REPO_ROOT / 'data' / 'BTCUSD_1h.csv')
PROMOTED_QUEUE_FILE = REPO_ROOT / 'data' / 'promoted_queue.json'

# Load thresholds from policies/ (single source of truth)
sys.path.insert(0, str(REPO_ROOT / 'scripts'))
try:
    from policy_loader import load_kill_criteria
    _val = load_kill_criteria()['validation']
    COST_PCT = 0.1  # base cost
    COST_STRESS = _val['cost_stress_pct']
except (ImportError, FileNotFoundError):
    COST_PCT = 0.1
    COST_STRESS = 0.15


# ── Strategy configs ─────────────────────────────────────────────

STRATEGIES = {
    'H004': {
        'name': 'Volatility-Adjusted Trend Following',
        'research_id': 'R007',
        'archetype': VolAdjustedTrend,
        'timeframe_hours': 4,  # screened on 4H bars
        'params': {
            'ma_period': 30, 'atr_period': 20,
            'stop_atr_mult': 3.0, 'target_atr_mult': 6.0,
            'trend_filter_period': 80, 'long_only': True,
        },
        'sensitivity': {
            'ma_period': [24, 30, 36],
            'atr_period': [16, 20, 24],
            'stop_atr_mult': [2.5, 3.0, 3.5],
            'target_atr_mult': [5.0, 6.0, 7.0],
            'trend_filter_period': [60, 80, 100],
        },
        'walk_forward_window': 1095,  # ~6 months of 4H bars
    },
    'H005': {
        'name': 'Donchian Channel Breakout',
        'research_id': 'R009',
        'archetype': DonchianBreakout,
        'timeframe_hours': 4,  # screened on 4H bars
        'params': {
            'channel_period': 20, 'stop_pct': 2.0,
            'target_pct': 6.0, 'long_only': True,
        },
        'sensitivity': {
            'channel_period': [15, 20, 25],
            'stop_pct': [1.5, 2.0, 2.5],
            'target_pct': [5.0, 6.0, 7.0],
        },
        'walk_forward_window': 1095,
    },
    'H006': {
        'name': 'Daily Timeframe Trend',
        'research_id': 'R011',
        'archetype': DailyTrend,
        'timeframe_hours': 24,
        'params': {
            'fast_period': 5, 'slow_period': 40,
            'stop_pct': 6.0, 'target_pct': 24.0,
            'long_only': True,
        },
        'sensitivity': {
            'fast_period': [3, 5, 7],
            'slow_period': [30, 40, 50],
            'stop_pct': [5.0, 6.0, 7.0],
            'target_pct': [20.0, 24.0, 28.0],
        },
        'walk_forward_window': 182,  # ~6 months of daily bars
    },
}


# ── Helpers ───────────────────────────────────────────────────────

def run_baseline(data, config, cost_pct):
    """Run full-sample backtest with base params."""
    factory = lambda: config['archetype'](**config['params'])
    bt = Backtest(data, cost_pct=cost_pct)
    bt.run(factory())
    return bt.result


def run_sensitivity(data, config, cost_pct):
    """Test each parameter at ±20% (or specified values).

    Returns list of {param, value, pf, trades, sharpe}.
    """
    results = []
    base_params = config['params'].copy()

    for param, values in config['sensitivity'].items():
        for val in values:
            test_params = base_params.copy()
            test_params[param] = val
            strategy = config['archetype'](**test_params)
            bt = Backtest(data, cost_pct=cost_pct)
            bt.run(strategy)
            r = bt.result
            results.append({
                'param': param,
                'value': val,
                'is_base': val == base_params[param],
                'pf': r.profit_factor,
                'trades': r.total_trades,
                'sharpe': r.sharpe_ratio,
                'win_rate': r.win_rate,
                'net_pnl': r.total_pnl,
            })
    return results


def format_result_line(res):
    """One-line summary of a BacktestResult."""
    return (f"PF={res.profit_factor:.2f}  Sharpe={res.sharpe_ratio:.2f}  "
            f"Trades={res.total_trades}  WR={res.win_rate:.1%}  "
            f"Net=${res.total_pnl:,.0f}  MaxDD=${res.max_drawdown:,.0f}")


# ── Main validation ──────────────────────────────────────────────

def validate_strategy(hypothesis_id, data_1h, report_lines):
    """Run full validation suite for one strategy."""
    config = STRATEGIES[hypothesis_id]
    name = config['name']

    print(f"\n{'='*60}")
    print(f"  {hypothesis_id}: {name}")
    print(f"{'='*60}")

    # Prepare data at correct timeframe
    if config['timeframe_hours'] > 1:
        data = resample(data_1h, hours=config['timeframe_hours'])
        print(f"  Resampled to {config['timeframe_hours']}H: {len(data)} bars")
    else:
        data = data_1h
        print(f"  Using 1H data: {len(data)} bars")

    report_lines.append(f"\n## {hypothesis_id}: {name}\n")
    report_lines.append(f"Research ID: {config['research_id']}  |  "
                       f"Timeframe: {config['timeframe_hours']}H  |  "
                       f"Bars: {len(data):,}\n")

    factory = lambda: config['archetype'](**config['params'])

    # ── 1. Full-sample baseline ──
    print("\n  [1/5] Full-sample baseline...")
    baseline = run_baseline(data, config, COST_PCT)
    print(f"    {format_result_line(baseline)}")

    report_lines.append("### 1. Full-Sample Baseline (0.1% costs)\n")
    report_lines.append(f"| Metric | Value |")
    report_lines.append(f"|--------|-------|")
    report_lines.append(f"| Profit Factor | {baseline.profit_factor:.2f} |")
    report_lines.append(f"| Sharpe Ratio | {baseline.sharpe_ratio:.2f} |")
    report_lines.append(f"| Total Trades | {baseline.total_trades} |")
    report_lines.append(f"| Win Rate | {baseline.win_rate:.1%} |")
    report_lines.append(f"| Net P&L | ${baseline.total_pnl:,.2f} |")
    report_lines.append(f"| Gross P&L | ${baseline.total_pnl_gross:,.2f} |")
    report_lines.append(f"| Total Costs | ${baseline.total_costs:,.2f} |")
    report_lines.append(f"| Max Drawdown | ${baseline.max_drawdown:,.2f} |")
    report_lines.append(f"| Max DD Duration | {baseline.max_drawdown_duration_days:.0f} days |")
    report_lines.append(f"| Avg Trade Duration | {baseline.avg_trade_duration_hours:.1f}h |")
    report_lines.append(f"| Expectancy | ${baseline.expectancy:,.2f}/trade |")
    report_lines.append(f"| Sortino | {baseline.sortino_ratio:.2f} |")
    report_lines.append(f"| Buy & Hold | ${baseline.buy_hold_pnl:,.2f} ({baseline.buy_hold_pnl_pct:.1f}%) |")
    report_lines.append("")

    # Live readiness
    checks = baseline.live_readiness_check()
    passed = sum(1 for c in checks.values() if c['passed'])
    report_lines.append(f"**Live Readiness: {passed}/{len(checks)}**\n")
    for name_c, c in checks.items():
        icon = "PASS" if c['passed'] else "FAIL"
        report_lines.append(f"- [{icon}] {name_c}: {c['value']} (target: {c['target']})")
    report_lines.append("")

    # ── 2. Walk-forward ──
    print("\n  [2/5] Walk-forward validation...")
    wf_window = config['walk_forward_window']
    wf_results = walk_forward(data, factory, window_bars=wf_window, cost_pct=COST_PCT)
    wf_text = walk_forward_summary(wf_results)
    print(wf_text)

    report_lines.append(f"### 2. Walk-Forward Validation ({wf_window} bars/window)\n")
    report_lines.append("```")
    report_lines.append(wf_text.strip())
    report_lines.append("```\n")

    # Compute walk-forward verdict
    profitable_windows = sum(1 for r in wf_results if r['result'].total_pnl > 0)
    total_windows = len(wf_results)
    pf_values = [r['result'].profit_factor for r in wf_results if r['result'].total_trades > 0]
    wf_mean_pf = statistics.mean(pf_values) if pf_values else 0
    wf_min_pf = min(pf_values) if pf_values else 0

    report_lines.append(f"- Profitable windows: {profitable_windows}/{total_windows}")
    report_lines.append(f"- Mean PF across windows: {wf_mean_pf:.2f}")
    report_lines.append(f"- Worst window PF: {wf_min_pf:.2f}")

    try:
        _wf_pct = _val['wf_profitable_pct']
        _wf_pf = _val['wf_mean_pf_min']
    except NameError:
        _wf_pct = 0.6
        _wf_pf = 1.1
    wf_pass = profitable_windows >= (total_windows * _wf_pct) and wf_mean_pf > _wf_pf
    report_lines.append(f"- **Walk-forward verdict: {'PASS' if wf_pass else 'FAIL'}**")
    report_lines.append("")

    # ── 3. In-sample / Out-of-sample ──
    print("\n  [3/5] In-sample vs out-of-sample (70/30)...")
    ios_results = run_in_out_of_sample(data, factory, train_pct=0.7, cost_pct=COST_PCT)
    ios_text = in_out_of_sample_summary(ios_results)
    print(ios_text)

    report_lines.append("### 3. In-Sample vs Out-of-Sample (70/30 split)\n")
    report_lines.append("```")
    report_lines.append(ios_text.strip())
    report_lines.append("```\n")

    oos = ios_results['out_of_sample']
    is_res = ios_results['in_sample']
    if is_res.profit_factor > 0:
        pf_decay = (oos.profit_factor - is_res.profit_factor) / is_res.profit_factor * 100
    else:
        pf_decay = 0

    try:
        _oos_min = _val['full_oos_pf_min']
        _oos_decay = _val['full_oos_decay_max']
    except NameError:
        _oos_min = 1.2
        _oos_decay = 30.0
    oos_pass = oos.profit_factor >= _oos_min and pf_decay > -_oos_decay
    report_lines.append(f"- OOS Profit Factor: {oos.profit_factor:.2f}")
    report_lines.append(f"- PF degradation: {pf_decay:+.1f}%")
    report_lines.append(f"- **OOS verdict: {'PASS' if oos_pass else 'FAIL'}** "
                       f"(need PF >= 1.2, decay < 30%)")
    report_lines.append("")

    # ── 4. Parameter sensitivity ──
    print("\n  [4/5] Parameter sensitivity...")
    sens_results = run_sensitivity(data, config, COST_PCT)

    report_lines.append("### 4. Parameter Sensitivity\n")
    report_lines.append("| Parameter | Value | PF | Trades | Sharpe | WR | Net P&L |")
    report_lines.append("|-----------|-------|----|--------|--------|----|---------|")

    for s in sens_results:
        marker = " **BASE**" if s['is_base'] else ""
        report_lines.append(
            f"| {s['param']} | {s['value']}{marker} | {s['pf']:.2f} | "
            f"{s['trades']} | {s['sharpe']:.2f} | {s['win_rate']:.1%} | "
            f"${s['net_pnl']:,.0f} |"
        )
    report_lines.append("")

    # Sensitivity verdict: all non-base PFs > 1.0
    non_base_pfs = [s['pf'] for s in sens_results if not s['is_base']]
    min_sens_pf = min(non_base_pfs) if non_base_pfs else 0
    above_1 = sum(1 for pf in non_base_pfs if pf > 1.0)
    try:
        _sens_pct = _val['sensitivity_pass_pct']
        _sens_worst = _val['sensitivity_worst_pf']
    except NameError:
        _sens_pct = 0.8
        _sens_worst = 0.9
    sens_pass = above_1 >= len(non_base_pfs) * _sens_pct and min_sens_pf > _sens_worst

    report_lines.append(f"- Variants with PF > 1.0: {above_1}/{len(non_base_pfs)}")
    report_lines.append(f"- Worst variant PF: {min_sens_pf:.2f}")
    report_lines.append(f"- **Sensitivity verdict: {'PASS' if sens_pass else 'FAIL'}**")
    report_lines.append("")

    # ── 5. Cost stress test ──
    print(f"\n  [5/5] Cost stress test ({COST_STRESS}% per trade)...")
    stress = run_baseline(data, config, COST_STRESS)
    print(f"    {format_result_line(stress)}")

    report_lines.append(f"### 5. Cost Stress Test ({COST_STRESS}% vs {COST_PCT}%)\n")
    report_lines.append("| Metric | Base (0.1%) | Stress (0.15%) |")
    report_lines.append("|--------|------------|----------------|")
    report_lines.append(f"| Profit Factor | {baseline.profit_factor:.2f} | {stress.profit_factor:.2f} |")
    report_lines.append(f"| Net P&L | ${baseline.total_pnl:,.0f} | ${stress.total_pnl:,.0f} |")
    report_lines.append(f"| Sharpe | {baseline.sharpe_ratio:.2f} | {stress.sharpe_ratio:.2f} |")
    report_lines.append(f"| Costs | ${baseline.total_costs:,.0f} | ${stress.total_costs:,.0f} |")
    report_lines.append("")

    try:
        _cost_min = _val['cost_stress_pf_min']
    except NameError:
        _cost_min = 1.15
    cost_pass = stress.profit_factor >= _cost_min
    report_lines.append(f"- **Cost stress verdict: {'PASS' if cost_pass else 'FAIL'}** "
                       f"(need PF >= 1.15 at {COST_STRESS}% costs)")
    report_lines.append("")

    # ── Overall verdict ──
    verdicts = {
        'walk_forward': wf_pass,
        'out_of_sample': oos_pass,
        'sensitivity': sens_pass,
        'cost_stress': cost_pass,
    }
    passed_count = sum(1 for v in verdicts.values() if v)
    try:
        _min_pass = _val['min_tests_passed']
    except NameError:
        _min_pass = 3
    overall = passed_count >= _min_pass

    report_lines.append("### Overall Verdict\n")
    report_lines.append(f"| Test | Result |")
    report_lines.append(f"|------|--------|")
    for test_name, passed_v in verdicts.items():
        report_lines.append(f"| {test_name} | {'PASS' if passed_v else 'FAIL'} |")
    report_lines.append("")
    verdict_str = "VALIDATED" if overall else "FAILED VALIDATION"
    report_lines.append(f"**{hypothesis_id} {verdict_str} ({passed_count}/4 tests passed)**\n")

    if overall:
        report_lines.append(f"**Recommendation:** Proceed to paper trading evaluation.\n")
    else:
        report_lines.append(f"**Recommendation:** Archive or refine. Edge not robust enough for live deployment.\n")

    report_lines.append("---\n")

    return {
        'hypothesis': hypothesis_id,
        'baseline_pf': baseline.profit_factor,
        'baseline_sharpe': baseline.sharpe_ratio,
        'baseline_trades': baseline.total_trades,
        'wf_pass': wf_pass,
        'oos_pass': oos_pass,
        'oos_pf': oos.profit_factor,
        'sens_pass': sens_pass,
        'cost_pass': cost_pass,
        'overall': overall,
        'passed_count': passed_count,
    }


ARCHETYPE_KEY_MAP = {
    VolAdjustedTrend: 'vol_adjusted_trend',
    DonchianBreakout: 'donchian_breakout',
    DailyTrend: 'daily_trend',
}
for _name, _klass in ARCHETYPES.items():
    ARCHETYPE_KEY_MAP.setdefault(_klass, _name)


def register_for_paper_trading(hyp_id, config, result):
    """Auto-register a validated strategy in the paper trade registry.

    Adds the strategy to data/paper_trade_registry.json with its
    validated params and default graduation criteria.
    """
    registry_path = REPO_ROOT / 'data' / 'paper_trade_registry.json'
    try:
        registry = json.loads(registry_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        registry = {"active": [], "graduated": [], "killed": []}

    # Skip if already registered (active, graduated, or killed)
    all_ids = set()
    for section in ['active', 'graduated', 'killed']:
        for s in registry.get(section, []):
            all_ids.add(s['id'])

    if hyp_id in all_ids:
        print(f"  {hyp_id} already in paper trade registry, skipping.")
        return False

    archetype_key = ARCHETYPE_KEY_MAP.get(config['archetype'], 'unknown')

    entry = {
        "id": hyp_id,
        "archetype": archetype_key,
        "timeframe_hours": config['timeframe_hours'],
        "params": config['params'],
        "started": datetime.now().strftime('%Y-%m-%d'),
        "graduation": {
            "min_days": 30,
            "min_trades": 5,
            "min_net_pf": 1.0,
            "max_drawdown_pct": 25,
            "kill_pf_below": 0.7,
            "kill_min_trades": 10,
        },
    }

    registry['active'].append(entry)
    registry_path.write_text(json.dumps(registry, indent=2) + '\n')
    print(f"  {hyp_id} registered for paper trading.")

    # Send notification email
    try:
        sys.path.insert(0, str(REPO_ROOT / 'scripts'))
        from email_sender import send_email, markdown_to_html
        body = (f"### Strategy Entering Paper Trading\n\n"
                f"**{hyp_id}** ({config['name']}) has passed walk-forward validation "
                f"and has been automatically registered for paper trading.\n\n"
                f"- Baseline PF: {result['baseline_pf']:.2f}\n"
                f"- OOS PF: {result['oos_pf']:.2f}\n"
                f"- Tests passed: {result['passed_count']}/4\n"
                f"- Timeframe: {config['timeframe_hours']}H\n\n"
                f"Paper trading will run automatically every 4 hours. "
                f"You will be emailed when the strategy is ready for live deployment.\n")
        send_email(
            subject=f"[RBI] {hyp_id} validated — entering paper trading",
            body=markdown_to_html(body),
            html=True,
        )
    except Exception as e:
        print(f"  Notification email failed: {e}")

    return True


def _default_promoted_queue():
    return {
        'pending_validation': [],
        'validated': [],
        'failed': [],
    }


def _load_promoted_queue():
    if not PROMOTED_QUEUE_FILE.exists():
        return _default_promoted_queue()
    try:
        queue = json.loads(PROMOTED_QUEUE_FILE.read_text())
        if not isinstance(queue, dict):
            return _default_promoted_queue()
        queue.setdefault('pending_validation', [])
        queue.setdefault('validated', [])
        queue.setdefault('failed', [])
        return queue
    except json.JSONDecodeError:
        return _default_promoted_queue()


def _save_promoted_queue(queue):
    PROMOTED_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROMOTED_QUEUE_FILE.write_text(json.dumps(queue, indent=2) + '\n')


def _build_sensitivity_from_params(params):
    sensitivity = {}
    for param, base in params.items():
        if isinstance(base, bool):
            continue
        if isinstance(base, int):
            values = [int(round(base * m)) for m in (0.8, 1.0, 1.2)]
        elif isinstance(base, float):
            values = [round(base * m, 6) for m in (0.8, 1.0, 1.2)]
        else:
            continue
        # Keep order, remove duplicates.
        deduped = list(dict.fromkeys(values))
        if len(deduped) > 1:
            sensitivity[param] = deduped
    return sensitivity


def _build_config_from_queue_entry(entry):
    archetype_key = entry.get('archetype')
    if archetype_key not in ARCHETYPES:
        raise KeyError(f"Unknown archetype: {archetype_key}")

    params = dict(entry.get('params') or {})
    return {
        'name': entry.get('name', entry['research_id']),
        'research_id': entry['research_id'],
        'archetype': ARCHETYPES[archetype_key],
        'timeframe_hours': int(entry.get('timeframe_hours', 4)),
        'params': params,
        'sensitivity': _build_sensitivity_from_params(params),
        'walk_forward_window': 182 if int(entry.get('timeframe_hours', 4)) >= 24 else 1095,
    }


def _append_queue_validation_summary(report, all_results):
    report.append("\n## Summary\n")
    report.append("| Strategy | Baseline PF | OOS PF | Walk-Fwd | OOS | Sensitivity | Cost Stress | **Verdict** |")
    report.append("|----------|------------|--------|----------|-----|-------------|-------------|-------------|")
    for r in all_results:
        report.append(
            f"| {r['hypothesis']} | {r['baseline_pf']:.2f} | {r['oos_pf']:.2f} | "
            f"{'PASS' if r['wf_pass'] else 'FAIL'} | "
            f"{'PASS' if r['oos_pass'] else 'FAIL'} | "
            f"{'PASS' if r['sens_pass'] else 'FAIL'} | "
            f"{'PASS' if r['cost_pass'] else 'FAIL'} | "
            f"**{'VALIDATED' if r['overall'] else 'FAILED'}** |"
        )
    report.append("")


def validate_from_queue():
    print("=" * 60)
    print("WALK-FORWARD VALIDATION — QUEUED PROMOTIONS")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Queue: {PROMOTED_QUEUE_FILE}")
    print("=" * 60)

    queue = _load_promoted_queue()
    pending = list(queue.get('pending_validation', []))
    if not pending:
        print("nothing to validate")
        return []

    print("\nLoading 1H data...")
    data_1h = load_csv(DATA_FILE)
    print(f"  {len(data_1h):,} bars: {data_1h[0]['datetime']} → {data_1h[-1]['datetime']}")

    report = [
        f"# Walk-Forward Validation Report (Queue)",
        f"",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"**Data:** BTCUSD 1H, {len(data_1h):,} bars  ",
        f"**Period:** {data_1h[0]['datetime'].strftime('%Y-%m-%d')} → {data_1h[-1]['datetime'].strftime('%Y-%m-%d')}  ",
        f"**Base cost:** {COST_PCT}%  |  **Stress cost:** {COST_STRESS}%",
        f"",
        f"---",
        f"",
    ]

    all_results = []
    for entry in pending:
        hyp_id = entry.get('hypothesis_id')
        if not hyp_id:
            entry['validation_error'] = 'Missing hypothesis_id.'
            queue['failed'].append(entry)
            continue

        try:
            config = _build_config_from_queue_entry(entry)
            STRATEGIES[hyp_id] = config
            result = validate_strategy(hyp_id, data_1h, report)
            all_results.append(result)

            audited_entry = dict(entry)
            audited_entry['validated_date'] = datetime.now().strftime('%Y-%m-%d')
            audited_entry['validation_passed_tests'] = result['passed_count']
            audited_entry['validation_overall'] = result['overall']

            if result['overall']:
                queue['validated'].append(audited_entry)
                register_for_paper_trading(hyp_id, config, result)
            else:
                queue['failed'].append(audited_entry)

        except Exception as e:
            entry['validation_error'] = str(e)
            queue['failed'].append(entry)
        finally:
            # Preserve legacy strategies as-is; queue strategies are additive.
            if hyp_id not in ('H004', 'H005', 'H006'):
                STRATEGIES.pop(hyp_id, None)

    queue['pending_validation'] = []
    _save_promoted_queue(queue)

    if all_results:
        _append_queue_validation_summary(report, all_results)
        out_dir = REPO_ROOT / 'data'
        out_path = out_dir / f"validation_{datetime.now().strftime('%Y%m%d')}.md"
        out_path.write_text('\n'.join(report))
        print(f"\nReport saved to: {out_path}")

    print(f"\n{'='*60}")
    print("QUEUE VALIDATION COMPLETE")
    for r in all_results:
        status = "VALIDATED" if r['overall'] else "FAILED"
        print(f"  {r['hypothesis']}: {status} ({r['passed_count']}/4) — "
              f"PF {r['baseline_pf']:.2f}, OOS PF {r['oos_pf']:.2f}")
    print(f"{'='*60}")

    return all_results


def main():
    print("=" * 60)
    print("WALK-FORWARD VALIDATION — PROMOTED STRATEGIES")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Data: {DATA_FILE}")
    print(f"Cost: {COST_PCT}% (stress: {COST_STRESS}%)")
    print("=" * 60)

    # Load data
    print("\nLoading 1H data...")
    data_1h = load_csv(DATA_FILE)
    print(f"  {len(data_1h):,} bars: {data_1h[0]['datetime']} → {data_1h[-1]['datetime']}")

    report = [
        f"# Walk-Forward Validation Report",
        f"",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"**Data:** BTCUSD 1H, {len(data_1h):,} bars  ",
        f"**Period:** {data_1h[0]['datetime'].strftime('%Y-%m-%d')} → {data_1h[-1]['datetime'].strftime('%Y-%m-%d')}  ",
        f"**Base cost:** {COST_PCT}%  |  **Stress cost:** {COST_STRESS}%",
        f"",
        f"---",
        f"",
    ]

    all_results = []

    for hyp_id in ['H004', 'H005', 'H006']:
        result = validate_strategy(hyp_id, data_1h, report)
        all_results.append(result)

    # ── Summary table ──
    report.append("\n## Summary\n")
    report.append("| Strategy | Baseline PF | OOS PF | Walk-Fwd | OOS | Sensitivity | Cost Stress | **Verdict** |")
    report.append("|----------|------------|--------|----------|-----|-------------|-------------|-------------|")
    for r in all_results:
        report.append(
            f"| {r['hypothesis']} | {r['baseline_pf']:.2f} | {r['oos_pf']:.2f} | "
            f"{'PASS' if r['wf_pass'] else 'FAIL'} | "
            f"{'PASS' if r['oos_pass'] else 'FAIL'} | "
            f"{'PASS' if r['sens_pass'] else 'FAIL'} | "
            f"{'PASS' if r['cost_pass'] else 'FAIL'} | "
            f"**{'VALIDATED' if r['overall'] else 'FAILED'}** |"
        )
    report.append("")

    validated = [r for r in all_results if r['overall']]
    failed = [r for r in all_results if not r['overall']]

    if validated:
        report.append(f"### Validated ({len(validated)})")
        for r in validated:
            report.append(f"- **{r['hypothesis']}**: Ready for paper trading. "
                         f"Baseline PF {r['baseline_pf']:.2f}, OOS PF {r['oos_pf']:.2f}")
    if failed:
        report.append(f"\n### Failed Validation ({len(failed)})")
        for r in failed:
            report.append(f"- **{r['hypothesis']}**: {r['passed_count']}/4 tests. "
                         f"Archive or refine.")
    report.append("")

    # Auto-register validated strategies for paper trading
    for r in all_results:
        if r['overall']:
            config = STRATEGIES[r['hypothesis']]
            register_for_paper_trading(r['hypothesis'], config, r)

    # Save report
    out_dir = REPO_ROOT / 'data'
    out_path = out_dir / f"validation_{datetime.now().strftime('%Y%m%d')}.md"
    out_path.write_text('\n'.join(report))
    print(f"\nReport saved to: {out_path}")

    # Print summary
    print(f"\n{'='*60}")
    print("VALIDATION COMPLETE")
    for r in all_results:
        status = "VALIDATED" if r['overall'] else "FAILED"
        print(f"  {r['hypothesis']}: {status} ({r['passed_count']}/4) — "
              f"PF {r['baseline_pf']:.2f}, OOS PF {r['oos_pf']:.2f}")
    print(f"{'='*60}")

    return all_results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Walk-forward validator')
    parser.add_argument(
        '--from-queue',
        action='store_true',
        help='Validate promoted strategies from data/promoted_queue.json',
    )
    args = parser.parse_args()

    if args.from_queue:
        validate_from_queue()
    else:
        main()
