"""Tests for MealBot data models."""

import pytest

from mealbot.models import (
    GroceryItem,
    Ingredient,
    Macros,
    MealPlan,
    MealSlot,
    Recipe,
)


class TestMacros:
    """Tests for the Macros dataclass."""

    def test_macros_creation(self) -> None:
        """Macros can be created with all required fields."""
        macros = Macros(
            calories=500,
            protein_g=30.0,
            carbs_g=40.0,
            fat_g=20.0,
        )
        assert macros.calories == 500
        assert macros.protein_g == 30.0
        assert macros.carbs_g == 40.0
        assert macros.fat_g == 20.0


class TestIngredient:
    """Tests for the Ingredient dataclass."""

    def test_ingredient_creation(self) -> None:
        """Ingredient can be created with all required fields."""
        ingredient = Ingredient(
            name="tofu ferme",
            quantity=400.0,
            unit="g",
            category="proteines",
        )
        assert ingredient.name == "tofu ferme"
        assert ingredient.quantity == 400.0
        assert ingredient.unit == "g"
        assert ingredient.category == "proteines"


class TestRecipe:
    """Tests for the Recipe dataclass."""

    def test_recipe_creation_minimal(self) -> None:
        """Recipe can be created with only required fields."""
        recipe = Recipe(
            id="test-recipe",
            name="Test Recipe",
            servings=2,
            prep_time_min=15,
            ingredients=[],
            instructions=["Step 1", "Step 2"],
        )
        assert recipe.id == "test-recipe"
        assert recipe.name == "Test Recipe"
        assert recipe.servings == 2
        assert recipe.prep_time_min == 15
        assert recipe.ingredients == []
        assert recipe.instructions == ["Step 1", "Step 2"]
        # Check defaults
        assert recipe.tags == []
        assert recipe.macros is None
        assert recipe.season == []
        assert recipe.storage_days == 3
        assert recipe.reheatable is True

    def test_recipe_creation_full(self, sample_macros: Macros) -> None:
        """Recipe can be created with all fields."""
        ingredient = Ingredient(
            name="lentilles",
            quantity=200.0,
            unit="g",
            category="proteines",
        )
        recipe = Recipe(
            id="dal-lentilles",
            name="Dal de lentilles",
            servings=4,
            prep_time_min=30,
            ingredients=[ingredient],
            instructions=["Cuire les lentilles", "Ajouter les epices"],
            tags=["batch", "indien", "hiver"],
            macros=sample_macros,
            season=["automne", "hiver"],
            storage_days=5,
            reheatable=True,
        )
        assert recipe.id == "dal-lentilles"
        assert len(recipe.ingredients) == 1
        assert recipe.tags == ["batch", "indien", "hiver"]
        assert recipe.macros == sample_macros
        assert recipe.storage_days == 5


class TestMealSlot:
    """Tests for the MealSlot dataclass."""

    def test_meal_slot_creation(self) -> None:
        """MealSlot can be created with all fields."""
        slot = MealSlot(
            day="lundi",
            meal_type="lunch",
            recipe_id="curry-tofu",
            portions=1,
        )
        assert slot.day == "lundi"
        assert slot.meal_type == "lunch"
        assert slot.recipe_id == "curry-tofu"
        assert slot.portions == 1

    def test_meal_slot_default_portions(self) -> None:
        """MealSlot defaults to 1 portion."""
        slot = MealSlot(
            day="mardi",
            meal_type="diner",
            recipe_id="salade",
        )
        assert slot.portions == 1


class TestMealPlan:
    """Tests for the MealPlan dataclass."""

    def test_meal_plan_creation(self) -> None:
        """MealPlan can be created with slots."""
        slots = [
            MealSlot(day="lundi", meal_type="lunch", recipe_id="curry"),
            MealSlot(day="lundi", meal_type="diner", recipe_id="salade"),
        ]
        plan = MealPlan(
            week="2026-W06",
            slots=slots,
            prep_order=["curry", "salade"],
            total_prep_time_min=45,
        )
        assert plan.week == "2026-W06"
        assert len(plan.slots) == 2
        assert plan.prep_order == ["curry", "salade"]
        assert plan.total_prep_time_min == 45

    def test_meal_plan_defaults(self) -> None:
        """MealPlan has sensible defaults."""
        plan = MealPlan(week="2026-W07", slots=[])
        assert plan.prep_order == []
        assert plan.total_prep_time_min == 0


class TestGroceryItem:
    """Tests for the GroceryItem dataclass."""

    def test_grocery_item_creation_minimal(self) -> None:
        """GroceryItem can be created with only required fields."""
        item = GroceryItem(
            ingredient_name="tofu ferme",
            total_quantity=800.0,
            unit="g",
        )
        assert item.ingredient_name == "tofu ferme"
        assert item.total_quantity == 800.0
        assert item.unit == "g"
        assert item.coop_product_name is None
        assert item.coop_product_url is None
        assert item.coop_price is None

    def test_grocery_item_creation_with_coop(self) -> None:
        """GroceryItem can include Coop product information."""
        item = GroceryItem(
            ingredient_name="tofu ferme",
            total_quantity=800.0,
            unit="g",
            coop_product_name="Coop Naturaplan Tofu Bio ferme 2x200g",
            coop_product_url="https://www.coop.ch/tofu-bio",
            coop_price=4.95,
        )
        assert item.coop_product_name == "Coop Naturaplan Tofu Bio ferme 2x200g"
        assert item.coop_product_url == "https://www.coop.ch/tofu-bio"
        assert item.coop_price == 4.95
