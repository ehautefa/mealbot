"""Tests for nutrition validation."""

from __future__ import annotations

import pytest

from mealbot.models import Macros, MealSlot, MealPlan, Recipe, Ingredient
from mealbot.planner.nutrition import (
    validate_daily_protein,
    validate_daily_carbs,
    is_high_carb_recipe,
    validate_meal_plan_nutrition,
    NutritionValidationResult,
    DAILY_PROTEIN_MIN_G,
    DAILY_CARBS_MAX_G,
    HIGH_CARB_THRESHOLD_G,
)


class TestProteinValidation:
    """Tests for protein target validation."""

    def test_meal_plan_meets_protein_target(self) -> None:
        """Le plan doit atteindre minimum 60g proteines/jour."""
        # 3 meals with 25g protein each = 75g total
        daily_macros = [
            Macros(calories=400, protein_g=25.0, carbs_g=30.0, fat_g=15.0),
            Macros(calories=500, protein_g=30.0, carbs_g=40.0, fat_g=20.0),
            Macros(calories=350, protein_g=20.0, carbs_g=25.0, fat_g=12.0),
        ]
        result = validate_daily_protein(daily_macros)

        assert result.is_valid is True
        assert result.total == 75.0
        assert result.target == DAILY_PROTEIN_MIN_G

    def test_meal_plan_fails_protein_target(self) -> None:
        """Un plan avec trop peu de proteines echoue."""
        # 3 meals with only 15g protein each = 45g total (below 60g target)
        daily_macros = [
            Macros(calories=400, protein_g=15.0, carbs_g=50.0, fat_g=15.0),
            Macros(calories=400, protein_g=15.0, carbs_g=50.0, fat_g=15.0),
            Macros(calories=400, protein_g=15.0, carbs_g=50.0, fat_g=15.0),
        ]
        result = validate_daily_protein(daily_macros)

        assert result.is_valid is False
        assert result.total == 45.0
        assert result.deficit == 15.0  # 60 - 45


class TestCarbValidation:
    """Tests for carb limit validation."""

    def test_meal_plan_limits_carbs(self) -> None:
        """Les glucides ne doivent pas depasser 150g/jour."""
        # 3 meals with 40g carbs each = 120g total (under 150g limit)
        daily_macros = [
            Macros(calories=400, protein_g=25.0, carbs_g=40.0, fat_g=15.0),
            Macros(calories=400, protein_g=25.0, carbs_g=40.0, fat_g=15.0),
            Macros(calories=400, protein_g=25.0, carbs_g=40.0, fat_g=15.0),
        ]
        result = validate_daily_carbs(daily_macros)

        assert result.is_valid is True
        assert result.total == 120.0
        assert result.target == DAILY_CARBS_MAX_G

    def test_meal_plan_exceeds_carbs(self) -> None:
        """Un plan avec trop de glucides echoue."""
        # 3 meals with 60g carbs each = 180g total (over 150g limit)
        daily_macros = [
            Macros(calories=500, protein_g=20.0, carbs_g=60.0, fat_g=20.0),
            Macros(calories=500, protein_g=20.0, carbs_g=60.0, fat_g=20.0),
            Macros(calories=500, protein_g=20.0, carbs_g=60.0, fat_g=20.0),
        ]
        result = validate_daily_carbs(daily_macros)

        assert result.is_valid is False
        assert result.total == 180.0
        assert result.excess == 30.0  # 180 - 150


class TestHighCarbRecipe:
    """Tests for high-carb recipe flagging."""

    def test_recipe_flags_high_carb(self) -> None:
        """Une recette avec >50g glucides/portion est flaggee."""
        high_carb_macros = Macros(
            calories=600,
            protein_g=15.0,
            carbs_g=55.0,  # Over 50g threshold
            fat_g=20.0,
        )
        recipe = Recipe(
            id="pasta",
            name="Pasta",
            servings=2,
            prep_time_min=20,
            ingredients=[],
            instructions=["Cook pasta"],
            macros=high_carb_macros,
        )

        assert is_high_carb_recipe(recipe) is True

    def test_recipe_not_flagged_under_threshold(self) -> None:
        """Une recette avec <=50g glucides/portion n'est pas flaggee."""
        normal_macros = Macros(
            calories=450,
            protein_g=25.0,
            carbs_g=35.0,  # Under 50g threshold
            fat_g=18.0,
        )
        recipe = Recipe(
            id="curry",
            name="Curry",
            servings=4,
            prep_time_min=30,
            ingredients=[],
            instructions=["Make curry"],
            macros=normal_macros,
        )

        assert is_high_carb_recipe(recipe) is False

    def test_recipe_without_macros_not_flagged(self) -> None:
        """Une recette sans macros n'est pas flaggee."""
        recipe = Recipe(
            id="simple",
            name="Simple dish",
            servings=2,
            prep_time_min=15,
            ingredients=[],
            instructions=["Cook"],
            macros=None,
        )

        assert is_high_carb_recipe(recipe) is False

    def test_recipe_at_threshold_not_flagged(self) -> None:
        """Une recette avec exactement 50g glucides n'est pas flaggee."""
        threshold_macros = Macros(
            calories=500,
            protein_g=20.0,
            carbs_g=50.0,  # Exactly at threshold
            fat_g=15.0,
        )
        recipe = Recipe(
            id="borderline",
            name="Borderline dish",
            servings=2,
            prep_time_min=20,
            ingredients=[],
            instructions=["Cook"],
            macros=threshold_macros,
        )

        assert is_high_carb_recipe(recipe) is False


class TestMealPlanValidation:
    """Tests for full meal plan nutrition validation."""

    def test_validate_meal_plan_all_valid(self) -> None:
        """Un plan equilibre passe toutes les validations."""
        recipes = {
            "breakfast": Recipe(
                id="breakfast",
                name="Chia pudding",
                servings=1,
                prep_time_min=5,
                ingredients=[],
                instructions=[],
                macros=Macros(calories=350, protein_g=15.0, carbs_g=30.0, fat_g=18.0),
            ),
            "lunch": Recipe(
                id="lunch",
                name="Buddha bowl",
                servings=1,
                prep_time_min=15,
                ingredients=[],
                instructions=[],
                macros=Macros(calories=550, protein_g=30.0, carbs_g=45.0, fat_g=22.0),
            ),
            "dinner": Recipe(
                id="dinner",
                name="Tofu stir-fry",
                servings=1,
                prep_time_min=20,
                ingredients=[],
                instructions=[],
                macros=Macros(calories=450, protein_g=25.0, carbs_g=35.0, fat_g=18.0),
            ),
        }

        slots = [
            MealSlot(day="lundi", meal_type="petit-dej", recipe_id="breakfast"),
            MealSlot(day="lundi", meal_type="lunch", recipe_id="lunch"),
            MealSlot(day="lundi", meal_type="diner", recipe_id="dinner"),
        ]

        plan = MealPlan(week="2026-W06", slots=slots)

        result = validate_meal_plan_nutrition(plan, recipes, day="lundi")

        # Total protein: 15 + 30 + 25 = 70g (>= 60g target)
        # Total carbs: 30 + 45 + 35 = 110g (<= 150g limit)
        assert result.protein_valid is True
        assert result.carbs_valid is True
        assert result.is_valid is True
