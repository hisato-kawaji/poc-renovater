from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class AgentRepository(ABC):
    @abstractmethod
    async def get(self, upload_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def save(self, upload_id: str, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def update(self, upload_id: str, updates: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_issues(self, upload_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def save_issue(self, upload_id: str, issue_id: str, issue_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def update_issue(self, upload_id: str, issue_id: str, updates: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_pulls(self, upload_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def save_pull(self, upload_id: str, pull_data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def update_pull(self, upload_id: str, pr_number: int, updates: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def save_deployment(self, upload_id: str, deployment_data: Dict[str, Any]) -> None:
        pass
