"""Tests for grocery list aggregation."""

from __future__ import annotations

import pytest

from mealbot.models import Ingredient, Recipe, Macros, MealPlan, MealSlot, GroceryItem
from mealbot.grocery.aggregator import (
    aggregate_ingredients,
    GroceryList,
    PANTRY_STAPLES,
    IngredientCategory,
)


@pytest.fixture
def recipe_curry() -> Recipe:
    """Curry recipe with tofu and coconut milk."""
    return Recipe(
        id="curry-tofu",
        name="Curry tofu",
        servings=4,
        prep_time_min=30,
        ingredients=[
            Ingredient(name="tofu ferme", quantity=400, unit="g", category="proteines"),
            Ingredient(name="boisson coco", quantity=400, unit="ml", category="base"),
            Ingredient(name="courge butternut", quantity=500, unit="g", category="legumes"),
            Ingredient(name="huile d'olive", quantity=20, unit="ml", category="base"),
            Ingredient(name="sel", quantity=5, unit="g", category="base"),
        ],
        instructions=["Cook"],
    )


@pytest.fixture
def recipe_lentils() -> Recipe:
    """Lentil salad recipe."""
    return Recipe(
        id="salade-lentilles",
        name="Salade lentilles",
        servings=2,
        prep_time_min=25,
        ingredients=[
            Ingredient(name="lentilles vertes", quantity=200, unit="g", category="proteines"),
            Ingredient(name="carotte", quantity=150, unit="g", category="legumes"),
            Ingredient(name="huile d'olive", quantity=15, unit="ml", category="base"),
            Ingredient(name="sel", quantity=3, unit="g", category="base"),
        ],
        instructions=["Cook"],
    )


@pytest.fixture
def recipe_soup() -> Recipe:
    """Soup recipe with shared ingredients."""
    return Recipe(
        id="soupe",
        name="Soupe legumes",
        servings=4,
        prep_time_min=30,
        ingredients=[
            Ingredient(name="carotte", quantity=200, unit="g", category="legumes"),
            Ingredient(name="poireau", quantity=300, unit="g", category="legumes"),
            Ingredient(name="boisson coco", quantity=200, unit="ml", category="base"),
            Ingredient(name="sel", quantity=5, unit="g", category="base"),
        ],
        instructions=["Cook"],
    )


