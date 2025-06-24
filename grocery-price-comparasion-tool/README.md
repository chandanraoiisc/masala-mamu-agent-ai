# Price Comparison Agent

A Python-based intelligent agent that helps users find and compare product prices across multiple online platforms in India. The agent uses web scraping to gather real-time price data from popular e-commerce and grocery delivery platforms.

## Features

- **Multi-platform Price Comparison**: Compare prices across Blinkit, Zepto, Swiggy Instamart
- **Intelligent Search**: Natural language product search with AI-powered query processing
- **Real-time Data**: Live price scraping from QuickCompare.in
- **Best Deal Identification**: Automatically highlights cheapest and most expensive options
- **Comprehensive Analysis**: Provides insights about price differences and platform availability

## Architecture

The system consists of three main components:

1. **QuickCompare Scraper** (`quickcompare_tool.py`): Web scraping tool using Playwright
2. **Agent Logic** (`price_compare_agent.py`): LangChain-based agent with tool calling capabilities
3. **System Prompts** (`price_compare_agent_prompt.py`): AI agent instructions and behavior

## Installation

### Prerequisites

- Python 3.8 or higher
- Google API key for Gemini model access

### Dependencies

```bash
pip install langchain-google-genai
pip install langchain-core
pip install langchain
pip install playwright
pip install asyncio
pip install dataclasses
pip install logging
```

### Playwright Setup

After installing Playwright, you need to install the browser binaries:

```bash
playwright install
```

## Configuration

### Environment Setup

Set your Google API key as an environment variable:

```bash
export GOOGLE_API_KEY="your-google-api-key-here"
```

## Example Output

```
QuickCompare Results for 'eggs' (showing top 3 results):

Brand: Fresho
Product: Farm Fresh Eggs 6 pieces
Offers:
  - BigBasket: ₹48 (6)
  - Blinkit: ₹52 (6)
  - Zepto: ₹45 (6)
---

Brand: Happy Hens
Product: Brown Eggs 12 pieces
Offers:
  - Swiggy Instamart: ₹85 (12)
  - JioMart: ₹88 (12)
  - BigBasket: ₹82 (12)
---
```

## License

This project is provided as-is for educational and personal use. Please respect the terms of service of the scraped websites.

## Disclaimer

This tool is for educational and personal use only. Users are responsible for complying with the terms of service of the websites being scraped. The authors are not responsible for any misuse of this tool.