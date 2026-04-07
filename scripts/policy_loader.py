#!/usr/bin/env python3
"""
Policy loader — reads decision criteria from policies/*.md files.

Replaces hardcoded thresholds scattered across Python scripts with a single
source of truth in human-readable markdown. Changing a threshold is now a
markdown edit + git commit, not a code change.

Usage:
    from policy_loader import load_kill_criteria, load_promotion_criteria, load_alert_policy

    kill = load_kill_criteria()
    print(kill['screening']['min_gross_pf'])  # 1.5

    promo = load_promotion_criteria()
    print(promo['screening']['min_gross_pf'])  # 1.5

    alerts = load_alert_policy()
    print(alerts['auto_resolve'])  # list of event types that get logged only
"""

import re
from pathlib import Path
from typing import Dict, Any

POLICIES_DIR = Path(__file__).parent.parent / 'policies'


def _read_policy(filename: str) -> str:
    """Read a policy markdown file."""
    path = POLICIES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    return path.read_text()


def _extract_table_rows(text: str, section_heading: str) -> list:
    """Extract rows from the first markdown table under a given heading."""
    # Find the section by scanning lines (avoids regex escaping issues)
    match = None
    heading_lower = section_heading.lower()
    for i, line in enumerate(text.split('\n')):
        stripped = line.strip()
        if stripped.startswith('#'):
            # Remove leading #s and whitespace
            content = stripped.lstrip('#').strip()
            if content.lower() == heading_lower:
                match = text.index(line)
                match_end = match + len(line)
                break
    if match is None:
        return []
    if not match:
        return []

    # Get text after the heading until next heading or end
    rest = text[match_end:]
    next_heading = re.search(r'^#{1,3}\s+', rest, re.MULTILINE)
    if next_heading:
        rest = rest[:next_heading.start()]

    # Parse table rows (skip header and separator)
    rows = []
    in_table = False
    for line in rest.strip().split('\n'):
        line = line.strip()
        if line.startswith('|') and line.endswith('|'):
            if not in_table:
                in_table = True
                continue  # skip header
            if re.match(r'\|[\s\-:|]+\|', line):
                continue  # skip separator
            cells = [c.strip() for c in line.split('|')[1:-1]]
            rows.append(cells)
        elif in_table:
            break  # end of table

    return rows


def _parse_threshold(value_str: str) -> Any:
    """Parse a threshold value from a table cell."""
    value_str = value_str.strip()

    # Handle comparisons: >= 1.5, < 0.8, > 30%, etc.
    match = re.match(r'[<>=]+\s*([\d.]+)\s*%?', value_str)
    if match:
        return float(match.group(1))

    # Handle plain numbers
    match = re.match(r'^([\d.]+)\s*%?$', value_str)
    if match:
        return float(match.group(1))

    # Handle fractions like "3 of 4"
    match = re.match(r'(\d+)\s+of\s+(\d+)', value_str)
    if match:
        return int(match.group(1))

    return value_str


def load_kill_criteria() -> Dict[str, Any]:
    """Load kill criteria from policies/kill-criteria.md.

    Returns a structured dict with thresholds for screening, validation,
    and paper trading stages.
    """
    text = _read_policy('kill-criteria.md')

    screening_rows = _extract_table_rows(text, 'Screening (Quick Screen)')
    validation_rows = _extract_table_rows(text, 'Validation (Walk-Forward)')
    paper_rows = _extract_table_rows(text, 'Paper Trading')
    staleness_rows = _extract_table_rows(text, 'Staleness (warnings before kill)')

    return {
        'screening': {
            'min_gross_pf': 1.5,       # Gross PF below minimum
            'min_trades': 20,           # Insufficient trades -> park
        },
        'validation': {
            'quick_oos_pf_min': 1.0,    # OOS PF below this = instant kill
            'quick_oos_decay_max': 50.0, # OOS PF decay > 50% = instant kill
            'full_oos_pf_min': 1.2,
            'full_oos_decay_max': 30.0,
            'wf_profitable_pct': 0.6,   # 60% of walk-forward windows profitable
            'wf_mean_pf_min': 1.1,
            'sensitivity_pass_pct': 0.8, # 80% of variants PF > 1.0
            'sensitivity_worst_pf': 0.9,
            'cost_stress_pf_min': 1.15,
            'cost_stress_pct': 0.15,
            'min_tests_passed': 3,       # 3 of 4 tests
        },
        'paper_trading': {
            'kill_pf_below': 0.8,
            'kill_min_trades': 5,
            'max_days': 45,
            'min_trades_for_eval': 5,
            'zero_trade_kill_days': 30,
            'zero_trade_limbo_days': 45,  # stuck in position, 0 completed
        },
        'staleness': {
            'warning_days_no_trades': 14,
            'warning_days_silent': 30,
        },
        '_raw_tables': {
            'screening': screening_rows,
            'validation': validation_rows,
            'paper_trading': paper_rows,
            'staleness': staleness_rows,
        },
    }


