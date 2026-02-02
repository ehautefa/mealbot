"""Nutrition validation for meal plans."""

from __future__ import annotations

from dataclasses import dataclass

from mealbot.models import Macros, MealPlan, Recipe


# Nutrition targets and thresholds
DAILY_PROTEIN_MIN_G = 60.0  # Minimum daily protein target
DAILY_CARBS_MAX_G = 150.0  # Maximum daily carbs limit
HIGH_CARB_THRESHOLD_G = 50.0  # Carbs per portion to flag as high-carb


@dataclass
class ValidationResult:
    """Result of a single nutrition validation."""

    is_valid: bool
    total: float
    target: float
    deficit: float = 0.0  # For protein (below target)
    excess: float = 0.0  # For carbs (above limit)


@dataclass
class NutritionValidationResult:
    """Result of full meal plan nutrition validation."""

    protein_valid: bool
    carbs_valid: bool
    protein_total: float = 0.0
    carbs_total: float = 0.0
    high_carb_recipes: list[str] | None = None

    @property
    def is_valid(self) -> bool:
        """Check if all nutrition validations passed."""
        return self.protein_valid and self.carbs_valid


def validate_daily_protein(daily_macros: list[Macros]) -> ValidationResult:
    """Validate that daily protein meets the minimum target.

    Args:
        daily_macros: List of Macros for each meal in the day

    Returns:
        ValidationResult with protein validation details
    """
    total_protein = sum(m.protein_g for m in daily_macros)
    is_valid = total_protein >= DAILY_PROTEIN_MIN_G
    deficit = max(0.0, DAILY_PROTEIN_MIN_G - total_protein)

    return ValidationResult(
        is_valid=is_valid,
        total=total_protein,
        target=DAILY_PROTEIN_MIN_G,
        deficit=deficit,
    )


def validate_daily_carbs(daily_macros: list[Macros]) -> ValidationResult:
    """Validate that daily carbs don't exceed the maximum limit.

    Args:
        daily_macros: List of Macros for each meal in the day

    Returns:
        ValidationResult with carbs validation details
    """
    total_carbs = sum(m.carbs_g for m in daily_macros)
    is_valid = total_carbs <= DAILY_CARBS_MAX_G
    excess = max(0.0, total_carbs - DAILY_CARBS_MAX_G)

    return ValidationResult(
        is_valid=is_valid,
        total=total_carbs,
        target=DAILY_CARBS_MAX_G,
        excess=excess,
    )


def is_high_carb_recipe(recipe: Recipe) -> bool:
    """Check if a recipe has high carbs per portion.

    Args:
        recipe: Recipe to check

    Returns:
        True if carbs per portion exceed the threshold
    """
    if recipe.macros is None:
        return False

    return recipe.macros.carbs_g > HIGH_CARB_THRESHOLD_G


def validate_meal_plan_nutrition(
    plan: MealPlan,
    recipes: dict[str, Recipe],
    day: str,
) -> NutritionValidationResult:
    """Validate nutrition for a specific day in a meal plan.

    Args:
        plan: The meal plan to validate
        recipes: Dictionary mapping recipe IDs to Recipe objects
        day: The day to validate (e.g., "lundi")

    Returns:
        NutritionValidationResult with all validation details
    """
    # Get all meals for the specified day
    day_slots = [slot for slot in plan.slots if slot.day == day]

    # Collect macros for each meal
    daily_macros: list[Macros] = []
    high_carb_recipes: list[str] = []

    for slot in day_slots:
        recipe = recipes.get(slot.recipe_id)
        if recipe and recipe.macros:
            # Account for portions
            macros = Macros(
                calories=recipe.macros.calories * slot.portions,
                protein_g=recipe.macros.protein_g * slot.portions,
                carbs_g=recipe.macros.carbs_g * slot.portions,
                fat_g=recipe.macros.fat_g * slot.portions,
            )
            daily_macros.append(macros)

            if is_high_carb_recipe(recipe):
                high_carb_recipes.append(recipe.id)

    # Validate protein and carbs
    protein_result = validate_daily_protein(daily_macros)
    carbs_result = validate_daily_carbs(daily_macros)

    return NutritionValidationResult(
        protein_valid=protein_result.is_valid,
        carbs_valid=carbs_result.is_valid,
        protein_total=protein_result.total,
        carbs_total=carbs_result.total,
        high_carb_recipes=high_carb_recipes if high_carb_recipes else None,
    )
