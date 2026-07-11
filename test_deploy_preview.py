import asyncio
import os
import sys

# Add apps/api to path
sys.path.append(os.path.abspath('apps/api'))

from app.deps import Deps
from app.settings import get_settings
from app.adapters.scm_github import GitHubScmAdapter
from app.application.agents.deploy import DeployAgentClient

async def main():
    settings = get_settings()
    deps = Deps(settings, "test-tenant")
    
    client = DeployAgentClient(deps)
    
    # We will test against a public repo or just see if the command works
    # For a real test, let's use a dummy repo that exists
    repo_url = "https://github.com/poc-recycle/poc-todo-app.git" # Example
    branch = "main"
    service_name = "test-preview-deploy"
    
    print("Testing deploy...")
    try:
        url = await client.deploy(repo_url, branch, service_name)
        print(f"Deploy success! URL: {url}")
    except Exception as e:
        print(f"Deploy failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
