import os
import logging
import asyncio
import requests
import vertexai

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai.types import Content, Part
from dotenv import load_dotenv


print("✅ All libraries are ready to go!")




# <-----  I.    CONFIGURE LOGGING  ------>

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_and_custom_weather_tool.log"),
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


# <---  Initialize Session Service  --->
# This one service will manage all the different sessions.
session_service = InMemorySessionService()
my_user_id = "adk_adventurer_007"

LOCATION_COORDINATES = {
    "sunnyvale": "37.3688,-122.0363",
    "san francisco": "37.7749,-122.4194",
    "lake tahoe": "39.0968,-120.0324"
}




# <-----  III.   TOOL DEFINITION: A FUNCTION THAT CALLS A LIVE PUBLIC API  ------>

def get_live_weather_forecast(location: str) -> dict:
    """
    Gets the current, real-time weather forecast for a specified location in the US.
    Args:
        location: The city name, e.g., "San Francisco".
    Returns:
        A dictionary containing the temperature and a detailed forecast.
    """
    print(f"TOOL CALLED: get_live_weather_forecast(location='{location}')")

    # Find coordinates for the location
    normalized_location = location.lower()
    coords_str = None
    for key, val in LOCATION_COORDINATES.items():
        if key in normalized_location:
            coords_str = val
            break
    if not coords_str:
        return {"status": "error", "message": f"I don't have coordinates for {location}."}
    

    try:
        #   NWS API requires TWO steps:
        # 1.    Get the forecast URL from the coordinates.
        points_url = f"https://api.weather.gov/points/{coords_str}"
        headers = {"User-Agent": "ADK Example IDE"}
        points_response = requests.get(points_url, headers=headers)
        points_response.raise_for_status() # Raise an exception for bad status codes
        forecast_url = points_response.json()['properties']['forecast']

        # 2.    Get the actual forecast from the URL.
        forecast_response = requests.get(forecast_url, headers=headers)
        forecast_response.raise_for_status() # Raise an exception for bad status codes

        # Extract the relevant forecast details
        current_period = forecast_response.json()['properties']['periods'][0]

        return {
            "status": "success",
            "temperature": f"{current_period['temperature']}°{current_period['temperatureUnit']}",
            "forecast": current_period['detailedForecast']
        }
        
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"API request failed: {e}"}





#  <-----     IV.    FUNCTION TO DEFINE THE WEATHER AGENT    ----->

def create_weather_planner_agent() -> Agent:
    "Create the Weather Agent"
    
    instruction = (
        """
        You are a cautious trip planner. Before suggesting any outdoor activities, you MUST use the 'get_live_weather_forecast' tool to check conditions.
        Incorporate the live weather details into your recommendation.
        """
    )

    return Agent(
        name="weather_aware_planner",
        model="gemini-2.5-flash",
        description="A trip planner that checks the real-time weather before making suggestions.",
        instruction=instruction,
        tools=[get_live_weather_forecast]
    )


weather_agent = create_weather_planner_agent()
print(f" Agent: {weather_agent.name} is created and can now call a live weather API!")




#  <-----     V.    FUNCTION TO RUN AGENT    ----->

async def run_agent_query(agent: Agent, query: str, session: Session, user_id: str, is_router: bool = False) -> str | None:
    """Initializes a runner and executes a query for a given agent and session."""

    print(f"\nRunning query for agent: '{agent.name}' in session: '{session.id}'...")
    runner = Runner(agent=agent, session_service=session_service, app_name=agent.name)
    final_response = ""

    try:
        async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=Content(parts=[Part(text=query)], role="user")):
            if not is_router:
                # Let's see what the agent is thinking!
                print(f"EVENT: {event}")
            if event.is_final_response() and event.content and event.content.parts:
                final_response = event.content.parts[0].text

    except Exception as e:
        final_response = f"An error occurred in run_agent_query: {e}"

    if not is_router:
        print("\n" + "-"*50)
        print("✅ Final Response:\n")
        print(final_response)
        print("-"*50 + "\n")
    
    return final_response




#  <-----     VI.    FUNCTION TO TEST THE WEATHER PLANNER AGENT    ----->

async def test_weather_planner_agent():
    # Create a new, single-use session for this query

    weather_session = await session_service.create_session(
        app_name=weather_agent.name, 
        user_id=my_user_id
    )

    query = "I want to go hiking near Lake Tahoe, what's the weather like?"
    print(f"User query: '{query}'")

    await run_agent_query(weather_agent, query, weather_session, my_user_id)





if __name__ == "__main__":
    asyncio.run(test_weather_planner_agent())
