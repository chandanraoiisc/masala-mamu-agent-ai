from typing import Dict, Any, List, Callable, TypeVar, cast
from langgraph.graph import StateGraph
from models.state import AgentState
from agents.base_agent import BaseAgent
from agents.response_generator_agent import ResponseGeneratorAgent

T = TypeVar('T')


class WorkflowOrchestrator:
    """Orchestrates the workflow between agents using LangGraph"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.graph = StateGraph(AgentState)
        self._is_compiled = False

    def register_agent(self, agent: BaseAgent) -> None:
        self.agents[agent.name] = agent
        self.graph.add_node(agent.name, self._create_agent_function(agent))

    def _create_agent_function(self, agent: BaseAgent) -> Callable[[AgentState], Dict[str, Any]]:

        async def agent_function(state: AgentState) -> Dict[str, Any]:
            if not agent.validate_inputs(state):
                return {"error": f"Missing required inputs for {agent.name}"}

            try:
                state_updates = {"current_agent": agent.name}

                agent_updates = await agent.process(state)
                state_updates.update(agent_updates)
                completed = state.get("completed_agents", []).copy()
                completed.append(agent.name)
                state_updates["completed_agents"] = completed

                return state_updates
            except Exception as e:
                return {"error": f"Error in {agent.name}: {str(e)}"}

        return agent_function

    def _determine_next_agent(self, state: AgentState) -> str:
        required = state.get("required_agents", [])
        completed = state.get("completed_agents", [])

        for agent_name in required:
            if agent_name not in completed:
                return agent_name

        return "response_generator"

    def build_workflow(self) -> None:

        self.graph.add_node("router", self._router_function)

        response_generator_agent = ResponseGeneratorAgent(
            gpt_client=next(iter(self.agents.values())).gpt_client if self.agents else None)
        self.graph.add_node("response_generator", self._create_agent_function(response_generator_agent))


        self.graph.set_entry_point("router")

        # Add conditional edge from router to agents
        self.graph.add_conditional_edges(
            "router",
            lambda state: self._determine_next_agent(state),
            {agent_name: agent_name for agent_name in self.agents.keys()} |
            {"response_generator": "response_generator"}
        )

        for agent_name in self.agents.keys():
            self.graph.add_edge(agent_name, "router")

        self._is_compiled = True

    async def _router_function(self, state: AgentState) -> Dict[str, Any]:
        """Router function that determines the execution flow"""
        # If we have a direct response from an agent, go straight to response generator
        if any(key.endswith("_direct_response") for key in state.keys()):
            return {"next": "response_generator"}

        # If we have an error, go straight to response generator
        if state.get("error"):
            return {"next": "response_generator"}

        # If all required agents are completed, go to response generator
        required = state.get("required_agents", [])
        completed = state.get("completed_agents", [])

        if all(agent in completed for agent in required):
            return {"next": "response_generator"}

        next_agent = self._determine_next_agent(state)
        return {"next": next_agent}

    async def _response_generator(self, state: AgentState) -> Dict[str, Any]:
        """Generate the final response to the user"""
        if state.get("error"):
            return {"response": f"Sorry, an error occurred: {state['error']}"}
            # Check for direct responses from agents
        for key in state:
            if key.endswith("_direct_response"):
                return {"response": state[key]}

        response_parts = []

        # Add recipe information if available
        if recipe_data := state.get("recipe_data"):
            # Handle both Pydantic model and dictionary
            try:
                name = recipe_data.name
                ingredients = recipe_data.ingredients
                instructions = recipe_data.instructions
            except AttributeError:
                # Fall back to dictionary access if not a Pydantic model
                name = recipe_data.get("name", "Unknown Recipe")
                ingredients = recipe_data.get("ingredients", [])
                instructions = recipe_data.get("instructions", [])

            response_parts.append(f"Here's a recipe for {name}:")
            response_parts.append("Ingredients:")
            for ingredient in ingredients:
                # Handle both dictionary and object access
                ingredient_name = ingredient.get("name", ingredient["name"]) if isinstance(ingredient,
                                                                                           dict) else ingredient.name
                ingredient_amount = ingredient.get("amount", ingredient["amount"]) if isinstance(ingredient,
                                                                                                 dict) else ingredient.amount
                response_parts.append(f"- {ingredient_amount} {ingredient_name}")

            response_parts.append("\nInstructions:")
            for i, step in enumerate(instructions, 1):
                response_parts.append(f"{i}. {step}")


        if shopping_data := state.get("shopping_data"):
            try:
                best_option = shopping_data.best_option
                total_cost = shopping_data.total_cost
                platform_comparisons = shopping_data.platform_comparisons
            except AttributeError:
                best_option = shopping_data.get("best_option", "")
                total_cost = shopping_data.get("total_cost", 0)
                platform_comparisons = shopping_data.get("platform_comparisons", {})

            if best_option and total_cost > 0:
                response_parts.append("\nShopping Information:")
                response_parts.append(f"Best place to buy: {best_option}")
                response_parts.append(f"Total cost: ₹{total_cost}")

                # Add delivery times if available
                for platform, details in platform_comparisons.items():
                    delivery_time = details.get("delivery_time", "") if isinstance(details, dict) else getattr(details,
                                                                                                               "delivery_time",
                                                                                                               "")
                    if delivery_time:
                        response_parts.append(f"{platform.capitalize()} delivery time: {delivery_time}")

        # Add health information if available
        if health_data := state.get("health_data"):
            try:
                calories = health_data.calories_per_serving
                macros = health_data.macros
                dietary_notes = health_data.dietary_notes
            except AttributeError:
                calories = health_data.get("calories_per_serving", 0)
                macros = health_data.get("macros", {})
                dietary_notes = health_data.get("dietary_notes", "")

            if calories > 0:
                response_parts.append("\nNutritional Information:")
                response_parts.append(f"Calories per serving: {calories}")
                response_parts.append("Macros:")
                for macro, value in macros.items():
                    response_parts.append(f"- {macro}: {value}g")
                if dietary_notes:
                    response_parts.append(f"\nDietary notes: {dietary_notes}")

        return {"response": "\n".join(response_parts)}
    def compile(self):
        """Compile the workflow graph"""
        if not self._is_compiled:
            self.build_workflow()
        return self.graph.compile()

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow with a given state"""
        if not self._is_compiled:
            self.build_workflow()

        app = self.compile()

        # Execute the workflow
        result = await app.ainvoke(state)
        return result