import asyncio
from app.deps import Deps

async def run_agent(deps: Deps, agent_name: str, build_fn, input_data: str):
    if deps.settings.agent_runtime == "agent_engine":
        agent_id = f"projects/{deps.settings.google_cloud_project}/locations/{deps.settings.google_cloud_region}/agents/{agent_name}"
        # Remote Agent Engine invocation mock (ADK's remote client is not installed in this environment)
        print(f"Mocking remote call to {agent_id} using local engine")
        engine = build_fn()
        result = await asyncio.to_thread(engine.run, input_data)
        return result.content.parts[0].text
    else:
        engine = build_fn()
        result = await asyncio.to_thread(engine.run, input_data)
        return result.content.parts[0].text
