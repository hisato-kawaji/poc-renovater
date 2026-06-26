from app.deps import Deps
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../packages")))
from agents.charter import build_charter_agent
from shared.python.schemas import CharterEvaluation, Analysis

from app.application.agents.runner import run_agent

class CharterAgentClient:
    def __init__(self, deps: Deps):
        self.deps = deps

    async def evaluate(self, analysis: Analysis, source_tree: str, file_contents: dict) -> CharterEvaluation:
        input_data = {
            "analysis": analysis.model_dump(),
            "source_tree": source_tree,
            "file_contents": file_contents
        }
        json_str = await run_agent(self.deps, "charter-agent", build_charter_agent, str(input_data))
        return CharterEvaluation.model_validate_json(json_str)
