"""Data models for MealBot."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Macros:
    """Nutritional macros per portion."""

    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float


@dataclass
class Ingredient:
    """An ingredient with quantity and category."""

    name: str  # e.g., "tofu ferme"
    quantity: float  # e.g., 400
    unit: str  # e.g., "g"
    category: str  # e.g., "proteines", "legumes", "base"


@dataclass
class Recipe:
    """A recipe with ingredients, instructions, and metadata."""

    id: str
    name: str  # e.g., "Curry rouge tofu & courge"
    servings: int  # portions batch, e.g., 4
    prep_time_min: int  # e.g., 25
    ingredients: list[Ingredient]
    instructions: list[str]
    tags: list[str] = field(default_factory=list)  # e.g., ["batch", "curry", "automne"]
    macros: Macros | None = None
    season: list[str] = field(default_factory=list)  # e.g., ["automne", "hiver"]
    storage_days: int = 3
    reheatable: bool = True


@dataclass
class MealSlot:
    """A single meal slot in the weekly plan."""

    day: str  # e.g., "lundi"
    meal_type: str  # "petit-dej", "lunch", "diner"
    recipe_id: str
    portions: int = 1


@dataclass
class MealPlan:
    """A weekly meal plan."""

    week: str  # ISO week format, e.g., "2026-W06"
    slots: list[MealSlot]
    prep_order: list[str] = field(default_factory=list)  # Optimal prep order for Sunday
    total_prep_time_min: int = 0


@dataclass
class GroceryItem:
    """An item on the grocery list with optional Coop product match."""

    ingredient_name: str  # e.g., "tofu ferme"
    total_quantity: float  # Aggregated from all recipes, e.g., 800
    unit: str
    coop_product_name: str | None = None  # e.g., "Coop Naturaplan Tofu Bio ferme 2x200g"
    coop_product_url: str | None = None
    coop_price: float | None = None
