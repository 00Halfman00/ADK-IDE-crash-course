import os
import logging
import vertexai
import asyncio

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService

from routed_agents_v1 import (
    create_day_trip_agent,
    create_foodie_agent,
    create_weekend_guide_agent,
    create_transportation_agent,
    create_router_agent_v1)
from agent_query import run_agent_query

print("✅ ALL LIBRARIES ARE LOADED AND READY TO GO!")




# <-----  I.    CONFIGURE LOGGING  ------>


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("routing_agents1.log"),
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

foodie_agent: Agent = create_foodie_agent()
weekend_guide_agent:Agent = create_weekend_guide_agent()
day_trip_agent:Agent = create_day_trip_agent()
transportation_agent:Agent = create_transportation_agent()

print("✅ ALL SPECIALIST AGENTS ARE LOADED AND READY TO GO!")




# <-----  IV.   LOAD/INIT AI VARIABLES/INFO  ------>

ROUTE_DESCRIPTIONS = {
    "foodie_agent": "Only for food, restaurants, or eating.",
    "weekend_guide_agent": "For events, concerts, or weekend activities.",
    "day_trip_agent": "General planner for other day trip requests.",
    "find_and_navigate_combo": "Complex queries needing a place found THEN directions."
}

options_str = "\n".join([f"- '{k}': {v}" for k, v in ROUTE_DESCRIPTIONS.items()])


worker_agents: dict[str, Agent] = {
    "foodie_agent": foodie_agent,
    "weekend_guide_agent": weekend_guide_agent,
    "day_trip_agent": day_trip_agent,
    "transportation_agent": transportation_agent
}

queries = [
    "I want to eat the best sushi in Palo Alto.",
    "Are there any cool outdoor concerts this weekend?",
    "Find me the best sushi in Palo Alto and then tell me how to get there from the Caltrain station."
]

print("✅ AGENT INFO IS READY TO GO!")




# <-----  V.    DEFINE CUSTOM AGENT WORKFLOWS (COMBO ROUTES)  ------>

async def handle_and_navigate(query):
    foodie_session = await session_service.create_session(app_name=foodie_agent.name, user_id=my_user_id)
    foodie_response = await run_agent_query(foodie_agent, query, foodie_session, my_user_id, session_service)
    print(f"FOODIE AGENT'S RESPONSE: '{foodie_response}'")

    directions_query = f"Return directions from this recommendated place: {foodie_response}. Starting directions is Palo Alto Caltrain station."
    transportation_session = await session_service.create_session(app_name=transportation_agent.name, user_id=my_user_id)
    await run_agent_query(transportation_agent, directions_query, transportation_session, my_user_id, session_service)
    print(f"FIND AND NAVIGATE COMBO FINISHED RUNNING.")




# <-----  VI.   DEFINE THE BRAINS OF THE OPERATION: THE ROUTER AGENT  ------>

router_agent_v1 = create_router_agent_v1(options_str)




# <-----  VII.   RUN SEQUENCE ROUTER  ------>

async def run_sequence_router(queries: list[str]):
    for query in queries:
        router_v1_session = await session_service.create_session(app_name=router_agent_v1.name, user_id=my_user_id)
        chosen_route = await run_agent_query(router_agent_v1, query, router_v1_session, my_user_id, session_service, is_router=True)
        if chosen_route:
            chosen_route = chosen_route.strip().strip("'\"").strip()
        print(f"ROUTER HAS SELECTED THIS ROUTE: '{chosen_route}'")


        if chosen_route == "find_and_naviagate_combo":
            await handle_and_navigate(query)
            continue
        

        if chosen_route in worker_agents:
            worker_agent = worker_agents.get(chosen_route, day_trip_agent)
        

        worker_session = await session_service.create_session(app_name=router_agent_v1.name, user_id=my_user_id)
        await run_agent_query(worker_agent, query, worker_session, my_user_id, session_service)



if __name__ == "__main__":
    asyncio.run(run_sequence_router(queries))