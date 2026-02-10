#!/usr/bin/env python3
"""Send an alert email when a GitHub Actions workflow fails."""

import os
import sys
import json
from urllib import request, error

def main():
    api_key = os.environ.get("RESEND_API_KEY", "")
    email_to = os.environ.get("EMAIL_TO", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "unknown/repo")
    run_id = os.environ.get("GITHUB_RUN_ID", "0")
    workflow = os.environ.get("GITHUB_WORKFLOW", "unknown")

    if not api_key or not email_to:
        print("Cannot send alert: missing RESEND_API_KEY or EMAIL_TO")
        sys.exit(0)

    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"

    payload = {
        "from": "onboarding@resend.dev",
        "to": [email_to],
        "subject": f"[ALERT] {workflow} FAILED",
        "html": (
            f"<h2>{workflow} failed</h2>"
            f"<p>The GitHub Actions workflow failed or timed out.</p>"
            f"<p>Check: <a href='{run_url}'>workflow run</a></p>"
            f"<p><em>Automated alert from AI Chief of Staff</em></p>"
        ),
    }

    data = json.dumps(payload).encode()
    req = request.Request(
        "https://api.resend.com/emails",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15) as resp:
            print(f"Alert sent: {resp.read().decode()}")
    except Exception as e:
        print(f"Alert failed: {e}")


if __name__ == "__main__":
    main()
