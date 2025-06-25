# 🌶️ Masala Mamu: AI Kitchen Assistant

*An intelligent, multi-agent kitchen assistant that helps you manage recipes, inventory, shopping, and nutrition tracking with advanced AI capabilities.*

## 🎯 Project Overview

Masala Mamu is a comprehensive AI-powered kitchen management system built using modern agentic AI architecture. The system leverages multiple specialized agents that work together to provide personalized cooking assistance, inventory management, price comparison shopping, and nutritional analysis.

## 🏗️ Architecture

The project follows a sophisticated multi-agent architecture with the following key components:

### Frontend Applications
- **Streamlit Web App** (`chatbot_app.py`) - Primary user interface with chat, voice interaction, and nutrition dashboard
- **Nutrition Dashboard** (`nutrition_dashboard.py`) - Advanced analytics and visualization for nutrition tracking

### Backend API (`backend/`)
- **FastAPI Server** (`app.py`) - RESTful API endpoints for chat queries and bill processing
- **Agent Orchestration** - LangGraph-powered workflow management
- **Multi-Agent System** - Specialized agents for different kitchen tasks

## 🤖 AI Agents & Services

### 1. **Recipe Agent** (`agents/recipe_agent.py`)
- **Purpose**: Generates detailed recipes based on user requests and available ingredients
- **Features**:
  - HuggingFace LLM integration for recipe generation
  - Adaptive recipes based on inventory availability
  - Structured output with ingredients, instructions, cooking time, and servings
  - GitHub Models integration for enhanced recipe suggestions

### 2. **Inventory Agent** (`agents/inventory_agent.py`)
- **Purpose**: Manages kitchen inventory and tracks ingredient availability
- **Features**:
  - MongoDB integration for persistent storage
  - RAG (Retrieval Augmented Generation) for natural language inventory queries
  - Automatic ingredient comparison with recipes
  - CRUD operations via natural language
  - Missing ingredient detection

### 3. **Shopping Agent** (`agents/shopping_agent.py`)
- **Purpose**: Compares prices across multiple grocery delivery platforms
- **Features**:
  - Multi-platform price comparison (Blinkit, Zepto, Instamart)
  - Google API integration for real-time price data
  - Cost optimization recommendations
  - Delivery time comparison
  - Shopping list generation

### 4. **Health Agent** (`agents/health_agent.py`)
- **Purpose**: Provides nutritional analysis and dietary recommendations
- **Features**:
  - Comprehensive macro and micronutrient analysis
  - Calorie calculation per serving
  - Database storage of nutrition records
  - Dietary restriction accommodation
  - Health trend tracking and visualization

### 5. **Response Generator Agent** (`agents/response_generator_agent.py`)
- **Purpose**: Synthesizes information from all agents into coherent user responses
- **Features**:
  - Context-aware response generation
  - Intent-based information filtering
  - Structured output formatting
  - Multi-modal response support

## 🔧 Core Infrastructure

### Intent Parser (`router/parser.py`)
- **Function**: Analyzes user queries to determine required agents and execution flow
- **Technology**: Azure OpenAI with structured output schemas
- **Features**: Multi-intent recognition, entity extraction, agent flow optimization

### Workflow Orchestrator (`router/orchestrator.py`)
- **Function**: Manages agent execution flow using LangGraph
- **Features**: Conditional routing, state management, error handling, parallel execution

### GPT Client (`services/gpt_client.py`)
- **Function**: Centralized Azure OpenAI API integration
- **Features**: Structured output generation, temperature control, error handling

## 💾 Data Management

### State Management (`models/state.py`)
- **AgentState**: Central state container for workflow data
- **Data Models**: Pydantic models for Recipe, Inventory, Shopping, and Health data
- **Type Safety**: TypedDict implementation for robust data flow

### Database Integration
- **MongoDB**: Inventory storage and retrieval
- **SQLite**: Nutrition tracking and analytics
- **Vector Storage**: Enhanced search capabilities for inventory queries

## 🖥️ User Interface Features

### Chat Interface
- **Voice Input/Output**: Speech recognition and text-to-speech
- **Real-time Chat**: WebSocket-like streaming responses
- **Modern UI**: Gradient backgrounds, animations, and responsive design
- **Multi-modal**: Text, voice, and image input support

### Bill Processing
- **OCR Integration**: Automatic grocery bill parsing
- **Image Upload**: Support for receipt image processing
- **Inventory Auto-update**: Automatic ingredient addition from bills

### Nutrition Dashboard
- **Analytics**: Comprehensive nutrition tracking over time
- **Visualizations**: Interactive charts and trend analysis
- **User Profiles**: Personalized nutrition recommendations

## 🚀 Advanced Features

### 1. **Multi-Platform Integration**
- **APIs**: Google Search, Azure OpenAI, HuggingFace Models
- **Platforms**: Grocery delivery services integration
- **Cloud**: MongoDB Atlas for scalable data storage

### 2. **Natural Language Processing**
- **Intent Recognition**: Multi-layered query understanding
- **Entity Extraction**: Ingredient, quantity, and dietary restriction parsing
- **Context Awareness**: Conversation history and user preference tracking

### 3. **Price Intelligence**
- **Real-time Pricing**: Live data from multiple grocery platforms
- **Cost Optimization**: Intelligent shopping recommendations
- **Delivery Analysis**: Time and cost factor optimization

### 4. **Nutrition Science**
- **USDA Integration**: Comprehensive nutrition database
- **Macro Tracking**: Protein, carbohydrates, fat, and calorie analysis
- **Health Insights**: Personalized dietary recommendations

