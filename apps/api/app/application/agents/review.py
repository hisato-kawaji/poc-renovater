from app.deps import Deps
import asyncio
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../packages")))
from shared.python.schemas import ReviewResult, CharterEvaluation
from agents.review import build_review_agent

from app.application.agents.runner import run_agent

class ReviewAgentClient:
    def __init__(self, deps: Deps):
        self.deps = deps

    async def review(self, diff: str, charter: CharterEvaluation, issue: dict) -> ReviewResult:
        input_data = {
            "diff": diff,
            "charter": charter.model_dump(),
            "issue": issue
        }
        json_str = await run_agent(self.deps, "review-agent", build_review_agent, str(input_data))
        return ReviewResult.model_validate_json(json_str)

    async def execute(self, repo_name: str, pr_number: int, review: ReviewResult):
        self.deps.scm.review_pr(repo_name, pr_number, review.state, "\\n".join(review.comments))
        return True
