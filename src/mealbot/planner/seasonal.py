"""Swiss seasonal ingredients calendar."""

from __future__ import annotations

from enum import Enum


class SeasonalCategory(Enum):
    """Categories of seasonal ingredients."""

    LEGUMES = "legumes"
    FRUITS = "fruits"
    HERBES = "herbes"


# Swiss seasonal calendar by month
# Sources: Swiss farmer markets, local agriculture calendars
_SEASONAL_CALENDAR: dict[int, dict[SeasonalCategory, list[str]]] = {
    # Janvier - Winter storage
    1: {
        SeasonalCategory.LEGUMES: [
            "carotte", "panais", "celeri-rave", "poireau", "chou",
            "chou-rouge", "chou-frise", "betterave", "navet", "rutabaga",
            "topinambour", "salsifis", "endive", "mache"
        ],
        SeasonalCategory.FRUITS: [
            "pomme", "poire"
        ],
        SeasonalCategory.HERBES: [
            "persil", "romarin", "thym", "sauge"
        ],
    },
    # Fevrier - Late winter
    2: {
        SeasonalCategory.LEGUMES: [
            "carotte", "panais", "celeri-rave", "poireau", "chou",
            "chou-rouge", "chou-frise", "betterave", "navet", "rutabaga",
            "topinambour", "salsifis", "endive", "mache", "epinard"
        ],
        SeasonalCategory.FRUITS: [
            "pomme", "poire"
        ],
        SeasonalCategory.HERBES: [
            "persil", "romarin", "thym", "sauge"
        ],
    },
    # Mars - Early spring
    3: {
        SeasonalCategory.LEGUMES: [
            "carotte", "panais", "celeri-rave", "poireau", "chou",
            "epinard", "mache", "radis", "cresson"
        ],
        SeasonalCategory.FRUITS: [
            "pomme", "poire", "rhubarbe"
        ],
        SeasonalCategory.HERBES: [
            "persil", "ciboulette", "ail-des-ours"
        ],
    },
    # Avril - Spring
    4: {
        SeasonalCategory.LEGUMES: [
            "asperge", "radis", "epinard", "cresson", "laitue",
            "oignon-nouveau", "carotte-nouvelle"
        ],
        SeasonalCategory.FRUITS: [
            "rhubarbe"
        ],
        SeasonalCategory.HERBES: [
            "persil", "ciboulette", "ail-des-ours", "cerfeuil"
        ],
    },
    # Mai - Late spring
    5: {
        SeasonalCategory.LEGUMES: [
            "asperge", "radis", "epinard", "laitue", "petit-pois",
            "feve", "oignon-nouveau", "carotte-nouvelle", "chou-rave"
        ],
        SeasonalCategory.FRUITS: [
            "rhubarbe", "fraise"
        ],
        SeasonalCategory.HERBES: [
            "persil", "ciboulette", "basilic", "menthe", "cerfeuil", "estragon"
        ],
    },
    # Juin - Early summer
    6: {
        SeasonalCategory.LEGUMES: [
            "asperge", "petit-pois", "feve", "haricot-vert", "courgette",
            "concombre", "laitue", "radis", "chou-rave", "fenouil", "bette"
        ],
        SeasonalCategory.FRUITS: [
            "fraise", "cerise", "framboise", "groseille"
        ],
        SeasonalCategory.HERBES: [
            "persil", "ciboulette", "basilic", "menthe", "aneth", "coriandre"
        ],
    },
    # Juillet - Summer peak
    7: {
        SeasonalCategory.LEGUMES: [
            "tomate", "courgette", "aubergine", "poivron", "concombre",
            "haricot-vert", "petit-pois", "fenouil", "bette", "mais",
            "laitue", "celeri-branche"
        ],
        SeasonalCategory.FRUITS: [
            "fraise", "framboise", "myrtille", "groseille", "cerise",
            "abricot", "peche", "prune"
        ],
        SeasonalCategory.HERBES: [
            "basilic", "persil", "ciboulette", "menthe", "aneth",
            "coriandre", "origan", "marjolaine"
        ],
    },
    # Aout - Late summer
    8: {
        SeasonalCategory.LEGUMES: [
            "tomate", "courgette", "aubergine", "poivron", "concombre",
            "haricot-vert", "fenouil", "bette", "mais", "oignon", "ail"
        ],
        SeasonalCategory.FRUITS: [
            "framboise", "myrtille", "mure", "prune", "peche",
            "poire", "pomme", "melon", "pasteque"
        ],
        SeasonalCategory.HERBES: [
            "basilic", "persil", "ciboulette", "menthe", "aneth",
            "coriandre", "origan", "thym"
        ],
    },
    # Septembre - Early autumn
    9: {
        SeasonalCategory.LEGUMES: [
            "tomate", "courgette", "aubergine", "poivron", "courge",
            "potimarron", "butternut", "haricot-vert", "fenouil", "bette",
            "chou", "poireau", "carotte"
        ],
        SeasonalCategory.FRUITS: [
            "pomme", "poire", "prune", "raisin", "figue", "mure"
        ],
        SeasonalCategory.HERBES: [
            "persil", "ciboulette", "thym", "romarin", "sauge"
        ],
    },
    # Octobre - Autumn
    10: {
        SeasonalCategory.LEGUMES: [
            "courge", "potimarron", "butternut", "chou", "chou-rouge",
            "chou-frise", "poireau", "carotte", "panais", "celeri-rave",
            "betterave", "navet", "fenouil", "brocoli"
        ],
        SeasonalCategory.FRUITS: [
            "pomme", "poire", "raisin", "coing", "chataigne", "noix"
        ],
        SeasonalCategory.HERBES: [
            "persil", "thym", "romarin", "sauge"
        ],
    },
    # Novembre - Late autumn
    11: {
        SeasonalCategory.LEGUMES: [
            "courge", "potimarron", "butternut", "chou", "chou-rouge",
            "chou-frise", "chou-de-bruxelles", "poireau", "carotte",
            "panais", "celeri-rave", "betterave", "navet", "topinambour",
            "salsifis", "endive", "mache"
        ],
        SeasonalCategory.FRUITS: [
            "pomme", "poire", "coing", "chataigne", "noix"
        ],
        SeasonalCategory.HERBES: [
            "persil", "thym", "romarin", "sauge"
        ],
    },
    # Decembre - Winter
    12: {
        SeasonalCategory.LEGUMES: [
            "chou", "chou-rouge", "chou-frise", "chou-de-bruxelles",
            "poireau", "carotte", "panais", "celeri-rave", "betterave",
            "navet", "rutabaga", "topinambour", "salsifis", "endive", "mache"
        ],
        SeasonalCategory.FRUITS: [
            "pomme", "poire"
        ],
        SeasonalCategory.HERBES: [
            "persil", "thym", "romarin", "sauge"
        ],
    },
}


def get_seasonal_ingredients(month: int) -> dict[SeasonalCategory, list[str]]:
    """Get seasonal ingredients for a given month in Switzerland.

    Args:
        month: Month number (1-12)

    Returns:
        Dictionary mapping SeasonalCategory to list of ingredient names

    Raises:
        ValueError: If month is not between 1 and 12
    """
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be between 1 and 12, got {month}")

    return _SEASONAL_CALENDAR[month]


def is_ingredient_in_season(ingredient: str, month: int) -> bool:
    """Check if an ingredient is in season for a given month.

    Args:
        ingredient: Name of the ingredient (lowercase)
        month: Month number (1-12)

    Returns:
        True if ingredient is in season
    """
    seasonal = get_seasonal_ingredients(month)
    ingredient_lower = ingredient.lower()

    for category_items in seasonal.values():
        if ingredient_lower in category_items:
            return True

    return False