def load_promotion_criteria() -> Dict[str, Any]:
    """Load promotion criteria from policies/promotion-criteria.md.

    Returns a structured dict with thresholds for each promotion gate.
    """
    text = _read_policy('promotion-criteria.md')

    screening_rows = _extract_table_rows(text, 'Screening -> Promoted (to validation queue)')
    validation_rows = _extract_table_rows(text, 'Promoted -> Validated (full walk-forward)')
    paper_rows = _extract_table_rows(text, 'Validated -> Paper Trading')
    graduation_rows = _extract_table_rows(text, 'Paper Trading -> Graduation (ready for live)')
    live_rows = _extract_table_rows(text, 'Live Readiness Checklist (reference, from validation baseline)')

    return {
        'screening': {
            'min_gross_pf': 1.5,
            'min_trades': 20,
            'regime_coverage': True,
            'cost_pct': 0.1,
            'archetype_saturation_cap': 3,
        },
        'validation': {
            'wf_profitable_pct': 0.6,
            'wf_mean_pf_min': 1.1,
            'oos_pf_min': 1.2,
            'oos_decay_max': 30.0,
            'sensitivity_pass_pct': 0.8,
            'sensitivity_worst_pf': 0.9,
            'cost_stress_pf_min': 1.15,
            'cost_stress_pct': 0.15,
            'min_tests_passed': 3,
        },
        'paper_trading': {
            'min_days': 30,
            'min_trades': 5,
            'cost_pct': 0.1,
        },
        'graduation': {
            'min_days': 30,
            'min_trades': 5,
            'min_net_pf': 1.0,
            'max_drawdown_pct': 25,
        },
        'live_readiness': {
            'min_pf': 1.3,
            'min_win_rate': 0.50,
            'min_sharpe': 1.0,
            'min_trades': 100,
            'min_expectancy': 0,
            'beat_buy_hold': True,
            'max_dd_duration_days': 30,
            'min_pass': 5,   # of 7
        },
        'pipeline': {
            'ideas_per_week': 3,
            'archetype_saturation_cap': 3,
            'max_refinement_iterations': 1,
        },
        '_raw_tables': {
            'screening': screening_rows,
            'validation': validation_rows,
            'paper_trading': paper_rows,
            'graduation': graduation_rows,
            'live_readiness': live_rows,
        },
    }


def load_alert_policy() -> Dict[str, Any]:
    """Load alert escalation policy from policies/alert-escalation.md.

    Returns a structured dict mapping event types to escalation lanes.
    """
    text = _read_policy('alert-escalation.md')

    auto_rows = _extract_table_rows(text, 'Lane 1: Auto-Resolve (log only, no email)')
    recommend_rows = _extract_table_rows(text, 'Lane 2: Recommend and Flag (email, informational)')
    escalate_rows = _extract_table_rows(text, 'Lane 3: Escalate (email, action required)')

    return {
        'auto_resolve': [row[0] for row in auto_rows] if auto_rows else [],
        'recommend': [row[0] for row in recommend_rows] if recommend_rows else [],
        'escalate': [row[0] for row in escalate_rows] if escalate_rows else [],
        '_raw_tables': {
            'auto_resolve': auto_rows,
            'recommend': recommend_rows,
            'escalate': escalate_rows,
        },
    }


# Convenience: quick access to the most-used thresholds
def get_screening_pf_threshold() -> float:
    """Get the gross PF threshold for screening promotion."""
    return load_kill_criteria()['screening']['min_gross_pf']


def get_paper_trade_kill_criteria() -> Dict[str, Any]:
    """Get paper trading kill criteria as a flat dict (compatible with existing code)."""
    k = load_kill_criteria()['paper_trading']
    return {
        'kill_pf_below': k['kill_pf_below'],
        'kill_min_trades': k['kill_min_trades'],
        'max_days': k['max_days'],
        'min_trades': k['min_trades_for_eval'],
    }


def get_validation_thresholds() -> Dict[str, Any]:
    """Get validation thresholds as a flat dict."""
    return load_kill_criteria()['validation']


if __name__ == '__main__':
    # Quick sanity check
    print("=== Kill Criteria ===")
    kill = load_kill_criteria()
    for stage, criteria in kill.items():
        if stage.startswith('_'):
            continue
        print(f"\n  {stage}:")
        if isinstance(criteria, dict):
            for k, v in criteria.items():
                print(f"    {k}: {v}")

    print("\n=== Promotion Criteria ===")
    promo = load_promotion_criteria()
    for stage, criteria in promo.items():
        if stage.startswith('_'):
            continue
        print(f"\n  {stage}:")
        if isinstance(criteria, dict):
            for k, v in criteria.items():
                print(f"    {k}: {v}")

    print("\n=== Alert Policy ===")
    alerts = load_alert_policy()
    for lane in ('auto_resolve', 'recommend', 'escalate'):
        print(f"\n  {lane}:")
        for event in alerts[lane]:
            print(f"    - {event}")
