import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../shared/python")))
from schemas import AutoFixIssuePlan
from google.adk.agents.llm_agent import LlmAgent

def build_autofix_planner_agent() -> LlmAgent:
    prompt = """
    You are an expert software engineer analyzing a PoC codebase.
    Your goal is to critically identify ONLY basic minimum operational issues that prevent the app from building, deploying, or connecting to the DB correctly.
    
    CRITICAL QUALITY GUIDELINE: Before suggesting any fixes, you MUST provide a deep, step-by-step `critical_analysis` of the codebase.
    Specifically verify:
    1. DB configuration: Are environment variable names correct (e.g., Firebase/Firestore)?
    2. Build configuration: Are there incompatible Next.js config files (e.g., `next.config.ts` vs `next.config.mjs`) or `package.json` syntax errors?
    3. Are there any critical initialization bugs that will crash the application on startup?
    
    If you find these critical blockers, output a VERY SMALL, highly targeted list of GitHub Issues to fix them immediately.
    If the app already seems to build and work fine at a basic level, output an empty list of issues.
    Output ALL titles, descriptions, and text fields in Japanese.
    """
    
    agent = LlmAgent(
        name="autofix_planner",
        model=os.getenv("GEMINI_MODEL_FLASH", "gemini-3.5-flash"),
        instruction=prompt,
        output_schema=AutoFixIssuePlan
    )
    
    return agent
