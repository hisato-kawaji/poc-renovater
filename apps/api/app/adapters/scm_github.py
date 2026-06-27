import os
import github
from github import Github, GithubIntegration
from app.ports.scm import ScmPort
from google.cloud import secretmanager

class GitHubScmAdapter(ScmPort):
    def __init__(self, app_id: str, installation_id: str, private_key: str, org: str, project_id: str):
        self.app_id = app_id
        self.installation_id = installation_id
        self.org = org
        
        if private_key.startswith("projects/"):
            client = secretmanager.SecretManagerServiceClient()
            name = private_key
            response = client.access_secret_version(request={"name": name})
            private_key = response.payload.data.decode("UTF-8")
        else:
            # Replace escaped newlines with actual newlines
            private_key = private_key.replace('\\n', '\n')
            
        self.integration = GithubIntegration(self.app_id, private_key)
    
    def _get_github(self):
        access_token = self.integration.get_access_token(int(self.installation_id)).token
        return Github(access_token)

    def create_repo(self, repo_name: str, description: str) -> str:
        gh = self._get_github()
        org = gh.get_organization(self.org)
        repo = org.create_repo(
            repo_name,
            description=description,
            private=True,
            auto_init=True
        )
        return repo.html_url

    def commit_files(self, repo_name: str, files: dict[str, str], message: str):
        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        
        ref = repo.get_git_ref("heads/main")
        base_commit = repo.get_git_commit(ref.object.sha)
        base_tree = base_commit.tree
        
        tree_elements = []
        for path, content in files.items():
            blob = repo.create_git_blob(content, "utf-8")
            tree_elements.append(
                github.InputGitTreeElement(path, '100644', 'blob', sha=blob.sha)
            )
        
        new_tree = repo.create_git_tree(tree_elements, base_tree)
        new_commit = repo.create_git_commit(message, new_tree, [base_commit])
        ref.edit(new_commit.sha)

    def create_issue(self, repo_name: str, title: str, body: str) -> str:
        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        issue = repo.create_issue(title=title, body=body)
        return issue.html_url

    def create_pr(self, repo_name: str, title: str, body: str, head: str, base: str = "main") -> str:
        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        pr = repo.create_pull(title=title, body=body, head=head, base=base)
        return pr.html_url

    def get_tree(self, repo_name: str, branch: str = "main") -> list[str]:
        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        ref = repo.get_git_ref(f"heads/{branch}")
        tree = repo.get_git_tree(ref.object.sha, recursive=True)
        return [elem.path for elem in tree.tree if elem.type == "blob"]

    def create_branch(self, repo_name: str, branch: str, base: str = "main"):
        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        base_ref = repo.get_git_ref(f"heads/{base}")
        repo.create_git_ref(f"refs/heads/{branch}", base_ref.object.sha)

    def commit_files_to_branch(self, repo_name: str, branch: str, files: dict[str, str], message: str):
        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        ref = repo.get_git_ref(f"heads/{branch}")
        base_commit = repo.get_git_commit(ref.object.sha)
        base_tree = base_commit.tree
        
        tree_elements = []
        for path, content in files.items():
            blob = repo.create_git_blob(content, "utf-8")
            tree_elements.append(
                github.InputGitTreeElement(path, '100644', 'blob', sha=blob.sha)
            )
        
        new_tree = repo.create_git_tree(tree_elements, base_tree)
        new_commit = repo.create_git_commit(message, new_tree, [base_commit])
        ref.edit(new_commit.sha)

    def get_pr_diff(self, repo_name: str, pr_number: int) -> str:
        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        pr = repo.get_pull(pr_number)
        files = pr.get_files()
        diff = ""
        for f in files:
            diff += f"File: {f.filename}\\nPatch:\\n{f.patch}\\n\\n"
        return diff

    def review_pr(self, repo_name: str, pr_number: int, state: str, body: str):
        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        pr = repo.get_pull(pr_number)
        event = "APPROVE" if state == "approved" else "REQUEST_CHANGES"
        try:
            pr.create_review(body=body, event=event)
        except Exception as e:
            print(f"Failed to create review: {e}. Falling back to COMMENT.")
            pr.create_review(body=body, event="COMMENT")

    def merge_pr(self, repo_name: str, pr_number: int):
        gh = self._get_github()
        repo = gh.get_repo(f"{self.org}/{repo_name}")
        pr = repo.get_pull(pr_number)
        pr.merge(merge_method="squash")
