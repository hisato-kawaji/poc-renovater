from app.ports.storage import StoragePort
from google.cloud import storage

class GCSStorageAdapter(StoragePort):
    def __init__(self, bucket_name: str, project: str, tenant_id: str):
        self.bucket_name = bucket_name
        self.tenant_id = tenant_id
        self.client = storage.Client(project=project)
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_zip(self, agent_id: str, zip_bytes: bytes) -> str:
        blob = self.bucket.blob(f"tenants/{self.tenant_id}/agents/{agent_id}/upload.zip")
        blob.upload_from_string(zip_bytes, content_type="application/zip")
        return f"gs://{self.bucket_name}/tenants/{self.tenant_id}/agents/{agent_id}/upload.zip"

    def download_zip(self, agent_id: str) -> bytes:
        blob = self.bucket.blob(f"tenants/{self.tenant_id}/agents/{agent_id}/upload.zip")
        return blob.download_as_bytes()
