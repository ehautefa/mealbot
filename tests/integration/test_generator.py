"""Integration tests for meal plan generator with mocked Claude API."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mealbot.models import MealPlan, Recipe, Ingredient, Macros, MealSlot
from mealbot.planner.generator import MealPlanGenerator, GeneratorConstraints
from mealbot.planner.seasonal import SeasonalCategory


# Sample Claude API response fixture
SAMPLE_MEAL_PLAN_RESPONSE = {
    "recipes": [
        {
            "id": "chia-pudding",
            "name": "Chia pudding coco-mangue",
            "servings": 4,
            "prep_time_min": 10,
            "ingredients": [
                {"name": "graines de chia", "quantity": 60, "unit": "g", "category": "base"},
                {"name": "boisson coco", "quantity": 400, "unit": "ml", "category": "base"},
                {"name": "mangue", "quantity": 200, "unit": "g", "category": "fruits"},
            ],
            "instructions": [
                "Melanger les graines de chia avec le lait de coco",
                "Laisser reposer au frigo toute la nuit",
                "Servir avec la mangue coupee en des",
            ],
            "tags": ["batch", "petit-dej", "transportable"],
            "macros": {"calories": 280, "protein_g": 8, "carbs_g": 25, "fat_g": 18},
            "season": ["toute-saison"],
            "storage_days": 4,
            "reheatable": False,
        },
        {
            "id": "curry-tofu-courge",
            "name": "Curry rouge tofu & courge",
            "servings": 4,
            "prep_time_min": 35,
            "ingredients": [
                {"name": "tofu ferme", "quantity": 400, "unit": "g", "category": "proteines"},
                {"name": "courge butternut", "quantity": 500, "unit": "g", "category": "legumes"},
                {"name": "boisson coco", "quantity": 400, "unit": "ml", "category": "base"},
                {"name": "pate de curry rouge", "quantity": 30, "unit": "g", "category": "base"},
            ],
            "instructions": [
                "Couper le tofu en cubes et la courge en morceaux",
                "Faire revenir le tofu",
                "Ajouter la pate de curry, la courge et le lait de coco",
                "Mijoter 25 minutes",
            ],
            "tags": ["batch", "lunch", "diner"],
            "macros": {"calories": 420, "protein_g": 22, "carbs_g": 28, "fat_g": 26},
            "season": ["automne", "hiver"],
            "storage_days": 4,
            "reheatable": True,
        },
        {
            "id": "salade-lentilles",
            "name": "Salade de lentilles tiede",
            "servings": 2,
            "prep_time_min": 25,
            "ingredients": [
                {"name": "lentilles vertes", "quantity": 200, "unit": "g", "category": "proteines"},
                {"name": "carotte", "quantity": 150, "unit": "g", "category": "legumes"},
                {"name": "celeri-rave", "quantity": 100, "unit": "g", "category": "legumes"},
                {"name": "vinaigrette", "quantity": 30, "unit": "ml", "category": "base"},
            ],
            "instructions": [
                "Cuire les lentilles",
                "Raper les legumes",
                "Melanger et assaisonner",
            ],
            "tags": ["batch", "lunch", "rapide"],
            "macros": {"calories": 380, "protein_g": 20, "carbs_g": 45, "fat_g": 10},
            "season": ["hiver"],
            "storage_days": 3,
            "reheatable": True,
        },
        {
            "id": "soupe-poireau",
            "name": "Soupe poireau-pomme de terre",
            "servings": 4,
            "prep_time_min": 30,
            "ingredients": [
                {"name": "poireau", "quantity": 400, "unit": "g", "category": "legumes"},
                {"name": "pomme de terre", "quantity": 300, "unit": "g", "category": "legumes"},
                {"name": "bouillon de legumes", "quantity": 1000, "unit": "ml", "category": "base"},
            ],
            "instructions": [
                "Emincer les poireaux",
                "Couper les pommes de terre",
                "Cuire dans le bouillon et mixer",
            ],
            "tags": ["batch", "diner", "rapide-rechauffage"],
            "macros": {"calories": 180, "protein_g": 5, "carbs_g": 32, "fat_g": 4},
            "season": ["hiver"],
            "storage_days": 5,
            "reheatable": True,
        },
    ],
    "meal_plan": {
        "week": "2026-W06",
        "slots": [
            {"day": "lundi", "meal_type": "petit-dej", "recipe_id": "chia-pudding", "portions": 1},
            {"day": "lundi", "meal_type": "lunch", "recipe_id": "curry-tofu-courge", "portions": 1},
            {"day": "lundi", "meal_type": "diner", "recipe_id": "soupe-poireau", "portions": 1},
            {"day": "mardi", "meal_type": "petit-dej", "recipe_id": "chia-pudding", "portions": 1},
            {"day": "mardi", "meal_type": "lunch", "recipe_id": "salade-lentilles", "portions": 1},
            {"day": "mardi", "meal_type": "diner", "recipe_id": "curry-tofu-courge", "portions": 1},
            {"day": "mercredi", "meal_type": "petit-dej", "recipe_id": "chia-pudding", "portions": 1},
            {"day": "mercredi", "meal_type": "lunch", "recipe_id": "curry-tofu-courge", "portions": 1},
            {"day": "mercredi", "meal_type": "diner", "recipe_id": "soupe-poireau", "portions": 1},
            {"day": "jeudi", "meal_type": "petit-dej", "recipe_id": "chia-pudding", "portions": 1},
            {"day": "jeudi", "meal_type": "lunch", "recipe_id": "salade-lentilles", "portions": 1},
            {"day": "jeudi", "meal_type": "diner", "recipe_id": "curry-tofu-courge", "portions": 1},
            {"day": "vendredi", "meal_type": "petit-dej", "recipe_id": "chia-pudding", "portions": 1},
            {"day": "vendredi", "meal_type": "lunch", "recipe_id": "curry-tofu-courge", "portions": 1},
            {"day": "vendredi", "meal_type": "diner", "recipe_id": "soupe-poireau", "portions": 1},
            {"day": "samedi", "meal_type": "petit-dej", "recipe_id": "chia-pudding", "portions": 1},
            {"day": "samedi", "meal_type": "lunch", "recipe_id": "salade-lentilles", "portions": 1},
            {"day": "samedi", "meal_type": "diner", "recipe_id": "soupe-poireau", "portions": 1},
            {"day": "dimanche", "meal_type": "petit-dej", "recipe_id": "chia-pudding", "portions": 1},
            {"day": "dimanche", "meal_type": "lunch", "recipe_id": "curry-tofu-courge", "portions": 1},
            {"day": "dimanche", "meal_type": "diner", "recipe_id": "soupe-poireau", "portions": 1},
        ],
        "prep_order": ["chia-pudding", "curry-tofu-courge", "soupe-poireau", "salade-lentilles"],
        "total_prep_time_min": 100,
    },
}


@pytest.fixture
def mock_claude_response():
    """Mock Claude API response with valid meal plan."""
    return json.dumps(SAMPLE_MEAL_PLAN_RESPONSE)


@pytest.fixture
def mock_anthropic_client(mock_claude_response):
    """Mock Anthropic client."""
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=mock_claude_response)]
    mock_client.messages.create = MagicMock(return_value=mock_message)
    return mock_client


@pytest.fixture
def generator(mock_anthropic_client):
    """Generator with mocked client."""
    gen = MealPlanGenerator(api_key="test-key")
    gen._client = mock_anthropic_client
    return gen


@pytest.fixture
def default_constraints():
    """Default dietary constraints."""
    return GeneratorConstraints(
        exclude_ingredients=["lactose", "oeuf", "lait", "fromage", "creme"],
        max_meat_fish_per_week=1,
        min_protein_per_day=60,
        max_carbs_per_day=150,
        batch_cooking=True,
        portable_breakfast=True,
        quick_dinner_max_min=15,
    )


class TestGeneratorStructure:
    """Tests for meal plan structure validation."""

    def test_generate_plan_returns_valid_structure(
        self, generator: MealPlanGenerator, default_constraints: GeneratorConstraints
    ) -> None:
        """Le plan genere contient 7 jours x 3 repas."""
        result = generator.generate(week="2026-W06", month=2, constraints=default_constraints)

        assert result.meal_plan is not None
        assert result.meal_plan.week == "2026-W06"

        # Check 7 days x 3 meals = 21 slots
        assert len(result.meal_plan.slots) == 21

        # Verify all days are present
        days = {"lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"}
        plan_days = {slot.day for slot in result.meal_plan.slots}
        assert plan_days == days

        # Verify all meal types for each day
        for day in days:
            day_slots = [s for s in result.meal_plan.slots if s.day == day]
            meal_types = {s.meal_type for s in day_slots}
            assert meal_types == {"petit-dej", "lunch", "diner"}

    def test_generate_plan_returns_recipes(
        self, generator: MealPlanGenerator, default_constraints: GeneratorConstraints
    ) -> None:
        """Le plan inclut les recettes referencees."""
        result = generator.generate(week="2026-W06", month=2, constraints=default_constraints)

        assert len(result.recipes) > 0

        # All recipe_ids in slots should have corresponding recipes
        recipe_ids_in_plan = {slot.recipe_id for slot in result.meal_plan.slots}
        recipe_ids_available = {r.id for r in result.recipes}
        assert recipe_ids_in_plan.issubset(recipe_ids_available)


class TestGeneratorConstraints:
    """Tests for dietary constraint validation."""

    def test_generate_plan_respects_constraints(
        self, generator: MealPlanGenerator, default_constraints: GeneratorConstraints
    ) -> None:
        """Pas de lactose, pas d'oeufs, max 1 repas viande/poisson par semaine."""
        result = generator.generate(week="2026-W06", month=2, constraints=default_constraints)

        # Check no excluded ingredients in any recipe
        excluded = {"lactose", "oeuf", "lait", "fromage", "creme"}
        for recipe in result.recipes:
            for ingredient in recipe.ingredients:
                ingredient_lower = ingredient.name.lower()
                for exc in excluded:
                    assert exc not in ingredient_lower, (
                        f"Recipe {recipe.name} contains excluded ingredient: {ingredient.name}"
                    )

    def test_generate_plan_prompt_includes_constraints(
        self, generator: MealPlanGenerator, mock_anthropic_client, default_constraints: GeneratorConstraints
    ) -> None:
        """Le prompt envoyé à Claude inclut les contraintes."""
        generator.generate(week="2026-W06", month=2, constraints=default_constraints)

        # Verify the API was called
        mock_anthropic_client.messages.create.assert_called_once()

        # Get the prompt that was sent
        call_args = mock_anthropic_client.messages.create.call_args
        messages = call_args.kwargs.get("messages", [])
        assert len(messages) > 0

        prompt_text = messages[0]["content"]

        # Check constraints are in the prompt
        assert "lactose" in prompt_text.lower() or "sans lactose" in prompt_text.lower()
        assert "oeuf" in prompt_text.lower() or "sans oeuf" in prompt_text.lower()


