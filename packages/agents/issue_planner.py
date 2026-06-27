import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../shared/python")))
from schemas import IssuePlan
from google.adk.agents.llm_agent import LlmAgent

def build_issue_planner_agent() -> LlmAgent:
    prompt = """
    You are an expert technical project manager.
    Given the Analysis and Charter of a PoC, generate a list of small, actionable GitHub Issues.
    Break down the work into very small PRs (e.g. Add Dockerfile, Add CI, Refactor hardcoded secrets, etc).
    Output ALL titles, descriptions, and text fields in Japanese.
    """
    
    agent = LlmAgent(
        name="issue_planner",
        model=os.getenv("GEMINI_MODEL_FLASH", "gemini-3.5-flash"),
        instruction=prompt,
        output_schema=IssuePlan
    )
    
    return agent
