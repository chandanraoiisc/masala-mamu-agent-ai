# Health & Diet Agent for Kitchen Assistant

A LangChain-based health and diet agent that analyzes recipes and ingredients for nutritional information. This agent is designed to work as part of a larger kitchen assistant system with router-based architecture.

## Features

- **Recipe Nutrition Analysis**: Complete macro breakdown for entire recipes
- **Individual Ingredient Analysis**: Detailed nutrition for each ingredient
- **Per-Serving Calculations**: Automatically calculates nutrition per serving
- **Web Search Integration**: Uses DuckDuckGo Search for current, accurate nutrition data
- **Cooking Method Awareness**: Considers how cooking methods affect nutrition
- **Router Integration**: Designed to work with LangChain router nodes
- **Conversational Memory**: Maintains context across interactions

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API keys:
```bash
cp .env.example .env
# Edit .env with your actual API keys
```

3. Get API keys:
   - OpenAI API key from https://platform.openai.com/api-keys

## Usage

### Standalone Usage

```python
from health_diet_agent import HealthDietAgent
import os
from dotenv import load_dotenv

load_dotenv()

agent = HealthDietAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Analyze a recipe
result = agent.analyze_nutrition("What are the macros for chicken tikka masala with rice?")
print(result["analysis"])

# Analyze with individual breakdown
result = agent.analyze_nutrition("Give me individual breakdown for pasta carbonara ingredients")
print(result["analysis"])
```

### Router Integration

```python
from router_integration import create_kitchen_assistant_with_nutrition

# Create router with nutrition agent
router = create_kitchen_assistant_with_nutrition(
    openai_api_key="your_openai_key"
)

# Route queries
result = router.route_query("What are the macros for this recipe?")
if result["can_handle"]:
    print(result["response"])
```

## Architecture

### Core Components

- **HealthDietAgent**: Main agent class with LangChain integration
- **NutritionSearchTool**: Web search tools for nutrition data
- **Models**: Pydantic models for structured data
- **Router Integration**: Interface for multi-agent systems

### Data Models

- **MacroNutrient**: Calories, protein, carbs, fat, fiber, sugar, sodium
- **IngredientNutrition**: Individual ingredient with amounts and macros
- **RecipeNutrition**: Complete recipe analysis with per-serving breakdowns
- **NutritionQuery**: Parsed user query with metadata

## Integration with Kitchen Assistant

The agent is designed to work with a router-based kitchen assistant system:

1. **Router Registration**: Agents register their capabilities
2. **Query Routing**: Router determines which agent can handle each query
3. **Context Sharing**: Agents can share context and conversation history
4. **Unified Interface**: Consistent response format across all agents

### Router Methods

- `can_handle_query()`: Determines if agent can process a query
- `get_agent_info()`: Returns agent capabilities and keywords
- `set_context()`: Accepts context from other agents
- `get_conversation_history()`: Shares conversation state

## Example Queries

The agent can handle various types of nutrition queries:

- "What are the macros for chicken tikka masala?"
- "Analyze nutrition for 200g chicken breast, 1 cup rice, vegetables"
- "Give me individual breakdown for each ingredient in pasta carbonara"
- "How many calories in a serving of homemade pizza?"
- "What's the protein content of this smoothie recipe?"

## API Response Format

```json
{
  "success": true,
  "analysis": "Detailed nutrition analysis...",
  "query_info": {
    "query_type": "recipe",
    "servings": 4,
    "include_individual_breakdown": true
  }
}
```

## Testing

Run the test scripts:

```bash
# Test standalone agent
python main.py

# Test router integration
python test_router.py
```

## Dependencies

- langchain: LLM framework and agent orchestration
- langchain-openai: OpenAI integration
- langchain-community: Community tools including Tavily search
- tavily-python: Web search API
- pydantic: Data validation and models
- python-dotenv: Environment variable management

## Future Enhancements

- Integration with nutrition databases (USDA, etc.)
- Support for dietary restrictions and allergies
- Meal planning and nutrition goals
- Integration with grocery price comparison
- Recipe modification suggestions for better nutrition
