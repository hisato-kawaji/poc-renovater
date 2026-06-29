import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared/python")))
from schemas import CodeChange
from google.adk.agents.llm_agent import LlmAgent

def build_coding_agent() -> LlmAgent:
    prompt = """
    You are an expert software engineer.
    Given an Issue and the Charter of a PoC, return the exact changes to the codebase.
    Output the branch name, PR title and body, and the new file contents for the files that should be modified or created.
    Keep the changes minimal and focused exactly on solving the Issue.
    """
    
    agent = LlmAgent(
        name="coding",
        model=os.getenv("GEMINI_MODEL_PRO", "gemini-3.1-pro-preview"),
        instruction=prompt,
        output_schema=CodeChange
    )
    return agent
