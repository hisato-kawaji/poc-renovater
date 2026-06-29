import json
import logging
import os
from typing import Any, Dict
from google.cloud import pubsub_v1
from app.ports.event import EventPublisherPort

logger = logging.getLogger(__name__)

class PubSubEventPublisher(EventPublisherPort):
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.publisher = pubsub_v1.PublisherClient()

    async def publish(self, topic: str, event_type: str, payload: Dict[str, Any]) -> str:
        topic_path = self.publisher.topic_path(self.project_id, topic)
        data = json.dumps(payload).encode("utf-8")
        
        import asyncio
        loop = asyncio.get_running_loop()
        
        def _publish():
            future = self.publisher.publish(topic_path, data, event_type=event_type)
            return future.result()
            
        try:
            message_id = await loop.run_in_executor(None, _publish)
            logger.info(f"Published event {event_type} to {topic} with ID {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to publish event {event_type} to {topic}: {e}")
            raise
