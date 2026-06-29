import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../shared/python")))
from schemas import IssueItem
from google.adk.agents.llm_agent import LlmAgent

def build_self_improve_agent() -> LlmAgent:
    prompt = """
    You are an expert Self-Improvement Agent.
    Your task is to analyze CI failure logs, review comments, or Preview execution results.
    You must output exactly ONE new Issue that details the root cause and the required fix.
    """
    
    agent = LlmAgent(
        name="self_improve",
        model=os.getenv("GEMINI_MODEL_PRO", "gemini-3.1-pro-preview"),
        instruction=prompt,
        output_schema=IssueItem
    )
    return agent
