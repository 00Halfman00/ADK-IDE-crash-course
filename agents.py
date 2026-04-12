from google.adk.agents import Agent, SequentialAgent, ParallelAgent, BaseAgent, LoopAgent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search
from typing import cast


model = "gemini-2.5-flash"

# <-----  I.   DEFINE THE SPECIALIST AGENTS  ------>


# Assume 'db_agent' is a pre-defined NL2SQL Agent.
def create_db_agent() -> Agent:
    """Create the Database Agenty"""

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
        instruction=instruction
    )




def create_food_critic_agent() -> Agent:
    """Create a Food Critic Agent"""

    instruction = (
        """
        You are a snobby but brilliant food critic.
        You ONLY respond with a single, witty restaurant suggestion nearby the location.
        """
    )

    return Agent(
        name="food_critic_agent",
        model=model,
        instruction=instruction
    )




def create_concierge_agent() -> Agent:
    """Create the Concierge Agent"""

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
        instruction=instruction,
        tools=[AgentTool(agent=create_food_critic_agent())]
    )




def create_multi_day_trip_agent() -> Agent:
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
        model=model,
        description="Agent that progressively plans a multi-day trip, remembering previous days and adapting to user feedback",
        instruction=instructions,
        tools=[google_search]
    )


########################################################################################################################
# <-----  I.   DEFINE THE SPECIALIST AGENTS FOR ROUTER V1  ------>

def create_day_trip_agent() -> Agent:
    """Create the Spontaneous Day Trip Generator Agent"""

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
        instruction=instructions,
        tools=[google_search]
    )




def create_foodie_agent() -> Agent:
    """Create the Food Critic Agent that takes general questions"""

    instruction = (
        """
        You are an expert food critic. Your goal is to find the absolute best food, restaurants, or culinary experiences based on a user's request.
        When you recommend a place, state its name clearly and return one sentence. For example: "The best asian restaruant is the Chicagoland area is Chi Tung."
        """
    )

    return Agent(
        name="foodie_agent",
        model=model,
        tools=[google_search],
        instruction=instruction
    )




def create_weekend_guide_agent() -> Agent:
    """Create the Weekend Guide Agent"""

    instruction = (
        """
        You are a local events guide. Your task is to find interesting events, concerts, festivals, and activities happening on a specific weekend.
        """
    )
    
    return Agent(
    name="weekend_guide_agent",
    model=model,
    tools=[google_search],
    instruction=instruction
)




def create_transportation_agent() -> Agent:

    instruction = "You are a navigation assistant. Given a starting point and a destination, provide clear directions on how to get from the start to the end."

    return Agent(
        name="transportation_agent",
        model=model,
        tools=[google_search],
        instruction=instruction
    )


def create_router_agent_v1(options_str:str) -> Agent:
    instruction = (
        f"""
        You are a request router. Analyze the user's query and choose the best option from the list below.
        Do not answer the query yourself; only return the name of the choice.

        Available Options:
        {options_str}

        Return only the key name (e.g., 'foodie_agent') and nothing else.
        If you are unsure, default to 'day_trip_agent'.
        """
    )
    return Agent(
        name="router_agent_v1",
        model=model,
        instruction=instruction
    )

######################################################################################################################################################


def create_restaurant_agent() -> Agent:
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









def create_transport_agent() -> Agent:
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


def create_find_and_navigate_agent() -> SequentialAgent:
    return SequentialAgent(
        name="find_and_navigate_agent",
        sub_agents=[create_restaurant_agent(), create_transport_agent()],
        description="A workflow that first finds a location and then provides directions to it."
    )


def create_router_agent_v2(options_str: str) -> Agent:
    instruction = (
        f"""
        You are a request router. Your job is to analyze a user's query and decide which of the following agents or workflows is best suited to handle it.
        Do not answer the query yourself, only return the name of the most appropriate choice.
        Available Options: {options_str}
        Return only the key name (e.g., 'foodie_agent') and nothing else.
        If you are unsure, default to 'day_trip_agent'.
        """
    )

    return Agent(
        name="router_agent_v2",
        model=model,
        instruction=instruction
    )




#############################################################################################################################################


COMPLETION_PHRASE = "The plan is feasible and meets all constraints."


