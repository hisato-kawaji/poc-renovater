import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../shared/python")))
from schemas import CharterEvaluation
from google.adk.agents.llm_agent import LlmAgent

def build_charter_agent() -> LlmAgent:
    prompt = """
    You are an expert Google Cloud Solutions Architect evaluating an application against the 'Cloud Run Charter' rules.
    Evaluate the provided Analysis context and the Source Code.
    Score out of 100.
    1. Must be stateless or state must be in an external DB (Firestore).
    2. Must have a Dockerfile or be easily containerizable.
    3. Configuration must be via environment variables.
    4. Must not store hardcoded secrets.
    Return the evaluation.
    """
    
    agent = LlmAgent(
        model=os.getenv("GEMINI_MODEL_PRO", "gemini-3.1-pro-preview"),
        system_instruction=prompt,
        output_schema=CharterEvaluation
    )
    return agent
