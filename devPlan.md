# MealBot — Plan de développement TDD

## Vision

Un bot Telegram qui, chaque semaine, génère un meal plan personnalisé, produit une liste de courses optimisée, et remplit automatiquement le panier sur coop.ch pour du Click & Collect.

---

## Stack technique

| Composant | Choix | Justification |
|-----------|-------|---------------|
| Langage | Python 3.9+ | Écosystème riche (scraping, API, bot). Utiliser `from __future__ import annotations` pour la compatibilité des type hints. |
| Tests | pytest + pytest-asyncio | Standard Python, TDD friendly |
| Bot | python-telegram-bot | Lib mature, async native |
| IA | Claude API (Anthropic SDK) | Génération meal plan + adaptation |
| Scraping | Playwright | Automatisation navigateur pour coop.ch |
| Base de données | SQLite (via sqlite3) | Local, zero config, suffisant pour 1 user |
| Config | pydantic-settings | Validation des configs, .env support |
| Task scheduler | APScheduler | Planification des envois hebdo |

---

## Architecture

```
mealbot/
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
├── src/
│   └── mealbot/
│       ├── __init__.py
│       ├── config.py              # Settings & env vars
│       ├── models.py              # Dataclasses: Recipe, MealPlan, Ingredient, Product
│       ├── db/
│       │   ├── __init__.py
│       │   ├── repository.py      # SQLite CRUD
│       │   └── migrations.py      # Schema setup
│       ├── planner/
│       │   ├── __init__.py
│       │   ├── seasonal.py        # Calendrier de saison Suisse
│       │   ├── generator.py       # Appel Claude API → MealPlan
│       │   └── nutrition.py       # Validation macros (protéines/glucides)
│       ├── grocery/
│       │   ├── __init__.py
│       │   ├── aggregator.py      # MealPlan → liste d'ingrédients agrégée
│       │   └── formatter.py       # Formatage pour affichage Telegram
│       ├── coop/
│       │   ├── __init__.py
│       │   ├── search.py          # Recherche produits sur coop.ch
│       │   ├── cart.py            # Ajout au panier + checkout
│       │   └── auth.py            # Login coop.ch
│       ├── bot/
│       │   ├── __init__.py
│       │   ├── handlers.py        # Commandes Telegram (/plan, /courses, /commander)
│       │   ├── conversations.py   # Flows conversationnels (validation, modifications)
│       │   └── scheduler.py       # Envoi automatique dimanche matin
│       └── main.py                # Entry point
├── tests/
│   ├── conftest.py                # Fixtures partagées
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_seasonal.py
│   │   ├── test_nutrition.py
│   │   ├── test_aggregator.py
│   │   └── test_formatter.py
│   ├── integration/
│   │   ├── test_generator.py      # Avec mock Claude API
│   │   ├── test_repository.py     # Avec SQLite in-memory
│   │   ├── test_coop_search.py    # Avec mock Playwright
│   │   └── test_coop_cart.py
│   └── e2e/
│       ├── test_full_pipeline.py  # Plan → courses → panier
│       └── test_bot_flow.py       # Simulation conversation Telegram
```

---

## Modèle de données

```python
@dataclass
class Ingredient:
    name: str                    # "tofu ferme"
    quantity: float              # 400
    unit: str                    # "g"
    category: str                # "protéines", "légumes", "base"

@dataclass
class Recipe:
    id: str
    name: str                    # "Curry rouge tofu & courge"
    servings: int                # 4 (portions batch)
    prep_time_min: int           # 25
    ingredients: list[Ingredient]
    instructions: list[str]
    tags: list[str]              # ["batch", "curry", "automne"]
    macros: Macros               # protéines, glucides, lipides par portion
    season: list[str]            # ["automne", "hiver"]
    storage_days: int            # 4
    reheatable: bool             # True

@dataclass
class Macros:
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float

@dataclass
class MealSlot:
    day: str                     # "lundi"
    meal_type: str               # "petit-dej", "lunch", "diner"
    recipe_id: str
    portions: int                # 1

@dataclass
class MealPlan:
    week: str                    # "2026-W06"
    slots: list[MealSlot]
    prep_order: list[str]        # Ordre de préparation optimal pour le dimanche
    total_prep_time_min: int

@dataclass
class GroceryItem:
    ingredient_name: str         # "tofu ferme"
    total_quantity: float        # 800 (agrégé de toutes les recettes)
    unit: str
    coop_product_name: str | None  # "Coop Naturaplan Tofu Bio ferme 2x200g"
    coop_product_url: str | None
    coop_price: float | None
```

---

## Sprints TDD

### 🏃 Sprint 0 — Setup (1 session) ✅

**Objectif** : Projet bootable, premier test qui passe.