def exit_loop(tool_context: ToolContext) -> object:
    """Call this function ONLY when the plan is approved, signaling the loop should end."""

    print(f" [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    return {}



# Agent 1: Proposes an initial plan
def create_planner_agent() -> Agent:
    instruction = (
        """
        You are a trip planner. Based on the user's request, propose a single activity and a single restaurant.
        Output only the names, like: 'Activity': Exploratorium, Restaurant: 'La Mar'.
        """
    )

    return Agent(
        name="planner_agent",
        model=model,
        instruction=instruction,
        output_key="current_plan"
    )



# Agent 2 (in loop): Critiques the plan
def create_critic_agent() -> Agent:
    instruction = (
        f"""
        You are a logistics expert. Your job is to critique a travel plan. The user has a strict constraint: total travel time must be short.
        Current Plan: {{current_plan}}
        Use your tools to check the travel time between the two locations.

        IF the travel time is over 45 minutes, provide a critique, like: 'This plan is inefficient. Find a restaurant closer to the activity.
        ELSE, respond with texact phrase: '{COMPLETION_PHRASE}'
        """
    )

    return Agent(
        name="critic_agent",
        model=model,
        tools=[google_search],
        instruction=instruction,
        output_key="criticism"
    )


# Agent 3 (in loop): Refines the plan or exits
def create_refiner_agent() -> Agent:
    instruction = (
        f"""
        You are a trip planner, refining a plan based on criticism.
        Original request: {{session.query}}
        Critique: {{criticism}}
        IF the critique is '{COMPLETION_PHRASE}', you MUST call the 'exit_loop' tool.
        ELSE, generate a NEW plan that addresses the critique. Output only the new names, like: 'Activity: de Young Museum, Restaurant: Nopa'.
        """
    )

    return Agent(
        name="refiner_agent",
        model=model,
        tools=[google_search, exit_loop],
        instruction=instruction,
        output_key="current_plan"
    )

def create_refinement_loop_agent(agents: list[Agent]) -> LoopAgent:
    return LoopAgent(
        name="refinement_agent",
        sub_agents=cast(list[BaseAgent], agents)
    )



def create_iterative_planner_agent(agents: list[Agent | LoopAgent]) -> SequentialAgent:
    return SequentialAgent(
        name="iterative_planner_agent",
        sub_agents=cast(list[BaseAgent], agents),
        description="A workflow that iteratively plans and refines a trip to meet constraints"
    )





#############################################################################################################################################

def create_museum_finder_agent() -> Agent:
    instruction = (
        """
        You are a museum expert. Find the best museum based on the user's query. Output only the museum's name.
        """
    )

    return Agent(
        name="museum_finger_agent",
        model=model,
        tools=[google_search],
        instruction=instruction,
        output_key="museum_result"
    )



def create_concert_finder_agent() -> Agent:
    instruction = (
        """
        You are an events guide. Finda a concert based on the user's query. Output only the concert name and artist.
        """
    )

    return Agent(
        name="concert_finder-agent",
        model=model,
        instruction=instruction,
        tools=[google_search],
        output_key="concert_result"
    )




def create_restaurant_finder_agent() -> Agent:
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
        output_key="restaurant_result"
    )



def create_parallel_research_agent(agents:list[Agent]) -> ParallelAgent:
    return ParallelAgent(
        name="parallel_research_agent",
        sub_agents=cast(list[BaseAgent], agents)
    )


def create_synthesis_agent() -> Agent:
    instrucion = (
        """
        You are a helpful assistant. Combine the following research results into a clear, bulleted list for the user.
        -   Museum: {museum_result}
        -   Concert: {concert_result}
        -   Restaurant: {restaurant_result}
        """
    )

    return Agent(
        name="syntesis_agent",
        model=model,
        instruction=instrucion
    )



def create_parallel_planner_agent(agents: list[Agent | ParallelAgent]) -> SequentialAgent:
    return SequentialAgent(
        name="parallel_planner_agent",
        sub_agents=cast(list[BaseAgent], agents),
        description="A workflow that finds multiple things in parllel and then summarizes the results."
    )



def create_router_agent_v3(options_str: str) -> Agent:
    instruction = (
        f"""
        You are a master request router. Your job is to analyze a user's query and decice which of the following agents or workflows is best suited to handle it.
        Do not answer the query yourself, only return the name of the most appropriate choice.

        Available Options: {options_str}
        Only return the single, most appropriate option's name and nothing else.
        """
    )

    return Agent(
        name="router_agent",
        model=model,
        instruction=instruction
    )