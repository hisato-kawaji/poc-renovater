import asyncio
import logging
from app.deps import Deps
from google.genai import types
from google.adk.runners import InMemoryRunner

logger = logging.getLogger(__name__)

async def run_agent(deps: Deps, agent_name: str, build_fn, input_data: str):
    def _run():
        engine = build_fn()
        runner = InMemoryRunner(agent=engine)
        content = types.Content(role="user", parts=[types.Part.from_text(text=input_data)])
        session = runner.session_service.create_session_sync(user_id="default_user", app_name=runner.app_name)
        
        logger.info(f"[{agent_name}] Agent started processing... engine.name={engine.name}")
        all_events = []
        for event in runner.run(
            user_id=session.user_id,
            session_id=session.id,
            new_message=content
        ):
            all_events.append(event)
            # Log raw event for debugging
            logger.info(f"[{agent_name}] Raw Event: author={event.author}")
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        logger.info(f"[{agent_name}] (AI Text) {part.text[:100]}...")
                    if part.function_call:
                        logger.info(f"[{agent_name}] (ToolCall) Executing {part.function_call.name}...")
                    if part.function_response:
                        logger.info(f"[{agent_name}] (ToolResponse) Completed {part.function_response.name}.")

        logger.info(f"DEBUG: run_agent events returned {len(all_events)} events")
        for event in reversed(all_events):
            if event.author == engine.name and event.content and event.content.parts:
                return "".join([p.text for p in event.content.parts if p.text])
        # Fallback
        for event in reversed(all_events):
            if event.author != "user" and event.content and event.content.parts:
                return "".join([p.text for p in event.content.parts if p.text])
        return ""

    if deps.settings.agent_runtime == "agent_engine":
        agent_id = f"projects/{deps.settings.google_cloud_project}/locations/{deps.settings.google_cloud_region}/agents/{agent_name}"
        logger.info(f"Mocking remote call to {agent_id} using local engine")
        return await asyncio.to_thread(_run)
    else:
        return await asyncio.to_thread(_run)
