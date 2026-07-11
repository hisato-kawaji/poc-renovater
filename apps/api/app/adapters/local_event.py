import httpx
import asyncio
import json
import base64
import logging
from typing import Any, Dict
from app.ports.event import EventPublisherPort

logger = logging.getLogger(__name__)

class LocalEventPublisher(EventPublisherPort):
    def __init__(self, endpoint_url: str = "http://127.0.0.1:8000/api/events/pubsub"):
        self.endpoint_url = endpoint_url

    async def publish(self, topic: str, event_type: str, payload: Dict[str, Any]) -> str:
        data_str = json.dumps(payload)
        data_b64 = base64.b64encode(data_str.encode("utf-8")).decode("utf-8")
        
        push_message = {
            "message": {
                "data": data_b64,
                "attributes": {
                    "event_type": event_type
                },
                "messageId": "local-mock-id"
            },
            "subscription": "projects/mock/subscriptions/mock"
        }
        
        async def _send():
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(self.endpoint_url, json=push_message, timeout=300.0)
                    resp.raise_for_status()
                    logger.info(f"LocalEventPublisher: Successfully sent {event_type} to {self.endpoint_url}")
            except Exception as e:
                logger.error(f"LocalEventPublisher: Failed to send {event_type}: {e}")

        # Fire and forget
        asyncio.create_task(_send())
        return "local-mock-id"
