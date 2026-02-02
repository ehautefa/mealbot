"""Grocery list aggregation from meal plans."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mealbot.models import Ingredient, MealPlan, Recipe


class IngredientCategory(Enum):
    """Categories for grouping grocery items."""

    LEGUMES = "legumes"
    FRUITS = "fruits"
    PROTEINES = "proteines"
    EPICERIE = "epicerie"
    FRAIS = "frais"
    SURGELES = "surgeles"
    BOISSONS = "boissons"
    AUTRE = "autre"


# Pantry staples that are typically already at home
PANTRY_STAPLES = {
    "sel",
    "poivre",
    "huile d'olive",
    "huile",
    "vinaigre",
    "sucre",
    "farine",
    "eau",
    "poivre noir",
    "sel fin",
    "gros sel",
}


# Mapping from ingredient category strings to IngredientCategory enum
CATEGORY_MAPPING = {
    "legumes": IngredientCategory.LEGUMES,
    "légumes": IngredientCategory.LEGUMES,
    "fruits": IngredientCategory.FRUITS,
    "proteines": IngredientCategory.PROTEINES,
    "protéines": IngredientCategory.PROTEINES,
    "viande": IngredientCategory.PROTEINES,
    "poisson": IngredientCategory.PROTEINES,
    "epicerie": IngredientCategory.EPICERIE,
    "épicerie": IngredientCategory.EPICERIE,
    "base": IngredientCategory.EPICERIE,
    "frais": IngredientCategory.FRAIS,
    "surgeles": IngredientCategory.SURGELES,
    "surgelés": IngredientCategory.SURGELES,
    "boissons": IngredientCategory.BOISSONS,
}


@dataclass
class GroceryListItem:
    """An item on the aggregated grocery list."""

    ingredient_name: str
    total_quantity: float
    unit: str
    category: IngredientCategory = IngredientCategory.AUTRE
    coop_product_name: str | None = None
    coop_product_url: str | None = None
    coop_price: float | None = None


@dataclass
class GroceryList:
    """Aggregated grocery list from a meal plan."""

    items: list[GroceryListItem] = field(default_factory=list)

    @property
    def total_items(self) -> int:
        """Return the total number of items."""
        return len(self.items)

    def by_category(self) -> dict[IngredientCategory, list[GroceryListItem]]:
        """Return items grouped by category."""
        result: dict[IngredientCategory, list[GroceryListItem]] = {}
        for item in self.items:
            if item.category not in result:
                result[item.category] = []
            result[item.category].append(item)
        return result


def _normalize_ingredient_name(name: str) -> str:
    """Normalize ingredient name for comparison."""
    return name.lower().strip()


def _is_pantry_staple(name: str) -> bool:
    """Check if an ingredient is a pantry staple."""
    normalized = _normalize_ingredient_name(name)
    for staple in PANTRY_STAPLES:
        if staple in normalized or normalized in staple:
            return True
    return False


def _get_category(category_str: str) -> IngredientCategory:
    """Map category string to IngredientCategory enum."""
    normalized = category_str.lower().strip()
    return CATEGORY_MAPPING.get(normalized, IngredientCategory.AUTRE)


def aggregate_ingredients(
    plan: MealPlan,
    recipes: dict[str, Recipe],
    exclude_pantry: bool = True,
) -> GroceryList:
    """Aggregate ingredients from a meal plan into a grocery list.

    Args:
        plan: The meal plan with slots
        recipes: Dictionary mapping recipe IDs to Recipe objects
        exclude_pantry: Whether to exclude pantry staples (default True)

    Returns:
        GroceryList with aggregated ingredients
    """
    # Track aggregated quantities by normalized ingredient name
    aggregated: dict[str, dict[str, Any]] = {}

    for slot in plan.slots:
        recipe = recipes.get(slot.recipe_id)
        if not recipe:
            continue

        # Calculate the portion multiplier
        # portions = how many portions we eat
        # recipe.servings = how many portions the recipe makes
        portion_multiplier = slot.portions / recipe.servings

        for ingredient in recipe.ingredients:
            normalized_name = _normalize_ingredient_name(ingredient.name)

            # Skip pantry staples if configured
            if exclude_pantry and _is_pantry_staple(ingredient.name):
                continue

            # Calculate quantity for this usage
            quantity = ingredient.quantity * portion_multiplier

            if normalized_name in aggregated:
                # Add to existing quantity (same unit assumed)
                aggregated[normalized_name]["quantity"] += quantity
            else:
                # New ingredient
                aggregated[normalized_name] = {
                    "name": ingredient.name,
                    "quantity": quantity,
                    "unit": ingredient.unit,
                    "category": _get_category(ingredient.category),
                }

    # Convert to GroceryListItems
    items = [
        GroceryListItem(
            ingredient_name=data["name"],
            total_quantity=data["quantity"],
            unit=data["unit"],
            category=data["category"],
        )
        for data in aggregated.values()
    ]

    # Sort by category then by name
    items.sort(key=lambda x: (x.category.value, x.ingredient_name.lower()))

    return GroceryList(items=items)
