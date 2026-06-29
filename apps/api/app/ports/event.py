from typing import Protocol, Any, Dict

class EventPublisherPort(Protocol):
    async def publish(self, topic: str, event_type: str, payload: Dict[str, Any]) -> str:
        """Publishes an event to a topic. Returns the message ID."""
        ...