- [x] Init projet : `pyproject.toml`, `src/mealbot/`, `tests/`
- [x] Config pytest + structure
- [x] Premier test : `test_models.py` — vérifier que les dataclasses se construisent correctement
- [x] Setup `.env.example` avec les variables nécessaires
- [x] Setup `.gitignore` (`.venv/`, `*.egg-info/`, `__pycache__/`, `.env`, `*.db`)
- [x] README avec instructions de setup

```bash
# Commandes de setup
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip  # Requis pour editable install avec pyproject.toml
pip install -e ".[dev]"
pytest  # → 10 tests passent ✅
```

**Apprentissages Sprint 0 :**
- Pip doit être mis à jour pour supporter `pip install -e` avec `pyproject.toml`
- Ajouter `from __future__ import annotations` en haut des fichiers Python pour compatibilité 3.9

---

### 🏃 Sprint 1 — Calendrier de saison + Nutrition (2-3 sessions) ✅

**Objectif** : Savoir ce qui est de saison et valider les macros.

#### Tests écrits (16 tests) :
- `test_seasonal.py` : 7 tests (légumes hiver/été, fruits, herbes, validation mois)
- `test_nutrition.py` : 9 tests (protéines, glucides, recettes high-carb, validation plan)

#### Implémentation :
- [x] `seasonal.py` : calendrier complet 12 mois avec `SeasonalCategory` enum
- [x] `nutrition.py` : `validate_daily_protein`, `validate_daily_carbs`, `is_high_carb_recipe`, `validate_meal_plan_nutrition`

#### Constantes définies :
- `DAILY_PROTEIN_MIN_G = 60.0`
- `DAILY_CARBS_MAX_G = 150.0`
- `HIGH_CARB_THRESHOLD_G = 50.0`

---

### 🏃 Sprint 2 — Génération du Meal Plan via Claude (2-3 sessions) ✅

**Objectif** : Claude génère un plan de repas cohérent.

#### Tests écrits (10 tests) :
- Structure: 7 jours × 3 repas, recettes incluses
- Contraintes: exclusions d'ingrédients, prompt validation
- Saisonnier: pas de tomates en février, info saison dans prompt
- Batch cooking: recettes réutilisées, ordre de préparation
- Repas: petit-dej transportable, dîner rapide ou batch

#### Implémentation :
- [x] `config.py` : Settings pydantic avec variables d'environnement
- [x] `generator.py` : `MealPlanGenerator` classe avec prompt template
- [x] `GeneratorConstraints` : dataclass pour les contraintes alimentaires
- [x] Prompt template complet avec format JSON structuré
- [x] Parsing de la réponse Claude → `MealPlan` + `Recipe[]`

#### Apprentissages Sprint 2 :
- Architecture mismatch possible avec packages binaires (pydantic-core, jiter) → réinstaller pour l'architecture correcte
- Tests de fixtures doivent éviter les faux positifs (ex: "lait de coco" ≠ "lait")

---

### 🏃 Sprint 3 — Agrégation courses (1-2 sessions) ✅

**Objectif** : Transformer un MealPlan en liste de courses intelligente.

#### Tests écrits (18 tests) :
- `test_aggregator.py` : 10 tests (combinaison, portions, pantry, catégories)
- `test_formatter.py` : 8 tests (Telegram markdown, emojis, sections)

#### Implémentation :
- [x] `aggregator.py` : `aggregate_ingredients()`, `GroceryList`, `GroceryListItem`
- [x] `formatter.py` : `format_grocery_list()`, `format_meal_plan()`
- [x] `IngredientCategory` enum (légumes, fruits, protéines, épicerie, frais, surgelés, boissons)
- [x] `PANTRY_STAPLES` set pour exclusion configurable
- [x] Calcul par portion: `quantity * (portions / servings)`

#### Apprentissages Sprint 3 :
- Les portions dans MealSlot = nombre de portions consommées, pas la recette entière
- Formule: `ingredient_qty * (slot.portions / recipe.servings)`

---

### 🏃 Sprint 4 — SQLite + Persistance (1-2 sessions)

**Objectif** : Stocker recettes, plans, préférences et historique.

#### Tests à écrire AVANT le code :

```python
# test_repository.py (SQLite in-memory)
def test_save_and_load_recipe():
def test_save_meal_plan():
def test_get_recent_plans_avoids_repetition():
    """Le générateur peut vérifier l'historique pour varier les repas."""
def test_save_user_preferences():
def test_update_preference():
```

#### Implémentation :
- `repository.py` : CRUD SQLite
- `migrations.py` : création de tables

---

### 🏃 Sprint 5 — Intégration Coop.ch (3-4 sessions)

**Objectif** : Chercher des produits et remplir un panier sur coop.ch.

