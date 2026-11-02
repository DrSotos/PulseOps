"""Email notification sender using aiosmtplib."""

from __future__ import annotations

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def send_email_notification(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> tuple[bool, str | None]:
    """Send an asynchronous email via SMTP."""
    if not settings.SMTP_HOST:
        logger.info(f"SMTP_HOST not configured. Mocking email delivery to {to_email}")
        return True, None

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.SMTP_FROM_EMAIL or "alerts@pulseops.local"
    msg["To"] = to_email
    msg["Subject"] = subject

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME or None,
            password=settings.SMTP_PASSWORD or None,
            use_tls=settings.SMTP_USE_TLS,
            timeout=15,
        )
        logger.info(f"Email successfully delivered to {to_email}")
        return True, None
    except Exception as e:  # noqa: BLE001
        err = f"SMTP error ({type(e).__name__}): {str(e)[:300]}"
        logger.error(f"Failed sending email to {to_email}: {err}")
        return False, err


def build_incident_email(
    endpoint_name: str,
    endpoint_url: str,
    incident_type: str,
    severity: str,
    status: str,
    description: str,
    detected_at: datetime,
    incident_id: str,
    base_url: str = "http://localhost:3000",
) -> tuple[str, str]:
    """Format subject and HTML body for incident alerting."""
    color_map = {
        "critical": "#ef4444",
        "high": "#f97316",
        "medium": "#eab308",
        "low": "#3b82f6",
    }
    badge_color = color_map.get(severity.lower(), "#64748b")
    subject = f"[PulseOps Alert] [{severity.upper()}] {incident_type.replace('_', ' ').title()} - {endpoint_name}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f19; color: #f3f4f6; padding: 24px;">
      <div style="max-width: 600px; margin: 0 auto; background-color: #111827; border: 1px solid #1f2937; border-radius: 8px; overflow: hidden;">
        <div style="background-color: {badge_color}; padding: 14px 24px;">
          <h2 style="margin: 0; color: #ffffff; font-size: 18px; text-transform: uppercase;">PulseOps Alert: {severity}</h2>
        </div>
        <div style="padding: 24px;">
          <p style="font-size: 16px; margin-top: 0;">An incident has occurred on monitored endpoint <strong>{endpoint_name}</strong>.</p>
          <table style="width: 100%; border-collapse: collapse; margin-top: 16px;">
            <tr>
              <td style="padding: 8px 0; color: #9ca3af; width: 140px;">URL:</td>
              <td style="padding: 8px 0; font-family: monospace; color: #60a5fa;">{endpoint_url}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #9ca3af;">Type:</td>
              <td style="padding: 8px 0; text-transform: capitalize;">{incident_type.replace('_', ' ')}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #9ca3af;">Status:</td>
              <td style="padding: 8px 0; font-weight: 600;">{status.upper()}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #9ca3af;">Detected At:</td>
              <td style="padding: 8px 0;">{detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
            </tr>
            <tr>
              <td style="padding: 8px 0; color: #9ca3af;">Details:</td>
              <td style="padding: 8px 0; color: #f87171;">{description}</td>
            </tr>
          </table>
          <div style="margin-top: 24px;">
            <a href="{base_url}/incidents/{incident_id}" style="background-color: #2563eb; color: #ffffff; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: 500; display: inline-block;">View Incident Details</a>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    return subject, html
