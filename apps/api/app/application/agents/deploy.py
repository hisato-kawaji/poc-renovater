import asyncio
import os
import shutil
import tempfile
import logging
from typing import Dict, Any
from app.deps import Deps

logger = logging.getLogger(__name__)

class DeployAgentClient:
    def __init__(self, deps: Deps):
        self.deps = deps

    async def deploy(self, repo_url: str, branch: str, service_name: str) -> str:
        """
        Deploy the specified branch of the repo to Cloud Run using gcloud.
        """
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            # 1. Clone the repository at the specific branch
            # Use gh auth token for authentication
            auth_proc = await asyncio.create_subprocess_shell("gh auth token", stdout=asyncio.subprocess.PIPE)
            auth_stdout, _ = await auth_proc.communicate()
            token = auth_stdout.decode().strip()
            
            auth_url = repo_url.replace("https://", f"https://x-access-token:{token}@")
            clone_cmd = f"git clone --branch {branch} --single-branch {auth_url} {temp_dir}"
            logger.info(f"Cloning repo (URL masked)")
            proc = await asyncio.create_subprocess_shell(
                clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise Exception(f"Git clone failed: {stderr.decode()}")

            import pathlib
            project_id = self.deps.settings.google_cloud_project
            package_json_paths = sorted(list(pathlib.Path(temp_dir).rglob("package.json")), key=lambda p: len(p.parts))
            source_dir = str(package_json_paths[0].parent) if package_json_paths else temp_dir
            logger.info(f"Auto-detected source directory: {source_dir}")

            deploy_cmd = (
                f"gcloud run deploy {service_name} "
                f"--source {source_dir} "
                f"--region asia-northeast1 "
                f"--allow-unauthenticated "
                f"--project {project_id} "
                f"--quiet "
                f"--set-env-vars NEXT_PUBLIC_FIREBASE_PROJECT_ID={project_id},NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyDummyKeyForPreviewPurposeOnly123,NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=dummy-domain "
                f"--set-build-env-vars NEXT_PUBLIC_FIREBASE_PROJECT_ID={project_id},NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyDummyKeyForPreviewPurposeOnly123,NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=dummy-domain "
                f"--format='value(status.url)'"
            )
            logger.info(f"Deploying to Cloud Run: {deploy_cmd}")
            proc = await asyncio.create_subprocess_shell(
                deploy_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise Exception(f"gcloud run deploy failed: {stderr.decode()}")

            url = stdout.decode().strip()
            return url
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
