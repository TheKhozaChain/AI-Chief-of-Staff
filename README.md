# AI Chief of Staff

A GitHub-native personal operating system that runs via scheduled Actions. No servers, no daemons, no always-on infrastructure.

## What This Does

Twice daily (08:00 and 20:00 AEDT), this system generates:
- **Morning Brief**: Priorities, focus blocks, and leverage ideas to start the day
- **Evening Review**: Reflection prompts, momentum assessment, and tomorrow's seed

All output is saved to `data/` as timestamped markdown files. Nothing is executed automatically—only recommendations are generated.

## Architecture

```
.
├── USER.md                 # Who you are, what you want
├── MISSION.md              # What this system does (and doesn't)
├── OPERATING_PRINCIPLES.md # How it behaves
├── PROMPTS/                # Prompt templates
│   ├── morning_brief.md
│   ├── evening_review.md
│   └── reverse_prompt.md
├── scripts/                # Python runners
│   ├── llm.py              # Minimal LLM wrapper
│   ├── run_morning.py
│   └── run_evening.py
├── data/                   # Outputs and state
│   ├── memory.json         # Persistent context
│   └── todo.json           # Task tracking
└── .github/workflows/      # Scheduled automation
    ├── morning.yml
    └── evening.yml
```

## Setup

### 1. Clone and Configure

```bash
git clone https://github.com/TheKhozaChain/AI-Chief-of-Staff.git
cd AI-Chief-of-Staff
```

### 2. Set Repository Secrets

In GitHub → Settings → Secrets and variables → Actions, add:

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (recommended) |
| `OPENAI_API_KEY` | Your OpenAI API key (alternative) |
| `LLM_PROVIDER` | `anthropic` or `openai` (default: `anthropic`) |
| `RESEND_API_KEY` | (Optional) Resend API key for email delivery |
| `EMAIL_TO` | (Optional) Your email address for receiving briefs |

### 3. Enable Actions

Go to the Actions tab and enable workflows if prompted.

### 4. Test Locally (Optional)

```bash
pip install anthropic openai python-dotenv
export ANTHROPIC_API_KEY=your_key
python scripts/run_morning.py
```

## How to Pause

Option A: Disable workflows in GitHub Actions settings
Option B: Comment out the `schedule` block in `.github/workflows/*.yml`
Option C: Delete the workflow files (they're versioned, easy to restore)

## How to Resume

Uncomment the cron schedule or re-enable workflows.

## Cost

- Anthropic Claude Haiku: ~$0.002 per run
- Two runs per day = ~$0.12/month
- Even with Claude Sonnet: under $2/month

## Manual Runs

You can trigger either workflow manually via GitHub Actions → Select workflow → "Run workflow"

## Email Delivery (Optional)

To receive briefs in your inbox:

1. Sign up at [resend.com](https://resend.com) (free tier: 100 emails/day)
2. Create an API key
3. Add these secrets to GitHub:
   - `RESEND_API_KEY`: Your Resend API key
   - `EMAIL_TO`: Your email address

Emails are sent automatically if both secrets are set. If not set, the system still works—it just saves to files only.

## Evolution Path

This system is designed to grow:

1. **Quant Research Support**: Add prompts for strategy journaling, backtest summaries, prop-firm rule checks
2. **Project Planning**: Add prompts for e-commerce milestones, content calendars
3. **Memory Expansion**: The `memory.json` can accumulate insights, patterns, and decisions over time
4. **GitHub Issues Integration**: Output can be posted as issues for tracking
5. **Email Delivery**: Add SendGrid/Resend for inbox delivery

No architectural changes required—just add prompts and extend the runners.

## Philosophy

This system is intentionally boring. It:
- Runs on a schedule
- Generates text
- Saves files
- Does nothing else

That's the point. Reliability over cleverness. Human control over automation. Momentum over perfection.

---

Built for Sipho Khoza. Powered by scheduled cron and an LLM.
