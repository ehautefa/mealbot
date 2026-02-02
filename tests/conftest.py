"""Shared pytest fixtures for MealBot tests."""

import pytest

from mealbot.models import Ingredient, Macros, Recipe


@pytest.fixture
def sample_macros() -> Macros:
    """Sample macros for testing."""
    return Macros(
        calories=450,
        protein_g=25.0,
        carbs_g=35.0,
        fat_g=18.0,
    )


@pytest.fixture
def sample_ingredient() -> Ingredient:
    """Sample ingredient for testing."""
    return Ingredient(
        name="tofu ferme",
        quantity=400.0,
        unit="g",
        category="proteines",
    )


@pytest.fixture
def sample_recipe(sample_ingredient: Ingredient, sample_macros: Macros) -> Recipe:
    """Sample recipe for testing."""
    return Recipe(
        id="curry-tofu-courge",
        name="Curry rouge tofu & courge",
        servings=4,
        prep_time_min=25,
        ingredients=[
            sample_ingredient,
            Ingredient(name="courge butternut", quantity=500.0, unit="g", category="legumes"),
            Ingredient(name="lait de coco", quantity=400.0, unit="ml", category="base"),
        ],
        instructions=[
            "Couper le tofu en cubes et la courge en morceaux.",
            "Faire revenir le tofu dans un peu d'huile.",
            "Ajouter la pate de curry et faire revenir.",
            "Ajouter la courge et le lait de coco.",
            "Laisser mijoter 20 minutes.",
        ],
        tags=["batch", "curry", "automne"],
        macros=sample_macros,
        season=["automne", "hiver"],
        storage_days=4,
        reheatable=True,
    )
