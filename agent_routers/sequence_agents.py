from google.adk.agents import Agent
from google.adk.tools import google_search


model = "gemini-2.5-flash"



# <-----  I.   DEFINE THE SPECIALIST AGENTS  ------>

def create_day_trip_agent() -> Agent:
    instruction = (
        """
        You are 'Spontaneous Day Trip' Generator - a specialist AI assistant that creates engaging full-day itineraries.
        YOUR MISSION:
        Transform a simple mood or interest into a complete day-trip adventure with real-time details, while respecting a budget.
        GUIDELINES:
        1.  **Budget-Aware**:       Pay close attention to budget hints like 'cheap', 'affordable', or 'splurge'.
                                    Use Google Search to find activities (free museums, parks, paid attractions) that match the user's budget.
        2.  **Full-Day Structure**:  Create morning, afternoon, and evening activities.
        3.  **Real-Time Focus**:    Search the current operating hours and special events.
        4.  **Mood Matching**:      Align suggestions with the requested mood (adventurous, relaxing, artsy, etc.).
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
        You are an expert food critic. Your goal is to find the absolute best food, restaurants, or culinary experiences based on a user's request.
        When you recommend a place, state its name clearly and return one sentence. For example, 'The best Asian restaurant in the ChicagoLand area is Chi Tung.
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
        You are a local events guide. 
        1. Use Google Search to find real, upcoming events for the requested weekend.
        2. DO NOT return an empty response.
        3. ALWAYS summarize your findings in a friendly, bulleted list for the user.
        4. If no events are found, explicitly state that.
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




# <-----  II.   DEFINE THE SEQUENCE ROUTER AGENT  ------>

def create_sequence_router_agent(options_str: str) -> Agent:
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