import os
import requests

def send_slack_notification(message: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("[ERROR] SLACK_WEBHOOK_URL not set in environment!")
        return False
    payload = {"text": message}
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("[INFO] Slack notification sent!")
            return True
        else:
            print(f"[ERROR] Slack notification failed: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Exception sending Slack notification: {e}")
        return False
