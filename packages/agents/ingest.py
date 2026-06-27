import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../shared/python")))
from schemas import Analysis
from google.adk.agents.llm_agent import LlmAgent

def build_ingest_agent() -> LlmAgent:
    prompt = """
    You are an expert software architect and technical analyzer.
    Your task is to analyze the provided source code tree and file contents of a Proof of Concept (PoC) application.
    Extract the tech stack, check for basic quality measures (tests, README, secrets), and evaluate Cloud Run readiness.
    Return a structured JSON according to the requested schema.
    Output ALL descriptions, summaries, and text fields in Japanese.
    """
    
    agent = LlmAgent(
        name="ingest",
        model=os.getenv("GEMINI_MODEL_FLASH", "gemini-3.5-flash"),
        instruction=prompt,
        output_schema=Analysis
    )
    return agent
