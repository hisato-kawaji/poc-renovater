import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../shared/python")))
from schemas import IssuePlan
from google.adk.agents.llm_agent import LlmAgent

def build_autofix_planner_agent() -> LlmAgent:
    prompt = """
    You are an expert software engineer analyzing a PoC codebase.
    Your goal is to identify ONLY basic minimum operational issues that prevent the app from building, deploying, or connecting to the DB correctly.
    This includes:
    1. DB connection environment variable typos or missing real-time sync setups.
    2. Build or configuration errors (e.g., using `next.config.ts` in older Next.js versions that only support `.js` or `.mjs`, package.json misconfigurations, etc.).
    3. Critical initial setup bugs that crash the application on startup.
    
    If there are such issues, generate exactly one or very few small GitHub Issues to fix them immediately so the app can build and work at a minimum level.
    If the app already seems to build and work fine at a basic level, return an empty list of issues.
    Output ALL titles, descriptions, and text fields in Japanese.
    """
    
    agent = LlmAgent(
        name="autofix_planner",
        model=os.getenv("GEMINI_MODEL_FLASH", "gemini-3.5-flash"),
        instruction=prompt,
        output_schema=IssuePlan
    )
    
    return agent
