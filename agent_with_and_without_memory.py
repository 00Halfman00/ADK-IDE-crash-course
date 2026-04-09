import os
import asyncio
import logging
import vertexai


from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService


from agent_query import run_agent_query
from agent_with_memory_adaptive_planner import create_multi_day_trip_agent


print("✅ ALL LIBRARIES ARE LOADED AND READY TO GO!")




# <-----  I.    CONFIGURE LOGGING  ------>

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_with_and_without_memory.log"),
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
else:
    logger.error("No project id is found. AI features will be disabled.")


# <---  Initialize Session Service  --->
# This one service will manage all the different sessions.
session_service = InMemorySessionService()
my_user_id = "adk_adventurer_007"


multi_day_trip_agent = create_multi_day_trip_agent()
print(f"AGENT '{multi_day_trip_agent}' IS DEFINED AND READY.")


# Change to False to run failed memory agent
flag: bool = False





# <-----  III.   TEST THE ADAPTIVE-PLANNER-WITH-MEMORY AGENT  ------>

async def test_memory_success_demo() -> None:
    print("\n" + "#"*60)
    print("AGENT THAT SUCCEEDS TO ADAPT MEMORY FROM THE SAME SESSION.")
    print("#"*60)

    trip_session = await session_service.create_session( app_name=multi_day_trip_agent.name, user_id=my_user_id)
    print("\n" + "#"*60)
    print(f"SESSION WITH ID: '{trip_session.id}' HAS BEEN CREATED")
    print("#"*60)

    # Turn 1: The user initiates the trip
    query1 = "hi! I want to plan a 2-day trip to Paris, France. I'm interested in the country's history and the local food."
    await run_agent_query(multi_day_trip_agent, query1, trip_session, my_user_id, session_service)

    # Turn 2: The user gives feedback and ask for a change
    # The same trip session object is used to enable continuous memory
    query2 = "That sounds good, but I am not a fan of museums. Can you replace the morning activity for Day 1 with something else historical."
    await run_agent_query(multi_day_trip_agent, query2, trip_session, my_user_id, session_service)

    # Turn 3: The user confirms and asks to continue
    query3 = "yes, the new plan for Day 1 is perfect. Please plan Day 2 now, keeping the food theme in mind."
    await run_agent_query(multi_day_trip_agent, query3, trip_session, my_user_id, session_service)





# <-----  IV.   TEST THE ADAPTIVE-PLANNER-WITHOUT-MEMORY AGENT  ------>

async def test_memory_failure_demo() -> None:
    print("\n" + "#"*60)
    print("AGENT THAT FAILS TO ADAPT MEMORY FROM THE SESSION.")
    print("#"*60)
    
    # (Turn 1) The user initiates the trip with session_one
    query1 = "hi! I want to plan a 2-day trip to Paris, France. I'm interested in the country's history and the local food."
    session_one = await session_service.create_session(app_name=multi_day_trip_agent.name, user_id=my_user_id)
    await run_agent_query(multi_day_trip_agent, query1, session_one, my_user_id, session_service)


    # (Turn 2) The user ask to continue but in a seperate new session
    query2 = "That sounds like a good plan for Day 1. Please plan Day 2 now."
    session_two = await session_service.create_session(app_name=multi_day_trip_agent.name, user_id=my_user_id)
    await run_agent_query(multi_day_trip_agent, query2, session_two, my_user_id, session_service)




if __name__ == "__main__":
    if flag:
        asyncio.run(test_memory_success_demo())
    else:
        asyncio.run(test_memory_failure_demo())