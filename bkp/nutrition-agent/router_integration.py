"""
Router Integration Module for Health & Diet Agent

This module provides the necessary interfaces and utilities to integrate
the Health & Diet Agent with a LangChain router system.
"""

from typing import Dict, Any, List, Optional, Literal
import os
from health_diet_agent import HealthDietAgent
from llm_config import create_llm_config
import json
from utils.logger import setup_logger


class NutritionAgentRouter:
    """Router interface for the Health & Diet Agent."""

    def __init__(
        self,
        agent: Optional[HealthDietAgent] = None,
        llm_provider: Literal["openai", "github", "groq"] = "openai",
        llm_config: Optional[Dict[str, Any]] = None,
    ):
        # Setup logger
        self.logger = setup_logger(__name__)
        if agent:
            self.logger.info("Using provided agent instance")
            self.agent = agent
        else:
            # Prepare config dict, ensuring no API keys
            config = llm_config or {}
            self.logger.info(f"Creating new agent instance with {llm_provider} provider")

            # Initialize the agent with the LLM configuration
            self.agent = HealthDietAgent(
                llm_provider=llm_provider,
                llm_config=config
            )

        self.agent_info = self.agent.get_agent_info()
        self.logger.debug(f"Agent info: {self.agent_info['name']}")

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
        self.logger.debug(f"Returning agent capabilities: {self.agent_info.get('name', 'unknown')}")
        return self.agent_info

    def reset_conversation(self):
        """Reset the agent's conversation memory."""
        self.logger.info("Resetting nutrition agent conversation memory")
        self.agent.clear_memory()


class KitchenAssistantRouter:
    """
    Main router class for the kitchen assistant project.
    Manages multiple specialized agents including the nutrition agent.
    """

    def __init__(self):
        # Setup logger
        self.logger = setup_logger(__name__)
        self.agents = {}
        self.conversation_history = []
        self.logger.info("KitchenAssistantRouter initialized")

    def register_agent(self, agent_router: NutritionAgentRouter):
        """Register an agent with the router."""
        agent_info = agent_router.get_capabilities()
        self.agents[agent_info["name"]] = agent_router
        self.logger.info(f"Registered agent: {agent_info['name']}")
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
        self.logger.info(f"Routing query to appropriate agent: '{query[:50]}...'")

        # Try each agent to see if it can handle the query
        for agent_name, agent_router in self.agents.items():
            self.logger.debug(f"Trying agent: {agent_name}")
            result = agent_router.route_query(query, context)

            if result["can_handle"]:
                self.logger.info(f"Query handled by agent: {agent_name}")
                # Update conversation history
                self.conversation_history.append({
                    "query": query,
                    "agent": agent_name,
                    "response": result["response"],
                    "success": result["success"]
                })

                return result

        # No agent can handle the query
        self.logger.warning("No agent could handle the query")
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
        self.logger.info("Clearing conversation history for all agents")
        for agent_router in self.agents.values():
            agent_router.reset_conversation()
        self.conversation_history.clear()


# Example usage for router integration
def create_kitchen_assistant_with_nutrition(
    llm_provider: Literal["openai", "github", "groq"] = "openai",
    llm_config: Optional[Dict[str, Any]] = None,
) -> KitchenAssistantRouter:
    """
    Create a kitchen assistant router with the nutrition agent registered.

    Args:
        llm_provider: LLM provider to use ('openai', 'github', or 'groq')
        llm_config: Configuration parameters for the LLM provider (NOT API keys)

    Returns:
        Configured KitchenAssistantRouter instance
    """
    # Setup logger for this function
    logger = setup_logger(__name__)
    # Prepare config dict, ensuring no API keys
    config = llm_config or {}
    logger.info(f"Creating kitchen assistant with {llm_provider} provider")

    # Remove any API keys from config
    for key in ["api_key", "openai_api_key", "github_token", "groq_api_key"]:
        if key in config:
            logger.warning(f"Removing API key {key} from config for security")
            del config[key]

    # Create the nutrition agent with the LLM configuration
    logger.info("Initializing Health Diet Agent")
    nutrition_agent = HealthDietAgent(
        llm_provider=llm_provider,
        llm_config=config
    )

    # Create router interface for the agent
    logger.info("Creating nutrition agent router")
    nutrition_router = NutritionAgentRouter(nutrition_agent)

    # Create main router and register the nutrition agent
    logger.info("Creating kitchen assistant router and registering nutrition agent")
    kitchen_router = KitchenAssistantRouter()
    kitchen_router.register_agent(nutrition_router)

    logger.info("Kitchen assistant with nutrition agent successfully created")
    return kitchen_router
