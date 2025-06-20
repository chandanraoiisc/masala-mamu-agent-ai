import asyncio

from agents.base_agent import BaseAgent
from agents.health_diet_agent.health_diet_agent import HealthDietAgent
from models.state import AgentState, HealthData
from typing import Dict, Any

class HealthAgent(BaseAgent):
    def __init__(self):
        self.agent = HealthDietAgent(enable_db=True)

    @property
    def name(self) -> str:
        return "health_agent"

    @property
    def required_input_keys(self) -> list[str]:
        return ["query"]

    async def process(self, state: AgentState) -> Dict[str, Any]:
        query = state.get("query", "")
        result = await asyncio.to_thread(self.agent.analyze_nutrition, query)

        if result["success"]:
            macros = result.get("macros", {})
            health_data = HealthData(
                calories_per_serving=macros.calories,
                macros={
                    "protein": macros.protein,
                    "carbs": macros.carbohydrates,
                    "fat": macros.fat
                },
                dietary_notes=result["analysis"]
            )
            return {"health_data": health_data}
        else:
            return {"error": result.get("error", "HealthAgent failed")}
