#!/usr/bin/env python3
"""
Priority Executor for AI Chief of Staff.

Reads the KANBAN board, maps priorities to executable actions,
runs them, updates state, and produces an execution report.

Designed to run AFTER the morning brief is generated and emailed.
This is the "execution layer" that turns recommendations into results.

Usage:
    python run_priorities.py                  # Execute KANBAN priorities
    python run_priorities.py --dry-run        # Show plan without executing
    python run_priorities.py --max 2          # Execute at most 2 priorities
"""

import os
import re
import sys
import json
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from llm import generate
from email_sender import send_email, markdown_to_html

REPO_ROOT = Path(__file__).parent.parent
KANBAN_FILE = REPO_ROOT / "KANBAN.md"
BACKLOG_FILE = REPO_ROOT / "strategies" / "RESEARCH_BACKLOG.md"
DATA_DIR = REPO_ROOT / "data"
STRATEGIES_DIR = REPO_ROOT / "strategies"

# Maximum LLM calls per execution to control costs
MAX_LLM_CALLS = 6


# ---------------------------------------------------------------------------
# KANBAN Parser
# ---------------------------------------------------------------------------

def parse_kanban() -> Dict:
    """Parse KANBAN.md into structured data."""
    text = KANBAN_FILE.read_text()
    result = {"doing": [], "up_next": [], "done": []}

    # Parse Doing section
    doing_match = re.search(
        r"## Doing.*?\n\|.*?\n\|[-:| ]+\n(.*?)(?=\n---|\n## )",
        text, re.DOTALL
    )
    if doing_match:
        for line in doing_match.group(1).strip().split("\n"):
            line = line.strip()
            if line.startswith("|") and not line.startswith("| Item"):
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if len(cells) >= 4:
                    result["doing"].append({
                        "item": cells[0],
                        "owner": cells[1],
                        "started": cells[2],
                        "status": cells[3],
                    })

    # Parse Up Next section
    upnext_match = re.search(
        r"## Up Next.*?\n\|.*?\n\|[-:| ]+\n(.*?)(?=\n---|\n## )",
        text, re.DOTALL
    )
    if upnext_match:
        for line in upnext_match.group(1).strip().split("\n"):
            line = line.strip()
            if line.startswith("|") and not line.startswith("| #"):
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if len(cells) >= 4:
                    result["up_next"].append({
                        "number": cells[0],
                        "item": cells[1],
                        "rbi_phase": cells[2],
                        "notes": cells[3] if len(cells) > 3 else "",
                    })

    return result


def update_kanban(completed_items: List[str], new_doing: Optional[List[Dict]] = None):
    """Move completed items to Done and optionally update Doing section."""
    text = KANBAN_FILE.read_text()
    today = datetime.now().strftime("%Y-%m-%d")

    # Update header
    text = re.sub(
        r"> Last updated: .+",
        f"> Last updated: {today} by AI Chief of Staff (auto-execution)",
        text,
    )

    # Remove completed items by filtering out whole lines
    # This is safer than regex cell matching which can corrupt table rows
    lines = text.split("\n")
    filtered_lines = []
    for line in lines:
        skip = False
        for item_text in completed_items:
            if item_text in line and line.strip().startswith("|"):
                skip = True
                break
        if not skip:
            filtered_lines.append(line)
    text = "\n".join(filtered_lines)

    # Add completed items to Done (after the Done table header)
    done_header = "| Item | Completed |\n|------|-----------|"
    new_rows = ""
    for item_text in completed_items:
        new_rows += f"\n| {item_text} | {today} |"

    if new_rows:
        text = text.replace(done_header, done_header + new_rows)

    # Renumber Up Next items (only lines in the Up Next section)
    lines = text.split("\n")
    in_up_next = False
    counter = 1
    for i, line in enumerate(lines):
        if "## Up Next" in line:
            in_up_next = True
            continue
        if in_up_next and line.startswith("---"):
            in_up_next = False
            continue
        if in_up_next and re.match(r"^\|\s*\d+\s*\|", line):
            lines[i] = re.sub(r"^\|\s*\d+\s*\|", f"| {counter} |", line)
            counter += 1
    text = "\n".join(lines)

    KANBAN_FILE.write_text(text)
    print(f"KANBAN updated: {len(completed_items)} items moved to Done")