class TestAggregateIngredients:
    """Tests for ingredient aggregation."""

    def test_aggregate_combines_same_ingredient(
        self, recipe_curry: Recipe, recipe_soup: Recipe
    ) -> None:
        """Soup has 200g carotte for 4 servings, 1 portion = 50g."""
        recipes = [recipe_curry, recipe_soup]
        # Create meal plan that uses both recipes
        slots = [
            MealSlot(day="lundi", meal_type="lunch", recipe_id="curry-tofu", portions=1),
            MealSlot(day="lundi", meal_type="diner", recipe_id="soupe", portions=1),
        ]
        plan = MealPlan(week="2026-W06", slots=slots)

        grocery_list = aggregate_ingredients(plan, {r.id: r for r in recipes})

        # Find carotte in the list - only soup has carotte
        carotte = next(
            (item for item in grocery_list.items if "carotte" in item.ingredient_name.lower()),
            None,
        )
        assert carotte is not None
        # Soup: 200g carotte / 4 servings * 1 portion = 50g
        assert carotte.total_quantity == 50

    def test_aggregate_combines_same_ingredient_multiple_recipes(
        self, recipe_lentils: Recipe, recipe_soup: Recipe
    ) -> None:
        """Lentils: 150g/2 servings, soup: 200g/4 servings → combined per portion."""
        recipes = [recipe_lentils, recipe_soup]
        slots = [
            MealSlot(day="lundi", meal_type="lunch", recipe_id="salade-lentilles", portions=1),
            MealSlot(day="lundi", meal_type="diner", recipe_id="soupe", portions=1),
        ]
        plan = MealPlan(week="2026-W06", slots=slots)

        grocery_list = aggregate_ingredients(plan, {r.id: r for r in recipes})

        carotte = next(
            (item for item in grocery_list.items if "carotte" in item.ingredient_name.lower()),
            None,
        )
        assert carotte is not None
        # Lentils: 150g / 2 servings * 1 = 75g
        # Soup: 200g / 4 servings * 1 = 50g
        # Total: 125g
        assert carotte.total_quantity == 125

    def test_aggregate_handles_unit_conversion(
        self, recipe_curry: Recipe, recipe_soup: Recipe
    ) -> None:
        """Curry: 400ml/4, soup: 200ml/4 → combined per portion."""
        recipes = [recipe_curry, recipe_soup]
        slots = [
            MealSlot(day="lundi", meal_type="lunch", recipe_id="curry-tofu", portions=1),
            MealSlot(day="lundi", meal_type="diner", recipe_id="soupe", portions=1),
        ]
        plan = MealPlan(week="2026-W06", slots=slots)

        grocery_list = aggregate_ingredients(plan, {r.id: r for r in recipes})

        coco = next(
            (item for item in grocery_list.items if "coco" in item.ingredient_name.lower()),
            None,
        )
        assert coco is not None
        # Curry: 400ml / 4 servings * 1 = 100ml
        # Soup: 200ml / 4 servings * 1 = 50ml
        # Total: 150ml
        assert coco.total_quantity == 150
        assert coco.unit == "ml"

    def test_aggregate_excludes_pantry_staples(
        self, recipe_curry: Recipe
    ) -> None:
        """Sel, poivre, huile d'olive ne sont pas sur la liste par defaut."""
        slots = [
            MealSlot(day="lundi", meal_type="lunch", recipe_id="curry-tofu", portions=1),
        ]
        plan = MealPlan(week="2026-W06", slots=slots)

        grocery_list = aggregate_ingredients(
            plan,
            {"curry-tofu": recipe_curry},
            exclude_pantry=True,
        )

        ingredient_names = [item.ingredient_name.lower() for item in grocery_list.items]

        # Pantry staples should be excluded
        assert not any("sel" in name for name in ingredient_names)
        assert not any("huile d'olive" in name for name in ingredient_names)

        # Regular ingredients should be present
        assert any("tofu" in name for name in ingredient_names)
        assert any("courge" in name for name in ingredient_names)

    def test_aggregate_includes_pantry_when_disabled(
        self, recipe_curry: Recipe
    ) -> None:
        """Pantry staples are included when exclude_pantry=False."""
        slots = [
            MealSlot(day="lundi", meal_type="lunch", recipe_id="curry-tofu", portions=1),
        ]
        plan = MealPlan(week="2026-W06", slots=slots)

        grocery_list = aggregate_ingredients(
            plan,
            {"curry-tofu": recipe_curry},
            exclude_pantry=False,
        )

        ingredient_names = [item.ingredient_name.lower() for item in grocery_list.items]

        # Pantry staples should be included
        assert any("sel" in name for name in ingredient_names)
        assert any("huile" in name for name in ingredient_names)

    def test_aggregate_groups_by_category(
        self, recipe_curry: Recipe, recipe_lentils: Recipe
    ) -> None:
        """La liste est groupee: legumes, proteines, epicerie seche, frais..."""
        recipes = [recipe_curry, recipe_lentils]
        slots = [
            MealSlot(day="lundi", meal_type="lunch", recipe_id="curry-tofu", portions=1),
            MealSlot(day="mardi", meal_type="lunch", recipe_id="salade-lentilles", portions=1),
        ]
        plan = MealPlan(week="2026-W06", slots=slots)

        grocery_list = aggregate_ingredients(plan, {r.id: r for r in recipes})

        # Check items are categorized
        categories_found = set()
        for item in grocery_list.items:
            if item.category:
                categories_found.add(item.category)

        # Should have multiple categories
        assert len(categories_found) >= 2

    def test_aggregate_handles_portions(
        self, recipe_curry: Recipe
    ) -> None:
        """Quantities are multiplied by portions."""
        slots = [
            MealSlot(day="lundi", meal_type="lunch", recipe_id="curry-tofu", portions=2),
        ]
        plan = MealPlan(week="2026-W06", slots=slots)

        grocery_list = aggregate_ingredients(
            plan,
            {"curry-tofu": recipe_curry},
            exclude_pantry=True,
        )

        tofu = next(
            (item for item in grocery_list.items if "tofu" in item.ingredient_name.lower()),
            None,
        )
        assert tofu is not None
        # Base recipe has 400g for 4 servings, 2 portions = 200g
        # Wait, portions means how many times we eat it, so 2 portions = 2 * (400/4) = 200g
        # Actually, let me reconsider: portions in MealSlot means how many portions we eat
        # The recipe serves 4, so 1 portion = 400/4 = 100g tofu
        # 2 portions = 200g tofu
        assert tofu.total_quantity == 200  # 2 portions * (400g / 4 servings)

    def test_aggregate_multiple_uses_same_recipe(
        self, recipe_curry: Recipe
    ) -> None:
        """Using same recipe multiple times aggregates correctly."""
        slots = [
            MealSlot(day="lundi", meal_type="lunch", recipe_id="curry-tofu", portions=1),
            MealSlot(day="mardi", meal_type="lunch", recipe_id="curry-tofu", portions=1),
            MealSlot(day="mercredi", meal_type="diner", recipe_id="curry-tofu", portions=1),
        ]
        plan = MealPlan(week="2026-W06", slots=slots)

        grocery_list = aggregate_ingredients(
            plan,
            {"curry-tofu": recipe_curry},
            exclude_pantry=True,
        )

        tofu = next(
            (item for item in grocery_list.items if "tofu" in item.ingredient_name.lower()),
            None,
        )
        assert tofu is not None
        # 3 uses * 1 portion each * (400g / 4 servings) = 300g
        assert tofu.total_quantity == 300


class TestGroceryList:
    """Tests for GroceryList structure."""

    def test_grocery_list_total_items(
        self, recipe_curry: Recipe, recipe_lentils: Recipe
    ) -> None:
        """GroceryList tracks total number of items."""
        recipes = [recipe_curry, recipe_lentils]
        slots = [
            MealSlot(day="lundi", meal_type="lunch", recipe_id="curry-tofu", portions=1),
            MealSlot(day="mardi", meal_type="lunch", recipe_id="salade-lentilles", portions=1),
        ]
        plan = MealPlan(week="2026-W06", slots=slots)

        grocery_list = aggregate_ingredients(
            plan,
            {r.id: r for r in recipes},
            exclude_pantry=True,
        )

        assert grocery_list.total_items > 0
        assert grocery_list.total_items == len(grocery_list.items)

    def test_grocery_list_by_category(
        self, recipe_curry: Recipe
    ) -> None:
        """GroceryList can return items grouped by category."""
        slots = [
            MealSlot(day="lundi", meal_type="lunch", recipe_id="curry-tofu", portions=1),
        ]
        plan = MealPlan(week="2026-W06", slots=slots)

        grocery_list = aggregate_ingredients(
            plan,
            {"curry-tofu": recipe_curry},
            exclude_pantry=True,
        )

        by_category = grocery_list.by_category()

        assert isinstance(by_category, dict)
        # Should have legumes (courge) and proteines (tofu)
        assert len(by_category) >= 2
