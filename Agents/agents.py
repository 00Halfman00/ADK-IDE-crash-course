import logging

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search



# <-----  I.    CONFIGURE LOGGING  ------>

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agents.log")
    ],
    force=True
)

logger = logging.getLogger(__name__)

print("✅ LOGGERS ARE CONFIGURED, LOADED AND READY TO GO!")




model = "gemini-2.5-flash"

# <-----  II.   DEFINE THE SPECIALIST AGENTS  ------>


def create_day_trip_agent() -> Agent:
    instructions = (
        """
        You are the "Spontaneous Day Trip" Generator - a specialized AI assistant that creates engaging full-day itineraries.
        YOUR MISSION:
        Transform a simple mood or interest into a complete day-trip adventure with real-time details, while respecting a budget.
        GUIDELINES:
        1.  **Budget-Aware**: Pay close attention to budget hints like 'cheap', 'affordable', or 'splurge'.
            Use Google Search to find activities (free museums, parks, paid attractions) that match the user's budget.
        2.  **Full-Day Structure**: Create morning, afternoon, and evening activities.
        3.  **Real-Time Focus**: Search for current operating hours and special events.
        4.  **Mood Matching**: Align suggestions with the requested mood (adventurous, relaxing, artsy, etc.).
        RETURN itinerary with clear time blocks and specific venue names.
        """
    )

    return Agent(
        name="day_trip_agent",
        model=model,
        description="Generates spontaneous full-day itineraries based on mood, budget, and real-time data.",
        instruction=instructions,
        tools=[google_search]
    )

###############################################################################################################################

def create_weather_planner_agent(callback) -> Agent:
    instruction = (
        """
        You are a cautious trip planner. Before suggesting any outdoor activities, you MUST use the 'get_live_weather_forecast' tool to check conditions.
        Incorporate the live weather details into your recommendation.
        """
    )

    return Agent(
        name="weather_aware_planner",
        model=model,
        description="A trip planner that checks the real-time weather before making suggestions.",
        instruction=instruction,
        tools=[callback]
    )

###############################################################################################################################



# Assume 'db_agent' is a pre-defined NL2SQL Agent.
def create_db_agent() -> Agent:
    instruction = (
        """
        You are a database agent. When asked for data, return this mock JSON object:
        {
        'status': 'success',
        'data': [{'name': 'The Grand Hotel', 'rating': 5, 'reviews': 450}, {'name': 'Seaside Inn', 'rating': 4, 'reviews': 650}]
        }
        """
    )

    return Agent(
        name="db_agent",
        model=model,
        description="Queries the travel database for hotel information and ratings.",
        instruction=instruction
    )




def create_food_critic_agent() -> Agent:
    instruction = (
        """
        You are a snobby but brilliant food critic.
        You ONLY respond with a single, witty restaurant suggestion nearby the location.
        """
    )

    return Agent(
        name="food_critic_agent",
        model=model,
        description="A witty food critic providing single, high-quality restaurant recommendations.",
        instruction=instruction
    )




def create_concierge_agent(agent: Agent) -> Agent:
    instruction = (
        """
        You are a five star hotel concierge.
        If the user asks for a restaurant recommendation, you MUST use the 'food_critic_agent' tool.
        Present the opinion to the user politely.
        """
    )

    return Agent(
        name="concierge_agent",
        model=model,
        description="A high-end concierge that coordinates with a food critic for restaurant advice.",
        instruction=instruction,
        tools=[AgentTool(agent=agent)]
    )


def create_orchestrator_agent(*callbacks) -> Agent:
    instruction = (
        """
        You are a master travel planner who uses data to make recommendations.
        1.  **ALWAYS start with the 'call_db_agent' tool** to fetch a list of places (like hotels) that match the user's criteria.
        2.  After you have the data, **use the 'call_concierge_agent' tool to answer any follow-up questions for recommendations, opinions, or advice related to the data you just found.
        """
    )
    
    return Agent(
        name="orchestrator_agent",
        model=model,
        description="Top-level agent that queries a database for travel data, then calls a concierge agent for recommendations.",
        tools=list(callbacks),
        instruction=instruction
    )



###############################################################################################################################

def create_multi_day_trip_agent() -> Agent:
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
        model=model,
        description="Agent that progressively plans a multi-day trip, remembering previous days and adapting to user feedback",
        instruction=instructions,
        tools=[google_search]
    )