# ---------------------------------------------------------------------------
# Action Registry — maps priority patterns to executable functions
# ---------------------------------------------------------------------------

def action_source_ideas(**kwargs) -> Tuple[bool, str]:
    """Source new research ideas via LLM."""
    print("  Executing: run_rbi.py --source-ideas")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "run_rbi.py"), "--source-ideas"],
        capture_output=True, text=True, timeout=300,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "strategies" / "backtest")},
    )
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr[-300:]}")
        return False, f"run_rbi.py --source-ideas failed (exit {result.returncode})"
    # Check if ideas were actually added (LLM call might silently fail)
    if "New ideas sourced:" in result.stdout or "Added" in result.stdout:
        return True, "Sourced new research ideas via LLM"
    if "LLM call failed" in result.stdout or "No parseable ideas" in result.stdout:
        return False, "LLM idea sourcing failed (API key missing or LLM error)"
    return True, "Sourced new research ideas via LLM"


def action_screen_ideas(idea_ids: str = "", **kwargs) -> Tuple[bool, str]:
    """Screen specific research ideas."""
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "run_rbi.py")]
    if idea_ids:
        cmd.extend(["--ids", idea_ids])
    print(f"  Executing: run_rbi.py --ids {idea_ids}")
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=600,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "strategies" / "backtest")},
    )
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr[-300:]}")
        return False, f"Screening failed (exit {result.returncode})"
    return True, f"Screened ideas: {idea_ids or 'all new'}"


def action_walk_forward_validate(idea_ids: str = "", **kwargs) -> Tuple[bool, str]:
    """Run walk-forward validation on promoted strategies by re-screening them."""
    # Walk-forward validation uses the same pipeline but on promoted strategies
    ids = idea_ids or "R007,R009,R011"
    print(f"  Executing: run_rbi.py --ids {ids} (walk-forward re-screen)")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "run_rbi.py"), "--ids", ids],
        capture_output=True, text=True, timeout=600,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "strategies" / "backtest")},
    )
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr[-300:]}")
        return False, f"Walk-forward validation failed (exit {result.returncode})"
    return True, f"Walk-forward validation completed for {ids}"


def action_create_hypothesis_docs(idea_ids: str = "", **kwargs) -> Tuple[bool, str]:
    """Generate hypothesis documents for promoted strategies using LLM."""
    # Read the research backlog to get promoted strategy details
    backlog_text = BACKLOG_FILE.read_text()

    # Find promoted strategies
    promoted = []
    for line in backlog_text.split("\n"):
        if "promoted" in line.lower() and line.strip().startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 5:
                promoted.append({
                    "id": cells[0],
                    "name": cells[1],
                    "source": cells[2],
                    "thesis": cells[3],
                    "notes": cells[5] if len(cells) > 5 else "",
                })

    if not promoted:
        return False, "No promoted strategies found in backlog"

    # Determine next hypothesis number
    existing = list(STRATEGIES_DIR.glob("HYPOTHESIS_*.md"))
    existing_nums = []
    for f in existing:
        m = re.search(r"HYPOTHESIS_(\d+)", f.name)
        if m:
            existing_nums.append(int(m.group(1)))
    next_num = max(existing_nums) + 1 if existing_nums else 1

    created = []
    for strat in promoted:
        hyp_num = f"{next_num:03d}"
        filename = f"HYPOTHESIS_{hyp_num}.md"
        filepath = STRATEGIES_DIR / filename

        if filepath.exists():
            print(f"  Skipping {filename} — already exists")
            next_num += 1
            continue

        print(f"  Generating {filename} for {strat['id']} ({strat['name']})...")

        # Load existing hypothesis as template reference
        template_ref = ""
        template_file = STRATEGIES_DIR / "HYPOTHESIS_003.md"
        if template_file.exists():
            template_ref = template_file.read_text()[:2000]

        prompt = f"""Create a hypothesis document for a promoted trading strategy.

## Strategy Details
- Research ID: {strat['id']}
- Name: {strat['name']}
- Source: {strat['source']}
- Thesis: {strat['thesis']}
- Screen Results: {strat['notes']}

## Template Reference (follow this structure)
{template_ref}

## Instructions
- Create a HYPOTHESIS_{hyp_num}.md document following the exact same structure as the template
- Status should be "PROMOTED — awaiting full validation"
- Include the screening results from the notes above
- Fill in all sections: Thesis, Parameters, Edge Hypothesis, Validation Criteria, Implementation Plan
- Data Requirements: we have 3 years of BTCUSD 15m and 1h data (105K and 26K bars)
- Include the best parameters from screening
- This is a PROMOTED strategy that passed quick-screen — next step is walk-forward validation
"""

        system = """You are a quantitative trading researcher. Generate clean, structured hypothesis documents in markdown. Be precise with numbers and parameters. Follow the template exactly."""

        try:
            content = generate(prompt=prompt, system=system)
            # Ensure proper header
            if not content.startswith("# Strategy Hypothesis"):
                content = f"# Strategy Hypothesis {hyp_num}: {strat['name']}\n\n{content}"

            filepath.write_text(content)
            created.append(filename)
            print(f"  Created: {filepath}")
        except Exception as e:
            print(f"  Failed to generate {filename}: {e}")

        next_num += 1

    if created:
        return True, f"Created hypothesis docs: {', '.join(created)}"
    return False, "No new hypothesis docs created"


