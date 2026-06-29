import json
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.domain.repositories.agent_repository import AgentRepository

class SQLAgentRepository(AgentRepository):
    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def get(self, upload_id: str) -> Optional[Dict[str, Any]]:
        result = await self.session.execute(
            text("SELECT data FROM agents WHERE id = :upload_id AND tenant_id = :tenant_id"),
            {"upload_id": upload_id, "tenant_id": self.tenant_id}
        )
        row = result.fetchone()
        if not row:
            return None
        return json.loads(row[0])

    async def list(self) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            text("SELECT data FROM agents WHERE tenant_id = :tenant_id"),
            {"tenant_id": self.tenant_id}
        )
        return [json.loads(row[0]) for row in result.fetchall()]

    async def save(self, upload_id: str, data: Dict[str, Any]) -> None:
        data_json = json.dumps(data)
        await self.session.execute(
            text("""
                INSERT INTO agents (id, tenant_id, data) 
                VALUES (:upload_id, :tenant_id, :data)
                ON CONFLICT (id, tenant_id) DO UPDATE SET data = EXCLUDED.data
            """),
            {"upload_id": upload_id, "tenant_id": self.tenant_id, "data": data_json}
        )
        await self.session.commit()

    async def update(self, upload_id: str, updates: Dict[str, Any]) -> None:
        existing = await self.get(upload_id)
        if not existing:
            return
        
        existing.update(updates)
        await self.save(upload_id, existing)

    async def get_issues(self, upload_id: str) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            text("SELECT data FROM issues WHERE agent_id = :upload_id AND tenant_id = :tenant_id"),
            {"upload_id": upload_id, "tenant_id": self.tenant_id}
        )
        return [json.loads(row[0]) for row in result.fetchall()]

    async def save_issue(self, upload_id: str, issue_id: str, issue_data: Dict[str, Any]) -> None:
        data_json = json.dumps(issue_data)
        await self.session.execute(
            text("""
                INSERT INTO issues (id, agent_id, tenant_id, data) 
                VALUES (:issue_id, :upload_id, :tenant_id, :data)
                ON CONFLICT (id, agent_id, tenant_id) DO UPDATE SET data = EXCLUDED.data
            """),
            {"issue_id": issue_id, "upload_id": upload_id, "tenant_id": self.tenant_id, "data": data_json}
        )
        await self.session.commit()

    async def update_issue(self, upload_id: str, issue_id: str, updates: Dict[str, Any]) -> None:
        result = await self.session.execute(
            text("SELECT data FROM issues WHERE id = :issue_id AND agent_id = :upload_id AND tenant_id = :tenant_id"),
            {"issue_id": issue_id, "upload_id": upload_id, "tenant_id": self.tenant_id}
        )
        row = result.fetchone()
        if not row:
            return
            
        existing = json.loads(row[0])
        existing.update(updates)
        await self.save_issue(upload_id, issue_id, existing)

    async def get_pulls(self, upload_id: str) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            text("SELECT data FROM pulls WHERE agent_id = :upload_id AND tenant_id = :tenant_id"),
            {"upload_id": upload_id, "tenant_id": self.tenant_id}
        )
        return [json.loads(row[0]) for row in result.fetchall()]

    async def save_pull(self, upload_id: str, pull_data: Dict[str, Any]) -> None:
        data_json = json.dumps(pull_data)
        await self.session.execute(
            text("""
                INSERT INTO pulls (agent_id, tenant_id, data) 
                VALUES (:upload_id, :tenant_id, :data)
            """),
            {"upload_id": upload_id, "tenant_id": self.tenant_id, "data": data_json}
        )
        await self.session.commit()

    async def update_pull(self, upload_id: str, pr_number: int, updates: Dict[str, Any]) -> None:
        pulls = await self.get_pulls(upload_id)
        # Assuming URL contains pr_number
        pull = next((p for p in pulls if str(pr_number) in p.get("url", "")), None)
        if not pull:
            return
            
        pull.update(updates)
        # NOTE: A robust implementation would extract an ID for pulls. This is a simplified overwrite for PoC.
        # This will be replaced by a proper UPDATE matching the specific row.
        data_json = json.dumps(pull)
        await self.session.execute(
            text("""
                UPDATE pulls SET data = :data 
                WHERE agent_id = :upload_id AND tenant_id = :tenant_id AND data->>'url' LIKE :pr_url
            """),
            {"data": data_json, "upload_id": upload_id, "tenant_id": self.tenant_id, "pr_url": f"%/{pr_number}%"}
        )
        await self.session.commit()

    async def save_deployment(self, upload_id: str, deployment_data: Dict[str, Any]) -> None:
        data_json = json.dumps(deployment_data)
        await self.session.execute(
            text("""
                INSERT INTO deployments (agent_id, tenant_id, data) 
                VALUES (:upload_id, :tenant_id, :data)
            """),
            {"upload_id": upload_id, "tenant_id": self.tenant_id, "data": data_json}
        )
        await self.session.commit()

    async def get_messages(self, upload_id: str) -> List[Dict[str, Any]]:
        result = await self.session.execute(
            text("SELECT data FROM messages WHERE agent_id = :upload_id AND tenant_id = :tenant_id ORDER BY created_at ASC"),
            {"upload_id": upload_id, "tenant_id": self.tenant_id}
        )
        return [json.loads(row[0]) for row in result.fetchall()]

    async def save_message(self, upload_id: str, message_data: Dict[str, Any]) -> None:
        data_json = json.dumps(message_data)
        await self.session.execute(
            text("""
                INSERT INTO messages (agent_id, tenant_id, data) 
                VALUES (:upload_id, :tenant_id, :data)
            """),
            {"upload_id": upload_id, "tenant_id": self.tenant_id, "data": data_json}
        )
        await self.session.commit()
