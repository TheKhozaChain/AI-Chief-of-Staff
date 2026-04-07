# Alert Escalation Policy

Decision policy for what warrants an email alert vs logging vs silence.
Inspired by ClawChief's three-lane model: auto-resolve / recommend / escalate.

---

## Lane 1: Auto-Resolve (log only, no email)

Actions the system takes autonomously. Logged in output files and git history
but no email sent. This is the default for routine operations.

| Event | Action | Log Location |
|-------|--------|-------------|
| Strategy killed at screening | Update backlog status | RBI screen output, RESEARCH_BACKLOG.md |
| Strategy parked (insufficient data) | Update backlog status | RBI screen output |
| Idea sourced and queued | Add to backlog | RBI screen output |
| Paper trade running normally (no events) | Update state file | paper_trade_*_state.json |
| Morning brief generated | Save to data/ | data/morning_*.md |
| Evening review generated | Save to data/ | data/evening_*.md |
| Data refresh completed | Log success | Workflow output |
| Duplicate idea filtered | Skip silently | Pipeline log |
| Saturated archetype skipped | Skip silently | Pipeline log |

---

## Lane 2: Recommend and Flag (email, informational)

Events that Sipho should know about but don't require immediate action.
Included in morning brief and/or sent as individual email alerts.

| Event | Email Subject Pattern | Why Email |
|-------|----------------------|-----------|
| Paper trade ENTRY signal | `[{id} Paper] ENTRY - {direction} BTCUSD` | Track live activity |
| Paper trade EXIT (win or loss) | `[{id} Paper] {WIN/LOSS} - ${pnl}` | Track performance |
| Strategy promoted from screening | Included in RBI summary | Pipeline progress |
| Staleness warning (14+ days no trades) | `[{id} Paper] STALE - no trades detected` | May need regime review |
| Paper trade batch summary | Included in morning brief | Daily awareness |
| Validation results (pass or fail) | Validation report email | Pipeline progress |

---

## Lane 3: Escalate (email, action required)

Events that require Sipho's attention or decision. These are rare and important.

| Event | Email Subject Pattern | Required Action |
|-------|----------------------|----------------|
| Strategy GRADUATED paper trading | `READY FOR LIVE - {id} graduated` | Decide: deploy to live or not |
| Strategy KILLED in paper trading | `[{id} Paper] KILLED - removed` | Review cause, inform future sourcing |
| Zero-trade kill | `[{id} Paper] KILLED - zero trades after 30 days` | Review if regime/archetype mismatch |
| Workflow FAILURE | `[AI CoS] Workflow Failed: {name}` | Debug and fix |
| All paper trades underwater | (not yet implemented) | Review portfolio risk |
| Data pipeline broken | (not yet implemented) | Fix data source |
| Priority execution failure | Failure alert email | Review what broke |

---

## Silence Rules

The system should NOT send alerts for:

- Routine pipeline runs with no notable events
- Strategies that are paper trading normally with no new trades
- Morning/evening briefs (these are delivered separately on their own schedule)
- Duplicate information (if it's in the morning brief, don't also send a separate email)

**Principle: Only speak when there's new, actionable information.**
If nothing changed since last run, the correct output is silence (or `HEARTBEAT_OK`
in ClawChief terms).

---

## Alert Delivery

| Channel | Used For |
|---------|----------|
| Email (Resend API) | All Lane 2 and Lane 3 alerts |
| Git commit + push | All Lane 1 logging |
| Morning brief | Daily digest of pipeline state |
| Evening review | Daily reflection on progress |
| GitHub Actions logs | Debug-level detail |

---

## Future Considerations

- Slack/Telegram integration for Lane 3 (faster than email for urgent items)
- Aggregate alerting: batch Lane 2 events into a single digest instead of per-event
- Smart silence: suppress Lane 2 emails during known quiet periods (weekends, holidays)