def action_fetch_multi_asset(assets: str = "ETHUSDT,SOLUSDT", **kwargs) -> Tuple[bool, str]:
    """Fetch data for additional crypto assets. Skips files that already exist."""
    fetched = []
    skipped = []
    failed = []
    for symbol in assets.split(","):
        symbol = symbol.strip()
        if not symbol:
            continue
        clean_name = symbol.replace("USDT", "USD")
        output_path = DATA_DIR / f"{clean_name}_1h.csv"

        # Skip if data already exists and is reasonably fresh (>100 bytes)
        if output_path.exists() and output_path.stat().st_size > 100:
            print(f"  {clean_name} data already exists ({output_path.stat().st_size:,} bytes). Skipping.")
            skipped.append(clean_name)
            continue

        print(f"  Fetching 1h data for {symbol}...")
        try:
            _fetch_symbol(symbol, "1h", 1095, output_path)
            if output_path.exists() and output_path.stat().st_size > 100:
                fetched.append(clean_name)
            else:
                failed.append(f"{symbol}: empty output")
        except Exception as e:
            print(f"  Failed to fetch {symbol}: {e}")
            failed.append(f"{symbol}: {e}")

    msg_parts = []
    if skipped:
        msg_parts.append(f"Already exists: {', '.join(skipped)}")
    if fetched:
        msg_parts.append(f"Fetched: {', '.join(fetched)}")
    if failed:
        msg_parts.append(f"Failed: {', '.join(failed)}")

    if fetched or skipped:
        return True, "; ".join(msg_parts)
    return False, "; ".join(msg_parts) or "No data fetched"


# Hard limits for data fetching (prevents hangs on CI)
FETCH_MAX_REQUESTS = 200        # ~200K candles max
FETCH_TIMEOUT_PER_REQ = 15      # seconds per HTTP request
FETCH_TOTAL_TIMEOUT = 300       # 5 min hard ceiling per symbol
FETCH_MAX_CONSECUTIVE_ERRORS = 5  # give up after 5 failures in a row


def _fetch_symbol(symbol: str, interval: str, days: int, output_path: Path):
    """Fetch OHLCV data with Binance → Bybit fallback (handles HTTP 451 geoblock)."""
    import csv
    import time as _time
    from datetime import timedelta
    import urllib.request
    import urllib.error

    # Try Binance first, fall back to Bybit if geoblocked (HTTP 451)
    all_data = []
    try:
        all_data = _fetch_binance(symbol, interval, days)
    except RuntimeError as e:
        if "451" in str(e) or "403" in str(e):
            print(f"  Binance geoblocked. Falling back to Bybit...")
            try:
                all_data = _fetch_bybit(symbol, interval, days)
            except Exception as bybit_err:
                raise RuntimeError(
                    f"Both Binance and Bybit failed for {symbol}. "
                    f"Binance: {e} | Bybit: {bybit_err}"
                )
        else:
            raise

    if not all_data:
        raise RuntimeError(f"No data received for {symbol} from any source")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["datetime", "open", "high", "low", "close", "volume"])
        for candle in all_data:
            ts = datetime.fromtimestamp(candle[0] / 1000)
            writer.writerow([
                ts.strftime("%Y-%m-%d %H:%M:%S"),
                candle[1], candle[2], candle[3], candle[4], candle[5],
            ])

    print(f"  Saved {len(all_data):,} candles to {output_path}")


