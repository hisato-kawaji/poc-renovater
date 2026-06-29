from fastapi import Depends, Request, HTTPException, status
from app.settings import get_settings, Settings
from app.adapters.storage_gcs import GCSStorageAdapter
from app.ports.storage import StoragePort
from app.adapters.scm_github import GitHubScmAdapter
from app.ports.scm import ScmPort
from app.domain.repositories.agent_repository import AgentRepository
from app.adapters.repositories.firestore_agent_repository import FirestoreAgentRepository
from app.ports.event import EventPublisherPort
from app.adapters.pubsub_event import PubSubEventPublisher

class Deps:
    def __init__(self, settings: Settings, tenant_id: str):
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
        self.agent_repo: AgentRepository = FirestoreAgentRepository(
            project_id=settings.google_cloud_project,
            tenant_id=tenant_id
        )
        self.event_publisher: EventPublisherPort = PubSubEventPublisher(
            project_id=settings.google_cloud_project
        )

def get_deps(request: Request, settings: Settings = Depends(get_settings)) -> Deps:
    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Tenant-ID header is missing"
        )
    return Deps(settings, tenant_id)
