import asyncio
from google.adk.runners import InMemoryRunner
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent

async def main():
    engine = LlmAgent(name="test", instruction="Say hello", model="gemini-2.5-flash")
    runner = InMemoryRunner(agent=engine)
    content = types.Content(role="user", parts=[types.Part.from_text(text="test")])
    session = runner.session_service.create_session_sync(user_id="user1", app_name=runner.app_name)
    
    events = list(runner.run(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content
    ))
    
    print(f"Got {len(events)} events")
    for e in events:
        print(f"Event author: {e.author}, content: {e.content.parts[0].text if e.content and e.content.parts else None}")

if __name__ == "__main__":
    asyncio.run(main())