def _fetch_binance(symbol: str, interval: str, days: int) -> list:
    """Fetch from Binance API. Returns list of [ts, o, h, l, c, v, ...] candles."""
    import time as _time
    from datetime import timedelta
    import urllib.request

    base_url = "https://api.binance.com/api/v3/klines"
    all_data = []
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    current_start = start_time
    request_count = 0
    consecutive_errors = 0
    wall_start = _time.monotonic()

    print(f"  [Binance] Fetching {days} days of {interval} data for {symbol}...")

    while current_start < end_time:
        if request_count >= FETCH_MAX_REQUESTS:
            print(f"  Hit request limit ({FETCH_MAX_REQUESTS}). Stopping.")
            break
        if _time.monotonic() - wall_start > FETCH_TOTAL_TIMEOUT:
            print(f"  Hit time limit ({FETCH_TOTAL_TIMEOUT}s). Stopping.")
            break

        url = (
            f"{base_url}?symbol={symbol}&interval={interval}"
            f"&startTime={current_start}&limit=1000"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_PER_REQ) as response:
                data = json.loads(response.read().decode())
                if not data:
                    break
                all_data.extend(data)
                current_start = data[-1][0] + 1
                request_count += 1
                consecutive_errors = 0
                if request_count % 10 == 0:
                    print(f"    {len(all_data):,} candles ({request_count} reqs)...")
                if request_count % 50 == 0:
                    _time.sleep(1)
        except Exception as e:
            consecutive_errors += 1
            print(f"    Error ({consecutive_errors}/{FETCH_MAX_CONSECUTIVE_ERRORS}): {e}")
            if consecutive_errors >= FETCH_MAX_CONSECUTIVE_ERRORS:
                raise RuntimeError(
                    f"Fetch aborted for {symbol}: {FETCH_MAX_CONSECUTIVE_ERRORS} "
                    f"consecutive errors. Last: {e}"
                )
            _time.sleep(2)
            continue

    return all_data


def _fetch_bybit(symbol: str, interval: str, days: int) -> list:
    """Fetch from Bybit API. Returns Binance-compatible [ts, o, h, l, c, v] candles."""
    import time as _time
    from datetime import timedelta
    import urllib.request

    # Map Binance intervals to Bybit intervals
    interval_map = {"1h": "60", "4h": "240", "1d": "D", "15m": "15", "1m": "1", "5m": "5"}
    bybit_interval = interval_map.get(interval, interval)

    all_data = []
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    current_start = start_time
    request_count = 0
    consecutive_errors = 0
    wall_start = _time.monotonic()

    print(f"  [Bybit] Fetching {days} days of {interval} data for {symbol}...")

    while current_start < end_time:
        if request_count >= FETCH_MAX_REQUESTS:
            print(f"  Hit request limit ({FETCH_MAX_REQUESTS}). Stopping.")
            break
        if _time.monotonic() - wall_start > FETCH_TOTAL_TIMEOUT:
            print(f"  Hit time limit ({FETCH_TOTAL_TIMEOUT}s). Stopping.")
            break

        url = (
            f"https://api.bybit.com/v5/market/kline"
            f"?category=spot&symbol={symbol}&interval={bybit_interval}"
            f"&start={current_start}&limit=1000"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT_PER_REQ) as response:
                resp = json.loads(response.read().decode())
                rows = resp.get("result", {}).get("list", [])
                if not rows:
                    break
                # Bybit returns [ts, o, h, l, c, v, turnover] in DESCENDING order
                rows.sort(key=lambda r: int(r[0]))
                for r in rows:
                    ts_ms = int(r[0])
                    if ts_ms < current_start:
                        continue
                    # Convert to Binance-compatible format: [ts, o, h, l, c, v]
                    all_data.append([ts_ms, r[1], r[2], r[3], r[4], r[5]])
                current_start = int(rows[-1][0]) + 1
                request_count += 1
                consecutive_errors = 0
                if request_count % 10 == 0:
                    print(f"    {len(all_data):,} candles ({request_count} reqs)...")
                if request_count % 50 == 0:
                    _time.sleep(1)
        except Exception as e:
            consecutive_errors += 1
            print(f"    Error ({consecutive_errors}/{FETCH_MAX_CONSECUTIVE_ERRORS}): {e}")
            if consecutive_errors >= FETCH_MAX_CONSECUTIVE_ERRORS:
                raise RuntimeError(
                    f"Fetch aborted for {symbol} (Bybit): {FETCH_MAX_CONSECUTIVE_ERRORS} "
                    f"consecutive errors. Last: {e}"
                )
            _time.sleep(2)
            continue

    # Deduplicate by timestamp
    seen = set()
    deduped = []
    for candle in all_data:
        ts = candle[0]
        if ts not in seen:
            seen.add(ts)
            deduped.append(candle)
    deduped.sort(key=lambda c: c[0])

    print(f"  [Bybit] Got {len(deduped):,} candles in {request_count} requests")
    return deduped


