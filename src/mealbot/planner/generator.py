"""Meal plan generator using Claude API."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import anthropic

from mealbot.config import settings
from mealbot.models import Ingredient, Macros, MealPlan, MealSlot, Recipe
from mealbot.planner.seasonal import get_seasonal_ingredients, SeasonalCategory


@dataclass
class GeneratorConstraints:
    """Constraints for meal plan generation."""

    exclude_ingredients: list[str] = field(default_factory=list)
    max_meat_fish_per_week: int = 1
    min_protein_per_day: float = 60.0
    max_carbs_per_day: float = 150.0
    batch_cooking: bool = True
    portable_breakfast: bool = True
    quick_dinner_max_min: int = 15


@dataclass
class GeneratorResult:
    """Result of meal plan generation."""

    meal_plan: MealPlan
    recipes: list[Recipe]


PROMPT_TEMPLATE = """Tu es un expert en nutrition et en meal planning. Tu dois generer un plan de repas pour une semaine complete.

## Semaine
{week}

## Contraintes alimentaires
- Ingredients a EXCLURE (allergies/intolerances): {excluded_ingredients}
- Maximum {max_meat_fish} repas avec viande ou poisson par semaine
- Minimum {min_protein}g de proteines par jour
- Maximum {max_carbs}g de glucides par jour

## Ingredients de saison (mois: {month})
### Legumes
{seasonal_vegetables}

### Fruits
{seasonal_fruits}

### Herbes
{seasonal_herbs}

## Exigences
1. **Batch cooking**: Les recettes doivent etre optimisees pour le batch cooking du dimanche. Une recette peut servir plusieurs repas.
2. **Petit-dejeuner transportable**: Les petits-dejeuners doivent etre transportables (chia pudding, overnight oats, muffins, etc.)
3. **Diners rapides**: Les diners doivent prendre moins de {quick_dinner_max}min a preparer OU etre des restes du batch cooking (rechauffage rapide)
4. **Equilibre nutritionnel**: Chaque jour doit atteindre les objectifs de proteines et rester sous la limite de glucides
5. **Variete**: Eviter de manger exactement le meme repas plus de 2 fois dans la semaine

## Format de sortie (JSON strict)
Reponds UNIQUEMENT avec un JSON valide, sans texte avant ou apres:

```json
{{
  "recipes": [
    {{
      "id": "identifiant-unique",
      "name": "Nom de la recette",
      "servings": 4,
      "prep_time_min": 25,
      "ingredients": [
        {{"name": "ingredient", "quantity": 100, "unit": "g", "category": "legumes"}}
      ],
      "instructions": ["Etape 1", "Etape 2"],
      "tags": ["batch", "lunch"],
      "macros": {{"calories": 400, "protein_g": 25, "carbs_g": 30, "fat_g": 15}},
      "season": ["hiver"],
      "storage_days": 4,
      "reheatable": true
    }}
  ],
  "meal_plan": {{
    "week": "{week}",
    "slots": [
      {{"day": "lundi", "meal_type": "petit-dej", "recipe_id": "id-recette", "portions": 1}}
    ],
    "prep_order": ["recette-1", "recette-2"],
    "total_prep_time_min": 120
  }}
}}
```

## Jours de la semaine
lundi, mardi, mercredi, jeudi, vendredi, samedi, dimanche

## Types de repas
petit-dej, lunch, diner

Genere le plan de repas complet pour 7 jours avec 3 repas par jour (21 slots au total).
"""


class MealPlanGenerator:
    """Generates meal plans using Claude API."""

    def __init__(self, api_key: str | None = None):
        """Initialize the generator.

        Args:
            api_key: Anthropic API key. If not provided, uses settings.
        """
        self._api_key = api_key or settings.anthropic_api_key
        self._client = anthropic.Anthropic(api_key=self._api_key)
        self._model = settings.claude_model

    def generate(
        self,
        week: str,
        month: int,
        constraints: GeneratorConstraints | None = None,
    ) -> GeneratorResult:
        """Generate a meal plan for the specified week.

        Args:
            week: ISO week string (e.g., "2026-W06")
            month: Month number (1-12) for seasonal ingredients
            constraints: Optional dietary constraints

        Returns:
            GeneratorResult with meal plan and recipes
        """
        if constraints is None:
            constraints = GeneratorConstraints()

        # Build the prompt
        prompt = self._build_prompt(week, month, constraints)

        # Call Claude API
        response = self._call_claude(prompt)

        # Parse the response
        return self._parse_response(response)

    def _build_prompt(
        self,
        week: str,
        month: int,
        constraints: GeneratorConstraints,
    ) -> str:
        """Build the prompt for Claude."""
        # Get seasonal ingredients
        seasonal = get_seasonal_ingredients(month)

        vegetables = ", ".join(seasonal.get(SeasonalCategory.LEGUMES, []))
        fruits = ", ".join(seasonal.get(SeasonalCategory.FRUITS, []))
        herbs = ", ".join(seasonal.get(SeasonalCategory.HERBES, []))

        # Format excluded ingredients
        excluded = ", ".join(constraints.exclude_ingredients) if constraints.exclude_ingredients else "aucun"

        return PROMPT_TEMPLATE.format(
            week=week,
            month=month,
            excluded_ingredients=excluded,
            max_meat_fish=constraints.max_meat_fish_per_week,
            min_protein=constraints.min_protein_per_day,
            max_carbs=constraints.max_carbs_per_day,
            seasonal_vegetables=vegetables,
            seasonal_fruits=fruits,
            seasonal_herbs=herbs,
            quick_dinner_max=constraints.quick_dinner_max_min,
        )

    def _call_claude(self, prompt: str) -> str:
        """Call Claude API with the prompt."""
        message = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        return message.content[0].text

    def _parse_response(self, response: str) -> GeneratorResult:
        """Parse Claude's JSON response into structured data."""
        # Extract JSON from response (handle markdown code blocks)
        json_str = response
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()

        data = json.loads(json_str)

        # Parse recipes
        recipes = []
        for r in data["recipes"]:
            ingredients = [
                Ingredient(
                    name=i["name"],
                    quantity=float(i["quantity"]),
                    unit=i["unit"],
                    category=i["category"],
                )
                for i in r["ingredients"]
            ]

            macros = None
            if "macros" in r and r["macros"]:
                macros = Macros(
                    calories=r["macros"]["calories"],
                    protein_g=float(r["macros"]["protein_g"]),
                    carbs_g=float(r["macros"]["carbs_g"]),
                    fat_g=float(r["macros"]["fat_g"]),
                )

            recipe = Recipe(
                id=r["id"],
                name=r["name"],
                servings=r["servings"],
                prep_time_min=r["prep_time_min"],
                ingredients=ingredients,
                instructions=r["instructions"],
                tags=r.get("tags", []),
                macros=macros,
                season=r.get("season", []),
                storage_days=r.get("storage_days", 3),
                reheatable=r.get("reheatable", True),
            )
            recipes.append(recipe)

        # Parse meal plan
        plan_data = data["meal_plan"]
        slots = [
            MealSlot(
                day=s["day"],
                meal_type=s["meal_type"],
                recipe_id=s["recipe_id"],
                portions=s.get("portions", 1),
            )
            for s in plan_data["slots"]
        ]

        meal_plan = MealPlan(
            week=plan_data["week"],
            slots=slots,
            prep_order=plan_data.get("prep_order", []),
            total_prep_time_min=plan_data.get("total_prep_time_min", 0),
        )

        return GeneratorResult(meal_plan=meal_plan, recipes=recipes)
