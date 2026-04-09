import os
import logging
import vertexai
import asyncio

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService


from agents import create_day_trip_agent, create_foodie_agent, create_weekend_guide_agent, create_transportation_agent
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
    "find_and_navigate_combo": "Complex queries needing a place found THEN directions."
}

options_str = "\n".join([f"- '{k}': {v}" for k, v in ROUTE_DESCRIPTIONS.items()])


queries = [
    "I want to eat the best sushi in Palo Alto.",
    "Are there any cool outdoor concerts this weekend?",
    "Find me the best sushi in Palo Alto and then tell me how to get there from the Caltrain station."
]




# <-----  III.   DEFINE THE SPECIALIST AGENTS  ------>

foodie_agent: Agent = create_foodie_agent()
weekend_guide_agent:Agent = create_weekend_guide_agent()
day_trip_agent:Agent = create_day_trip_agent()
transportation_agent:Agent = create_transportation_agent()




# <-----  IV.    DEFINE CUSTOM AGENT WORKFLOWS (COMBO ROUTES)  ------>

async def handle_find_and_navigate(query):
    foodie_session = await session_service.create_session(app_name=foodie_agent.name, user_id=my_user_id)
    foodie_response = await run_agent_query(foodie_agent, query, foodie_session, my_user_id, session_service)
    print(f"FOODIE AGENT'S RESPONSE: '{foodie_response}'")

    directions_query = f"Give me directions to the place mentioned in this recommendation: {foodie_response}. Starting direction is Palo Alto Caltrain station."
    transport_session = await session_service.create_session(app_name=transportation_agent.name, user_id=my_user_id)
    await run_agent_query(transportation_agent, directions_query, transport_session, my_user_id ,session_service)
    print(f"FIND AND NAVIGATE COMBO FINISHED RUNNING.")




# <-----  V.   DEFINE THE BRAINS OF THE OPERATION: THE ROUTER AGENT  ------>

def create_router_agent() -> Agent:
    instruction = (
        f"""
        You are a request router. Analyze the user's query and choose the best option from the list below.
        Do not answer the query yourself; only return the name of the choice.

        Available Options:
        {options_str}

        Return only the key name (e.g., 'foodie_agent') and nothing else.
        If you are unsure, default to 'day_trip_agent'.
        """
    )
    return Agent(
        name="router_agent",
        model="gemini-2.5-flash",
        instruction=instruction
    )


router_agent = create_router_agent()




# <-----  VI.   DEFINE DICTIONARY OF ALL THE INDIVIDUAL WORKER AGENTS  ------>

worker_agents = {
    "foodie_agent": foodie_agent,
    "weekend_guide_agent": weekend_guide_agent,
    "day_trip_agent": day_trip_agent,
    "transportation_agent": transportation_agent
}

print("✅ ALL AGENTS ARE LOADED AND READY TO GO!")




# <-----  VII.   TESTS SEQUENCE  ------>

async def test_sequence_routing(queries: list[str]):
    for query in queries:
        # 1.    Router Agent output
        router_session = await session_service.create_session(app_name=router_agent.name, user_id=my_user_id)
        print(f"\nQUERY: '{query}'")
        print("ASKING THE ROUTER AGENT TO MAKE A DECISION.")
        chosen_route = await run_agent_query(router_agent, query, router_session, my_user_id, session_service, is_router=True)
        
        # Robust cleaning of router response
        if chosen_route:
            chosen_route = chosen_route.strip().strip("'\"").strip()
            
        print(f"ROUTER HAS SELECTED THIS ROUTE: '{chosen_route}'")

        # 2.    Routing logic
        if chosen_route == "find_and_navigate_combo":
            await handle_find_and_navigate(query)
            continue
        
        # Get the worker agent or default to day_trip_agent
        worker_agent = worker_agents.get(chosen_route, day_trip_agent)
        if chosen_route not in worker_agents:
            print(f"⚠️ ROUTE '{chosen_route}' NOT FOUND. DEFAULTING TO 'day_trip_agent'.")

        worker_session = await session_service.create_session(app_name=worker_agent.name, user_id=my_user_id)
        await run_agent_query(worker_agent, query, worker_session, my_user_id, session_service)




if __name__ == "__main__":
    asyncio.run(test_sequence_routing(queries))