def action_paper_trade_health_check(**kwargs) -> Tuple[bool, str]:
    """Check paper trading strategies for early kill criteria."""
    registry_path = DATA_DIR / "paper_trade_registry.json"
    if not registry_path.exists():
        return False, "No paper_trade_registry.json found"

    registry = json.loads(registry_path.read_text())
    active = registry.get("active", [])
    if not active:
        return True, "No active paper trading strategies"

    alerts = []
    healthy = []
    for strat in active:
        sid = strat["id"]
        state_file = DATA_DIR / f"paper_trade_{sid}_state.json"
        if not state_file.exists():
            healthy.append(f"{sid}: no state yet")
            continue

        state = json.loads(state_file.read_text())
        trades = state.get("trades", [])
        kill_pf = strat.get("graduation", {}).get("kill_pf_below", 0.7)
        kill_min = strat.get("graduation", {}).get("kill_min_trades", 10)
        max_dd = strat.get("graduation", {}).get("max_drawdown_pct", 25)

        # Check kill criteria
        if len(trades) >= kill_min:
            gross_wins = sum(t.get("pnl_pct", 0) for t in trades if t.get("pnl_pct", 0) > 0)
            gross_losses = abs(sum(t.get("pnl_pct", 0) for t in trades if t.get("pnl_pct", 0) < 0))
            pf = gross_wins / gross_losses if gross_losses > 0 else 99
            if pf < kill_pf:
                alerts.append(f"{sid}: PF {pf:.2f} below kill threshold {kill_pf} ({len(trades)} trades)")
            else:
                healthy.append(f"{sid}: PF {pf:.2f}, {len(trades)} trades")
        else:
            healthy.append(f"{sid}: {len(trades)} trades (need {kill_min} for kill check)")

    msg_parts = []
    if alerts:
        msg_parts.append(f"ALERTS: {'; '.join(alerts)}")
    msg_parts.append(f"Healthy: {len(healthy)}/{len(active)} strategies")

    return True, "; ".join(msg_parts)


def action_test_evening_review(**kwargs) -> Tuple[bool, str]:
    """Test the evening review workflow end-to-end."""
    print("  Executing: run_evening.py (dry test)")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "run_evening.py")],
        capture_output=True, text=True, timeout=120,
        env={
            **os.environ,
            # Don't send a real email during test
            "RESEND_API_KEY": "",
            "EMAIL_TO": "",
        },
    )
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr[-300:]}")
        return False, f"Evening review test failed (exit {result.returncode})"
    return True, "Evening review workflow tested successfully (no email sent)"


# ---------------------------------------------------------------------------
# Priority Matcher — maps KANBAN items to actions
# ---------------------------------------------------------------------------

