import os
import logging
import asyncio
import vertexai

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.sessions import InMemorySessionService
from dotenv import load_dotenv

from agents import create_day_trip_agent
from agent_query import run_agent_query


print("✅ ALL LIBRARIES ARE LOADED AND READY TO GO!")




# <-----  I.    CONFIGURE LOGGING  ------>

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_and_search_tool.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)




# <-----  II.   LOAD/INIT ENVIRNONMENT VARIABLES  ------>

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("REGION", "us-central1")

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    logger.info('Found project id!')
else:
    logger.error("No project id found. AI features will be disabled.")

# <---  Initialize Session Service  --->
# This one service will manage all the different sessions.
session_service = InMemorySessionService()
my_user_id = "adk_adventurer_007"




#  <-----     III.    FUNCTION TO DEFINE DAY TRIP AGENT    ----->

day_trip_agent= create_day_trip_agent()
print(f"AGENTt: {day_trip_agent.name} IS UP AND READY TO CREATE TRIPS.")




#  <-----     V.    FUNCTION TO TEST THE DAY TRIP AGENT    ----->

async def test_day_trip_genie() -> None:
    # Create a new, single-use session for this query

    day_trip_session = await session_service.create_session(app_name=day_trip_agent.name, user_id=my_user_id)
    query = "Plan a relaxing and artsy day trip near Chicago, Il. Keep it affordable!"
    print(f"USER QUERY: '{query}'")
    await run_agent_query(day_trip_agent, query, day_trip_session, my_user_id, session_service)






if __name__ == "__main__":
    asyncio.run(test_day_trip_genie())
