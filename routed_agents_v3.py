from google.adk.agents import Agent, SequentialAgent, ParallelAgent, BaseAgent, LoopAgent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search
from typing import cast


model = "gemini-2.5-flash"




# <-----  I.    AGENT DEFINITIONS FOR ITERATIVE WORKFLOW     ----->

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





# <-----  II.    AGENT DEFINITIONS FOR PARALLEL WORKFLOW     ----->

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