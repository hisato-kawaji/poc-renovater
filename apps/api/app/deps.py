from fastapi import Depends
from app.settings import get_settings, Settings
from app.adapters.storage_gcs import GCSStorageAdapter
from app.ports.storage import StoragePort
from app.adapters.scm_github import GitHubScmAdapter
from app.ports.scm import ScmPort

class Deps:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.storage: StoragePort = GCSStorageAdapter(
            bucket_name=settings.gcs_upload_bucket,
            project=settings.google_cloud_project
        )
        self.scm: ScmPort = GitHubScmAdapter(
            app_id=str(settings.github_app_id),
            installation_id=str(settings.github_app_installation_id),
            org=settings.github_org,
            project_id=settings.google_cloud_project
        )

def get_deps(settings: Settings = Depends(get_settings)) -> Deps:
    return Deps(settings)
