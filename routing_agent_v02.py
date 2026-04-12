import os
import logging
import vertexai
import asyncio

from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService

from agents import create_day_trip_agent, create_weekend_guide_agent
from routed_agents_v2 import (
    create_foodie_agent_v2,
    create_transportation_agent_v2,
    create_find_and_navigate_agent,
    create_router_agent_v2)
from agent_query import run_agent_query

print("✅ ALL LIBRARIES ARE LOADED AND READY TO GO!")



# <-----  I.    CONFIGURE LOGGING  ------>


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("routing_agents_v2.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

print("✅ LOGGER ARE CONFIGURED, LOADED AND READY TO GO!")




# <-----  II.   LOAD/INIT ENVIRNONMENT VARIABLES  ------>

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("REGION", "us-central1")

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
else:
    logger.error("No project id is found. AI features will be disabled.")

session_service = InMemorySessionService()
my_user_id = "adk_adventurer_007"

print("✅ ALL ENVIRONMENT VARIABLES ARE LOADED AND READY TO GO!")



# <-----  III.   DEFINE THE SPECIALIST AGENTS  ------>
day_trip_agent = create_day_trip_agent()
foodie_agent_v2 = create_foodie_agent_v2()
weekend_guide_agent = create_weekend_guide_agent()
transportation_agent_v2 = create_transportation_agent_v2()
find_and_navigate_agent = create_find_and_navigate_agent([foodie_agent_v2, transportation_agent_v2])

print("✅ ALL SPECIALIST AGENTS ARE LOADED AND READY TO GO!")




# <-----  IV.   LOAD/INIT AI VARIABLES/INFO  ------>

ROUTE_DESCRIPTIONS = {
    "foodie_agent": "Only for food, restaurants, or eating.",
    "weekend_guide_agent": "For events, concerts, or weekend activities.",
    "day_trip_agent": "General planner for other day trip requests.",
    "find_and_navigate_agent": "Complex queries needing a place found THEN directions."
}

options_str = "\n".join([f"- '{k}': {v}" for k, v in ROUTE_DESCRIPTIONS.items()])

worker_agents = {
    "foodie_agent": foodie_agent_v2,
    "weekend_guide_agent": weekend_guide_agent,
    "day_trip_agent": day_trip_agent,
    "transport_agent": transportation_agent_v2
}

queries = [
    "I want to eat the best sushi in Palo Alto.",
    "Are there any cool outdoor concerts this weekend?",
    "Find me the best sushi in Palo Alto and then tell me how to get there from the Caltrain station."
]

print("✅ AGENT INFO IS READY TO GO!")




# <-----  V.   DEFINE THE BRAINS OF THE OPERATION: THE ROUTER AGENT  ------>

router_agent_v2 = create_router_agent_v2(options_str)




# <-----  VII.   RUN SEQUENCE ROUTER  ------>

async def run_sequence_router(queries: list[str]):
    for query in queries:
        router_session = await session_service.create_session(app_name=router_agent_v2.name, user_id=my_user_id)
        chosen_route = await run_agent_query(router_agent_v2, query, router_session, my_user_id, session_service, is_router=True)

        if chosen_route:
            chosen_route = chosen_route.strip().strip("'\"").strip()
        if chosen_route in worker_agents:
            worker_agent = worker_agents.get(chosen_route, day_trip_agent)
        else:
            worker_agent = day_trip_agent


        worker_session = await session_service.create_session(app_name=worker_agent.name, user_id=my_user_id)
        await run_agent_query(worker_agent, query, worker_session, my_user_id, session_service)




if __name__ == "__main__":
    asyncio.run(run_sequence_router(queries))