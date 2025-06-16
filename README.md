# Masala Mamu AI Kitchen Assistant

This project implements an AI-powered kitchen assistant that combines several specialized agents:

1. **Price Comparison Agent** - Compares grocery prices across different platforms in India
2. **Nutrition Analysis Agent** - Analyzes recipes and ingredients for nutritional content
3. **Chatbot Interface** - Streamlit-based UI for interacting with the agents

## Features

### Price Comparison
- Compare grocery prices across major Indian e-commerce platforms
- Get price trends and best deals for products
- Find alternatives and substitutes for ingredients

### Nutrition Analysis
- Get detailed macronutrient breakdown for recipes and ingredients
- Track nutrition intake over time
- Visualize nutrition trends with interactive charts
- Generate nutrition reports for meals and recipes

### Interactive Dashboard
- Real-time nutrition tracking dashboard
- Customizable nutrition goals and targets
- Visual analytics for macro consumption trends
- Downloadable nutrition data in CSV format

## Setup and Installation

1. Clone the repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up the required API keys in the `.env` file
4. Run the application:
   ```
   streamlit run chatbot_app.py
   ```

## Nutrition Agent Standalone Usage

You can also run the nutrition agent as a standalone application:

```bash
cd nutrition-agent
python main.py --model-provider github  # Or 'openai' or 'groq'
```

### Nutrition Agent Commands

- `history` - View your nutrition inquiry history
- `trends` - See your macro consumption trends
- `dashboard` - Launch the interactive Streamlit visualization dashboard

### Interactive Dashboard

The nutrition dashboard can be accessed in two ways:

1. Through the main chatbot application by selecting "Nutrition Dashboard" in the sidebar
2. By running the nutrition agent with the `--interactive` flag:
   ```
   python main.py --interactive
   ```

## Project Structure

- **chatbot_app.py** - Main Streamlit application for the chatbot UI
- **route_agent.py** - Router for directing queries to appropriate specialized agents
- **nutrition_dashboard.py** - Integration module for the nutrition visualization dashboard
- **nutrition-agent/** - Nutrition analysis and tracking module
  - **health_diet_agent.py** - Core nutrition analysis agent
  - **streamlit_viz.py** - Interactive Streamlit visualization components
  - **db.py** - Database management for nutrition records
  - **visualize.py** - Legacy visualization with matplotlib
- **tools/** - Shared tools used by various agents
- **agent/** - LangGraph agent implementations

## Dependencies

- Streamlit
- LangChain/LangGraph
- Plotly
- Pandas
- SQLite
- Various LLM providers support (OpenAI, Groq, GitHub Copilot)
