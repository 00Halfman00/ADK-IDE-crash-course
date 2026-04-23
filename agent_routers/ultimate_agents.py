from google.adk.agents import Agent, SequentialAgent, ParallelAgent, BaseAgent, LoopAgent
from google.adk.tools import ToolContext, google_search
from typing import cast


model = "gemini-2.5-flash"




# <-----  I.    AGENT DEFINITIONS FOR ITERATIVE WORKFLOW     ----->

COMPLETION_PHRASE = "The plan is feasible and meets all constraints."

#   DEFINE EXIT LOOP HELPER FUNCTION
def exit_loop(tool_context: ToolContext) -> object:
    """Call this function ONLY when the plan is approved, signaling the loop should end."""

    print(f" [Tool Call] exit_loop triggered by {tool_context.agent_name}")
    tool_context.actions.escalate = True
    return {}


#   DEFINE AGENT 1: PROPOSES INITIAL PLAN
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
        tools=[google_search],
        instruction=instruction,
        output_key="current_plan",
        description="Proposes an initial activity and restaurant for a trip."
    )


#   DEFINE AGENT 2 (IN LOOP): CRITIQUES THE PLAN
def create_critic_agent(name: str) -> Agent:
    instruction = (
        f"""
        You are a logistics expert. Your job is to critique a travel plan. The user has a strict constraint: total travel time must be short.
        Current Plan: {{current_plan}}
        Use your tools to check the travel time between the two locations.

        IF the travel time is over 45 minutes, provide a critique, like: 'This plan is inefficient. Find a restaurant closer to the activity.
        ELSE, respond with exact phrase: '{COMPLETION_PHRASE}'
        """
    )

    return Agent(
        name=name,
        model=model,
        tools=[google_search],
        instruction=instruction,
        output_key="criticism",
        description="Critiques a travel plan based on travel time constraints."
    )



#   DEFINE AGENT 3 (IN LOOP): REFINES THE PLAN OR EXITS
def create_refiner_agent() -> Agent:
    instruction = (
        f"""
        You are a trip planner, refining a plan based on criticism.
        Original request: {{session.query}}
        Critique: {{criticism}}
        
        1.  IF the critique is '{COMPLETION_PHRASE}', you MUST output the Current Plan exactly as it is: {{current_plan}}. Do not add any other text.
        2.  ELSE, use your tools to find a NEW activity and restaurant. Output only the names, like: 'Activity': Exploratorium, Restaurant: 'La Mar'.
        """
    )

    return Agent(
        name="refiner_agent",
        model=model,
        tools=[google_search],
        instruction=instruction,
        output_key="current_plan",
        description="Refines a travel plan based on criticism or confirms if it meets constraints."
    )

def create_judge_agent() -> Agent:
    instruction = (
        f"""
        You are a judge overseeing the refinement process. Your job is to ensure that the critique and refinement agents are doing their jobs correctly.
        Original request: {{session.query}}
        Current Plan: {{current_plan}}
        Critique: {{criticism}}

        
        1.  IF '{COMPLETION_PHRASE}' is in the Critique, you MUST call 'exit_loop' and output the following: {{current_plan}}.
        2.  IF the critique does not address the user's constraint (short travel time), respond with: 'The critique is not valid because it does not address the user's constraint.'
        3.  IF the refiner's new plan does not seem to address the critique, respond with: 'The refinement does not seem to address the critique.'
        """
    )

    return Agent(
        name="judge_agent",
        model=model,
        tools=[exit_loop],
        instruction=instruction,
        output_key="judgement",
        description="Oversees the refinement process, ensuring critiques are valid and refinements address them."
    )

#   DEFINE THE LOOP AGENT THAT ORCHESTRATES THE CRITIQUE-REFINE CYCLE
def create_refinement_loop_agent(agents: list[Agent]) -> LoopAgent:
    return LoopAgent(
        name="refinement_agent",
        sub_agents=cast(list[BaseAgent], agents),
        description="Orchestrates an iterative cycle of critiquing and refining a trip plan."
    )


