from app.deps import Deps
import asyncio
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../packages")))
from shared.python.schemas import IssuePlan, Analysis, CharterEvaluation
from agents.autofix_planner import build_autofix_planner_agent

from app.application.agents.runner import run_agent

class AutoFixPlannerClient:
    def __init__(self, deps: Deps):
        self.deps = deps

    async def plan(self, analysis: Analysis, charter: CharterEvaluation) -> IssuePlan:
        input_data = {
            "analysis": analysis.model_dump(),
            "charter": charter.model_dump()
        }
        json_str = await run_agent(self.deps, "autofix-planner-agent", build_autofix_planner_agent, str(input_data))
        return IssuePlan.model_validate_json(json_str)

    async def execute(self, repo_name: str, plan: IssuePlan):
        created_issues = []
        for issue in sorted(plan.issues, key=lambda x: x.priority):
            url = self.deps.scm.create_issue(repo_name, issue.title, issue.body)
            created_issues.append({"title": issue.title, "url": url})
        return created_issues
