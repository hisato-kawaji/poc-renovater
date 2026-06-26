from typing import Protocol, Dict

class ScmPort(Protocol):
    def create_repo(self, repo_name: str, description: str) -> str:
        """Create a repo and return its URL."""
        pass
    
    def commit_files(self, repo_name: str, files: Dict[str, str], message: str):
        """Commit files to main branch."""
        pass
    
    def create_issue(self, repo_name: str, title: str, body: str) -> str:
        pass
        
    def create_pr(self, repo_name: str, title: str, body: str, head: str, base: str = "main") -> str:
        pass
        
    def get_tree(self, repo_name: str, branch: str = "main") -> list[str]:
        pass
    
    def create_branch(self, repo_name: str, branch: str, base: str = "main"):
        pass
        
    def commit_files_to_branch(self, repo_name: str, branch: str, files: Dict[str, str], message: str):
        pass

    def get_pr_diff(self, repo_name: str, pr_number: int) -> str:
        pass
        
    def review_pr(self, repo_name: str, pr_number: int, state: str, body: str):
        pass
