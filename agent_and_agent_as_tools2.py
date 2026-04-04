import os
import asyncio
import logging
import requests
import vertexai


from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.tools import ToolContext
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.sessions import InMemorySessionService, Session


print("✅ All libraries are ready to go!")




# <-----  I.    CONFIGURE LOGGING  ------>

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_and_agents_as_tools2.log"),
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

session_service = InMemorySessionService()
my_user_id = "adk_adventurer_007"






# <-----  III.   DEFINE THE SPECIALIST AGENTS  ------>

# Assume 'db_agent' is a pre-defined NL2SQL Agent.
db_agent = Agent(
    name="db_agent",
    model="gemini-2.0-flash",
    instruction=(
        """
        You are a database agent. When asked for data, return this mock JSON object:
        {
        'status': 'success',
        'data': [{'name': 'The Grand Hotel':, 'rating': 5, 'reviews': 450}, {'name': 'Seaside Inn': 'rating': 4, 'reviews': 650}]
        }
        """
    )
)


food_critic_agent = Agent(
    name="food_critic_agent",
    model="gemini-2.0-flash",
    instruction=(
        """
        You are a snobby but brilliant food critic.
        You ONLY respond with a single, witty restaurant suggestion nearby the location.
        """
    )
)


# The Concierge knows how to use the Food Critic
concierge_agent = Agent(
    name="concierge_agent",
    model="gemini-2.0-flash",
    instruction=(
        """
        You are a five star hotel concierge.
        If the user asks for a restaurant recommendation, you MUST use the 'food_critic_agent' tool.
        Present the opinion to the user politely.
        """
    ),
    tools=[AgentTool(agent=food_critic_agent)]
)




# <-----  IV.   DEFINE THE TOOLS FOR THE ORCHESTRATOR  ------>

async def call_db_agent(question: str, tool_context: ToolContext):
    """Use this tool FIRST to connect to the database and retrieve a list of places, like hotels or landmarks."""

    print("<---  TOOL CALL: call_db_agent --->")
    agent_tool = AgentTool(agent=db_agent)
    db_agent_output = await agent_tool.run_async(args={"request": question}, tool_context=tool_context)

    # Store the retrieved data in the context's state
    tool_context.state["retrieved_data"] = db_agent_output
    return db_agent_output



async def call_concierge_agent(question: str, tool_context: ToolContext):
    """After getting data with call_db_agent, use this toool to get travel advice, opinions, or recommendations."""

    print("<---  TOOLCALL: call_concierge_agent  --->")
    # Retrieve the data fetched from the previous tool
    input_data = tool_context.state.get("retrieved_data", "No data fround.")

    # Formulate new prompt for the conciege, giving it the data context
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

orchestrator_agent = Agent(
    name="orchestrator_agent",
    model="gemini-2.0-flash",
    description="Top-level agent that queries a database for travel data, then calls a concierge agent for recommendations.",
    tools=[call_db_agent, call_concierge_agent],
    instruction=(
        """
        You are a master travel planner who uses data to make recommendations.
        1.  **ALWAYS start with the 'call_db_agent' tool** to fetch a list of places (like hotels) that match the user's criteria.
        2.  After you have the data, **use the 'call_concierge_agent' tool to answer any follow-up questions for recommendations, opinions, or advice related to the data you just found.
        """
    )
)

print(f"Orchestrator Agent: '{orchestrator_agent.name} is defined and ready.")




#  <-----     IV.    FUNCTION TO RUN THE ORCHESTRATOR AGENT    ----->

async def run_agent_query(agent: Agent, query: str, session: Session, user_id: str, is_router: bool = False):
    """Initializes a runner and executes a query for a given agent and session."""

    print(f"\nRunning query for agent: '{agent.name}' in session: '{session.id}'")

    runner = Runner(agent=agent, session_service=session_service, app_name=agent.name)
    final_response = ""

    

