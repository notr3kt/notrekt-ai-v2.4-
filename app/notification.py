"""
Notification system for HITL approvals (email, Slack, etc.)
"""
import os
import asyncio
import logging
from typing import Any, Dict

# Example: Slack notification (can be extended for email, etc.)
import httpx

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

async def send_slack_notification(action_id: str, action_context: Dict[str, Any]):
    if not SLACK_WEBHOOK_URL:
        logging.warning("No SLACK_WEBHOOK_URL set. Skipping Slack notification.")
        return
    message = f"[HITL] Approval requested for action {action_id}. Context: {action_context}"
    payload = {"text": message}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(SLACK_WEBHOOK_URL, json=payload)
            resp.raise_for_status()
            logging.info(f"Slack notification sent for action {action_id}")
        except Exception as e:
            logging.error(f"Failed to send Slack notification: {e}")

# Example: Email notification (stub)
async def send_email_notification(action_id: str, action_context: Dict[str, Any]):
    # Integrate with SMTP or email API as needed
    logging.info(f"[EMAIL][STUB] Would send email for action {action_id}: {action_context}")

# Unified notification dispatcher
async def notify_all(action_id: str, action_context: Dict[str, Any]):
    await asyncio.gather(
        send_slack_notification(action_id, action_context),
        send_email_notification(action_id, action_context)
    )
