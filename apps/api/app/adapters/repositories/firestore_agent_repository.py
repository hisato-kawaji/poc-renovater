import asyncio
from typing import Dict, Any, List, Optional
from google.cloud import firestore
from app.domain.repositories.agent_repository import AgentRepository

class FirestoreAgentRepository(AgentRepository):
    def __init__(self, project_id: str, tenant_id: str):
        self.db = firestore.Client(project=project_id)
        self.collection = self.db.collection("tenants").document(tenant_id).collection("agents")

    async def get(self, upload_id: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.collection.document(upload_id)
        doc = await asyncio.to_thread(doc_ref.get)
        if not doc.exists:
            return None
        return doc.to_dict()

    async def list(self) -> List[Dict[str, Any]]:
        agents = await asyncio.to_thread(lambda: list(self.collection.get()))
        return [doc.to_dict() for doc in agents]

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

    async def get_deployments(self, upload_id: str) -> List[Dict[str, Any]]:
        doc_ref = self.collection.document(upload_id)
        deployments = await asyncio.to_thread(lambda: list(doc_ref.collection("deployments").get()))
        return [{"id": d.id, **d.to_dict()} for d in deployments]

    async def save_deployment(self, upload_id: str, deployment_data: Dict[str, Any]) -> None:
        doc_ref = self.collection.document(upload_id).collection("deployments")
        await asyncio.to_thread(doc_ref.add, deployment_data)

    async def get_messages(self, upload_id: str) -> List[Dict[str, Any]]:
        doc_ref = self.collection.document(upload_id)
        # Order by timestamp to get conversation history in order
        query = doc_ref.collection("messages").order_by("timestamp")
        messages = await asyncio.to_thread(lambda: list(query.get()))
        return [{"id": m.id, **m.to_dict()} for m in messages]

    async def save_message(self, upload_id: str, message_data: Dict[str, Any]) -> None:
        doc_ref = self.collection.document(upload_id).collection("messages")
        await asyncio.to_thread(doc_ref.add, message_data)

    # --- Job Management ---
    async def get_jobs(self, upload_id: str) -> List[Dict[str, Any]]:
        doc_ref = self.collection.document(upload_id)
        jobs = await asyncio.to_thread(lambda: list(doc_ref.collection("jobs").get()))
        return [{"id": j.id, **j.to_dict()} for j in jobs]

    async def get_job(self, upload_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.collection.document(upload_id).collection("jobs").document(job_id)
        doc = await asyncio.to_thread(doc_ref.get)
        if not doc.exists:
            return None
        return {"id": doc.id, **doc.to_dict()}

    async def save_job(self, upload_id: str, job_id: str, job_data: Dict[str, Any]) -> None:
        doc_ref = self.collection.document(upload_id).collection("jobs").document(job_id)
        await asyncio.to_thread(doc_ref.set, job_data)

    async def update_job(self, upload_id: str, job_id: str, updates: Dict[str, Any]) -> None:
        doc_ref = self.collection.document(upload_id).collection("jobs").document(job_id)
        await asyncio.to_thread(doc_ref.update, updates)
