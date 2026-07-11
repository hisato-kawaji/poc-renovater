import asyncio
import os
import sys

sys.path.append(os.path.abspath('apps/api'))

from app.settings import get_settings
from app.deps import Deps
from app.application.agents.deploy import DeployAgentClient

async def main():
    settings = get_settings()
    deps = Deps(settings, "test-tenant")
    
    # Check if scm works
    token = deps.scm.get_access_token()
    print(f"Token acquired: {'Yes' if token else 'No'}")
    
    import urllib.request
    import json
    req = urllib.request.Request("https://api.github.com/installation/repositories", headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        repos = data.get("repositories", [])
    
    print(f"Found {len(repos)} repos.")
        
    repo_url = repos[0]["clone_url"]
    print("Using repo:", repo_url)
    branch = "main"
    service_name = "test-preview-deploy"
    client = DeployAgentClient(deps)
    
    print("Testing deploy...")
    try:
        url = await client.deploy(repo_url, branch, service_name)
        print(f"Deploy success! URL: {url}")
    except Exception as e:
        print(f"Deploy failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
