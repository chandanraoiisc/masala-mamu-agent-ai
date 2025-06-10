"""
Router Integration Module for Health & Diet Agent

This module provides the necessary interfaces and utilities to integrate
the Health & Diet Agent with a LangChain router system.
"""

from typing import Dict, Any, List, Optional
from health_diet_agent import HealthDietAgent
import json


class NutritionAgentRouter:
    """Router interface for the Health & Diet Agent."""

    def __init__(self, agent: HealthDietAgent):
        self.agent = agent
        self.agent_info = agent.get_agent_info()

    def route_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route a query to the nutrition agent if it can handle it.

        Args:
            query: User query string
            context: Optional context from previous interactions

        Returns:
            Dict containing routing decision and response
        """
        can_handle = self.agent.can_handle_query(query)

        if not can_handle:
            return {
                "can_handle": False,
                "agent_name": self.agent_info["name"],
                "reason": "Query not related to nutrition or diet analysis"
            }

        # Set context if provided
        if context:
            context_str = self._format_context(context)
            self.agent.set_context(context_str)

        # Process the query
        result = self.agent.analyze_nutrition(query)

        return {
            "can_handle": True,
            "agent_name": self.agent_info["name"],
            "response": result["analysis"] if result["success"] else f"Error: {result['error']}",
            "success": result["success"],
            "conversation_history": self.agent.get_conversation_history()
        }

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for the agent."""
        formatted_parts = []

        if "previous_queries" in context:
            formatted_parts.append(f"Previous queries: {context['previous_queries']}")

        if "user_preferences" in context:
            formatted_parts.append(f"User preferences: {context['user_preferences']}")

        if "current_recipe" in context:
            formatted_parts.append(f"Current recipe context: {context['current_recipe']}")

        return " | ".join(formatted_parts)

    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities for router decision making."""
        return self.agent_info

    def reset_conversation(self):
        """Reset the agent's conversation memory."""
        self.agent.clear_memory()


class KitchenAssistantRouter:
    """
    Main router class for the kitchen assistant project.
    Manages multiple specialized agents including the nutrition agent.
    """

    def __init__(self):
        self.agents = {}
        self.conversation_history = []

    def register_agent(self, agent_router: NutritionAgentRouter):
        """Register an agent with the router."""
        agent_info = agent_router.get_capabilities()
        self.agents[agent_info["name"]] = agent_router
        print(f"Registered agent: {agent_info['name']}")

    def route_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route a query to the appropriate agent.

        Args:
            query: User query
            context: Optional context from previous interactions

        Returns:
            Response from the selected agent
        """
        # Try each agent to see if it can handle the query
        for agent_name, agent_router in self.agents.items():
            result = agent_router.route_query(query, context)

            if result["can_handle"]:
                # Update conversation history
                self.conversation_history.append({
                    "query": query,
                    "agent": agent_name,
                    "response": result["response"],
                    "success": result["success"]
                })

                return result

        # No agent can handle the query
        return {
            "can_handle": False,
            "agent_name": None,
            "response": "I'm sorry, I don't know how to help with that query. I can assist with nutrition analysis, recipe breakdowns, and ingredient macro information.",
            "success": False
        }

    def get_conversation_summary(self) -> List[Dict[str, Any]]:
        """Get a summary of the conversation history."""
        return self.conversation_history

    def clear_all_conversations(self):
        """Clear conversation history for all agents."""
        for agent_router in self.agents.values():
            agent_router.reset_conversation()
        self.conversation_history.clear()


# Example usage for router integration
def create_kitchen_assistant_with_nutrition(openai_api_key: str) -> KitchenAssistantRouter:
    """
    Create a kitchen assistant router with the nutrition agent registered.

    Args:
        openai_api_key: OpenAI API key

    Returns:
        Configured KitchenAssistantRouter instance
    """
    # Create the nutrition agent
    nutrition_agent = HealthDietAgent(
        openai_api_key=openai_api_key
    )

    # Create router interface for the agent
    nutrition_router = NutritionAgentRouter(nutrition_agent)

    # Create main router and register the nutrition agent
    kitchen_router = KitchenAssistantRouter()
    kitchen_router.register_agent(nutrition_router)

    return kitchen_router
