from google.adk.agents import Agent, SequentialAgent, BaseAgent
from google.adk.tools import google_search
from typing import cast


model = "gemini-2.5-flash"




# <-----  I.   DEFINE THE SPECIALIST AGENTS  ------>



def create_foodie_agent_v2() -> Agent:
    instructions = (
        """
        You are an expert food critic. Your goal is to find the best restaurant based on a user's request.
        When you recommend a place, you must outpu *ONLY* the name of the establishment and nothing else.
        For example, if the best sushi is at 'Chi Tung', you should output only: Chi Tung
        """
    )

    return Agent(
        name="restaurant_agent",
        model=model,
        instruction=instructions,
        output_key="destination"
    )



def create_transportation_agent_v2() -> Agent:
    instruction = (
        """
        You are a navigation assistant. Given a destination, provide clear directions.
        The user wants to go to {destination}.
        Analyze the user's full original query to find their starting point.
        Then, provide clear directions from that starting point to {destination}.
        """
    )

    return Agent(
        name="transport_agent",
        model=model,
        tools=[google_search],
        instruction=instruction
    )


def create_find_and_navigate_agent(agents: list[Agent]) -> SequentialAgent:
    return SequentialAgent(
        name="find_and_navigate_agent",
        sub_agents=cast(list[BaseAgent], agents),
        description="A workflow that first finds a location and then provides directions to it."
    )



def create_router_agent_v2(options_str: str) -> Agent:
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
        name="router_agent_v2",
        model=model,
        instruction=instruction
    )