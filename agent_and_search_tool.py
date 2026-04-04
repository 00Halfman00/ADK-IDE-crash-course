import os
import sys
import json
import logging
import asyncio
import random
import string
from uuid import uuid4
from typing import Any, List

import pandas as pd
import plotly.graph_objects as go
import vertexai

# --- ADK, Agent, and Evaluation Components ---
from google.adk.agents import Agent
from google.adk.events import Event
from google.adk.runners import Runner
import google.adk as adk
from google.adk.tools import google_search
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from google.genai.types import Content, Part
from dotenv import load_dotenv


print("✅ All libraries are ready to go!")




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


session_service = InMemorySessionService()
my_user_id = "adk_adventurer_007"


#  <-----     III.    Function to define Agent    ----->


def create_day_trip_agent() -> Agent:
    """Create the Spontaneous Day Trip Generator Agent"""

    instructions = (
        """
        You are the "Spontaneous Day Trip" Generator - a specialized AI assistant that creates engaging full-day iteneraries.
        
        YOUR MISSION:
        Transform a simple mood or interest into a complete day-trip adventure with real-time details, while respecting a budget.

        GUIDELINES:
        1.  **Budget-Aware**: Pay close attention to budget hints like 'cheap', 'affordable', or 'splurge'.
            Use Google Search to find activvities (free museums, parks, paid attractions) that match the user's budget.
        2.  **Full-Day Stucture**: Create morning, afternoon, and evening activities.
        3.  **Real-Time Focus**: Search for current operating hours and special events.
        4.  **Mood Matching**: Align suggestions with the requested mood (adventurous, relaxing, artsy, etc.).

        RETURN itenerary with clear time blocks and specific venue names.
        """
    )

    return Agent(
        name="day_trip_agent",
        model="gemini-2.5-flash",
        instruction=instructions,
        tools=[google_search]
    )

day_trip_agent= create_day_trip_agent()
print(f"Agent: {day_trip_agent.name} is up and ready to create trips.")






#  <-----     IV.    Helper Functions to Run Agent    ----->

async def run_agent_query(agent: Agent, query: str, session: Session, user_id: str, is_router: bool = False) -> str | None:
    """Initializes a runner and executes a query for a given agent and session."""


    print(f"\nRunning query for agent: '{agent.name}' in session: '{session.id}'...")

    runner = Runner(
        agent=agent,
        session_service=session_service,
        app_name=agent.name
    )

    final_response = ""
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=Content(parts=[Part(text=query)], role="user")
        ):
            if not is_router:
                # Let's see what the agent is thinking!
                print(f"EVENT: {event}")
            if event.is_final_response() and event.content and event.content.parts:
                final_response = event.content.parts[0].text
    except Exception as e:
        final_response = f"An error occured in run_agent_query: {e}"

    if not is_router:
        print("\n" + "-"*50)
        print("✅ Final Response:\n")
        print(final_response)
        print("-"*50 + "\n")
    
    return final_response




async def run_day_trip_genie() -> None:
    # Create a new, single-sue session for this query

    day_trip_session = await session_service.create_session(
        app_name=day_trip_agent.name,
        user_id=my_user_id
    )

    query = "Plan a relaxing and artsy day trip near Chicago, Il. Keep it affordable!"
    print(f"user Query: '{query}'")

    await run_agent_query(day_trip_agent, query, day_trip_session, my_user_id)






if __name__ == "__main__":
    asyncio.run(run_day_trip_genie())
