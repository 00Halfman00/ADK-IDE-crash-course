import os
import asyncio
import logging
import vertexai


from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.sessions import InMemorySessionService


from agent_query import run_agent_query
from agents import create_db_agent, create_food_critic_agent, create_concierge_agent

print("✅ ALL LIBRARIES ARE LOADED AND READY!")




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
    logger.info("Found project id!")
else:
    logger.error("No project id found. AI features will be disabled.")

# <---  Initialize Session Service  --->
# This one service will manage all the different sessions.
session_service = InMemorySessionService()
my_user_id = "adk_adventurer_007"




# <-----  III.   DEFINE THE SPECIALIST AGENTS  ------>

db_agent = create_db_agent()
food_critic_agent = create_food_critic_agent()
# The Concierge knows how to use the Food Critic
concierge_agent = create_concierge_agent()




# <-----  IV.   DEFINE THE TOOLS FOR THE ORCHESTRATOR  ------>

async def call_db_agent(question: str, tool_context: ToolContext):
    """Use this tool FIRST to connect to the database and retrieve a list of places, like hotels or landmarks."""

    print("<---  TOOL CALL: call_db_agent --->")
    agent_tool = AgentTool(agent=db_agent)
    db_agent_output = await agent_tool.run_async(args={"request": question}, tool_context=tool_context)

    # Avoid storage collisions/overwrites by keys
    if "db_results" not in tool_context.state:
        tool_context.state["db_results"] = {}

    tool_context.state["db_results"]["retrieved_data"] = db_agent_output
    return db_agent_output



async def call_concierge_agent(question: str, tool_context: ToolContext):
    """After getting data with call_db_agent, use this tool to get travel advice, opinions, or recommendations."""

    print("<---  TOOL CALL: call_concierge_agent  --->")
    # Retrieve the data fetched from the previous tool
    input_data = tool_context.state.get("db_results", {})
    data = input_data.get("retrieved_data") or "No previous database data found."

    # Formulate new prompt for the concierge, giving it the data context
    question_with_data = (
        f"""
        context: The database returned the following data: {data}
        User's request: {question}
        """
    )

    agent_tool = AgentTool(agent=concierge_agent)
    concierge_output = await agent_tool.run_async(args={"request": question_with_data}, tool_context=tool_context)
    return concierge_output





# <-----  V.   DEFINE THE ORCHESTRATOR(TOP-LEVEL) AGENT  ------>

def create_orchestrator_agent() -> Agent:
    """Create the Orchestrator Agent"""

    instruction = (
        """
        You are a master travel planner who uses data to make recommendations.
        1.  **ALWAYS start with the 'call_db_agent' tool** to fetch a list of places (like hotels) that match the user's criteria.
        2.  After you have the data, **use the 'call_concierge_agent' tool to answer any follow-up questions for recommendations, opinions, or advice related to the data you just found.
        """
    )
    
    return Agent(
        name="orchestrator_agent",
        model="gemini-2.5-flash",
        description="Top-level agent that queries a database for travel data, then calls a concierge agent for recommendations.",
        tools=[call_db_agent, call_concierge_agent],
        instruction=instruction
    )


orchestrator_agent = create_orchestrator_agent()
print(f"ORCHESTRATOR AGENT '{orchestrator_agent.name} IS DEFINED AND READY.")




# <-----  VI.   TESTS THE ORCHESTRATOR(TOP-LEVEL) AGENT  ------>

async def test_orchestrator_agent() -> None:
    """Sets up a session and runs a query against the top-level orchestration_agent"""

    # Create a new, single-use session for this query
    orchestrator_session = await session_service.create_session(app_name=orchestrator_agent.name, user_id=my_user_id)
    # This query is designed to trigger the two step process:
    query = "Find the top-rated hotels in San Francisco from the database, then suggest a dinner spot near the one with the most reviews."
    print(f"USER QUERY: '{query}'")
    await run_agent_query(orchestrator_agent, query, orchestrator_session, my_user_id, session_service)





if __name__ == "__main__":
    asyncio.run(test_orchestrator_agent())