#   DEFINE THE SEQUENTIAL AGENT THAT WILL MANAGE THE WORKFLOW
def create_iterative_planner_agent(agents: list[Agent | LoopAgent]) -> SequentialAgent:
    return SequentialAgent(
        name="iterative_planner_agent",
        sub_agents=cast(list[BaseAgent], agents),
        description="A workflow that iteratively plans and refines a trip to meet constraints"
    )





# <-----  II.    AGENT DEFINITIONS FOR PARALLEL WORKFLOW     ----->

#   DEFINE AGENT 1
def create_museum_finder_agent() -> Agent:
    instruction = (
        """
        You are a museum expert. Find the best museum based on the user's query. Output only the museum's name.
        For example, if the museum is at 'San Francisco Museum of Modern Art (SFMOMA)', you should output only: San Frncisco Museum of Modern Art (SFMOMA).
        """
    )

    return Agent(
        name="museum_finder_agent",
        model=model,
        tools=[google_search],
        instruction=instruction,
        output_key="museum_result",
        description="Finds the best museum based on the user's query."
    )


#   DEFINE AGENT 2
def create_concert_finder_agent() -> Agent:
    instruction = (
        """
        You are an events guide. Find a concert based on the user's query. Output only the concert name and artist.
        For example, if the concert is at 'San Frncisco Symphony at Davies Hall', you should output only: San Frncisco Symphony.
        """
    )

    return Agent(
        name="concert_finder_agent",
        model=model,
        instruction=instruction,
        tools=[google_search],
        output_key="concert_result",
        description="Finds a concert based on the user's query."
    )



#   DEFINE AGENT 3
def create_restaurant_finder_agent() -> Agent:
    instructions = (
        """
        You are an expert food critic. Your goal is to find the best restaurant based on a user's request.
        When you recommend a place, you must output *ONLY* the name of the establishment and nothing else.
        For example, if the best sushi is at 'Chi Tung', you should output only: Chi Tung
        """
    )

    return Agent(
        name="restaurant_agent",
        model=model,
        instruction=instructions,
        tools=[google_search],
        output_key="restaurant_result",
        description="Finds the best restaurant based on the user's query."
    )


#   DEFINE THE PARALLEL AGENT THAT WILL RUNT AGENT 1, AGENT 2, AND AGENT 3 CONCURRENTLY
def create_parallel_research_agent(agents:list[Agent]) -> ParallelAgent:
    return ParallelAgent(
        name="parallel_research_agent",
        sub_agents=cast(list[BaseAgent], agents),
        description="Runs multiple research tasks concurrently to find museums, concerts, and restaurants."
    )


#   DEFINE AGENT THAT WILL SYNTHESIZE THE WORKFLOW
def create_synthesis_agent() -> Agent:
    instruction = (
        """
        You are a formatter. Your ONLY job is to take the provided research results and put them into this EXACT format.
        CRITICAL RULES:
        1. DO NOT add any descriptions, adjectives, or history about the locations.
        2. DO NOT explain why these were chosen.
        3. If a result contains extra text, STRIP IT and keep only the name.
        4. No introductory or concluding remarks.
        
        Format:
        - Museum: {museum_result}
        - Concert: {concert_result}
        - Restaurant: {restaurant_result}
        """
    )

    return Agent(
        name="synthesis_agent",
        model=model,
        instruction=instruction,
        description="Extracts names and formats them into a clean list without any extra fluff."
    )


#   DEFINE THE SEQUENTIAL AGENT THAT WILL MANAGE THE WORKFLOW
def create_parallel_planner_agent(agents: list[Agent | ParallelAgent]) -> SequentialAgent:
    return SequentialAgent(
        name="parallel_planner_agent",
        sub_agents=cast(list[BaseAgent], agents),
        description="A workflow that finds multiple things in parllel and then summarizes the results."
    )



#   DEFINE THE BRAINS OF THE OPERATION: THE ROUTER AGENT
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
        instruction=instruction,
        description="Analyzes a user's query and routes it to the most appropriate agent or workflow."
    )