class TestSeasonalIntegration:
    """Tests for seasonal ingredient integration."""

    def test_generate_plan_uses_seasonal_ingredients(
        self, generator: MealPlanGenerator, default_constraints: GeneratorConstraints
    ) -> None:
        """En fevrier, le plan ne propose pas de tomates fraiches."""
        result = generator.generate(week="2026-W06", month=2, constraints=default_constraints)

        # In February, tomatoes should not be in the ingredients
        for recipe in result.recipes:
            for ingredient in recipe.ingredients:
                # Fresh tomatoes are not in season in February
                assert "tomate" not in ingredient.name.lower() or "sechee" in ingredient.name.lower(), (
                    f"Fresh tomatoes found in February recipe: {recipe.name}"
                )

    def test_generate_plan_prompt_includes_seasonal_info(
        self, generator: MealPlanGenerator, mock_anthropic_client, default_constraints: GeneratorConstraints
    ) -> None:
        """Le prompt inclut les ingredients de saison."""
        generator.generate(week="2026-W06", month=2, constraints=default_constraints)

        call_args = mock_anthropic_client.messages.create.call_args
        messages = call_args.kwargs.get("messages", [])
        prompt_text = messages[0]["content"]

        # February seasonal vegetables should be mentioned
        assert "carotte" in prompt_text.lower() or "legumes de saison" in prompt_text.lower()


