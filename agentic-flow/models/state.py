from typing import Dict, List, Optional, TypedDict, Any
from pydantic import BaseModel


class InventoryData(BaseModel):
    available: List[Dict[str, Any]]
    missing: List[Dict[str, Any]]


class RecipeData(BaseModel):
    name: str
    ingredients: List[Dict[str, Any]]
    missing_ingredients: List[Dict[str, Any]]
    instructions: List[str]
    cooking_time: str
    servings: int


class ShoppingData(BaseModel):
    platform_comparisons: Dict[str, Dict[str, Any]]
    best_option: str
    total_cost: float


class HealthData(BaseModel):
    calories_per_serving: int
    macros: Dict[str, float]
    dietary_notes: str


class AgentState(TypedDict, total=False):
    """State passed between agents in the workflow"""
    query: str
    parsed_intent: Dict[str, Any]
    inventory_data: Optional[InventoryData]
    recipe_data: Optional[RecipeData]
    shopping_data: Optional[ShoppingData]
    health_data: Optional[HealthData]
    required_agents: List[str]
    completed_agents: List[str]
    current_agent: str
    response: Optional[str]
    error: Optional[str]