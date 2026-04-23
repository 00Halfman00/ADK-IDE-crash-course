import os
import logging
import vertexai

from dotenv import load_dotenv
from google.adk.agents import Agent, LoopAgent, ParallelAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai.types import Content, Part


print("✅ ALL LIBRARIES ARE LOADED AND READY!")




# <-----  I.    CONFIGURE LOGGING  ------>

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_query.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


print("✅ LOGGERS ARE CONFIGURED, LOADED AND READY TO GO!")




# <-----  II.   LOAD/INIT ENVIRNONMENT VARIABLES  ------>

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("REGION", "us-central1")

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    logger.info("Found project id!")
else:
    logger.error("No project id found. AI features will be disabled.")

print("✅ ALL ENVIRONMENT VARIABLES ARE LOADED AND READY TO GO!")




#  <-----     III.    FUNCTION TO RUN AGENT    ----->

async def run_agent_query(agent: Agent | SequentialAgent | ParallelAgent | LoopAgent, query: str, session: Session, user_id: str, session_service: InMemorySessionService, is_router: bool = False):
    """Initializes a runner and executes a query for a given agent and session."""

    import asyncio
    await asyncio.sleep(1)

    try:
        print(f"\nRUNNING QUERY AGENT: '{agent.name}' IN SESSION: '{session.id}'")
        runner = Runner(agent=agent, session_service=session_service, app_name=agent.name)
        final_response = ""
        try:
            async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=Content(parts=[Part(text=query)], role="user")):
                current_agent_name = agent.name 
                # Check if this specific event has a different author (the sub-agent)
                if hasattr(event, 'branch') and event.branch:
                    print(f"📍 PATH: {event.branch}")
                elif hasattr(event, 'author') and event.author:
                    print(f"👤 AUTHOR: {event.author}")
                print(f"--------------------------------------------------")
                print(f"✅ ACTIVE WORKER: {current_agent_name}")
                print(f"--------------------------------------------------")

                if not is_router:
                    # Let's see what the agent is thinking!
                    print(f"<---------------------------    EVENT:    -------------------------------------------->\n {event}")
                if event.is_final_response() and event.content and event.content.parts:
                    final_response = event.content.parts[0].text

        except Exception as e:
            print(f"--------------------------------------------------\n✅ FINAL RESPONSE:\nAn error occurred: \n{e}\n--------------------------------------------------")
            return None

        if not is_router:
            print(f"--------------------------------------------------\n✅ FINAL RESPONSE:\n {final_response}\n--------------------------------------------------")
        return final_response
    except Exception as e:
        print(f"--------------------------------------------------\n✅ FINAL RESPONSE:\nAn error occurred: \n{e}\n--------------------------------------------------")
        return None
