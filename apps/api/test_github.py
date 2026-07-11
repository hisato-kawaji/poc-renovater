import asyncio
from app.settings import get_settings
from app.adapters.scm_github import GitHubScmAdapter

async def main():
    settings = get_settings()
    scm = GitHubScmAdapter(
        app_id=settings.github_app_id,
        installation_id=settings.github_app_installation_id,
        private_key=settings.github_app_private_key,
        org=settings.github_org,
        project_id="MY_GCP_PROJECT"
    )
    repo_name = "poc-nextjs-firestore-app-863d369e"
    print("Testing repo:", repo_name)
    try:
        scm.create_branch(repo_name, "test-branch-123", "main")
        print("Branch created!")
    except Exception as e:
        print("Create branch error:", e)

    try:
        scm.commit_files_to_branch(repo_name, "test-branch-123", {"README.md": "Test", ".github/workflows/deploy.yml": "test"}, "Test commit")
        print("Commit successful!")
    except Exception as e:
        print("Commit error:", e)

if __name__ == "__main__":
    asyncio.run(main())
