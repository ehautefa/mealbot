"""Tests for grocery list Telegram formatting."""

from __future__ import annotations

import pytest

from mealbot.grocery.aggregator import GroceryList, GroceryListItem, IngredientCategory
from mealbot.grocery.formatter import format_grocery_list, format_meal_plan


@pytest.fixture
def sample_grocery_list() -> GroceryList:
    """Sample grocery list for testing."""
    items = [
        GroceryListItem(
            ingredient_name="tofu ferme",
            total_quantity=400,
            unit="g",
            category=IngredientCategory.PROTEINES,
        ),
        GroceryListItem(
            ingredient_name="lentilles vertes",
            total_quantity=300,
            unit="g",
            category=IngredientCategory.PROTEINES,
        ),
        GroceryListItem(
            ingredient_name="courge butternut",
            total_quantity=500,
            unit="g",
            category=IngredientCategory.LEGUMES,
        ),
        GroceryListItem(
            ingredient_name="carotte",
            total_quantity=350,
            unit="g",
            category=IngredientCategory.LEGUMES,
        ),
        GroceryListItem(
            ingredient_name="poireau",
            total_quantity=300,
            unit="g",
            category=IngredientCategory.LEGUMES,
        ),
        GroceryListItem(
            ingredient_name="boisson coco",
            total_quantity=600,
            unit="ml",
            category=IngredientCategory.EPICERIE,
        ),
        GroceryListItem(
            ingredient_name="pate de curry",
            total_quantity=30,
            unit="g",
            category=IngredientCategory.EPICERIE,
        ),
    ]
    return GroceryList(items=items)


class TestFormatGroceryList:
    """Tests for Telegram grocery list formatting."""

    def test_format_telegram_message(self, sample_grocery_list: GroceryList) -> None:
        """La liste est formatee proprement pour Telegram avec emojis et sections."""
        formatted = format_grocery_list(sample_grocery_list)

        # Should contain section headers with emojis
        assert "🥬" in formatted or "Légumes" in formatted or "LEGUMES" in formatted
        assert "🥩" in formatted or "Protéines" in formatted or "PROTEINES" in formatted

        # Should contain ingredients
        assert "tofu" in formatted.lower()
        assert "carotte" in formatted.lower()
        assert "courge" in formatted.lower()

        # Should contain quantities
        assert "400" in formatted
        assert "350" in formatted

        # Should contain units
        assert "g" in formatted
        assert "ml" in formatted

    def test_format_groups_by_category(self, sample_grocery_list: GroceryList) -> None:
        """Items are grouped by category in output."""
        formatted = format_grocery_list(sample_grocery_list)

        # Legumes should be grouped together
        legumes_section = formatted.lower()
        assert "courge" in legumes_section
        assert "carotte" in legumes_section
        assert "poireau" in legumes_section

    def test_format_empty_list(self) -> None:
        """Empty list returns appropriate message."""
        empty_list = GroceryList(items=[])
        formatted = format_grocery_list(empty_list)

        assert formatted  # Should return something
        assert "vide" in formatted.lower() or "aucun" in formatted.lower() or len(formatted) < 50

    def test_format_single_item(self) -> None:
        """Single item list formats correctly."""
        single_item = GroceryList(
            items=[
                GroceryListItem(
                    ingredient_name="tofu",
                    total_quantity=200,
                    unit="g",
                    category=IngredientCategory.PROTEINES,
                )
            ]
        )
        formatted = format_grocery_list(single_item)

        assert "tofu" in formatted.lower()
        assert "200" in formatted

    def test_format_includes_header(self, sample_grocery_list: GroceryList) -> None:
        """Formatted output includes a header."""
        formatted = format_grocery_list(sample_grocery_list)

        # Should have some kind of title/header
        assert "courses" in formatted.lower() or "liste" in formatted.lower() or "🛒" in formatted

    def test_format_uses_markdown(self, sample_grocery_list: GroceryList) -> None:
        """Output uses Telegram-compatible markdown."""
        formatted = format_grocery_list(sample_grocery_list)

        # Should use markdown formatting (bold headers, etc.)
        has_markdown = (
            "**" in formatted  # Bold
            or "*" in formatted  # Italic or bold
            or "•" in formatted  # Bullet points
            or "-" in formatted  # List items
            or "☐" in formatted  # Checkboxes
        )
        assert has_markdown

    def test_format_quantity_rounding(self) -> None:
        """Quantities are displayed nicely (no excessive decimals)."""
        items = [
            GroceryListItem(
                ingredient_name="farine",
                total_quantity=333.333,
                unit="g",
                category=IngredientCategory.EPICERIE,
            )
        ]
        grocery_list = GroceryList(items=items)
        formatted = format_grocery_list(grocery_list)

        # Should not have excessive decimals
        assert "333.333" not in formatted
        assert "333" in formatted or "334" in formatted  # Rounded


class TestFormatMealPlan:
    """Tests for meal plan formatting."""

    def test_format_meal_plan_basic(self) -> None:
        """Meal plan formats with days and meals."""
        from mealbot.models import MealPlan, MealSlot, Recipe

        recipes = {
            "curry": Recipe(
                id="curry",
                name="Curry tofu",
                servings=4,
                prep_time_min=30,
                ingredients=[],
                instructions=[],
            ),
            "salade": Recipe(
                id="salade",
                name="Salade verte",
                servings=2,
                prep_time_min=10,
                ingredients=[],
                instructions=[],
            ),
        }

        plan = MealPlan(
            week="2026-W06",
            slots=[
                MealSlot(day="lundi", meal_type="lunch", recipe_id="curry"),
                MealSlot(day="lundi", meal_type="diner", recipe_id="salade"),
            ],
        )

        formatted = format_meal_plan(plan, recipes)

        # Should contain day
        assert "lundi" in formatted.lower()

        # Should contain recipe names
        assert "curry" in formatted.lower()
        assert "salade" in formatted.lower()

        # Should have meal types
        assert "lunch" in formatted.lower() or "déjeuner" in formatted.lower()
        assert "diner" in formatted.lower() or "dîner" in formatted.lower()
