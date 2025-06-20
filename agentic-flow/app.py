import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import os
from agents.response_generator_agent import ResponseGeneratorAgent

from services.gpt_client import GPTClient
from router.parser import IntentParser
from router.orchestrator import WorkflowOrchestrator
from agents.inventory_agent import InventoryAgent
from agents.recipe_agent import RecipeAgent
from agents.shopping_agent import ShoppingAgent
from agents.health_agent import HealthAgent
from config import settings

app = FastAPI(title="Kitchen Assistant API")

# Initialize Azure OpenAI client
gpt_client = GPTClient(
    api_key=settings.AZURE_OPENAI_API_KEY,
    endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    deployment=settings.AZURE_OPENAI_DEPLOYMENT
)

# Initialize components
intent_parser = IntentParser(gpt_client=gpt_client)
orchestrator = WorkflowOrchestrator()

# Register agents
orchestrator.register_agent(InventoryAgent())
orchestrator.register_agent(RecipeAgent())
orchestrator.register_agent(ShoppingAgent(gpt_client=gpt_client))
orchestrator.register_agent(HealthAgent())
orchestrator.register_agent(ResponseGeneratorAgent(gpt_client=gpt_client))

# Build the workflow
orchestrator.build_workflow()


class QueryRequest(BaseModel):
    query: str


@app.post("/query", response_model=Dict[str, Any])
async def process_query(request: QueryRequest):
    """Process a user query through the kitchen assistant workflow"""
    try:
        # Parse the intent
        parsed_intent = await intent_parser.parse(request.query)

        # Initialize state with query and parsed intent
        initial_state = {
            "query": request.query,
            "parsed_intent": parsed_intent,
            "required_agents": parsed_intent.get("required_agents", []),
            "completed_agents": []
        }

        # Execute the workflow
        result = await orchestrator.execute(initial_state)

        if "error" in result and result["error"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Azure OpenAI connection
        test_response = await gpt_client.generate_completion(
            "Hello",
            "Respond with 'Azure OpenAI connection is healthy'"
        )
        return {
            "status": "healthy",
            "azure_openai": "connected",
            "test_response": test_response
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "azure_openai": "disconnected",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)