class TestBatchCooking:
    """Tests for batch cooking optimization."""

    def test_generate_plan_optimizes_batch_cooking(
        self, generator: MealPlanGenerator, default_constraints: GeneratorConstraints
    ) -> None:
        """Les recettes batch servent pour plusieurs repas de la semaine."""
        result = generator.generate(week="2026-W06", month=2, constraints=default_constraints)

        # Count how many times each recipe is used
        recipe_usage = {}
        for slot in result.meal_plan.slots:
            recipe_usage[slot.recipe_id] = recipe_usage.get(slot.recipe_id, 0) + 1

        # At least one recipe should be used multiple times (batch cooking)
        batch_recipes = [rid for rid, count in recipe_usage.items() if count > 1]
        assert len(batch_recipes) > 0, "No batch cooking recipes found"

        # Batch recipes should have 'batch' tag or servings > 2
        for rid in batch_recipes:
            recipe = next((r for r in result.recipes if r.id == rid), None)
            if recipe:
                is_batch = "batch" in recipe.tags or recipe.servings >= 4
                assert is_batch, f"Recipe {rid} used multiple times but not marked as batch"

    def test_generate_plan_has_prep_order(
        self, generator: MealPlanGenerator, default_constraints: GeneratorConstraints
    ) -> None:
        """Le plan inclut un ordre de preparation optimal."""
        result = generator.generate(week="2026-W06", month=2, constraints=default_constraints)

        assert len(result.meal_plan.prep_order) > 0
        assert result.meal_plan.total_prep_time_min > 0


