import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../shared/python")))
from schemas import ReviewResult
from google.adk.agents.llm_agent import LlmAgent

def build_review_agent() -> LlmAgent:
    prompt = """
    You are an expert code reviewer.
    Review the provided Code Change (PR diff) against the PoC Charter.
    Ensure there are no out-of-scope changes, the risk is low, and changes are minimal.
    Output your review state and comments.
    """
    
    agent = LlmAgent(
        name="review",
        model=os.getenv("GEMINI_MODEL_PRO", "gemini-3.1-pro-preview"),
        instruction=prompt,
        output_schema=ReviewResult
    )
    return agent