## 📁 Project Structure

```
Project/
├── chatbot_app.py              # Main Streamlit application
├── nutrition_dashboard.py      # Nutrition analytics interface
├── requirements.txt            # Python dependencies
├── backend/                    # Core API and agent logic
│   ├── app.py                 # FastAPI server
│   ├── config.py              # Configuration management
│   ├── cli.py                 # Command-line interface
│   ├── agents/                # AI agent implementations
│   │   ├── base_agent.py      # Abstract base class
│   │   ├── recipe_agent.py    # Recipe generation
│   │   ├── inventory_agent.py # Inventory management
│   │   ├── shopping_agent.py  # Price comparison
│   │   ├── health_agent.py    # Nutrition analysis
│   │   ├── response_generator_agent.py # Response synthesis
│   │   ├── health_diet_agent/ # Advanced nutrition module
│   │   ├── inventory_service/ # Database and RAG
│   │   ├── receipe_service/   # Recipe generation service
│   │   └── shopping_service/  # Price comparison service
│   ├── router/                # Request orchestration
│   │   ├── parser.py          # Intent parsing
│   │   └── orchestrator.py    # Workflow management
│   ├── models/                # Data models
│   │   └── state.py           # State management
│   └── services/              # External integrations
│       └── gpt_client.py      # Azure OpenAI client
├── bkp/                       # Backup and legacy code
│   ├── grocery-price-comparasion-mcp/
│   ├── grocery-price-comparasion-tool/
│   ├── image_processing_validation/
│   ├── inventory_db/
│   └── nutrition-agent/
├── images/                    # Sample images and outputs
└── report/                    # Project documentation
```

## 🛠️ Technology Stack

### Core Technologies
- **Python 3.12+**: Primary programming language
- **Streamlit**: Web application framework
- **FastAPI**: High-performance API framework
- **LangGraph**: Agent workflow orchestration
- **LangChain**: LLM application framework

### AI & ML
- **Azure OpenAI**: GPT-4 for natural language processing
- **HuggingFace Transformers**: Recipe generation models
- **GitHub Models**: Advanced AI model integration
- **OpenAI Structured Outputs**: Reliable data extraction

### Data & Storage
- **MongoDB Atlas**: Cloud-based document database
- **SQLite**: Local analytics database
- **Pydantic**: Data validation and serialization
- **Vector Storage**: Enhanced search capabilities

### External Integrations
- **Google APIs**: Search and price data
- **Speech Recognition**: Voice input processing
- **gTTS**: Text-to-speech conversion
- **OCR Libraries**: Bill and receipt processing

## 🚦 Getting Started

### Prerequisites
```bash
# Python 3.12 or higher
# Azure OpenAI API access
# MongoDB Atlas account (optional)
# Google API key (for shopping features)
```

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd Project

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the Streamlit app
streamlit run chatbot_app.py

# Or run the FastAPI backend
cd backend
uvicorn app:app --reload
```

### Configuration
Create a `Project/backend/.env` file with the following variables:
```env
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_key
```

## 📊 Use Cases

### 1. **Recipe Discovery**
- "Give me a recipe for chicken biryani"
- "What can I make with tomatoes, onions, and rice?"
- "Show me a healthy breakfast recipe"

### 2. **Inventory Management**
- "What ingredients do I have in my kitchen?"
- "I bought 2kg tomatoes and 1kg onions"
- "Do I have enough ingredients for pasta?"

### 3. **Shopping Optimization**
- "Where can I buy groceries cheapest for biryani?"
- "Compare prices for my shopping list"
- "Find the best deals on vegetables"

### 4. **Nutrition Tracking**
- "How many calories are in this recipe?"
- "Show me my nutrition trends this month"
- "Is this meal suitable for my diet?"

## 🔄 Workflow Examples

### Complete Recipe Workflow
```
User: "Give me a biryani recipe, check what I'm missing, and tell me where to buy ingredients cheapest"

Flow: Query → Intent Parser → Recipe Agent → Inventory Agent → Shopping Agent → Response Generator

Output: Complete recipe + missing ingredients + price comparison
```

### Nutrition Analysis Workflow
```
User: "How healthy is chicken curry? Show me the nutrition facts"

Flow: Query → Intent Parser → Recipe Agent → Health Agent → Response Generator

Output: Recipe + detailed nutrition analysis + dietary recommendations
```

## 🏆 Key Innovations

1. **Multi-Agent Architecture**: Specialized agents for different kitchen tasks
2. **LangGraph Integration**: Advanced workflow orchestration
3. **Real-time Price Comparison**: Live grocery price intelligence
4. **Voice-Enabled Interface**: Hands-free kitchen interaction
5. **Nutrition Intelligence**: Comprehensive dietary analysis
6. **Bill Processing**: Automatic inventory updates from receipts
7. **Personalized Recommendations**: User-specific cooking suggestions

## 🎯 Future Enhancements

- **Meal Planning**: Weekly meal planning and prep assistance
- **Smart Shopping Lists**: AI-generated shopping optimization
- **Recipe Scaling**: Automatic serving size adjustments
- **Dietary Compliance**: Advanced allergen and restriction management
- **Social Features**: Recipe sharing and community recommendations
- **IoT Integration**: Smart kitchen appliance connectivity

## 📝 License

This project is developed as part of the Deep Learning coursework at Indian Institute of Science (IISc).

---

*Built with ❤️ for smart cooking and healthy living*