class TestMealTypeRequirements:
    """Tests for meal-specific requirements."""

    def test_generate_plan_breakfast_is_portable(
        self, generator: MealPlanGenerator, default_constraints: GeneratorConstraints
    ) -> None:
        """Le petit-dejeuner est transportable (chia pudding, overnight oats...)."""
        result = generator.generate(week="2026-W06", month=2, constraints=default_constraints)

        breakfast_recipe_ids = {
            slot.recipe_id for slot in result.meal_plan.slots if slot.meal_type == "petit-dej"
        }

        for rid in breakfast_recipe_ids:
            recipe = next((r for r in result.recipes if r.id == rid), None)
            if recipe:
                # Breakfast should be transportable or quick to prepare
                is_portable = (
                    "transportable" in recipe.tags
                    or "petit-dej" in recipe.tags
                    or recipe.prep_time_min <= 10
                )
                assert is_portable, f"Breakfast recipe {recipe.name} is not portable"

    def test_generate_plan_dinner_is_quick_or_prepped(
        self, generator: MealPlanGenerator, default_constraints: GeneratorConstraints
    ) -> None:
        """Le diner prend <15min ou est deja pret du batch."""
        result = generator.generate(week="2026-W06", month=2, constraints=default_constraints)

        dinner_recipe_ids = {
            slot.recipe_id for slot in result.meal_plan.slots if slot.meal_type == "diner"
        }

        # Count recipe usage to identify batch recipes
        recipe_usage = {}
        for slot in result.meal_plan.slots:
            recipe_usage[slot.recipe_id] = recipe_usage.get(slot.recipe_id, 0) + 1

        for rid in dinner_recipe_ids:
            recipe = next((r for r in result.recipes if r.id == rid), None)
            if recipe:
                # Dinner should be quick OR reheatable (from batch) OR used multiple times
                is_quick = recipe.prep_time_min <= 15
                is_batch = recipe_usage.get(rid, 0) > 1 or recipe.reheatable
                assert is_quick or is_batch, (
                    f"Dinner recipe {recipe.name} is neither quick ({recipe.prep_time_min}min) nor batch"
                )
