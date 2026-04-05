#!/usr/bin/env python3
"""
Meta-analysis of the experiment journal — find what works.

Inspired by Karpathy's autoresearch analysis notebook: mine the experiment
log for patterns that inform future research direction.

Produces:
1. Archetype leaderboard (which strategy types perform best)
2. Parameter sensitivity analysis (what ranges work)
3. Simplicity vs performance (Karpathy's "keep if simple" criterion)
4. Kill pattern analysis (why things fail)
5. Actionable recommendations for the LLM idea sourcer

Usage:
    python scripts/analyze_experiments.py
    python scripts/analyze_experiments.py --json   # Machine-readable output
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
JOURNAL_FILE = REPO_ROOT / 'data' / 'experiment_journal.tsv'
INSIGHTS_FILE = REPO_ROOT / 'data' / 'experiment_insights.json'


def load_journal():
    """Load experiment journal TSV."""
    if not JOURNAL_FILE.exists():
        print(f"No journal found at {JOURNAL_FILE}. Run build_experiment_journal.py first.")
        sys.exit(1)

    rows = []
    with open(JOURNAL_FILE, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            # Convert numeric fields
            for field in ('gross_pf', 'net_pf', 'win_rate', 'sharpe', 'sortino',
                         'max_dd', 'expectancy_gross', 'expectancy_net',
                         'avg_duration_hours', 'strategy_pnl_gross', 'strategy_pnl_net',
                         'buy_hold_pnl', 'total_costs', 'cost_pct',
                         'max_dd_duration_days'):
                try:
                    row[field] = float(row[field]) if row.get(field) else 0.0
                except (ValueError, TypeError):
                    row[field] = 0.0
            for field in ('total_trades', 'param_count', 'data_bars'):
                try:
                    row[field] = int(row[field]) if row.get(field) else 0
                except (ValueError, TypeError):
                    row[field] = 0
            rows.append(row)
    return rows


def archetype_leaderboard(rows):
    """Rank archetypes by promotion rate and average PF."""
    stats = defaultdict(lambda: {
        'total': 0, 'promote': 0, 'kill': 0, 'park': 0,
        'pf_sum': 0, 'pf_max': 0, 'sharpe_sum': 0,
        'trade_sum': 0, 'best_idea': '', 'best_pf': 0,
    })

    for r in rows:
        arch = r.get('archetype', '')
        if not arch:
            continue
        s = stats[arch]
        s['total'] += 1
        s[r.get('verdict', 'parked')] += 1
        pf = r['gross_pf']
        s['pf_sum'] += pf
        s['sharpe_sum'] += r['sharpe']
        s['trade_sum'] += r['total_trades']
        if pf > s['best_pf']:
            s['best_pf'] = pf
            s['best_idea'] = r.get('idea_id', '')
        s['pf_max'] = max(s['pf_max'], pf)

    # Build leaderboard sorted by promotion rate then avg PF
    board = []
    for arch, s in stats.items():
        if s['total'] == 0:
            continue
        promo_rate = s['promote'] / s['total']
        avg_pf = s['pf_sum'] / s['total']
        avg_sharpe = s['sharpe_sum'] / s['total']
        avg_trades = s['trade_sum'] / s['total']
        board.append({
            'archetype': arch,
            'total_screens': s['total'],
            'promoted': s['promote'],
            'killed': s['kill'],
            'parked': s['park'],
            'promo_rate': round(promo_rate, 2),
            'avg_pf': round(avg_pf, 2),
            'max_pf': round(s['pf_max'], 2),
            'avg_sharpe': round(avg_sharpe, 2),
            'avg_trades': round(avg_trades, 0),
            'best_idea': s['best_idea'],
        })

    board.sort(key=lambda x: (-x['promo_rate'], -x['avg_pf']))
    return board


def simplicity_analysis(rows):
    """Analyze relationship between param count and performance.

    Autoresearch principle: "0.001 improvement that adds 20 lines? Not worth it.
    0.001 improvement from deleting code? Definitely keep."
    """
    by_complexity = defaultdict(lambda: {'pf_sum': 0, 'count': 0, 'promo': 0})

    for r in rows:
        pc = r['param_count']
        bucket = f"{pc} params"
        b = by_complexity[bucket]
        b['count'] += 1
        b['pf_sum'] += r['gross_pf']
        if r.get('verdict') == 'promote':
            b['promo'] += 1

    results = []
    for bucket, b in sorted(by_complexity.items()):
        if b['count'] == 0:
            continue
        results.append({
            'complexity': bucket,
            'count': b['count'],
            'avg_pf': round(b['pf_sum'] / b['count'], 2),
            'promo_rate': round(b['promo'] / b['count'], 2),
        })
    return results


def parameter_insights(rows):
    """Find which parameter values correlate with high PF.

    Looks at promoted strategies only to find the sweet spots.
    """
    promoted = [r for r in rows if r.get('verdict') == 'promote']
    if not promoted:
        return {}

    # Aggregate params from promoted strategies
    param_values = defaultdict(list)
    for r in promoted:
        try:
            params = json.loads(r.get('params_json', '{}'))
        except json.JSONDecodeError:
            continue
        for k, v in params.items():
            if isinstance(v, (int, float)) and k not in ('aux_timeframe_hours',):
                param_values[k].append({'value': v, 'pf': r['gross_pf']})

    # Find ranges and best values
    insights = {}
    for param, entries in param_values.items():
        if len(entries) < 3:
            continue
        values = [e['value'] for e in entries]
        pfs = [e['pf'] for e in entries]
        # Weighted average value (weighted by PF)
        total_pf = sum(pfs)
        if total_pf == 0:
            continue
        weighted_avg = sum(v * pf for v, pf in zip(values, pfs)) / total_pf
        insights[param] = {
            'count': len(entries),
            'min': round(min(values), 2),
            'max': round(max(values), 2),
            'avg': round(sum(values) / len(values), 2),
            'pf_weighted_avg': round(weighted_avg, 2),
            'best_value': round(entries[max(range(len(entries)), key=lambda i: entries[i]['pf'])]['value'], 2),
        }

    return insights


def kill_patterns(rows):
    """Analyze why strategies get killed — find common failure modes."""
    killed = [r for r in rows if r.get('verdict') == 'kill']
    if not killed:
        return []

    patterns = defaultdict(int)
    for r in killed:
        reason = r.get('reason', '')
        pf = r['gross_pf']
        if pf < 1.0:
            patterns['negative_expectancy'] += 1
        elif pf < 1.3:
            patterns['pf_below_1.3'] += 1
        elif pf < 1.5:
            patterns['pf_1.3_to_1.5_killed_by_threshold'] += 1

        if r['total_trades'] < 20:
            patterns['insufficient_trades'] += 1

    return dict(sorted(patterns.items(), key=lambda x: -x[1]))


def duplicate_detection(rows):
    """Find strategies that are effectively the same (same archetype+params)."""
    seen = {}
    duplicates = []
    for r in rows:
        key = f"{r.get('archetype', '')}|{r.get('params_json', '')}"
        if key in seen:
            duplicates.append({
                'original': seen[key],
                'duplicate': r.get('idea_id', ''),
                'archetype': r.get('archetype', ''),
                'pf': r['gross_pf'],
            })
        else:
            seen[key] = r.get('idea_id', '')
    return duplicates


def generate_sourcing_recommendations(board, simplicity, param_insights, kills):
    """Generate actionable recommendations for the LLM idea sourcer."""
    recs = []

    # Best archetypes
    top = [a for a in board if a['promo_rate'] > 0.3 and a['total_screens'] >= 2]
    if top:
        names = [a['archetype'] for a in top[:3]]
        recs.append(f"FOCUS archetypes (high promo rate): {', '.join(names)}")

    # Worst archetypes
    dead = [a for a in board if a['promo_rate'] == 0 and a['total_screens'] >= 3]
    if dead:
        names = [a['archetype'] for a in dead[:3]]
        recs.append(f"AVOID archetypes (0% promo rate): {', '.join(names)}")

    # Simplicity
    if simplicity:
        best_simple = min(simplicity, key=lambda x: -x['promo_rate'])
        recs.append(f"Simplicity sweet spot: {best_simple['complexity']} "
                   f"(promo rate {best_simple['promo_rate']:.0%})")

    # Parameter sweet spots
    if param_insights.get('stop_pct'):
        sp = param_insights['stop_pct']
        recs.append(f"Stop loss sweet spot: {sp['pf_weighted_avg']}% "
                   f"(range {sp['min']}-{sp['max']}%)")
    if param_insights.get('target_pct'):
        tp = param_insights['target_pct']
        recs.append(f"Target sweet spot: {tp['pf_weighted_avg']}% "
                   f"(range {tp['min']}-{tp['max']}%)")

    # Kill patterns
    if kills.get('pf_1.3_to_1.5_killed_by_threshold', 0) > 3:
        recs.append("Many strategies die in 1.3-1.5 PF range — threshold is working")

    return recs


def run_analysis(json_output=False):
    """Run full meta-analysis and print results."""
    rows = load_journal()
    print(f"Loaded {len(rows)} experiment entries")
    print(f"{'=' * 70}")

    # 1. Archetype leaderboard
    board = archetype_leaderboard(rows)
    print("\n## ARCHETYPE LEADERBOARD")
    print(f"{'Archetype':<30} {'Screens':>7} {'Promo':>6} {'Kill':>6} {'Rate':>6} {'AvgPF':>6} {'MaxPF':>6} {'Sharpe':>7}")
    print("-" * 95)
    for a in board:
        print(f"{a['archetype']:<30} {a['total_screens']:>7} {a['promoted']:>6} "
              f"{a['killed']:>6} {a['promo_rate']:>5.0%} {a['avg_pf']:>6.2f} "
              f"{a['max_pf']:>6.2f} {a['avg_sharpe']:>7.2f}")

    # 2. Simplicity analysis
    simplicity = simplicity_analysis(rows)
    print("\n## SIMPLICITY vs PERFORMANCE (Karpathy criterion)")
    print(f"{'Complexity':<15} {'Count':>6} {'AvgPF':>7} {'PromoRate':>10}")
    print("-" * 40)
    for s in simplicity:
        print(f"{s['complexity']:<15} {s['count']:>6} {s['avg_pf']:>7.2f} {s['promo_rate']:>9.0%}")

    # 3. Parameter insights
    param_ins = parameter_insights(rows)
    if param_ins:
        print("\n## PARAMETER SWEET SPOTS (from promoted strategies)")
        print(f"{'Parameter':<25} {'Count':>6} {'Range':<15} {'PF-Weighted':>12} {'Best':>8}")
        print("-" * 70)
        for param, ins in sorted(param_ins.items()):
            print(f"{param:<25} {ins['count']:>6} {ins['min']}-{ins['max']:<10} "
                  f"{ins['pf_weighted_avg']:>12.2f} {ins['best_value']:>8.2f}")

    # 4. Kill patterns
    kills = kill_patterns(rows)
    if kills:
        print("\n## KILL PATTERN ANALYSIS")
        for pattern, count in kills.items():
            print(f"  {pattern}: {count} occurrences")

    # 5. Duplicate detection
    dupes = duplicate_detection(rows)
    if dupes:
        print(f"\n## DUPLICATE STRATEGIES DETECTED: {len(dupes)}")
        for d in dupes[:10]:
            print(f"  {d['duplicate']} duplicates {d['original']} ({d['archetype']}, PF {d['pf']})")

    # 6. Recommendations
    recs = generate_sourcing_recommendations(board, simplicity, param_ins, kills)
    print("\n## SOURCING RECOMMENDATIONS")
    for i, rec in enumerate(recs, 1):
        print(f"  {i}. {rec}")

    # Save machine-readable insights
    insights = {
        'generated': __import__('datetime').datetime.now().isoformat(),
        'total_experiments': len(rows),
        'archetype_leaderboard': board,
        'simplicity_analysis': simplicity,
        'parameter_insights': param_ins,
        'kill_patterns': kills,
        'duplicates_found': len(dupes),
        'recommendations': recs,
    }

    INSIGHTS_FILE.write_text(json.dumps(insights, indent=2) + '\n')
    print(f"\nInsights saved to {INSIGHTS_FILE.name}")

    if json_output:
        print("\n--- JSON OUTPUT ---")
        print(json.dumps(insights, indent=2))

    return insights


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Analyze experiment journal')
    parser.add_argument('--json', action='store_true', help='Output JSON')
    args = parser.parse_args()
    run_analysis(json_output=args.json)
