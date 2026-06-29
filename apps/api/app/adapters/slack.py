import httpx
import logging

logger = logging.getLogger(__name__)

async def send_slack_notification(webhook_url: str, message: str) -> None:
    if not webhook_url:
        return
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(webhook_url, json={"text": message})
            if resp.status_code != 200:
                logger.warning(f"Slack notification failed: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")
