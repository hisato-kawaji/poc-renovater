import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../shared/python")))
from schemas import RepoPlan
from google.adk.agents.llm_agent import LlmAgent

def build_repo_agent() -> LlmAgent:
    prompt = """
    You are an expert repository manager.
    Given the Analysis and Charter of a PoC, generate a repository name (prefixed with 'poc-'), a short description, and a comprehensive README.md.
    Return the plan.
    """
    
    agent = LlmAgent(
        name="repo",
        model=os.getenv("GEMINI_MODEL_FLASH", "gemini-3.5-flash"),
        instruction=prompt,
        output_schema=RepoPlan
    )
    return agent
