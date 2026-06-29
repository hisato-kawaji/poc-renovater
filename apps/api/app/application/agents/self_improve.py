import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../packages")))
from agents.self_improve import build_self_improve_agent
from shared.python.schemas import IssueItem

from app.application.agents.runner import run_agent
from app.deps import Deps

class SelfImprovementClient:
    def __init__(self, deps: Deps):
        self.deps = deps

    async def analyze_failure(self, failure_log: str, context: dict) -> IssueItem:
        input_data = {
            "failure_log": failure_log,
            "context": context
        }
        json_str = await run_agent(self.deps, "self-improve-agent", build_self_improve_agent, str(input_data))
        return IssueItem.model_validate_json(json_str)