#### Tests à écrire AVANT le code :

```python
# test_coop_search.py
def test_search_product_returns_results(mock_playwright):
    """Rechercher 'tofu' retourne des produits avec nom, prix, URL."""

def test_search_product_handles_no_results(mock_playwright):
    """Un ingrédient introuvable retourne une liste vide."""

def test_match_best_product():
    """Pour 'tofu ferme 400g', le matcher choisit le produit le plus pertinent."""

# test_coop_cart.py
def test_add_to_cart(mock_playwright):
    """Ajouter un produit au panier incrémente le compteur."""

def test_full_cart_flow(mock_playwright):
    """Login → recherche → ajout → le panier contient tous les items."""
```

#### Implémentation :
- `auth.py` : login coop.ch via Playwright
- `search.py` : recherche produit + parsing résultats
- `cart.py` : ajout au panier, vérification
- ⚠️ **Point d'attention** : le scraping est fragile → prévoir des fallbacks et du logging

---

### 🏃 Sprint 6 — Bot Telegram (2-3 sessions)

**Objectif** : Interface conversationnelle complète.

#### Tests à écrire AVANT le code :

```python
# test_bot_flow.py
def test_command_plan_generates_and_sends_plan():
def test_user_can_swap_recipe():
    """L'utilisateur dit 'change le dîner de mardi' et reçoit une alternative."""
def test_command_courses_sends_grocery_list():
def test_command_commander_triggers_coop_flow():
def test_confirm_before_ordering():
    """Le bot demande confirmation avant de remplir le panier Coop."""
```

#### Commandes du bot :

| Commande | Action |
|----------|--------|
| `/plan` | Génère et affiche le meal plan de la semaine |
| `/swap [jour] [repas]` | Remplace un repas par une alternative |
| `/courses` | Affiche la liste de courses |
| `/commander` | Lance le remplissage du panier Coop |
| `/prefs` | Modifier les préférences |
| `/prep` | Affiche l'ordre de batch cooking du dimanche |

#### Implémentation :
- `handlers.py` : routage des commandes
- `conversations.py` : flux de validation multi-étapes
- `scheduler.py` : envoi automatique le samedi matin (rappel courses) et dimanche matin (plan + prep)

---

### 🏃 Sprint 7 — Pipeline E2E + Polish (2 sessions)

**Objectif** : Tout connecter et fiabiliser.

#### Tests à écrire AVANT le code :

```python
# test_full_pipeline.py
def test_end_to_end_saturday_flow():
    """
    Samedi matin :
    1. Génération meal plan → OK
    2. Agrégation courses → OK
    3. Matching produits Coop → OK
    4. Envoi message Telegram avec plan + courses → OK
    5. User confirme → remplissage panier Coop → OK
    """
```

#### Polish :
- Gestion d'erreurs robuste (Coop down, produit introuvable, API timeout)
- Retry logic
- Logging structuré
- Messages Telegram user-friendly avec formatage propre

---

## Flow utilisateur final

```
                SAMEDI MATIN (automatique)
                ┌─────────────────────────┐
                │  🤖 Bot envoie :        │
                │  "Voici ton plan pour    │
                │   la semaine !"         │
                │  + meal plan détaillé    │
                │  + liste de courses     │
                └──────────┬──────────────┘
                           │
                    Tu valides ou modifies
                    (/swap pour changer)
                           │
                           ▼
                ┌─────────────────────────┐
                │  "Parfait ! Je remplis  │
                │   ton panier Coop ?"    │
                └──────────┬──────────────┘
                           │
                     Tu confirmes
                           │
                           ▼
                ┌─────────────────────────┐
                │  🛒 Playwright remplit  │
                │  le panier sur coop.ch  │
                │  → Click & Collect prêt │
                └──────────┬──────────────┘
                           │
                  Tu vas chercher tes courses
                           │
                           ▼
                DIMANCHE MATIN (automatique)
                ┌─────────────────────────┐
                │  🍳 Bot envoie :        │
                │  "C'est l'heure du      │
                │   batch cooking !"      │
                │  + ordre de préparation │
                │  + timers               │
                └─────────────────────────┘
```

---

## Principe TDD rappel

Pour chaque feature, toujours dans cet ordre :

1. **🔴 RED** — Écrire un test qui échoue
2. **🟢 GREEN** — Écrire le minimum de code pour faire passer le test
3. **🔵 REFACTOR** — Nettoyer sans casser les tests

---

## Pour démarrer

```bash
# Sprint 0 — à lancer maintenant
mkdir mealbot && cd mealbot
python -m venv .venv && source .venv/bin/activate
pip install pytest pytest-asyncio anthropic python-telegram-bot playwright pydantic-settings
playwright install chromium
```
