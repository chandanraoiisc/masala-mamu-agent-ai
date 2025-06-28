# 🧑‍🍳 Masala Mamu: AI Kitchen Assistant

Masala Mamu is an AI-powered kitchen assistant designed to help users find and compare product prices across various Indian e-commerce platforms. Built with cutting-edge AI technology and web scraping capabilities, it provides a seamless experience for price comparison with both text and voice interactions.

## ✨ Features

### 🛒 Multi-Platform Price Comparison
Search and compare prices for groceries and household items across major Indian e-commerce platforms:

- **Quick Commerce**: BigBasket, Blinkit, Zepto, Swiggy Instamart

### 🤖 Intelligent AI Agent
- Powered by **Google's Gemini 2.0 Flash** model
- **LangChain-based** agent architecture
- Natural language understanding for complex queries
- Context-aware price comparison orchestration

### 🌐 Real-time Web Scraping
- **Playwright-powered** web scraping
- Real-time data fetching from QuickCompare.in
- Robust error handling and retry mechanisms
- Dynamic content loading support

### 💬 Interactive User Interface
- **Streamlit-based** chat interface
- Conversational AI experience
- Clean, intuitive design
- Real-time response streaming

### 🎤 Voice Integration
- **Speech-to-Text** input support
- **Text-to-Speech** response output
- Hands-free interaction capability
- Multi-language voice support

### 📊 Smart Results Display
- Organized price comparison tables
- **Highlighted cheapest/most expensive** options
- Visual price difference indicators
- Availability status tracking

---

## 🏗 Architecture

The application follows a **modular, microservices-inspired architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                       │
│                   (chatbot_app.py)                         │
├─────────────────────────────────────────────────────────────┤
│                    Routing Layer                            │
│                   (route_agent.py)                          │
├─────────────────────────────────────────────────────────────┤
│                 AI Agent Layer                              │
│        (price_compare_agent.py + prompts)                  │
├─────────────────────────────────────────────────────────────┤
│                   Tool Layer                                │
│                (quickcompare_tool.py)                       │
├─────────────────────────────────────────────────────────────┤
│                 MCP Server Layer                            │
│              (quickcompare_mcp_server.py)                   │
├─────────────────────────────────────────────────────────────┤
│                Web Scraping Layer                           │
│                   (Playwright)                              │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

| Component | File | Responsibility |
|-----------|------|----------------|
| **Frontend** | `chatbot_app.py` | User interface, chat management, voice I/O integration |
| **Router** | `route_agent.py` | Query routing, agent selection, request orchestration |
| **AI Agent** | `price_compare_agent.py` | Core AI logic, query understanding, response generation |
| **Prompts** | `price_compare_agent_prompt.py` | LLM prompt templates and configurations |
| **Tool Bridge** | `quickcompare_tool.py` | LangChain-MCP server integration |
| **MCP Server** | `quickcompare_mcp_server.py` | Web scraping orchestration, data processing |

---

## 🔧 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 2GB free space

### Required Accounts & API Keys
- **Google AI Studio Account** (for Gemini API access)
- **Stable internet connection** (for real-time scraping)

### Browser Dependencies
- **Chromium/Chrome** (automatically installed with Playwright)

---

## 🚀 Installation

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/chandanraoiisc/masala-mamu-agent-ai.git
cd grocery-price-comparasion-mcp
```

### 2️⃣ Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
# On Windows: venv\Scripts\activate
```

### 3️⃣ Install Python Dependencies
```bash
pip install -r requirements.txt
```
or manually:
```bash
pip install langchain-google-genai langchain-core streamlit SpeechRecognition gtts mcp playwright
```

### 4️⃣ Install Playwright Browsers
```bash
playwright install
```

### 5️⃣ Set Google API Key
Masala Mamu requires a Google API key for Gemini LLM.
Obtain a key via Google AI Studio, then:

```bash
export GOOGLE_API_KEY="YOUR_API_KEY"  # Linux/macOS
# Windows (cmd): set GOOGLE_API_KEY="YOUR_API_KEY"
# Windows (PowerShell): $env:GOOGLE_API_KEY="YOUR_API_KEY"
```

### 6️⃣ Run the Streamlit App
Open a **new terminal**:
```bash
streamlit run chatbot_app.py
```

---

## ⚙️ Configuration

---

## 🎯 Usage

### Starting the Application
```bash
# Start the Streamlit app
streamlit run chatbot_app.py

# Access the app at: http://localhost:8501
```

### Basic Usage Examples

#### Text-based Queries
```
🧑‍🍳 User: "Compare prices for basmati rice 1kg"
🤖 Mamu: Comparing basmati rice prices across platforms...

🧑‍🍳 User: "Find cheapest cooking oil in 1 liter"
🤖 Mamu: Searching for cooking oil options...

🧑‍🍳 User: "What's the price difference for Maggi noodles?"
🤖 Mamu: Analyzing Maggi noodles pricing...
```

#### Voice Interaction
1. Click the **🎤 Voice Input** button
2. Speak your query clearly
3. Wait for processing and voice response

#### Advanced Queries
```
🧑‍🍳 "Compare organic products under ₹500"
🧑‍🍳 "Find dairy products with fastest delivery"
🧑‍🍳 "Show price trends for household cleaning items"
```

## Example Output

### QuickCompare Web Interface
The agent scrapes price data from QuickCompare.in, which aggregates prices from multiple platforms:

![QuickCompare Interface](./images/quickcompare-site.png)


### AI Agent Response
The Masala Mamu AI Assistant processes user queries and provides comprehensive price comparisons:

![QuickCompare Interface](./images/AgentResponse.png)


### Sample Console Output

```
QuickCompare Results for 'eggs' (showing top 3 results):

Brand: Farm Made
Product: Farm Made Free Range Brown Eggs-Veg Fed & Non Fertile
Offers:
  - Swiggy Instamart: ₹131 (6 pieces)
  - Blinkit: ₹131 (6 pieces)  
  - Zepto: ₹139.84 (1 pack - 6 pcs)
---

Brand: UPF
Product: UPF Healthy Brown Eggs - 6 pieces
Offers:
  - Blinkit: ₹83 (6 pieces)
  - Zepto: ₹86.93 (1 pack - 6 pcs)
  - Swiggy Instamart: ₹88 (6 pieces)
---

Brand: Eggoz
Product: Eggoz Nutrition Protein Rich White Eggs
Offers:
  - Blinkit: ₹74 (6 pieces)
  - Zepto: ₹80 (1 pack - 6 pcs)
  - BigBasket: ₹90.2 (6 pieces)
---

Best Deal Summary:
✅ Cheapest: Farm Made Free Range Brown Eggs at ₹131 (Swiggy Instamart & Blinkit)
💰 Most Expensive: Farm Made Free Range Brown Eggs at ₹139.84 (Zepto)
📊 Price Range: ₹74 - ₹139.84
🛒 Platforms Available: 4 (Blinkit, Zepto, Swiggy Instamart, BigBasket)
```





<div align="center">
  <p><strong>Made with ❤️ for Indian families</strong></p>
  <p>Helping you save money, one comparison at a time! 🛒💰</p>
</div>