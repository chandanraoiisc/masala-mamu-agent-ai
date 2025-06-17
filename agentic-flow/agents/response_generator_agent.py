from typing import Dict, Any
from agents.base_agent import BaseAgent
from models.state import AgentState
from services.gpt_client import GPTClient


class ResponseGeneratorAgent(BaseAgent):
    """Agent for generating the final response to the user"""

    def __init__(self, gpt_client: GPTClient = None):
        self.gpt_client = gpt_client
        self.system_message = """
        You are a focused kitchen assistant that provides precise answers to user queries.
        Based on the information collected from various specialized agents, create a response
        that addresses ONLY what the user explicitly asked for.

        - Do not provide information that wasn't requested
        - Be concise and to the point
        - Format your response in a clear, structured way
        - If the user asks for a recipe, provide only the recipe
        - If the user asks where to buy ingredients, focus only on shopping information
        - If the user asks about nutritional information, provide only that
        - If the user asks for multiple pieces of information, provide only those specific items
        """

    @property
    def name(self) -> str:
        return "response_generator_agent"

    @property
    def required_input_keys(self) -> list[str]:
        return ["query", "parsed_intent"]

    async def process(self, state: AgentState) -> Dict[str, Any]:
        """
        Generate a comprehensive response based on all collected information

        Args:
            state: Current workflow state containing all agent outputs

        Returns:
            Dict with response key
        """
        original_query = state["query"]
        parsed_intent = state["parsed_intent"]

        # Determine what information the user actually requested
        primary_intent = parsed_intent.get("primary_intent", "")
        secondary_intents = parsed_intent.get("secondary_intents", [])

        # Collect only the requested information
        context_parts = []

        # Add recipe information only if requested
        if "recipe_generation" in [primary_intent] + secondary_intents:
            if recipe_data := state.get("recipe_data"):
                try:
                    context_parts.append(f"RECIPE: {recipe_data.name}")
                    context_parts.append("Ingredients:")
                    for ingredient in recipe_data.ingredients:
                        context_parts.append(f"- {ingredient['amount']} {ingredient['name']}")
                    context_parts.append("\nInstructions:")
                    for i, step in enumerate(recipe_data.instructions, 1):
                        context_parts.append(f"{i}. {step}")
                    context_parts.append(f"\nCooking time: {recipe_data.cooking_time}")
                    context_parts.append(f"Servings: {recipe_data.servings}")
                except AttributeError:
                    # Handle dictionary format
                    name = recipe_data.get('name', 'Unknown Recipe')
                    ingredients = recipe_data.get('ingredients', [])
                    instructions = recipe_data.get('instructions', [])
                    cooking_time = recipe_data.get('cooking_time', 'unknown')
                    servings = recipe_data.get('servings', 0)

                    context_parts.append(f"RECIPE: {name}")
                    context_parts.append("Ingredients:")
                    for ingredient in ingredients:
                        context_parts.append(f"- {ingredient.get('amount', '')} {ingredient.get('name', '')}")
                    context_parts.append("\nInstructions:")
                    for i, step in enumerate(instructions, 1):
                        context_parts.append(f"{i}. {step}")
                    context_parts.append(f"\nCooking time: {cooking_time}")
                    context_parts.append(f"Servings: {servings}")

        # Add inventory information only if requested
        if "inventory_check" in [primary_intent] + secondary_intents:
            if inventory_data := state.get("inventory_data"):
                try:
                    context_parts.append("\nINVENTORY:")
                    context_parts.append("Available ingredients:")
                    for item in inventory_data.available:
                        context_parts.append(f"- {item['name']}: {item['quantity']} {item['unit']}")
                    context_parts.append("\nMissing ingredients:")
                    for item in inventory_data.missing:
                        context_parts.append(f"- {item['name']}: {item['quantity']} {item['unit']}")
                except AttributeError:
                    # Handle dictionary format
                    available = inventory_data.get('available', [])
                    missing = inventory_data.get('missing', [])

                    context_parts.append("\nINVENTORY:")
                    context_parts.append("Available ingredients:")
                    for item in available:
                        context_parts.append(
                            f"- {item.get('name', '')}: {item.get('quantity', '')} {item.get('unit', '')}")
                    context_parts.append("\nMissing ingredients:")
                    for item in missing:
                        context_parts.append(
                            f"- {item.get('name', '')}: {item.get('quantity', '')} {item.get('unit', '')}")

        # Add shopping information only if requested
        if "shopping_comparison" in [primary_intent] + secondary_intents:
            if shopping_data := state.get("shopping_data"):
                try:
                    context_parts.append("\nSHOPPING:")
                    context_parts.append(f"Best place to buy: {shopping_data.best_option}")
                    context_parts.append(f"Total cost: ₹{shopping_data.total_cost}")
                    context_parts.append("\nPlatform comparison:")
                    for platform, details in shopping_data.platform_comparisons.items():
                        context_parts.append(
                            f"- {platform.capitalize()}: ₹{details.get('total', 0)}, Delivery: {details.get('delivery_time', 'unknown')}")
                except AttributeError:
                    # Handle dictionary format
                    best_option = shopping_data.get('best_option', '')
                    total_cost = shopping_data.get('total_cost', 0)
                    platform_comparisons = shopping_data.get('platform_comparisons', {})

                    context_parts.append("\nSHOPPING:")
                    context_parts.append(f"Best place to buy: {best_option}")
                    context_parts.append(f"Total cost: ₹{total_cost}")
                    context_parts.append("\nPlatform comparison:")
                    for platform, details in platform_comparisons.items():
                        if isinstance(details, dict):
                            context_parts.append(
                                f"- {platform.capitalize()}: ₹{details.get('total', 0)}, Delivery: {details.get('delivery_time', 'unknown')}")

        # Add health information only if requested
        if "health_advice" in [primary_intent] + secondary_intents:
            if health_data := state.get("health_data"):
                try:
                    context_parts.append("\nNUTRITIONAL INFORMATION:")
                    context_parts.append(f"Calories per serving: {health_data.calories_per_serving}")
                    context_parts.append("Macros:")
                    for macro, value in health_data.macros.items():
                        context_parts.append(f"- {macro}: {value}g")
                    context_parts.append(f"\nDietary notes: {health_data.dietary_notes}")
                except AttributeError:
                    # Handle dictionary format
                    calories = health_data.get('calories_per_serving', 0)
                    macros = health_data.get('macros', {})
                    dietary_notes = health_data.get('dietary_notes', '')

                    context_parts.append("\nNUTRITIONAL INFORMATION:")
                    context_parts.append(f"Calories per serving: {calories}")
                    context_parts.append("Macros:")
                    for macro, value in macros.items():
                        context_parts.append(f"- {macro}: {value}g")
                    context_parts.append(f"\nDietary notes: {dietary_notes}")

        context = "\n".join(context_parts)

        try:
            # Only attempt to use GPT if client is available
            if self.gpt_client:
                # Generate a comprehensive response using Azure OpenAI
                prompt = f"""
                Original user query: "{original_query}"

                User's primary intent: {primary_intent}
                User's secondary intents: {', '.join(secondary_intents)}

                Information available based on user's request:
                {context}

                Provide a response that addresses ONLY what the user explicitly asked for.
                Do not include information that wasn't requested.
                """

                response_text = await self.gpt_client.generate_completion(
                    prompt=prompt,
                    system_message=self.system_message
                )

                return {"response": response_text}
            else:
                raise ConnectionError("GPT client not available")

        except Exception as e:
            # Fallback to simple response if Azure OpenAI fails
            print(f"Azure OpenAI response generation failed: {str(e)}")

            # Create a simple response from the available data
            response_parts = []

            if recipe_data := state.get("recipe_data"):
                try:
                    response_parts.append(f"Here's a recipe for {recipe_data.name}:")
                    response_parts.append("Ingredients:")
                    for ingredient in recipe_data.ingredients:
                        response_parts.append(f"- {ingredient['amount']} {ingredient['name']}")
                    response_parts.append("\nInstructions:")
                    for i, step in enumerate(recipe_data.instructions, 1):
                        response_parts.append(f"{i}. {step}")
                except AttributeError:
                    # Handle dictionary format
                    pass

            if shopping_data := state.get("shopping_data"):
                try:
                    if shopping_data.best_option:
                        response_parts.append(
                            f"\nBest place to buy missing ingredients: {shopping_data.best_option} (₹{shopping_data.total_cost})")
                except AttributeError:
                    # Handle dictionary format
                    pass

            if health_data := state.get("health_data"):
                try:
                    response_parts.append(f"\nCalories per serving: {health_data.calories_per_serving}")
                except AttributeError:
                    # Handle dictionary format
                    pass

            return {"response": "\n".join(
                response_parts) or "I couldn't generate a response based on the available information."}
