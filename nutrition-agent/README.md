# Health & Diet Agent for Kitchen Assistant

A LangChain-based health and diet agent that analyzes recipes and ingredients for nutritional information. This agent is designed to work as part of a larger kitchen assistant system with router-based architecture.

## Contributor's Note

As the developer of the nutrition-agent module, I (Brijgopal Bharadwaj) built what became a cornerstone of our kitchen assistant system. I wanted to create something that could accurately break down nutritional content of any recipe or ingredient, so I designed an LLM-based agent with real-world usefulness in mind.

The system searches the web for up-to-date nutrition data using DuckDuckGo and structures this information cleanly with Pydantic models. I added a SQLite database to store past queries, which opened up the possibility for users to track their nutritional habits over time—something I visualized using Matplotlib charts and a Streamlit dashboard.

One challenge I tackled was making the system flexible enough to work with different LLM providers (it now supports OpenAI, GitHub Copilot, and Groq). I'm particularly proud of how the agent considers cooking methods when calculating nutrition—roasting vegetables changes their nutritional profile compared to eating them raw, for example.

To ensure this component worked smoothly with our broader kitchen assistant, I created a router integration layer that lets it communicate with other agents in our system. With comprehensive error handling, logging, and a functional CLI, this module ended up being one of the most complete parts of our project.

## Features

- **Recipe Nutrition Analysis**: Complete macro breakdown for entire recipes
- **Individual Ingredient Analysis**: Detailed nutrition for each ingredient
- **Per-Serving Calculations**: Automatically calculates nutrition per serving
- **Web Search Integration**: Uses DuckDuckGo Search for current, accurate nutrition data
- **Cooking Method Awareness**: Considers how cooking methods affect nutrition
- **Database Storage**: Stores nutrition inquiries in SQLite database for historical tracking
- **Visualization**: Plot macro trends over time to track nutrition goals
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

```python
from health_diet_agent import HealthDietAgent
import os
from dotenv import load_dotenv

load_dotenv()

# Using OpenAI
agent = HealthDietAgent(llm_provider="openai")

# Using GitHub
agent = HealthDietAgent(llm_provider="github")

# With custom configuration
config = {"temperature": 0.2, "model_name": "gpt-4-turbo-preview"}
agent = HealthDietAgent(llm_provider="openai", llm_config=config)

# Get nutrition analysis
result = agent.analyze_nutrition("What are the macros in a chicken sandwich?")
macros = agent.extract_macros(result)

# The agent automatically saves the inquiry to the database for tracking
```

### Command Line Usage

You can run the agent directly from the command line:

```bash
# Using OpenAI (default)
python main.py

# Using GitHub model
python main.py --model-provider github

# Using Groq API
python main.py --model-provider groq

# Disable database storage
python main.py --no-db

# View nutrition history
python main.py --history

# Show macro trends for the past 30 days
python main.py --trends 30

# Delete a specific nutrition record
python main.py --delete 123
```

### Visualization

You can visualize your nutrition data using the dedicated visualization script:

```bash
# Generate and display all plots
python visualize.py

# Generate specific type of visualization
python visualize.py --type trends
python visualize.py --type distribution

# Analyze data from the past 60 days
python visualize.py --days 60

# Save plots to directory instead of displaying
python visualize.py --save ./nutrition_plots
```

### Router Integration Usage

You can use the agent as part of a multi-agent system with the router integration:

```python
from router_integration import create_kitchen_assistant_with_nutrition

# Create a kitchen assistant router with the nutrition agent
router = create_kitchen_assistant_with_nutrition(
    llm_provider="openai",
    llm_config={"temperature": 0.1, "model_name": "gpt-4-turbo-preview"}
)

# Route a query to the appropriate agent
result = router.route_query("What are the macros in a chicken sandwich?")

# Process the result
if result["success"]:
    print(f"Response: {result['response']}")
else:
    print(f"Error: {result['reason']}")
```

## Architecture

### Core Components

- **HealthDietAgent**: Main agent class with LangChain integration
- **LLMConfig**: Platform-agnostic configuration for different LLM providers
- **NutritionSearchTool**: Web search tools for nutrition data
- **Models**: Pydantic models for structured data
- **Database**: SQLite database for storing nutrition inquiries and results
- **Visualization**: Matplotlib-based visualization of nutrition trends
- **Router Integration**: Interface for multi-agent systems

### Data Models

- **MacroNutrient**: Calories, protein, carbs, fat, fiber, sugar, sodium
- **IngredientNutrition**: Individual ingredient with amounts and macros
- **RecipeNutrition**: Complete recipe analysis with per-serving breakdowns
- **NutritionQuery**: Parsed user query with metadata

### Router Components

- **NutritionAgentRouter**: Wrapper for the HealthDietAgent that handles routing logic
- **KitchenAssistantRouter**: Main router that manages multiple specialized agents
- **Agent Registration**: Dynamic system for adding agents to the router

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
- `clear_memory()`: Resets conversation history

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

## Router Response Format

```json
{
  "can_handle": true,
  "agent_name": "NutritionAgent",
  "response": "Detailed nutrition analysis...",
  "success": true,
  "conversation_history": [
    {"role": "system", "content": "Context information"},
    {"role": "user", "content": "User query"},
    {"role": "assistant", "content": "Agent response"}
  ]
}
```

## Testing

Run the test suite to verify functionality:

```bash
# Test all components with OpenAI provider
python tests.py --test all --provider openai

# Test just router integration with Groq provider
python tests.py --test router --provider groq

# Test specific components
python tests.py --test config --provider openai
python tests.py --test agent --provider openai
python tests.py --test comprehensive --provider openai
```

## Future Enhancements

- Integration with nutrition databases (USDA, etc.)
- Support for dietary restrictions and allergies
- Meal planning and nutrition goals
- Integration with grocery price comparison
- Recipe modification suggestions for better nutrition
- Additional specialized agents for the kitchen assistant router
