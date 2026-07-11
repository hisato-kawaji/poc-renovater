from fastapi import Depends, Request, HTTPException, status
from app.settings import get_settings, Settings
from app.adapters.storage_gcs import GCSStorageAdapter
from app.ports.storage import StoragePort
from app.adapters.scm_github import GitHubScmAdapter
from app.ports.scm import ScmPort
from app.domain.repositories.agent_repository import AgentRepository
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.repositories.firestore_agent_repository import FirestoreAgentRepository
from app.adapters.repositories.sql_agent_repository import SQLAgentRepository
from app.adapters.repositories.database import get_db_session
from app.ports.event import EventPublisherPort
from app.adapters.pubsub_event import PubSubEventPublisher

class Deps:
    def __init__(self, settings: Settings, tenant_id: str, db_session: Optional[AsyncSession] = None):
        self.settings = settings
        self.tenant_id = tenant_id
        self.storage: StoragePort = GCSStorageAdapter(
            bucket_name=settings.gcs_upload_bucket,
            project=settings.google_cloud_project,
            tenant_id=tenant_id
        )
        self.scm: ScmPort = GitHubScmAdapter(
            app_id=str(settings.github_app_id),
            installation_id=str(settings.github_app_installation_id),
            private_key=settings.github_app_private_key,
            org=settings.github_org,
            project_id=settings.google_cloud_project
        )
        if db_session:
            self.agent_repo: AgentRepository = SQLAgentRepository(db_session, tenant_id)
        else:
            self.agent_repo: AgentRepository = FirestoreAgentRepository(
                project_id=settings.google_cloud_project,
                tenant_id=tenant_id
            )
        if settings.agent_runtime == "local":
            from app.adapters.local_event import LocalEventPublisher
            self.event_publisher: EventPublisherPort = LocalEventPublisher()
        else:
            self.event_publisher: EventPublisherPort = PubSubEventPublisher(
                project_id=settings.google_cloud_project
            )

async def get_deps(
    request: Request, 
    settings: Settings = Depends(get_settings),
    db_session: Optional[AsyncSession] = Depends(get_db_session)
) -> Deps:
    tenant_id = request.headers.get("X-Tenant-ID", "test-tenant")
    return Deps(settings, tenant_id, db_session)