# Pattern → (action_func, kwargs_extractor)
ACTION_PATTERNS = [
    # Source research ideas
    (r"[Ss]ource.*research ideas|[Ss]ource.*ideas.*LLM|run_rbi.*--source-ideas|[Ss]ource.*new.*ideas.*R\d{3}",
     action_source_ideas, {}),

    # Walk-forward validation
    (r"[Ww]alk.?forward.*valid|[Vv]alidate.*promoted|[Vv]alidate.*R\d{3}",
     action_walk_forward_validate, {}),

    # Create hypothesis docs
    (r"[Cc]reate.*HYPOTHESIS.*doc|[Cc]reate.*hypothesis.*doc|HYPOTHESIS_\d+/\d+/\d+",
     action_create_hypothesis_docs, {}),

    # Screen specific ideas
    (r"[Ss]creen.*(R\d{3}(?:.*R\d{3})*)",
     action_screen_ideas, {}),

    # Fetch multi-asset data (ETH/SOL)
    (r"[Ff]etch.*(?:ETH|SOL|multi.?asset)|(?:ETH|SOL).*data",
     action_fetch_multi_asset, {}),

    # Test evening review
    (r"[Tt]est.*evening.*review|evening.*review.*test",
     action_test_evening_review, {}),

    # Paper trading health check
    (r"[Pp]aper.*trad.*health|[Pp]aper.*trad.*check|[Cc]heck.*early.*kill",
     action_paper_trade_health_check, {}),
]


def match_action(item_text: str) -> Optional[Dict]:
    """Match a KANBAN item to an executable action."""
    for pattern, action_func, default_kwargs in ACTION_PATTERNS:
        match = re.search(pattern, item_text)
        if match:
            kwargs = dict(default_kwargs)
            # Extract idea IDs if present
            ids_match = re.findall(r"R\d{3}", item_text)
            if ids_match and "idea_ids" not in kwargs:
                kwargs["idea_ids"] = ",".join(ids_match)
            return {
                "action": action_func,
                "kwargs": kwargs,
                "name": action_func.__name__,
                "description": action_func.__doc__.strip().split("\n")[0],
            }
    return None


# ---------------------------------------------------------------------------
# Execution Engine
# ---------------------------------------------------------------------------

def build_execution_plan(kanban: Dict, max_items: int = 3) -> List[Dict]:
    """Build an ordered execution plan from KANBAN state."""
    plan = []

    # First: items in "Doing" (highest priority)
    for item in kanban["doing"]:
        action = match_action(item["item"])
        if action:
            plan.append({
                "source": "doing",
                "item_text": item["item"],
                **action,
            })

    # Then: items in "Up Next" (in order)
    for item in kanban["up_next"]:
        if len(plan) >= max_items:
            break
        action = match_action(item["item"])
        if action:
            plan.append({
                "source": f"up_next #{item['number']}",
                "item_text": item["item"],
                **action,
            })
        else:
            print(f"  WARNING: No action mapping for: {item['item']}")

    return plan[:max_items]


def execute_plan(plan: List[Dict], dry_run: bool = False) -> List[Dict]:
    """Execute the plan and return results."""
    results = []

    for i, step in enumerate(plan):
        print(f"\n{'='*60}")
        print(f"STEP {i+1}/{len(plan)}: {step['item_text']}")
        print(f"  Action: {step['name']}")
        print(f"  Source: {step['source']}")
        print(f"{'='*60}")

        if dry_run:
            print("  [DRY RUN] Would execute this action")
            results.append({
                "item": step["item_text"],
                "action": step["name"],
                "success": True,
                "message": "[dry run]",
            })
            continue

        try:
            success, message = step["action"](**step["kwargs"])
            print(f"\n  Result: {'SUCCESS' if success else 'FAILED'} — {message}")
            results.append({
                "item": step["item_text"],
                "action": step["name"],
                "success": success,
                "message": message,
            })
        except Exception as e:
            print(f"\n  EXCEPTION: {e}")
            results.append({
                "item": step["item_text"],
                "action": step["name"],
                "success": False,
                "message": f"Exception: {e}",
            })

    return results


