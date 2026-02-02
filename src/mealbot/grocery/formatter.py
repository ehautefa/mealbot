"""Telegram formatting for grocery lists and meal plans."""

from __future__ import annotations

from mealbot.grocery.aggregator import GroceryList, GroceryListItem, IngredientCategory
from mealbot.models import MealPlan, Recipe


# Emoji mapping for categories
CATEGORY_EMOJIS = {
    IngredientCategory.LEGUMES: "🥬",
    IngredientCategory.FRUITS: "🍎",
    IngredientCategory.PROTEINES: "🥩",
    IngredientCategory.EPICERIE: "🏪",
    IngredientCategory.FRAIS: "🧀",
    IngredientCategory.SURGELES: "🧊",
    IngredientCategory.BOISSONS: "🥤",
    IngredientCategory.AUTRE: "📦",
}

# Category display names
CATEGORY_NAMES = {
    IngredientCategory.LEGUMES: "Légumes",
    IngredientCategory.FRUITS: "Fruits",
    IngredientCategory.PROTEINES: "Protéines",
    IngredientCategory.EPICERIE: "Épicerie",
    IngredientCategory.FRAIS: "Frais",
    IngredientCategory.SURGELES: "Surgelés",
    IngredientCategory.BOISSONS: "Boissons",
    IngredientCategory.AUTRE: "Autres",
}

# Day emojis
DAY_EMOJIS = {
    "lundi": "1️⃣",
    "mardi": "2️⃣",
    "mercredi": "3️⃣",
    "jeudi": "4️⃣",
    "vendredi": "5️⃣",
    "samedi": "6️⃣",
    "dimanche": "7️⃣",
}

# Meal type display names
MEAL_TYPE_NAMES = {
    "petit-dej": "🌅 Petit-déjeuner",
    "lunch": "☀️ Déjeuner",
    "diner": "🌙 Dîner",
}


def _format_quantity(quantity: float) -> str:
    """Format quantity nicely (no unnecessary decimals)."""
    if quantity == int(quantity):
        return str(int(quantity))
    return f"{quantity:.0f}"


def _format_item(item: GroceryListItem) -> str:
    """Format a single grocery item."""
    quantity_str = _format_quantity(item.total_quantity)
    return f"☐ {item.ingredient_name} - {quantity_str}{item.unit}"


def format_grocery_list(grocery_list: GroceryList) -> str:
    """Format a grocery list for Telegram.

    Args:
        grocery_list: The grocery list to format

    Returns:
        Telegram-compatible markdown string
    """
    if not grocery_list.items:
        return "🛒 *Liste de courses*\n\n_Aucun article_"

    lines = ["🛒 *Liste de courses*", ""]

    # Group by category
    by_category = grocery_list.by_category()

    # Sort categories for consistent ordering
    category_order = [
        IngredientCategory.LEGUMES,
        IngredientCategory.FRUITS,
        IngredientCategory.PROTEINES,
        IngredientCategory.FRAIS,
        IngredientCategory.EPICERIE,
        IngredientCategory.BOISSONS,
        IngredientCategory.SURGELES,
        IngredientCategory.AUTRE,
    ]

    for category in category_order:
        items = by_category.get(category, [])
        if not items:
            continue

        emoji = CATEGORY_EMOJIS.get(category, "📦")
        name = CATEGORY_NAMES.get(category, "Autres")

        lines.append(f"{emoji} *{name}*")
        for item in items:
            lines.append(_format_item(item))
        lines.append("")

    # Add total count
    lines.append(f"_Total: {grocery_list.total_items} articles_")

    return "\n".join(lines)


def format_meal_plan(plan: MealPlan, recipes: dict[str, Recipe]) -> str:
    """Format a meal plan for Telegram.

    Args:
        plan: The meal plan to format
        recipes: Dictionary mapping recipe IDs to Recipe objects

    Returns:
        Telegram-compatible markdown string
    """
    lines = [f"📅 *Plan repas - {plan.week}*", ""]

    # Group slots by day
    days_order = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    slots_by_day: dict[str, list] = {day: [] for day in days_order}

    for slot in plan.slots:
        if slot.day in slots_by_day:
            slots_by_day[slot.day].append(slot)

    # Format each day
    for day in days_order:
        day_slots = slots_by_day.get(day, [])
        if not day_slots:
            continue

        emoji = DAY_EMOJIS.get(day, "📆")
        lines.append(f"{emoji} *{day.capitalize()}*")

        # Sort by meal type
        meal_order = ["petit-dej", "lunch", "diner"]
        day_slots.sort(key=lambda s: meal_order.index(s.meal_type) if s.meal_type in meal_order else 99)

        for slot in day_slots:
            recipe = recipes.get(slot.recipe_id)
            recipe_name = recipe.name if recipe else slot.recipe_id

            meal_display = MEAL_TYPE_NAMES.get(slot.meal_type, slot.meal_type)
            lines.append(f"  {meal_display}: {recipe_name}")

        lines.append("")

    # Add prep info if available
    if plan.prep_order:
        lines.append("🍳 *Ordre de préparation (dimanche)*")
        for i, recipe_id in enumerate(plan.prep_order, 1):
            recipe = recipes.get(recipe_id)
            recipe_name = recipe.name if recipe else recipe_id
            lines.append(f"  {i}. {recipe_name}")
        lines.append("")

    if plan.total_prep_time_min:
        hours = plan.total_prep_time_min // 60
        minutes = plan.total_prep_time_min % 60
        if hours:
            lines.append(f"⏱ _Temps total de préparation: {hours}h{minutes:02d}_")
        else:
            lines.append(f"⏱ _Temps total de préparation: {minutes}min_")

    return "\n".join(lines)
