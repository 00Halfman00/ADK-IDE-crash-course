import os
import logging
import vertexai
import asyncio

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService


from agents import create_day_trip_agent, create_restaurant_agent, create_weekend_guide_agent, create_transportation_agent ,create_find_and_navigate_agent, create_router_agent_v2
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

ROUTE_DESCRIPTIONS = {
    "foodie_agent": "Only for food, restaurants, or eating.",
    "weekend_guide_agent": "For events, concerts, or weekend activities.",
    "day_trip_agent": "General planner for other day trip requests.",
    "find_and_navigate_agent": "Complex queries needing a place found THEN directions."
}

options_str = "\n".join([f"- '{k}': {v}" for k, v in ROUTE_DESCRIPTIONS.items()])

queries = [
    "I want to eat the best sushi in Palo Alto.",
    "Are there any cool outdoor concerts this weekend?",
    "Find me the best sushi in Palo Alto and then tell me how to get there from the Caltrain station."
]




# <-----  III.   DEFINE THE SPECIALIST AGENTS  ------>
day_trip_agent = create_day_trip_agent()
restaurant_agent = create_restaurant_agent()
weekend_guide_agent = create_weekend_guide_agent()
transport_agent = create_transportation_agent()
find_and_navigate_agent = create_find_and_navigate_agent()




# <-----  IV.   DEFINE THE BRAINS OF THE OPERATION: THE ROUTER AGENT  ------>

router_agent_v2 = create_router_agent_v2(options_str)




# <-----  VI.   DEFINE DICTIONARY OF ALL THE INDIVIDUAL WORKER AGENTS  ------>

worker_agents = {
    "foodie_agent": restaurant_agent,
    "weekend_guide_agent": weekend_guide_agent,
    "day_trip_agent": day_trip_agent,
    "transport_agent": transport_agent
}


print("Agent team assembled with Sequential workflow locked, loaded and ready to go!")




# <-----  VII.   TESTS SEQUENCE  ------>

async def test_sequence_routing(queries: list[str]):

    for query in queries:
        print(f"\n{'='*60}\nPROCESSING NEW QUERY: '{query}'\n{'='*60}")

        # 1.    Router Agent returns the agent it has chosen for the query
        router_session = await session_service.create_session(app_name=router_agent_v2.name, user_id=my_user_id)
        print(f"\nQUERY: '{query}'")
        print("ASKING THE ROUTER AGENT TO MAKE A DECISION.")
        chosen_route = await run_agent_query(router_agent_v2, query, router_session, my_user_id, session_service, is_router=True)
        # Robust cleaning of router response
        if chosen_route:
            chosen_route = chosen_route.strip().strip("'\"").strip()
            
        print(f"ROUTER HAS SELECTED THIS ROUTE: '{chosen_route}'")

        # 2.     Execute the chosen route
        if chosen_route in worker_agents:
            worker_agent = worker_agents[chosen_route]
        else:
            worker_agent = day_trip_agent
        
        worker_session = await session_service.create_session(app_name=worker_agent.name, user_id=my_user_id)
        await run_agent_query(worker_agent, query, worker_session, my_user_id, session_service)




if __name__ == "__main__":
    asyncio.run(test_sequence_routing(queries))