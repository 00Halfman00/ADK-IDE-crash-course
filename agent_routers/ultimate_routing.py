import os
import logging
import vertexai
import asyncio

from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent, ParallelAgent, LoopAgent
from google.adk.sessions import InMemorySessionService

from sequence_agents import (
    create_day_trip_agent,
    create_foodie_agent
)

from sequential_agent_agents import (
    create_foodie_agent_v2,
    create_transportation_agent_v2,
    create_find_and_navigate_agent
)
from ultimate_agents import (
    create_museum_finder_agent, 
    create_concert_finder_agent,
    create_restaurant_finder_agent, 
    create_parallel_research_agent,
    create_synthesis_agent, 
    create_parallel_planner_agent,
    create_planner_agent,
    create_critic_agent,
    create_judge_agent,
    create_refiner_agent,
    create_refinement_loop_agent,
    create_iterative_planner_agent,
    create_router_agent_v3
)
from agent_query import run_agent_query

print("✅ ALL LIBRARIES ARE LOADED AND READY TO GO!")




# <-----  I.    CONFIGURE LOGGING  ------>

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("routing_agents_v3.log"),
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

# <---  Initialize Session Service  --->
# This one service will manage all the different sessions.
session_service = InMemorySessionService()
my_user_id = "adk_adventurer_007"

print("✅ ALL ENVIRONMENT VARIABLES ARE LOADED AND READY TO GO!")



# <-----  III.   DEFINE THE SPECIALIST AGENTS  ------>

day_trip_agent: Agent = create_day_trip_agent()
foodie_agent: Agent = create_foodie_agent()

print("✅ ALL SPECIALIST AGENTS ARE LOADED AND READY TO GO!")

foodie_agent_v2: Agent = create_foodie_agent_v2()
transportation_agent_v2: Agent = create_transportation_agent_v2()
find_and_navigate_agent: SequentialAgent = create_find_and_navigate_agent([
    foodie_agent_v2,
    transportation_agent_v2
])

print("✅ ALL SEQUENTIAL WORKFLOW AGENTS ARE LOADED AND READY TO GO!")

museum_finder_agent: Agent = create_museum_finder_agent()
concert_finder_agent: Agent = create_concert_finder_agent()
restaurant_finder_agent: Agent = create_restaurant_finder_agent()
parallel_research_agent: ParallelAgent = create_parallel_research_agent([
    museum_finder_agent,
    concert_finder_agent,
    restaurant_finder_agent
])
synthesis_agent: Agent = create_synthesis_agent()
parallel_planner_agent: SequentialAgent = create_parallel_planner_agent([
    parallel_research_agent, 
    synthesis_agent
])

print("✅ ALL PARALLEL WORKFLOW AGENS ARE LOADED AND READY TO GO!")

planner_agent: Agent = create_planner_agent()
critic_agent_1: Agent = create_critic_agent(name="initial_critic_agent")
critic_agent_2: Agent = create_critic_agent(name="final_critic_agent")
judge_agent: Agent = create_judge_agent()
refiner_agent: Agent = create_refiner_agent()

refinement_loop_agent: LoopAgent = create_refinement_loop_agent([
    critic_agent_1, 
    refiner_agent, 
    critic_agent_2, 
    judge_agent
])
iterative_planner_agent: SequentialAgent = create_iterative_planner_agent([
    planner_agent, 
    refinement_loop_agent
])

print("✅ ALL ITERATIVE WORKFLOW AGENTS ARE LOADED AND READY TO GO!")





# <-----  IV.   LOAD/INIT AI VARIABLES/INFO  ------>

ROUTE_DESCRIPTIONS = {
    "foodie_agent": "Only for food, restaurants, or eating.",
    "find_and_navigate_agent": "For queries that ask to *first find a place* and *then get directions* to it.",
    "iterative_planner_agent": "For planning a trip with a specific constraint that needs checking, like travel time.",
    "parallel_planner_agent": "For queries that ask to find multiple, independent things at once (e.g., a museum AND a concert AND a restaurant)",
    "day_trip_agent": "General planner for other day trip requests.",
}

options_str = "\n".join([f"- '{k}': {v}" for k, v in ROUTE_DESCRIPTIONS.items()])

worker_agents: dict[str, Agent | SequentialAgent | ParallelAgent | LoopAgent] = {
    "day_trip_agent": day_trip_agent, 
    "foodie_agent": foodie_agent, # For simple food queries
    "find_and_navigate_agent": find_and_navigate_agent, # Sequential
    "iterative_planner_agent": iterative_planner_agent, # Loop
    "parallel_planner_agent": parallel_planner_agent,   # Parallel
}

