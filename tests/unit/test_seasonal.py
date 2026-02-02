"""Tests for Swiss seasonal ingredients calendar."""

from __future__ import annotations

import pytest

from mealbot.planner.seasonal import get_seasonal_ingredients, SeasonalCategory


class TestSeasonalCalendar:
    """Tests for the seasonal ingredients calendar."""

    def test_february_vegetables_include_root_vegetables(self) -> None:
        """En fevrier en Suisse, on doit avoir carottes, panais, celeri-rave..."""
        ingredients = get_seasonal_ingredients(month=2)
        vegetables = ingredients.get(SeasonalCategory.LEGUMES, [])

        # Root vegetables available in February in Switzerland
        assert "carotte" in vegetables
        assert "panais" in vegetables
        assert "celeri-rave" in vegetables
        assert "poireau" in vegetables

        # Tomatoes are NOT in season in February
        assert "tomate" not in vegetables

    def test_summer_vegetables_include_tomates(self) -> None:
        """En juillet, les tomates sont de saison."""
        ingredients = get_seasonal_ingredients(month=7)
        vegetables = ingredients.get(SeasonalCategory.LEGUMES, [])

        assert "tomate" in vegetables
        assert "courgette" in vegetables
        assert "aubergine" in vegetables
        assert "poivron" in vegetables

    def test_get_seasonal_ingredients_returns_correct_categories(self) -> None:
        """Les ingredients sont categorises: legumes, fruits, herbes."""
        ingredients = get_seasonal_ingredients(month=6)

        # All three categories should be present
        assert SeasonalCategory.LEGUMES in ingredients
        assert SeasonalCategory.FRUITS in ingredients
        assert SeasonalCategory.HERBES in ingredients

        # Each category should have items
        assert len(ingredients[SeasonalCategory.LEGUMES]) > 0
        assert len(ingredients[SeasonalCategory.FRUITS]) > 0
        assert len(ingredients[SeasonalCategory.HERBES]) > 0

    def test_autumn_includes_squash(self) -> None:
        """En automne, les courges sont de saison."""
        ingredients = get_seasonal_ingredients(month=10)
        vegetables = ingredients.get(SeasonalCategory.LEGUMES, [])

        assert "courge" in vegetables or "butternut" in vegetables
        assert "potimarron" in vegetables

    def test_winter_fruits_include_storage_fruits(self) -> None:
        """En hiver, les fruits de conservation sont disponibles."""
        ingredients = get_seasonal_ingredients(month=1)
        fruits = ingredients.get(SeasonalCategory.FRUITS, [])

        assert "pomme" in fruits
        assert "poire" in fruits

    def test_invalid_month_raises_error(self) -> None:
        """Un mois invalide leve une erreur."""
        with pytest.raises(ValueError):
            get_seasonal_ingredients(month=0)

        with pytest.raises(ValueError):
            get_seasonal_ingredients(month=13)

    def test_fresh_herbs_available_in_summer(self) -> None:
        """Les herbes fraiches sont disponibles en ete."""
        ingredients = get_seasonal_ingredients(month=7)
        herbs = ingredients.get(SeasonalCategory.HERBES, [])

        assert "basilic" in herbs
        assert "persil" in herbs
        assert "ciboulette" in herbs