def save_execution_report(results: List[Dict]) -> Path:
    """Save execution report as markdown."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    report_path = DATA_DIR / f"execution_{timestamp}.md"

    lines = [
        f"# Priority Execution Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    if not results:
        lines.extend([
            "**No executable priorities found in KANBAN.**",
            "",
            "The system is in monitoring mode. Paper trading is running autonomously.",
            "Next scheduled work: check KANBAN Up Next for queued items.",
        ])
        report_path.write_text("\n".join(lines))
        print(f"\nExecution report saved to: {report_path}")
        return report_path

    lines.extend([
        f"Executed {len(results)} priorities.",
        "",
        "| # | Priority | Action | Result |",
        "|:-:|----------|--------|--------|",
    ])

    succeeded = 0
    for i, r in enumerate(results):
        status = "Done" if r["success"] else "FAILED"
        if r["success"]:
            succeeded += 1
        lines.append(f"| {i+1} | {r['item'][:50]} | {r['action']} | {status}: {r['message'][:60]} |")

    lines.extend([
        "",
        f"**Summary: {succeeded}/{len(results)} priorities completed successfully.**",
    ])

    report_path.write_text("\n".join(lines))
    print(f"\nExecution report saved to: {report_path}")
    return report_path


# ---------------------------------------------------------------------------
# Failure Alerting
# ---------------------------------------------------------------------------

def _send_failure_alert(results: List[Dict], report_path: Path):
    """Email Sipho when priority execution has failures."""
    failed = [r for r in results if not r["success"]]
    succeeded = [r for r in results if r["success"]]
    today = datetime.now().strftime("%Y-%m-%d")

    body = f"# Priority Execution Alert — {today}\n\n"
    body += f"**{len(failed)} of {len(results)} priorities FAILED.**\n\n"

    body += "## Failed\n\n"
    for r in failed:
        body += f"- **{r['item']}** — {r['message']}\n"

    if succeeded:
        body += "\n## Succeeded\n\n"
        for r in succeeded:
            body += f"- {r['item']}\n"

    body += f"\n---\n*Automated alert from AI Chief of Staff. "
    body += f"Report: {report_path.name}*\n"

    print("\n--- Sending failure alert email ---")
    sent = send_email(
        subject=f"[ALERT] {len(failed)} priority execution failure(s) — {today}",
        body=markdown_to_html(body),
        html=True
    )
    if sent:
        print("  Alert email sent.")
    else:
        print("  WARNING: Could not send alert email (check RESEND_API_KEY / EMAIL_TO)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Execute KANBAN priorities")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show execution plan without running anything")
    parser.add_argument("--max", type=int, default=3,
                        help="Maximum number of priorities to execute (default: 3)")
    args = parser.parse_args()

    print("=" * 60)
    print("AI CHIEF OF STAFF — PRIORITY EXECUTION")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Step 1: Parse KANBAN
    print("\n--- Reading KANBAN ---")
    kanban = parse_kanban()
    print(f"  Doing: {len(kanban['doing'])} items")
    print(f"  Up Next: {len(kanban['up_next'])} items")
    for item in kanban["doing"]:
        print(f"    [DOING] {item['item']}")
    for item in kanban["up_next"]:
        print(f"    [#{item['number']}] {item['item']}")

    # Step 2: Build execution plan
    print("\n--- Building Execution Plan ---")
    plan = build_execution_plan(kanban, max_items=args.max)

    if not plan:
        print("  No executable priorities found.")
        # Still generate a report so the system doesn't go silent
        report_path = save_execution_report([])
        print(f"  Empty execution report saved to: {report_path}")
        return

    print(f"\n  Execution plan ({len(plan)} steps):")
    for i, step in enumerate(plan):
        print(f"    {i+1}. [{step['source']}] {step['item_text']}")
        print(f"       → {step['description']}")

    if args.dry_run:
        print("\n  [DRY RUN MODE — no actions will be executed]")

    # Step 3: Execute
    print("\n--- Executing Priorities ---")
    results = execute_plan(plan, dry_run=args.dry_run)

    # Step 4: Update KANBAN with completed items
    if not args.dry_run:
        completed = [r["item"] for r in results if r["success"]]
        if completed:
            print("\n--- Updating KANBAN ---")
            update_kanban(completed)

    # Step 5: Save report
    report_path = save_execution_report(results)

    # Summary
    succeeded = sum(1 for r in results if r["success"])
    failed_count = len(results) - succeeded
    print(f"\n{'=' * 60}")
    print("EXECUTION COMPLETE")
    print(f"  Executed: {len(results)} priorities")
    print(f"  Succeeded: {succeeded}")
    print(f"  Failed: {failed_count}")
    print(f"  Report: {report_path}")
    print(f"{'=' * 60}")

    # Send failure alert email if anything went wrong
    if failed_count > 0 and not args.dry_run:
        _send_failure_alert(results, report_path)


if __name__ == "__main__":
    main()
