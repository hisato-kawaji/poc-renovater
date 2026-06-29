import asyncio
from app.adapters.repositories.firestore_agent_repository import FirestoreAgentRepository

async def main():
    repo = FirestoreAgentRepository("YOUR_PROJECT_ID")
    upload_id = "53bf97c6-9753-4f52-8c9a-e78318c2e7c1"
    
    doc = await repo.get(upload_id)
    print(f"Repo URL: {doc['repo']['url']}")
    
    pulls = await repo.get_pulls(upload_id)
    for p in pulls:
        if "17" in p.get("url", ""):
            print(f"Branch: {p.get('branch')}")

asyncio.run(main())
