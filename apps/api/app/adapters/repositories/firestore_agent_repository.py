import asyncio
from typing import Dict, Any, List, Optional
from google.cloud import firestore
from app.domain.repositories.agent_repository import AgentRepository

class FirestoreAgentRepository(AgentRepository):
    def __init__(self, project_id: str):
        self.db = firestore.Client(project=project_id)
        self.collection = self.db.collection("agents")

    async def get(self, upload_id: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.collection.document(upload_id)
        doc = await asyncio.to_thread(doc_ref.get)
        if not doc.exists:
            return None
        return doc.to_dict()

    async def save(self, upload_id: str, data: Dict[str, Any]) -> None:
        doc_ref = self.collection.document(upload_id)
        await asyncio.to_thread(doc_ref.set, data)

    async def update(self, upload_id: str, updates: Dict[str, Any]) -> None:
        doc_ref = self.collection.document(upload_id)
        await asyncio.to_thread(doc_ref.update, updates)

    async def get_issues(self, upload_id: str) -> List[Dict[str, Any]]:
        doc_ref = self.collection.document(upload_id)
        issues = await asyncio.to_thread(lambda: list(doc_ref.collection("issues").get()))
        return [{"id": i.id, **i.to_dict()} for i in issues]

    async def save_issue(self, upload_id: str, issue_id: str, issue_data: Dict[str, Any]) -> None:
        doc_ref = self.collection.document(upload_id).collection("issues").document(issue_id)
        await asyncio.to_thread(doc_ref.set, issue_data)

    async def update_issue(self, upload_id: str, issue_id: str, updates: Dict[str, Any]) -> None:
        doc_ref = self.collection.document(upload_id).collection("issues").document(issue_id)
        await asyncio.to_thread(doc_ref.update, updates)

    async def get_pulls(self, upload_id: str) -> List[Dict[str, Any]]:
        doc_ref = self.collection.document(upload_id)
        pulls = await asyncio.to_thread(lambda: list(doc_ref.collection("pulls").get()))
        return [{"id": p.id, **p.to_dict()} for p in pulls]

    async def save_pull(self, upload_id: str, pull_data: Dict[str, Any]) -> None:
        doc_ref = self.collection.document(upload_id).collection("pulls")
        await asyncio.to_thread(doc_ref.add, pull_data)

    async def update_pull(self, upload_id: str, pr_number: int, updates: Dict[str, Any]) -> None:
        pulls = await self.get_pulls(upload_id)
        pull_doc = next((p for p in pulls if str(pr_number) in p.get("url", "")), None)
        if pull_doc:
            doc_ref = self.collection.document(upload_id).collection("pulls").document(pull_doc["id"])
            await asyncio.to_thread(doc_ref.update, updates)

    async def save_deployment(self, upload_id: str, deployment_data: Dict[str, Any]) -> None:
        doc_ref = self.collection.document(upload_id).collection("deployments")
        await asyncio.to_thread(doc_ref.add, deployment_data)
