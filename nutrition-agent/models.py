from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import json


class MacroNutrient(BaseModel):
    """Represents a macronutrient with its amount and unit."""
    calories: Optional[float] = Field(default=None, description="Calories per serving")
    protein: Optional[float] = Field(default=None, description="Protein in grams")
    carbohydrates: Optional[float] = Field(default=None, description="Carbohydrates in grams")
    fat: Optional[float] = Field(default=None, description="Fat in grams")
    fiber: Optional[float] = Field(default=None, description="Fiber in grams")
    sugar: Optional[float] = Field(default=None, description="Sugar in grams")
    sodium: Optional[float] = Field(default=None, description="Sodium in mg")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in self.dict().items() if v is not None}


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
