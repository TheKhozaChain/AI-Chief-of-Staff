"""
Email sender for AI Chief of Staff.

Uses Resend (https://resend.com) - simple API, free tier includes 100 emails/day.
Set RESEND_API_KEY and EMAIL_TO in environment or GitHub Secrets.
"""

import os
import json
from urllib import request, error


def send_email(subject: str, body: str, html: bool = False) -> bool:
    """
    Send an email via Resend API.

    Args:
        subject: Email subject line
        body: Email body (plain text or HTML)
        html: If True, body is treated as HTML

    Returns:
        True if sent successfully, False otherwise

    Required environment variables:
        RESEND_API_KEY: Your Resend API key
        EMAIL_TO: Recipient email address
        EMAIL_FROM: (Optional) Sender address, defaults to onboarding@resend.dev
    """
    api_key = os.environ.get("RESEND_API_KEY")
    email_to = os.environ.get("EMAIL_TO")
    email_from = os.environ.get("EMAIL_FROM", "onboarding@resend.dev")

    if not api_key:
        print("Email skipped: RESEND_API_KEY not set")
        return False

    if not email_to:
        print("Email skipped: EMAIL_TO not set")
        return False

    # Build request
    url = "https://api.resend.com/emails"

    payload = {
        "from": email_from,
        "to": [email_to],
        "subject": subject,
    }

    if html:
        payload["html"] = body
    else:
        payload["text"] = body

    data = json.dumps(payload).encode("utf-8")

    req = request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AI-Chief-of-Staff/1.0",
        },
        method="POST"
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"Email sent: {result.get('id', 'success')}")
            return True
    except error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Email failed: {e.code}")
        print(f"Error details: {error_body}")
        print(f"Sender: {email_from}")
        print(f"Recipient: {email_to}")
        return False
    except Exception as e:
        print(f"Email failed: {e}")
        return False


def markdown_to_html(markdown: str) -> str:
    """
    Simple markdown to HTML conversion for email.
    Handles headers, bold, lists, and code blocks.
    """
    import re

    html = markdown

    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

    # Code blocks
    html = re.sub(r'```[\w]*\n(.*?)\n```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)

    # Inline code
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

    # Line breaks
    html = html.replace('\n\n', '</p><p>')
    html = html.replace('\n', '<br>')

    # Wrap in basic styling
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
        <p>{html}</p>
    </div>
    """

    return html


# Test when run directly
if __name__ == "__main__":
    print("Testing email sender...")

    test_body = """### Test Brief

**This is a test** of the AI Chief of Staff email system.

- Item one
- Item two

If you received this, email is working.
"""

    success = send_email(
        subject="Test - AI Chief of Staff",
        body=markdown_to_html(test_body),
        html=True
    )

    print(f"Test result: {'Success' if success else 'Failed'}")
