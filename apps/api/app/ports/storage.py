from typing import Protocol

class StoragePort(Protocol):
    def upload_zip(self, agent_id: str, zip_bytes: bytes) -> str:
        """Uploads zip and returns GCS path."""
        pass
    def download_zip(self, agent_id: str) -> bytes:
        """Downloads zip and returns bytes."""
        pass
