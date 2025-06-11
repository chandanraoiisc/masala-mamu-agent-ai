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
- **Multiple LLM Support**: Works with OpenAI, GitHub models, Groq API, and is easily extensible to other providers

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API keys:
```bash
cp sample.env .env
# Edit .env with your actual API keys
```

3. Get API keys:
   - OpenAI API key from https://platform.openai.com/api-keys
   - GitHub token with appropriate permissions
   - Groq API key from https://console.groq.com/keys

## Usage

### Standalone Usage

#### Using the LLM Configuration (Recommended)

```python
from health_diet_agent import HealthDietAgent
from dotenv import load_dotenv

load_dotenv()

# Using OpenAI (environment variables will be used)
agent = HealthDietAgent(
    llm_provider="openai"
)

# Or with custom configuration
agent = HealthDietAgent(
    llm_provider="openai",
    llm_config={
        "model_name": "gpt-4-turbo-preview",
        "temperature": 0.2
    }
)

# Using GitHub model
agent = HealthDietAgent(
    llm_provider="github",
    llm_config={
        "model": "model-name" # Replace with actual model name
    }
)

# Using Groq API
agent = HealthDietAgent(
    llm_provider="groq",
    llm_config={
        "model": "llama3-8b-8192",
        "temperature": 0.2
    }
)

# Analyze a recipe
result = agent.analyze_nutrition("What are the macros for chicken tikka masala with rice?")
print(result["analysis"])
```

#### Legacy Usage (Still Supported)

```python
from health_diet_agent import HealthDietAgent
import os
from dotenv import load_dotenv

load_dotenv()

# Using OpenAI
agent = HealthDietAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model_provider="openai"
)

# Using GitHub
agent = HealthDietAgent(
    model_provider="github",
    github_token=os.getenv("GITHUB_TOKEN"),
    model="model-name" # Replace with actual model name
)
```

### Command Line Usage

You can run the agent directly from the command line:

```bash
# Using OpenAI (default)
python main.py

# Using GitHub model
python main.py --model-provider github

# Using Groq API
python main.py --model-provider groq --groq-model "llama3-8b-8192"
```

### Router Integration

```python
from router_integration import create_kitchen_assistant_with_nutrition

# Create router with nutrition agent using default configuration
router = create_kitchen_assistant_with_nutrition(
    llm_provider="openai"
)

# Or with custom configuration
router = create_kitchen_assistant_with_nutrition(
    llm_provider="github",
    llm_config={
        "model": "model-name", # Replace with actual model name
        "temperature": 0.1
    }
)

# Route queries
result = router.route_query("What are the macros for this recipe?")
if result["can_handle"]:
    print(result["response"])
```

## Architecture

### Core Components

- **HealthDietAgent**: Main agent class with LangChain integration
- **LLMConfig**: Platform-agnostic configuration for different LLM providers
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
