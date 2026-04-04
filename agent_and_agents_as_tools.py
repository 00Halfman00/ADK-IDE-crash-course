import os
import sys
import json
import logging
import asyncio
import random
import string
import requests
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
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.genai import types
from google.genai.types import Content, Part
from dotenv import load_dotenv


print("✅ All libraries are ready to go!")




# <-----  I.    CONFIGURE LOGGING  ------>

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_and_agents_as_tools.log"),
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




# <-----  III.   DEFINE THE SPECIALIST AGENTS  ------>
# For this example, we'll create placeholder agents.

# Assume 'db_agent' is a pre-defined NL2SQL Agent.
db_agent = Agent(
    name="db_agent",
    model="gemini-2.5-flash",
    instruction="You are a database agent. When asked for data, return this mock JSON object: {'status': 'success', 'data': [{'name': 'The Grand Hotel', 'rating': 5, 'reviews': 450}, {'name': 'Seaside Inn', 'rating': 4, 'reviews': 620}]}"
)


food_critic_agent = Agent(
    name = "food_critic_agent",
    model="gemini-2.5-flash",
    instruction="You are a snobby but brilliant food critic. You ONLY respond with a single, witty restaurant suggention nearby the location."
)

# The Concierge knows how to use the Food Critic
concierge_agent = Agent(
    name = "concierge_agent",
    model="gemini-2.5-flash",
    instruction="You are a five-star hotel concierge. If the user asks for a restaurant recommendation, you MUST use the 'food_critic_agent' tool. Present the opinion to the user politely.",
    tools=[AgentTool(agent=food_critic_agent)]
)




# <-----  IV.   FUNCTIONS THAT DEFINE THE TOOLS FOR THE ORCHESTRATOR  ------>

async def call_db_agent(question: str, tool_context: ToolContext):
    """Use this tool FIRST to connect to the database and retrieve a list of places, like hotels or landmarks."""

    print("<---  TOOL CALL: call_db_agent  --->")
    agent_tool = AgentTool(agent=db_agent)
    db_agent_output = await agent_tool.run_async(args={"request": question}, tool_context=tool_context)

    # store the retrieved data in the context's state
    tool_context.state["retrieved_data"] = db_agent_output
    return db_agent_output



async def call_concierge_agent(question: str, tool_context: ToolContext):
    """After getting data with call_db_agent, use this tool to get travel advice, opnions, or recommendations."""

    print("<---  TOOL CALL: call_concierge_agent  --->")
    # Retrieve the data fetched from the previous tool
    input_data = tool_context.state.get("retrieved_data", "No data found.")

    # Formulate new prompt for the concierge, giving it the data context
    question_with_data = (
        f"""
        context: The database returned the following data: {input_data}
        User's request: {question}
        """
    )

    agent_tool = AgentTool(agent=concierge_agent)
    concierge_output = await agent_tool.run_async(args={"request": question_with_data}, tool_context=tool_context)
    return concierge_output








# <-----  V.   DEFINE THE ORCHESTRATOR(TOP-LEVEL) AGENT  ------>

trip_data_concierge_agent = Agent(
    name="trip_data_concierge",
    model="gemini-2.5-flash",
    description="Top-level agent that queries a database for travel data, then calls a concierge agent for recommendations.",
    tools=[call_db_agent, call_concierge_agent],
    instruction=(
        """
        You are a master travel planner who uses data to make recommendations.
        1.  **ALWASYS start with the 'call_db_agent' tool** to fetch a list of places (like hotels) that match the user's criteria.
        2.  After you have the data, **use the 'call_concierge_agent' tool** to answer any follow-up questions for recommendations, opinions, or advice related to the data you just found.
        """
    )

)

print(f"Orchestrator Agent: '{trip_data_concierge_agent.name} is defined and ready.")


#  <-----     IV.    FUNCTION TO RUN THE ORCHESTRATOR AGENT    ----->

async def run_agent_query(agent: Agent, query: str, session: Session, user_id: str, is_router: bool = False) -> str | None:
    """Initializes a runner and executes a query for a given agent and session."""


    print(f"\nRunning query for agent: '{agent.name}' in session: '{session.id}'...")

    runner = Runner(agent=agent, session_service=session_service, app_name=agent.name)
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


async def run_trip_concierge():
    """
    Sets up a session and runs a query against the top-level trip_data_concierge_agent.
    """

    # Create a new, single-use session for this query
    concierge_session = await session_service.create_session(
        app_name=trip_data_concierge_agent.name,
        user_id=my_user_id
    )

    # This query is specifically designed to trigger the full two-step process:
    # 1.    Get data from the db_agent
    # 2.    Get a recommendation from the concierge_agent based on that data.
    query = "Find the top-rated hotels in San Francisco from the database, then suggest a dinner spot near the one with the most reviews."
    print(f"User Query: '{query}'")

    # We call our existing helper function with the top-level orchestrator agent
    await run_agent_query(trip_data_concierge_agent, query, concierge_session, my_user_id)

# Run the test

if __name__ == "__main__":
    asyncio.run(run_trip_concierge())
