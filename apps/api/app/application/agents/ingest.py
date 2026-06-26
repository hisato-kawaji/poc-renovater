from app.deps import Deps
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../packages")))
from agents.ingest import build_ingest_agent
from shared.python.schemas import Analysis

from app.application.agents.runner import run_agent

class IngestAgentClient:
    def __init__(self, deps: Deps):
        self.deps = deps

    async def analyze(self, source_tree: str, file_contents: dict) -> Analysis:
        input_data = {"source_tree": source_tree, "file_contents": file_contents}
        json_str = await run_agent(self.deps, "ingest-agent", build_ingest_agent, str(input_data))
        return Analysis.model_validate_json(json_str)