# queries = [
#     # Test Case 1: Simple Sequential Flow
#     "Find me the best sushi in Palo Alto and then tell me how to get there from the Caltrain station.",
#     # Test Case 2: Iterative Loop Flow
#     "Plan me a day in San Francisco with a museum and a nice dinner, but make sure the travel time between them is very short.",
#     # Test Case 3: Parallel Flow
#     "Help me plan a trip to SF. I need one museum, one concert, and one great restaurant.",
#     # Test Case 4: General Food Query
#     "Find me a good coffee shop in the neighborhood of Pilsen in Chicago."
# ]

queries = [
    # Test Case 3: Parallel Flow
    "Help me plan a trip to SF. I need one museum, one concert, and one great restaurant.",
]


print("✅ AGENT INFO IS READY TO GO!")




# <-----  V.   DEFINE THE ROUTER AGENT  ------>

router_agent_v3: Agent = create_router_agent_v3(options_str)

print("✅ ROUTER AGENT IS LOADED AND READY TO GO!")


# <-----  VII.   TESTS ROUTING  ------>

async def run_fully_loaded_router(queries: list[str]):
    for query in queries:
        router_session = await session_service.create_session(app_name=router_agent_v3.name, user_id=my_user_id)
        chosen_route = await run_agent_query(router_agent_v3, query, router_session, my_user_id, session_service, is_router=True)
        if chosen_route:
            chosen_route = chosen_route.strip().strip("'\"").strip()
        
        print(f"ROUTER HAS SELECTED THIS ROUTE: '{chosen_route}'")
        worker_agent: Agent | SequentialAgent | ParallelAgent | LoopAgent = day_trip_agent
        if chosen_route in worker_agents:
            worker_agent = worker_agents[chosen_route]
            worker_session = await session_service.create_session(app_name=worker_agent.name, user_id=my_user_id)
            await run_agent_query(worker_agent, query, worker_session, my_user_id, session_service)
        else:
            print(f"🚨 Error: Router chose an unknown route: '{chosen_route}'")



if __name__ == "__main__":
    asyncio.run(run_fully_loaded_router(queries))



"""

✅ FINAL RESPONSE:      (QUERY 1)
Fuki Sushi is located at 4119 El Camino Real, Palo Alto, CA 94306. The Palo Alto Caltrain Station is located at 95 University Ave, Palo Alto, CA 94301.

Here are the directions to Fuki Sushi from the Palo Alto Caltrain Station:

**By Public Transit (Bus):**

The most straightforward public transit option involves taking a bus along El Camino Real.

1.  **Walk to the bus stop:** From the Palo Alto Caltrain Station (95 University Ave), head towards El Camino Real. This is about a 5-10 minute walk.
2.  **Take the VTA Line 22 or SamTrans ECR bus:** Both of these bus lines travel along El Camino Real.
    *   Catch the **VTA Line 22** bus heading South (towards Eastridge) from a stop near the intersection of University Avenue and El Camino Real.
    *   Alternatively, catch the **SamTrans ECR** bus heading South from a stop near the intersection of University Avenue and El Camino Real.
3.  **Exit at Arastradero Road:** Ride the bus for approximately 15-20 minutes, depending on traffic, and exit at the bus stop near Arastradero Road on El Camino Real. Fuki Sushi will be a short walk from this stop.
    *   Fuki Sushi is located at 4119 El Camino Real.

**By Walking:**

The walk from Palo Alto Caltrain Station to Fuki Sushi is approximately 2.5 to 3 miles and would take around 45-60 minutes.

1.  **Start at Palo Alto Caltrain Station:** Head southwest on University Avenue towards El Camino Real.
2.  **Turn left onto El Camino Real:** Continue south on El Camino Real for approximately 2.5 miles.
3.  **Fuki Sushi will be on your right:** Fuki Sushi is located at 4119 El Camino Real.
"""



"""✅ FINAL RESPONSE:      (QUERY 2)
Activity: California Academy of Sciences
Restaurant: The Moss Room
"""



"""✅ FINAL RESPONSE:      (QUERY 3)
- Museum: California Academy of Sciences
- Concert: Blomstedt Conducts Mahler 9
- Restaurant: Mister Jiu's
"""



"""✅ FINAL RESPONSE:      (QUERY 4)
✅ FINAL RESPONSE:
 The best coffee shop in the Pilsen neighborhood of Chicago is Cafe Jumping Bean.
"""