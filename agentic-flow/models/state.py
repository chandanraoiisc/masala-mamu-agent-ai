from datetime import datetime
from typing import Dict, List, Optional, TypedDict, Any
from pydantic import BaseModel,Field


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
    # platform: Dict[str, Dict[str, Any]]
    best_option: str
    total_cost: float


class HealthData(BaseModel):
    calories_per_serving: int
    macros: Dict[str, float]
    dietary_notes: str
    fiber: float = 0
    sugar: float = 0
    sodium: float = 0


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


class MacroNutrient(BaseModel):
    """Represents a macronutrient with its amount and unit."""
    calories: Optional[float] = Field(default=None, description="Calories per serving")
    protein: Optional[float] = Field(default=None, description="Protein in grams")
    carbohydrates: Optional[float] = Field(default=None, description="Carbohydrates in grams")
    fat: Optional[float] = Field(default=None, description="Fat in grams")
    fiber: Optional[float] = Field(default=None, description="Fiber in grams")
    sugar: Optional[float] = Field(default=None, description="Sugar in grams")
    sodium: Optional[float] = Field(default=None, description="Sodium in mg")
    sources: Optional[List[dict]] = Field(default=None, description="Sources of nutrition information")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in self.dict().items() if v is not None}


class Source(BaseModel):
    """Information about a source for nutrition data."""
    title: str = Field(description="Title or headline of the source")
    url: str = Field(description="URL of the source")
    snippet: Optional[str] = Field(default=None, description="Snippet text from the source")


class IngredientNutrition(BaseModel):
    """Nutrition information for a single ingredient."""
    ingredient: str = Field(description="Name of the ingredient")
    amount: str = Field(description="Amount of the ingredient (e.g., '1 cup', '200g')")
    macros: MacroNutrient = Field(description="Nutritional information")


class RecipeNutrition(BaseModel):
    """Complete nutrition analysis for a recipe."""
    recipe_name: str = Field(description="Name of the recipe/dish")
    servings: int = Field(default=1, description="Number of servings")
    total_macros: MacroNutrient = Field(description="Total nutritional information for entire recipe")
    per_serving_macros: MacroNutrient = Field(description="Nutritional information per serving")
    ingredients: List[IngredientNutrition] = Field(default=[], description="Individual ingredient nutrition breakdown")
    preparation_notes: Optional[str] = Field(default=None, description="Any notes about preparation affecting nutrition")


class NutritionQuery(BaseModel):
    """User query for nutrition analysis."""
    query_type: str = Field(description="Type of query: 'recipe' or 'ingredients'")
    content: str = Field(description="Recipe description or ingredient list")
    servings: Optional[int] = Field(default=1, description="Number of servings (if applicable)")
    include_individual_breakdown: bool = Field(default=False, description="Whether to include individual ingredient breakdown")


# Database-related models
class NutritionRecord(BaseModel):
    """A record of a nutrition inquiry stored in the database."""
    id: int = Field(description="Unique identifier for the nutrition record")
    query_text: str = Field(description="Original query text from the user")
    query_type: str = Field(description="Type of query: 'recipe' or 'ingredients'")
    timestamp: datetime = Field(description="Timestamp of when the inquiry was made")
    user_id: str = Field(default="anonymous", description="User identifier")
    recipe_name: Optional[str] = Field(default=None, description="Name of the recipe if applicable")
    servings: int = Field(default=1, description="Number of servings")
    macros: MacroNutrient = Field(description="Nutritional information")
    ingredients: Optional[List[IngredientNutrition]] = Field(default=None, description="Individual ingredient breakdown if available")


class MacroTrend(BaseModel):
    """Daily macro consumption trends."""
    date: str = Field(description="Date of the records (YYYY-MM-DD format)")
    total_calories: float = Field(default=0, description="Total calories for the day")
    total_protein: float = Field(default=0, description="Total protein for the day (g)")
    total_carbs: float = Field(default=0, description="Total carbohydrates for the day (g)")
    total_fat: float = Field(default=0, description="Total fat for the day (g)")
    record_count: int = Field(default=0, description="Number of nutrition records for the day")
