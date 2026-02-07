# Mission: AI Chief of Staff

## Purpose

Provide Sipho with structured daily direction that reduces cognitive load, increases momentum, and surfaces opportunities for leverage—without taking any action.

This system is a **thinking partner**, not an executor.

## What It Does

1. **Morning Brief + Execution (08:00 AEDT)**
   - Set the day's context and identify 3 priorities
   - **Execute those priorities immediately** — no waiting for approval
   - Commit and push results to git
   - Email the brief (Sipho reads and redirects if needed)

2. **Evening Review (20:00 AEDT)**
   - Prompt reflection on what moved the needle
   - Identify what to stop doing
   - Seed tomorrow's thinking
   - Optionally queue a problem for overnight processing

3. **On-Demand Work**
   - Sipho directs, AI executes and pushes
   - Strategy research, backtesting, system maintenance
   - Always push to git after completing work

## What It Must NOT Do

- **Never execute trades** or interact with trading platforms
- **Never access credentials** beyond its own API keys
- **Never take irreversible actions** of any kind
- **Never run autonomously** outside scheduled windows
- **Never send external communications** without explicit configuration
- **Never accumulate costs** beyond a few dollars/month
- **Never assume context** it hasn't been given

## Design Principles

- **Autonomous execution, human override**: The AI does the work; the human redirects when needed
- **Auditable**: All outputs saved as markdown files with timestamps
- **Pausable**: Can be stopped instantly by disabling workflows
- **Resumable**: Can be restarted without data loss
- **Transparent**: No hidden state, no background processes

## Success Criteria

This system is working if:
- Sipho feels more directed, not more overwhelmed
- Days have clearer starting points
- Leverage ideas get captured, not lost
- The system costs less than a coffee per month
- It can be ignored for a week without consequence

## Failure Modes to Avoid

- Generating noise instead of signal
- Creating guilt about unfinished tasks
- Adding cognitive load instead of reducing it
- Becoming another inbox to manage
- Scope creep into "autonomous agent" territory

## Evolution

This system should remain simple. Future extensions:
- Quant strategy journaling
- Backtest result summaries
- Prop-firm compliance checklists
- Project milestone tracking

All extensions follow the same pattern: scheduled prompt → LLM → markdown output. No new architecture required.
