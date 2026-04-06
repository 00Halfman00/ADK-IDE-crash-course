import os
import asyncio
import logging
import vertexai


from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.sessions import InMemorySessionService


from agent_query import run_agent_query


print("✅ ALL LIBRARIES ARE LOADED AND READY TO GO!")




# <-----  I.    CONFIGURE LOGGING  ------>


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_with_memory_adaptive_planner.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)






# <-----  II.   LOAD/INIT ENVIRNONMENT VARIABLES  ------>

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("REGION", 'us-central1')

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
else:
    logger.error("No project id found. AI features will be disabled.")

# <---  Initialize Session Service  --->
# This one service will manage all the different sessions.
session_service = InMemorySessionService()
my_user_id = "adk_adventurer_007"





# <-----  III.   DEFINE THE ADAPTIVE PLANNER WITH MEMORY AGENT  ------>

def create_multi_day_trip_agent():
    """Create the Progressive Multi-Day Planner agent"""

    instructions = (
        """
        You are the "Adaptive Trip Plannner" - an AI assistant that builds multi-day travel itineraries step-by-step.

        YOUR DEFINING FEATURE:
        You have short-term memory. You MUST refer back to our conversation to understand the trip's context, what has already been planned, and the user's preference.
        If the user asks for a change, you must adapt the plan while keeping the unchanged parts consistent.

        YOUR MISSION:
        1.  **Initiate**: Start by asking for the destination, trip duration, and interest.
        2.  **Plan Progressively**: Plan ONLY ONE DAY at a time. After presenting a plan, ask for confirmation.
        3.  **Handle Feedback**: If a user dislikes  a suggestion (e.g., "I don't like museums"), acknowledge their feedback and provide a *new alternative* suggestion for that time slot that still fits the overall theme.
        4.  **Maintain Context**: For each new day, ensure the activities are unique and build logically on the previous days. Do not suggest the same things repeatedly.
        5.  **Final Output**: Return each day's itenerary.
        """
    )

    return Agent(
        name="multi_day_trip_agent",
        model="gemini-2.5-flash",
        description="Agent that progressively plans a multi-day trip, remembering previous days and adapting to user feedback",
        instruction=instructions,
        tools=[google_search]
    )


multi_day_trip_agent = create_multi_day_trip_agent()
print(f"AGENT '{multi_day_trip_agent}' IS DEFINED AND READY.")




#  <-----     IV.    FUNCTION TO TEST ADAPTATION AND MEMORY    ----->

async def test_adaptive_memory_demonstration():
    print("AGENT THAT ADAPTS THE SAME SESSION.")

    # Create a session that will be reused for the entire conversation
    trip_session = await session_service.create_session(app_name=multi_day_trip_agent.name, user_id=my_user_id)
    print(f"CREATED SESSION FOR TRIP: {trip_session.id}")

    # Turn 1: The user initiates the trip
    query1 = "Hi! I want to plan a 2-day trip to Rome, Italy. I'm into historic sites and great local food."
    print(F"USER (TURN 1): '{query1}'")
    await run_agent_query(multi_day_trip_agent, query1, trip_session, my_user_id, session_service)

    # Turn 2: The user gives feedback and ask for a change
    # The same trip session object is used to enable continuous memory
    query2 = "That sounds good, but I am not a huge fan of Museums. Can you replace the activity for Day 1 with something else historical?"
    print(f"\nUSER (TURN 2) FEEDBACK: '{query2}'")
    await run_agent_query(multi_day_trip_agent, query2, trip_session, my_user_id, session_service)

    # Turn 3: The user confirms and asks to continue
    query3 = "Yes, the nnew plan for Day 1 is perfect! Please plan Day 2 now, keeping the food theme in mind."
    print(f"USER (TURN 3) CONFIRMATION: '{query3}'")
    await run_agent_query(multi_day_trip_agent, query3, trip_session, my_user_id, session_service)
 


if __name__ == "__main__":
    asyncio.run(test_adaptive_memory_demonstration())
