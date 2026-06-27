from app.deps import Deps
import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../packages")))
from agents.charter import build_charter_agent
from shared.python.schemas import CharterEvaluation, Analysis

from app.application.agents.runner import run_agent
from google import genai

class CharterAgentClient:
    def __init__(self, deps: Deps):
        self.deps = deps

    async def evaluate(self, analysis: Analysis, source_tree: str, file_contents: dict) -> CharterEvaluation:
        input_data = {
            "analysis": analysis.model_dump(),
            "source_tree": source_tree,
            "file_contents": file_contents
        }
        json_str = await run_agent(self.deps, "charter-agent", build_charter_agent, str(input_data))
        return CharterEvaluation.model_validate_json(json_str)

    async def chat(self, analysis_data: dict, charter_data: dict, messages: list) -> str:
        client = genai.Client()
        # Ensure we use Vertex AI if configured
        if os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "1":
            client = genai.Client(vertexai=True, project=os.getenv("GOOGLE_CLOUD_PROJECT"), location=os.getenv("GOOGLE_CLOUD_REGION", "us-central1"))
            
        system_instruction = f"""
You are an expert Google Cloud Solutions Architect evaluating an application against the 'Cloud Run Charter' rules.
The user is asking questions about the evaluation or the requirements.
Current Analysis: {analysis_data}
Current Evaluation: {charter_data}
Please answer the user's questions clearly and help them understand what needs to be changed.
ALWAYS reply in Japanese.
"""
        model = os.getenv("GEMINI_MODEL_PRO", "gemini-2.5-pro")
        
        contents = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            contents.append(
                genai.types.Content(
                    role=role,
                    parts=[genai.types.Part.from_text(text=m.get("content", ""))]
                )
            )
            
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model,
            contents=contents,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
            )
        )
        return response.text
