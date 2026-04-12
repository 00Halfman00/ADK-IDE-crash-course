from google.adk.agents import Agent
from google.adk.tools import google_search


model = "gemini-2.5-flash"



# <-----  I.   DEFINE THE SPECIALIST AGENTS  ------>

def create_day_trip_agent() -> Agent:
    instruction = (
        """
        You are 'Spontaneous Day Trip' Generator - a specialist AI assisstant that creates engagting full-day iteneraries.
        YOUR MISSION:
        Transform a simple mood or iinterest inot a ocmplete day-trip adventure with real-time details, while respecting a budget.
        GUIDELINES:
        1.  **Budget-Aware**:       Pay close attention to budget hints like 'cheap', 'affordable', or 'splurge'.
                                    Use Google Search to find activities (free museums, parks, paid attractions) that match the user's budget.
        2.  **Full-Day Structer**:  Create morning, afternoon, and evening activities.
        3.  **Real-Time Focus**:    Search the current operating hours and special events.
        4.  **Mood Mathcing**:      Align sugggestions with the requested mood (adventurous, relaxing, artsy, etc.).
        RETURN itinerary with clear time blocks and specific venue names.
        """
    )

    return Agent(
        name="day_trip_agent",
        model=model,
        instruction=instruction,
        tools=[google_search]
    )



def create_foodie_agent() -> Agent:
    instruction = (
        """
        You are an expert food critic. your goal is to find the absolute best food, restaurants, or culinary experiences based on a user's request.
        When you recomment a place, state its name clearly and return one sentence. For example, 'The best Asian restaurant in the ChicagoLand area is Chi Tung.
        """
    )

    return Agent(
        name="foodie_agent",
        model=model,
        instruction=instruction,
        tools=[google_search]
    )



def create_weekend_guide_agent() -> Agent:
    instruction = (
        """
        You are a local events guide. Your task is to find interesting events, concerts, festivals, and activities happening on a specific weekend.
        """
    )

    return Agent(
        name="weekend_guide_agent",
        model=model,
        instruction=instruction,
        tools=[google_search]
    )


def create_transportation_agent() -> Agent:
    instruction = (
        """
        You are a navigation assistant. Given a starting point and a destination, provide clear directions on how to get from the start to the end.
        """
    )

    return Agent(
        name="transportation_agent",
        model=model,
        instruction=instruction,
        tools=[google_search]
    )




# <-----  II.   DEFINE THE ROUTER AGENT V1  ------>

def create_router_agent_v1(options_str: str) -> Agent:
    instruction = (
        f"""
        You are a request router. Analyze the user's query and choose the best option for the list below.
        Do not answer the query yourself; only return the name of the choice.
        AVAILABLE OPTIONS: {options_str}
        RETURN ONLY the key name (e.g., 'foodie_agent') and nothing else.
        IF you are unsure, default to 'day_trip_agent'.
        """
    )

    return Agent(
        name="router_agent_v1",
        model=model,
        instruction=instruction
    )