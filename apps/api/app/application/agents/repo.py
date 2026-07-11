from app.deps import Deps
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../packages")))
from agents.repo import build_repo_agent
from shared.python.schemas import RepoPlan, Analysis, CharterEvaluation

from app.application.agents.runner import run_agent

class RepoAgentClient:
    def __init__(self, deps: Deps):
        self.deps = deps

    async def plan(self, upload_id: str, analysis: Analysis, charter: CharterEvaluation) -> RepoPlan:
        input_data = {
            "upload_id": upload_id,
            "analysis": analysis.model_dump(),
            "charter": charter.model_dump()
        }
        json_str = await run_agent(self.deps, "repo-agent", build_repo_agent, str(input_data))
        return RepoPlan.model_validate_json(json_str)

    async def execute(self, plan: RepoPlan, source_tree_str: str, file_contents: dict, upload_id: str):
        short_id = upload_id.split("-")[0]
        actual_repo_name = f"{plan.repositoryName}-{short_id}"
        url = self.deps.scm.create_repo(actual_repo_name, plan.repositoryDescription)
        
        files_to_commit = file_contents.copy()
        files_to_commit["README.md"] = plan.readmeContent
        
        template_dir = os.path.join(os.path.dirname(__file__), "../../../../../../templates")
        
        for root, _, files in os.walk(template_dir):
            for file in files:
                if file.endswith(".tmpl") and file == "README.md.tmpl":
                    continue # handled by agent plan
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, template_dir)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if rel_path.endswith(".tmpl"):
                    rel_path = rel_path[:-5]
                files_to_commit[rel_path] = content

        self.deps.scm.commit_files(actual_repo_name, files_to_commit, "Initial commit from PoC Renovater with templates")
        
        return url, actual_repo_name
