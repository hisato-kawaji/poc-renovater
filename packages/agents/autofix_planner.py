import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../shared/python")))
from schemas import IssuePlan
from google.adk.agents.llm_agent import LlmAgent

def build_autofix_planner_agent() -> LlmAgent:
    prompt = """
    You are an expert software engineer analyzing a PoC codebase.
    Your goal is to identify ONLY basic minimum operational issues (such as DB connection environment variable typos, missing real-time sync, or critical initial setup bugs).
    If there are such issues, generate exactly one or very few small GitHub Issues to fix them immediately so the app can connect to the DB and work at a minimum level.
    If the app already seems to work fine at a basic level, return an empty list of issues.
    Output ALL titles, descriptions, and text fields in Japanese.
    """
    
    agent = LlmAgent(
        name="autofix_planner",
        model=os.getenv("GEMINI_MODEL_FLASH", "gemini-3.5-flash"),
        instruction=prompt,
        output_schema=IssuePlan
    )
    
    return agent
