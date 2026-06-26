from app.deps import Deps
import asyncio
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../packages")))
from shared.python.schemas import CodeChange, CharterEvaluation
from agents.coding.engine import build_coding_agent

from app.application.agents.runner import run_agent

class CodingAgentClient:
    def __init__(self, deps: Deps):
        self.deps = deps

    async def implement(self, issue: dict, charter: CharterEvaluation, repo_name: str) -> CodeChange:
        tree = self.deps.scm.get_tree(repo_name)
        input_data = {
            "issue": issue,
            "charter": charter.model_dump(),
            "source_tree": tree
        }
        json_str = await run_agent(self.deps, "coding-agent", build_coding_agent, str(input_data))
        return CodeChange.model_validate_json(json_str)

    async def execute(self, repo_name: str, code_change: CodeChange):
        self.deps.scm.create_branch(repo_name, code_change.branchName, base="main")
        self.deps.scm.commit_files_to_branch(repo_name, code_change.branchName, code_change.fileChanges, code_change.prTitle)
        url = self.deps.scm.create_pr(repo_name, code_change.prTitle, code_change.prBody, code_change.branchName)
        return url, code_change.branchName
