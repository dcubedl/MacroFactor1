"""
Seed script — inserts 40 curated recipes (5 per cuisine × 8 cuisines) with
their ingredients into the Supabase database.

Usage (from the backend/ directory):
    python -m database.seed_recipes

Safe to re-run: skips any recipe whose name already exists in the DB.
"""

import os
import sys

# Load env before importing supabase client
from dotenv import load_dotenv
load_dotenv()

from database.supabase import service_client  # noqa: E402  (must be after load_dotenv)

# ---------------------------------------------------------------------------
# Recipe definitions
# ---------------------------------------------------------------------------
# Each recipe dict has:
#   name, cuisine, description, calories, protein_g, carbs_g, fat_g, fiber_g,
#   prep_time_minutes, servings, is_curated
# Each ingredient dict has:
#   ingredient_name, quantity, unit, is_optional

RECIPES: list[dict] = [

    # =========================================================================
    # INDIAN
    # =========================================================================
    {
        "recipe": {
            "name": "Dal Tadka", "cuisine": "indian",
            "description": "Creamy yellow lentils tempered with ghee, cumin, and garlic — "
                           "a high-protein, high-fibre staple.",
            "calories": 350, "protein_g": 18, "carbs_g": 52, "fat_g": 7, "fiber_g": 14,
            "prep_time_minutes": 30, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Red lentils",    "quantity": "200", "unit": "g",   "is_optional": False},
            {"ingredient_name": "Ghee",           "quantity": "2",   "unit": "tbsp","is_optional": False},
            {"ingredient_name": "Onion",          "quantity": "1",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Tomato",         "quantity": "2",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Cumin seeds",    "quantity": "1",   "unit": "tsp", "is_optional": False},
            {"ingredient_name": "Turmeric",       "quantity": "0.5", "unit": "tsp", "is_optional": False},
            {"ingredient_name": "Garam masala",   "quantity": "1",   "unit": "tsp", "is_optional": False},
            {"ingredient_name": "Garlic",         "quantity": "4",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Fresh ginger",   "quantity": "1",   "unit": "tbsp","is_optional": False},
            {"ingredient_name": "Fresh coriander","quantity": "2",   "unit": "tbsp","is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Chicken Tikka Masala", "cuisine": "indian",
            "description": "Tender chicken in a rich, spiced tomato-cream sauce — "
                           "restaurant quality in 40 minutes.",
            "calories": 485, "protein_g": 38, "carbs_g": 22, "fat_g": 28, "fiber_g": 4,
            "prep_time_minutes": 40, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Chicken breast",     "quantity": "400", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Plain yogurt",       "quantity": "150", "unit": "ml",   "is_optional": False},
            {"ingredient_name": "Tikka masala paste", "quantity": "3",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Canned tomatoes",    "quantity": "400", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Single cream",       "quantity": "50",  "unit": "ml",   "is_optional": True},
            {"ingredient_name": "Onion",              "quantity": "1",   "unit": "large","is_optional": False},
            {"ingredient_name": "Garlic",             "quantity": "4",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Fresh ginger",       "quantity": "1",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Garam masala",       "quantity": "1",   "unit": "tsp",  "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Masala Omelette", "cuisine": "indian",
            "description": "Spiced egg omelette with onion, tomato, and green chilli — "
                           "a quick high-protein breakfast.",
            "calories": 280, "protein_g": 22, "carbs_g": 8, "fat_g": 18, "fiber_g": 2,
            "prep_time_minutes": 10, "servings": 1, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Eggs",           "quantity": "3",   "unit": "large", "is_optional": False},
            {"ingredient_name": "Onion",          "quantity": "0.5", "unit": "small", "is_optional": False},
            {"ingredient_name": "Green chilli",   "quantity": "1",   "unit": "piece", "is_optional": True},
            {"ingredient_name": "Fresh coriander","quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Turmeric",       "quantity": "0.25","unit": "tsp",   "is_optional": False},
            {"ingredient_name": "Olive oil",      "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Tomato",         "quantity": "1",   "unit": "small", "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Paneer Bhurji", "cuisine": "indian",
            "description": "Scrambled Indian cottage cheese with spiced onions and peppers — "
                           "vegetarian, high-protein, and ready in 20 minutes.",
            "calories": 320, "protein_g": 24, "carbs_g": 12, "fat_g": 20, "fiber_g": 3,
            "prep_time_minutes": 20, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Paneer",      "quantity": "250", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Onion",       "quantity": "1",   "unit": "large","is_optional": False},
            {"ingredient_name": "Tomatoes",    "quantity": "2",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Green pepper","quantity": "1",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Fresh ginger","quantity": "1",   "unit": "tsp",  "is_optional": False},
            {"ingredient_name": "Cumin seeds", "quantity": "1",   "unit": "tsp",  "is_optional": False},
            {"ingredient_name": "Turmeric",    "quantity": "0.5", "unit": "tsp",  "is_optional": False},
            {"ingredient_name": "Olive oil",   "quantity": "2",   "unit": "tbsp", "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Rajma Rice", "cuisine": "indian",
            "description": "Slow-cooked kidney beans in a spiced tomato gravy served over "
                           "basmati rice — a plant-based protein powerhouse.",
            "calories": 490, "protein_g": 20, "carbs_g": 82, "fat_g": 8, "fiber_g": 16,
            "prep_time_minutes": 35, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Kidney beans (canned)","quantity": "400", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Basmati rice",         "quantity": "150", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Onion",                "quantity": "1",   "unit": "large","is_optional": False},
            {"ingredient_name": "Tomatoes",             "quantity": "2",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Rajma masala",         "quantity": "2",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Olive oil",            "quantity": "2",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Garlic",               "quantity": "3",   "unit": "cloves","is_optional": False},
        ],
    },

    # =========================================================================
    # ARAB
    # =========================================================================
    {
        "recipe": {
            "name": "Hummus with Wholemeal Pitta", "cuisine": "arab",
            "description": "Creamy chickpea hummus with tahini and lemon, served with "
                           "toasted wholemeal pitta — rich in fibre and plant protein.",
            "calories": 420, "protein_g": 18, "carbs_g": 52, "fat_g": 16, "fiber_g": 12,
            "prep_time_minutes": 10, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Chickpeas (canned)","quantity": "400", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Tahini",            "quantity": "3",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Lemon juice",       "quantity": "3",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Garlic",            "quantity": "2",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Olive oil",         "quantity": "2",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Ground cumin",      "quantity": "0.5", "unit": "tsp",  "is_optional": False},
            {"ingredient_name": "Wholemeal pitta",   "quantity": "2",   "unit": "pieces","is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Grilled Chicken Shawarma", "cuisine": "arab",
            "description": "Marinated chicken thighs with shawarma spices, wrapped with "
                           "fresh salad and garlic sauce.",
            "calories": 510, "protein_g": 44, "carbs_g": 38, "fat_g": 18, "fiber_g": 5,
            "prep_time_minutes": 25, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Chicken thighs",       "quantity": "400", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Shawarma spice mix",   "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Plain yogurt",         "quantity": "100", "unit": "ml",    "is_optional": False},
            {"ingredient_name": "Flatbread wraps",      "quantity": "2",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Cucumber",             "quantity": "0.5", "unit": "piece", "is_optional": False},
            {"ingredient_name": "Tomato",               "quantity": "1",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Garlic sauce (toum)",  "quantity": "2",   "unit": "tbsp",  "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Fattoush Salad", "cuisine": "arab",
            "description": "Crisp bread salad with radishes, tomatoes, and sumac dressing — "
                           "light, refreshing, and high in micronutrients.",
            "calories": 220, "protein_g": 6, "carbs_g": 28, "fat_g": 10, "fiber_g": 5,
            "prep_time_minutes": 15, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Romaine lettuce",  "quantity": "200", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Tomatoes",         "quantity": "2",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Cucumber",         "quantity": "1",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Radishes",         "quantity": "4",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Wholemeal pitta",  "quantity": "1",   "unit": "piece", "is_optional": False},
            {"ingredient_name": "Ground sumac",     "quantity": "1",   "unit": "tsp",   "is_optional": False},
            {"ingredient_name": "Olive oil",        "quantity": "3",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Lemon juice",      "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Fresh mint",       "quantity": "10",  "unit": "g",     "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Foul Medames", "cuisine": "arab",
            "description": "Slow-cooked fava beans with lemon, garlic, and olive oil — "
                           "the classic high-fibre Arab breakfast.",
            "calories": 380, "protein_g": 22, "carbs_g": 56, "fat_g": 8, "fiber_g": 18,
            "prep_time_minutes": 15, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Fava beans (canned)","quantity": "400", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Olive oil",          "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Lemon juice",        "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Garlic",             "quantity": "3",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Ground cumin",       "quantity": "1",   "unit": "tsp",   "is_optional": False},
            {"ingredient_name": "Fresh parsley",      "quantity": "3",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Pitta bread",        "quantity": "1",   "unit": "piece", "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Lamb Kofta with Tabbouleh", "cuisine": "arab",
            "description": "Spiced lamb skewers served with herb-packed bulgur wheat salad — "
                           "a complete meal rich in protein and minerals.",
            "calories": 580, "protein_g": 38, "carbs_g": 34, "fat_g": 32, "fiber_g": 8,
            "prep_time_minutes": 35, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Lamb mince",    "quantity": "400", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Bulgur wheat",  "quantity": "100", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Fresh parsley", "quantity": "50",  "unit": "g",    "is_optional": False},
            {"ingredient_name": "Fresh mint",    "quantity": "20",  "unit": "g",    "is_optional": False},
            {"ingredient_name": "Tomatoes",      "quantity": "3",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Onion",         "quantity": "0.5", "unit": "large","is_optional": False},
            {"ingredient_name": "Allspice",      "quantity": "1",   "unit": "tsp",  "is_optional": False},
            {"ingredient_name": "Cinnamon",      "quantity": "0.5", "unit": "tsp",  "is_optional": False},
            {"ingredient_name": "Lemon juice",   "quantity": "3",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Olive oil",     "quantity": "3",   "unit": "tbsp", "is_optional": False},
        ],
    },

    # =========================================================================
    # JAPANESE
    # =========================================================================
    {
        "recipe": {
            "name": "Salmon Sushi Bowl", "cuisine": "japanese",
            "description": "Sushi-grade salmon over seasoned rice with edamame, avocado, "
                           "and cucumber — omega-3 rich and naturally balanced.",
            "calories": 520, "protein_g": 34, "carbs_g": 62, "fat_g": 14, "fiber_g": 6,
            "prep_time_minutes": 20, "servings": 1, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Sushi rice",      "quantity": "150", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Salmon fillet",   "quantity": "200", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Avocado",         "quantity": "0.5", "unit": "piece", "is_optional": False},
            {"ingredient_name": "Edamame (shelled)","quantity": "50",  "unit": "g",    "is_optional": False},
            {"ingredient_name": "Cucumber",        "quantity": "0.5", "unit": "piece", "is_optional": False},
            {"ingredient_name": "Soy sauce",       "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Sesame oil",      "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Nori sheets",     "quantity": "2",   "unit": "sheets","is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Tofu Miso Soup", "cuisine": "japanese",
            "description": "Silken tofu and wakame seaweed in a warming dashi broth — "
                           "low-calorie, probiotic-rich, and deeply nourishing.",
            "calories": 180, "protein_g": 14, "carbs_g": 16, "fat_g": 7, "fiber_g": 4,
            "prep_time_minutes": 15, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Silken tofu",    "quantity": "200", "unit": "g",    "is_optional": False},
            {"ingredient_name": "White miso paste","quantity": "2",  "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Dashi stock",    "quantity": "800", "unit": "ml",   "is_optional": False},
            {"ingredient_name": "Spring onions",  "quantity": "3",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Dried wakame",   "quantity": "10",  "unit": "g",    "is_optional": False},
            {"ingredient_name": "Shiitake mushrooms","quantity": "100","unit": "g",  "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Chicken Teriyaki with Steamed Broccoli", "cuisine": "japanese",
            "description": "Juicy chicken breast glazed in homemade teriyaki sauce, "
                           "served with steamed broccoli and rice.",
            "calories": 450, "protein_g": 42, "carbs_g": 32, "fat_g": 16, "fiber_g": 6,
            "prep_time_minutes": 25, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Chicken breast", "quantity": "350", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Teriyaki sauce", "quantity": "4",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Sesame seeds",   "quantity": "1",   "unit": "tsp",  "is_optional": True},
            {"ingredient_name": "Broccoli",       "quantity": "200", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Jasmine rice",   "quantity": "100", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Sesame oil",     "quantity": "1",   "unit": "tsp",  "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Edamame with Sea Salt", "cuisine": "japanese",
            "description": "Steamed young soya beans with sea salt — the perfect "
                           "high-protein, plant-based snack.",
            "calories": 150, "protein_g": 12, "carbs_g": 12, "fat_g": 6, "fiber_g": 6,
            "prep_time_minutes": 5, "servings": 1, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Edamame in pods","quantity": "300", "unit": "g",   "is_optional": False},
            {"ingredient_name": "Sea salt",       "quantity": "0.5", "unit": "tsp", "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Lighter Tonkotsu Ramen", "cuisine": "japanese",
            "description": "Comforting ramen bowl with lean pork, soft-boiled eggs, and "
                           "nori in a rich chicken broth.",
            "calories": 560, "protein_g": 36, "carbs_g": 68, "fat_g": 16, "fiber_g": 5,
            "prep_time_minutes": 30, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Ramen noodles",  "quantity": "200", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Chicken broth",  "quantity": "800", "unit": "ml",    "is_optional": False},
            {"ingredient_name": "Lean pork belly","quantity": "100", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Eggs",           "quantity": "2",   "unit": "large", "is_optional": False},
            {"ingredient_name": "Spring onions",  "quantity": "3",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Nori sheets",    "quantity": "2",   "unit": "sheets","is_optional": True},
            {"ingredient_name": "Soy sauce",      "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Sesame oil",     "quantity": "1",   "unit": "tsp",   "is_optional": False},
        ],
    },

    # =========================================================================
    # ITALIAN
    # =========================================================================
    {
        "recipe": {
            "name": "Pasta Primavera", "cuisine": "italian",
            "description": "Penne with seasonal vegetables, cherry tomatoes, and fresh "
                           "basil — bright, colourful, and fibre-packed.",
            "calories": 480, "protein_g": 18, "carbs_g": 72, "fat_g": 14, "fiber_g": 10,
            "prep_time_minutes": 25, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Penne pasta",       "quantity": "180", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Courgette",         "quantity": "1",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Bell peppers",      "quantity": "2",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Cherry tomatoes",   "quantity": "150", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Garlic",            "quantity": "3",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Olive oil",         "quantity": "3",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Fresh basil",       "quantity": "20",  "unit": "g",    "is_optional": False},
            {"ingredient_name": "Parmesan",          "quantity": "30",  "unit": "g",    "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Caprese Salad", "cuisine": "italian",
            "description": "Classic tomato, mozzarella, and basil salad with balsamic "
                           "glaze — simple, elegant, and rich in calcium.",
            "calories": 320, "protein_g": 16, "carbs_g": 8, "fat_g": 24, "fiber_g": 2,
            "prep_time_minutes": 10, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Fresh mozzarella","quantity": "200", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Large tomatoes",  "quantity": "3",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Fresh basil",     "quantity": "20",  "unit": "g",    "is_optional": False},
            {"ingredient_name": "Olive oil",       "quantity": "3",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Balsamic glaze",  "quantity": "1",   "unit": "tbsp", "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Minestrone Soup", "cuisine": "italian",
            "description": "Hearty vegetable and bean soup with small pasta — "
                           "a fibre-rich one-pot meal that keeps you full for hours.",
            "calories": 280, "protein_g": 12, "carbs_g": 42, "fat_g": 7, "fiber_g": 12,
            "prep_time_minutes": 35, "servings": 4, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Canned tomatoes",   "quantity": "400", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Cannellini beans",  "quantity": "200", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Carrots",           "quantity": "2",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Celery",            "quantity": "2",   "unit": "sticks","is_optional": False},
            {"ingredient_name": "Courgette",         "quantity": "1",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Small pasta",       "quantity": "80",  "unit": "g",     "is_optional": False},
            {"ingredient_name": "Vegetable stock",   "quantity": "1",   "unit": "litre", "is_optional": False},
            {"ingredient_name": "Garlic",            "quantity": "3",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Olive oil",         "quantity": "2",   "unit": "tbsp",  "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Chicken and Vegetable Frittata", "cuisine": "italian",
            "description": "Oven-baked egg frittata with chicken, spinach, cherry "
                           "tomatoes, and feta — protein-dense and low-carb.",
            "calories": 340, "protein_g": 32, "carbs_g": 10, "fat_g": 20, "fiber_g": 3,
            "prep_time_minutes": 30, "servings": 4, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Eggs",            "quantity": "6",   "unit": "large", "is_optional": False},
            {"ingredient_name": "Chicken breast",  "quantity": "200", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Fresh spinach",   "quantity": "100", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Cherry tomatoes", "quantity": "100", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Feta cheese",     "quantity": "60",  "unit": "g",     "is_optional": False},
            {"ingredient_name": "Olive oil",       "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Mixed dried herbs","quantity": "1",  "unit": "tsp",   "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Grilled Sea Bass with Caponata", "cuisine": "italian",
            "description": "Herb-crusted sea bass fillet over Sicilian sweet-and-sour "
                           "aubergine caponata — omega-3 rich and Mediterranean.",
            "calories": 420, "protein_g": 38, "carbs_g": 22, "fat_g": 18, "fiber_g": 6,
            "prep_time_minutes": 35, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Sea bass fillets","quantity": "400", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Aubergine",       "quantity": "1",   "unit": "large", "is_optional": False},
            {"ingredient_name": "Tomatoes",        "quantity": "2",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Black olives",    "quantity": "50",  "unit": "g",     "is_optional": False},
            {"ingredient_name": "Capers",          "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Red onion",       "quantity": "1",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Olive oil",       "quantity": "3",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Red wine vinegar","quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Pine nuts",       "quantity": "30",  "unit": "g",     "is_optional": True},
        ],
    },

    # =========================================================================
    # MEXICAN
    # =========================================================================
    {
        "recipe": {
            "name": "Black Bean Burrito Bowl", "cuisine": "mexican",
            "description": "Brown rice topped with spiced black beans, corn, salsa, "
                           "and avocado — a plant-based fibre powerhouse.",
            "calories": 520, "protein_g": 22, "carbs_g": 78, "fat_g": 14, "fiber_g": 18,
            "prep_time_minutes": 30, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Black beans (canned)","quantity": "400","unit": "g",    "is_optional": False},
            {"ingredient_name": "Brown rice",         "quantity": "150","unit": "g",    "is_optional": False},
            {"ingredient_name": "Sweetcorn",          "quantity": "100","unit": "g",    "is_optional": False},
            {"ingredient_name": "Tomato salsa",       "quantity": "100","unit": "g",    "is_optional": False},
            {"ingredient_name": "Avocado",            "quantity": "0.5","unit": "piece","is_optional": False},
            {"ingredient_name": "Lime juice",         "quantity": "2",  "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Ground cumin",       "quantity": "1",  "unit": "tsp",  "is_optional": False},
            {"ingredient_name": "Fresh coriander",    "quantity": "20", "unit": "g",    "is_optional": True},
            {"ingredient_name": "Greek yogurt",       "quantity": "2",  "unit": "tbsp", "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Chicken Tacos", "cuisine": "mexican",
            "description": "Smoky spiced chicken in corn tortillas with shredded cabbage "
                           "and lime — a lean, balanced street-food classic.",
            "calories": 490, "protein_g": 38, "carbs_g": 44, "fat_g": 16, "fiber_g": 7,
            "prep_time_minutes": 25, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Chicken breast",  "quantity": "350", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Corn tortillas",  "quantity": "4",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "White cabbage",   "quantity": "100", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Tomato",          "quantity": "1",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Red onion",       "quantity": "0.5", "unit": "medium","is_optional": False},
            {"ingredient_name": "Lime juice",      "quantity": "3",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Chilli powder",   "quantity": "1",   "unit": "tsp",   "is_optional": False},
            {"ingredient_name": "Smoked paprika",  "quantity": "1",   "unit": "tsp",   "is_optional": False},
            {"ingredient_name": "Fresh coriander", "quantity": "20",  "unit": "g",     "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Avocado Toast with Pico de Gallo", "cuisine": "mexican",
            "description": "Creamy avocado on wholegrain toast topped with fresh "
                           "tomato salsa — healthy fats and fibre for breakfast.",
            "calories": 380, "protein_g": 12, "carbs_g": 42, "fat_g": 20, "fiber_g": 10,
            "prep_time_minutes": 10, "servings": 1, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Wholegrain bread","quantity": "2",   "unit": "slices","is_optional": False},
            {"ingredient_name": "Avocado",        "quantity": "1",   "unit": "large", "is_optional": False},
            {"ingredient_name": "Tomatoes",       "quantity": "2",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Red onion",      "quantity": "0.5", "unit": "small", "is_optional": False},
            {"ingredient_name": "Fresh coriander","quantity": "15",  "unit": "g",     "is_optional": False},
            {"ingredient_name": "Jalapeño",       "quantity": "1",   "unit": "piece", "is_optional": True},
            {"ingredient_name": "Lime juice",     "quantity": "2",   "unit": "tbsp",  "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Pozole Rojo", "cuisine": "mexican",
            "description": "Traditional Mexican hominy soup with slow-cooked chicken "
                           "and guajillo chilli broth — warming and protein-rich.",
            "calories": 360, "protein_g": 28, "carbs_g": 38, "fat_g": 10, "fiber_g": 8,
            "prep_time_minutes": 50, "servings": 4, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Chicken thighs",      "quantity": "400", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Hominy corn (canned)","quantity": "400", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Dried guajillo chillies","quantity": "3","unit": "pieces","is_optional": False},
            {"ingredient_name": "Onion",               "quantity": "1",   "unit": "large", "is_optional": False},
            {"ingredient_name": "Garlic",              "quantity": "5",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Dried oregano",       "quantity": "1",   "unit": "tsp",   "is_optional": False},
            {"ingredient_name": "Ground cumin",        "quantity": "1",   "unit": "tsp",   "is_optional": False},
            {"ingredient_name": "Chicken stock",       "quantity": "1.2", "unit": "litre", "is_optional": False},
            {"ingredient_name": "Lime",                "quantity": "2",   "unit": "pieces","is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Turkey Chilli", "cuisine": "mexican",
            "description": "Lean turkey mince with kidney beans and smoky spices — "
                           "high-protein, high-fibre, and meal-prep friendly.",
            "calories": 430, "protein_g": 36, "carbs_g": 48, "fat_g": 12, "fiber_g": 16,
            "prep_time_minutes": 40, "servings": 4, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Turkey mince",       "quantity": "400", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Kidney beans (canned)","quantity": "400","unit": "g",   "is_optional": False},
            {"ingredient_name": "Canned tomatoes",    "quantity": "400", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Onion",              "quantity": "1",   "unit": "large","is_optional": False},
            {"ingredient_name": "Bell peppers",       "quantity": "2",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Chilli powder",      "quantity": "2",   "unit": "tsp",  "is_optional": False},
            {"ingredient_name": "Ground cumin",       "quantity": "2",   "unit": "tsp",  "is_optional": False},
            {"ingredient_name": "Garlic",             "quantity": "3",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Chicken stock",      "quantity": "200", "unit": "ml",   "is_optional": False},
        ],
    },

    # =========================================================================
    # CHINESE
    # =========================================================================
    {
        "recipe": {
            "name": "Steamed Ginger Chicken with Bok Choy", "cuisine": "chinese",
            "description": "Silky steamed chicken breast with ginger soy dressing and "
                           "crisp bok choy — clean, lean, and deeply flavourful.",
            "calories": 320, "protein_g": 38, "carbs_g": 12, "fat_g": 12, "fiber_g": 4,
            "prep_time_minutes": 25, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Chicken breast","quantity": "350", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Bok choy",      "quantity": "400", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Fresh ginger",  "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Garlic",        "quantity": "3",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Soy sauce",     "quantity": "3",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Sesame oil",    "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Rice wine",     "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Jasmine rice",  "quantity": "100", "unit": "g",     "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Egg Fried Rice", "cuisine": "chinese",
            "description": "Classic Chinese egg fried rice with peas, carrots, and soy — "
                           "quick, satisfying, and a great way to use leftover rice.",
            "calories": 420, "protein_g": 16, "carbs_g": 64, "fat_g": 12, "fiber_g": 4,
            "prep_time_minutes": 15, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Cooked jasmine rice","quantity": "300","unit": "g",     "is_optional": False},
            {"ingredient_name": "Eggs",              "quantity": "3",  "unit": "large", "is_optional": False},
            {"ingredient_name": "Frozen peas",       "quantity": "80", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Carrots",           "quantity": "2",  "unit": "medium","is_optional": False},
            {"ingredient_name": "Spring onions",     "quantity": "4",  "unit": "pieces","is_optional": False},
            {"ingredient_name": "Soy sauce",         "quantity": "2",  "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Sesame oil",        "quantity": "1",  "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Vegetable oil",     "quantity": "1",  "unit": "tbsp",  "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Steamed Vegetable Dumplings", "cuisine": "chinese",
            "description": "Delicate dumplings stuffed with seasoned napa cabbage, "
                           "mushrooms, and ginger — a light, fibre-rich dim sum.",
            "calories": 300, "protein_g": 14, "carbs_g": 46, "fat_g": 7, "fiber_g": 5,
            "prep_time_minutes": 40, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Dumpling wrappers","quantity": "20",  "unit": "pieces","is_optional": False},
            {"ingredient_name": "Napa cabbage",    "quantity": "200", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Shiitake mushrooms","quantity": "150","unit": "g",    "is_optional": False},
            {"ingredient_name": "Carrot",          "quantity": "1",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Fresh ginger",    "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Spring onions",   "quantity": "3",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Sesame oil",      "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Soy sauce",       "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Garlic",          "quantity": "2",   "unit": "cloves","is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Hot and Sour Soup", "cuisine": "chinese",
            "description": "Silken tofu, mushrooms, and bamboo shoots in a tangy "
                           "vinegar broth — low-calorie and deeply satisfying.",
            "calories": 180, "protein_g": 14, "carbs_g": 20, "fat_g": 6, "fiber_g": 4,
            "prep_time_minutes": 20, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Firm tofu",        "quantity": "200", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Shiitake mushrooms","quantity": "100","unit": "g",    "is_optional": False},
            {"ingredient_name": "Bamboo shoots",    "quantity": "100", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Eggs",             "quantity": "2",   "unit": "large","is_optional": False},
            {"ingredient_name": "Vegetable stock",  "quantity": "1",   "unit": "litre","is_optional": False},
            {"ingredient_name": "Rice vinegar",     "quantity": "3",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Soy sauce",        "quantity": "2",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "White pepper",     "quantity": "0.5", "unit": "tsp",  "is_optional": False},
            {"ingredient_name": "Cornstarch",       "quantity": "2",   "unit": "tbsp", "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Kung Pao Tofu", "cuisine": "chinese",
            "description": "Crispy tofu with bell peppers, peanuts, and dried chillies "
                           "in a glossy Sichuan sauce — plant-based and bold.",
            "calories": 350, "protein_g": 20, "carbs_g": 28, "fat_g": 18, "fiber_g": 6,
            "prep_time_minutes": 25, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Firm tofu",     "quantity": "400", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Bell peppers",  "quantity": "2",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Roasted peanuts","quantity": "50",  "unit": "g",    "is_optional": False},
            {"ingredient_name": "Dried chillies","quantity": "6",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Spring onions", "quantity": "4",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Garlic",        "quantity": "3",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Fresh ginger",  "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Soy sauce",     "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Hoisin sauce",  "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Rice vinegar",  "quantity": "1",   "unit": "tbsp",  "is_optional": False},
        ],
    },

    # =========================================================================
    # BRITISH
    # =========================================================================
    {
        "recipe": {
            "name": "Healthy Full English Breakfast", "cuisine": "british",
            "description": "Lean back bacon, eggs, grilled tomatoes, mushrooms, and "
                           "baked beans on wholegrain toast — balanced and filling.",
            "calories": 450, "protein_g": 34, "carbs_g": 28, "fat_g": 22, "fiber_g": 6,
            "prep_time_minutes": 20, "servings": 1, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Lean back bacon",  "quantity": "2",   "unit": "rashers","is_optional": False},
            {"ingredient_name": "Eggs",             "quantity": "2",   "unit": "large",  "is_optional": False},
            {"ingredient_name": "Cherry tomatoes",  "quantity": "100", "unit": "g",      "is_optional": False},
            {"ingredient_name": "Mushrooms",        "quantity": "100", "unit": "g",      "is_optional": False},
            {"ingredient_name": "Baked beans",      "quantity": "150", "unit": "g",      "is_optional": False},
            {"ingredient_name": "Wholegrain toast", "quantity": "1",   "unit": "slice",  "is_optional": False},
            {"ingredient_name": "Fresh spinach",    "quantity": "50",  "unit": "g",      "is_optional": True},
            {"ingredient_name": "Olive oil",        "quantity": "1",   "unit": "tbsp",   "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Chicken and Vegetable Stew", "cuisine": "british",
            "description": "Slow-cooked chicken with root vegetables and pearl barley "
                           "in a herbed broth — hearty winter comfort food.",
            "calories": 380, "protein_g": 36, "carbs_g": 32, "fat_g": 10, "fiber_g": 8,
            "prep_time_minutes": 55, "servings": 4, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Chicken thighs", "quantity": "400", "unit": "g",      "is_optional": False},
            {"ingredient_name": "Carrots",        "quantity": "3",   "unit": "medium", "is_optional": False},
            {"ingredient_name": "Parsnips",       "quantity": "2",   "unit": "medium", "is_optional": False},
            {"ingredient_name": "Celery",         "quantity": "2",   "unit": "sticks", "is_optional": False},
            {"ingredient_name": "Onion",          "quantity": "1",   "unit": "large",  "is_optional": False},
            {"ingredient_name": "Chicken stock",  "quantity": "800", "unit": "ml",     "is_optional": False},
            {"ingredient_name": "Fresh thyme",    "quantity": "4",   "unit": "sprigs", "is_optional": False},
            {"ingredient_name": "Bay leaves",     "quantity": "2",   "unit": "leaves", "is_optional": False},
            {"ingredient_name": "Pearl barley",   "quantity": "50",  "unit": "g",      "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Smoked Salmon Scrambled Eggs on Rye", "cuisine": "british",
            "description": "Creamy soft-scrambled eggs with smoked salmon on rye bread "
                           "— a protein and omega-3 packed breakfast.",
            "calories": 390, "protein_g": 36, "carbs_g": 24, "fat_g": 16, "fiber_g": 4,
            "prep_time_minutes": 10, "servings": 1, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Smoked salmon", "quantity": "150", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Eggs",          "quantity": "4",   "unit": "large", "is_optional": False},
            {"ingredient_name": "Rye bread",     "quantity": "2",   "unit": "slices","is_optional": False},
            {"ingredient_name": "Crème fraîche", "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Lemon juice",   "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Fresh dill",    "quantity": "10",  "unit": "g",     "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Red Lentil and Vegetable Soup", "cuisine": "british",
            "description": "Thick, warming lentil soup with root vegetables and warming "
                           "spices — cheap, high-fibre, and meal-prep friendly.",
            "calories": 290, "protein_g": 18, "carbs_g": 42, "fat_g": 5, "fiber_g": 14,
            "prep_time_minutes": 35, "servings": 4, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Red lentils",    "quantity": "150", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Carrots",        "quantity": "2",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Celery",         "quantity": "2",   "unit": "sticks","is_optional": False},
            {"ingredient_name": "Onion",          "quantity": "1",   "unit": "large", "is_optional": False},
            {"ingredient_name": "Garlic",         "quantity": "3",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Vegetable stock","quantity": "1.2", "unit": "litre", "is_optional": False},
            {"ingredient_name": "Ground cumin",   "quantity": "1",   "unit": "tsp",   "is_optional": False},
            {"ingredient_name": "Turmeric",       "quantity": "0.5", "unit": "tsp",   "is_optional": False},
            {"ingredient_name": "Tomato puree",   "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Fresh spinach",  "quantity": "100", "unit": "g",     "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Lightened Cottage Pie", "cuisine": "british",
            "description": "Lean beef mince in a vegetable gravy, topped with creamy "
                           "sweet potato mash — a lighter twist on the British classic.",
            "calories": 460, "protein_g": 32, "carbs_g": 48, "fat_g": 14, "fiber_g": 8,
            "prep_time_minutes": 55, "servings": 4, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Lean beef mince",    "quantity": "400", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Onion",              "quantity": "1",   "unit": "large","is_optional": False},
            {"ingredient_name": "Carrots",            "quantity": "2",   "unit": "medium","is_optional": False},
            {"ingredient_name": "Celery",             "quantity": "2",   "unit": "sticks","is_optional": False},
            {"ingredient_name": "Frozen peas",        "quantity": "100", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Beef stock",         "quantity": "300", "unit": "ml",   "is_optional": False},
            {"ingredient_name": "Tomato puree",       "quantity": "2",   "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Worcestershire sauce","quantity": "1",  "unit": "tbsp", "is_optional": False},
            {"ingredient_name": "Sweet potatoes",     "quantity": "600", "unit": "g",    "is_optional": False},
            {"ingredient_name": "Butter",             "quantity": "20",  "unit": "g",    "is_optional": False},
        ],
    },

    # =========================================================================
    # KOREAN
    # =========================================================================
    {
        "recipe": {
            "name": "Bibimbap", "cuisine": "korean",
            "description": "Brown rice topped with seasoned vegetables, beef, and a "
                           "fried egg — a nutritionally complete Korean bowl.",
            "calories": 550, "protein_g": 28, "carbs_g": 72, "fat_g": 16, "fiber_g": 8,
            "prep_time_minutes": 35, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Brown rice",       "quantity": "150", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Beef mince",       "quantity": "150", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Fresh spinach",    "quantity": "100", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Bean sprouts",     "quantity": "100", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Carrot",           "quantity": "1",   "unit": "large", "is_optional": False},
            {"ingredient_name": "Courgette",        "quantity": "0.5", "unit": "medium","is_optional": False},
            {"ingredient_name": "Shiitake mushrooms","quantity": "50", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Eggs",             "quantity": "2",   "unit": "large", "is_optional": False},
            {"ingredient_name": "Gochujang",        "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Sesame oil",       "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Soy sauce",        "quantity": "2",   "unit": "tbsp",  "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Dak-Guk (Korean Chicken Soup)", "cuisine": "korean",
            "description": "Clean chicken soup with rice and spring onions — simple, "
                           "nourishing, and deeply restorative.",
            "calories": 340, "protein_g": 38, "carbs_g": 28, "fat_g": 8, "fiber_g": 3,
            "prep_time_minutes": 45, "servings": 4, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Chicken legs",   "quantity": "500", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Jasmine rice",   "quantity": "100", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Garlic",         "quantity": "6",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Fresh ginger",   "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Spring onions",  "quantity": "4",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Soy sauce",      "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Sesame oil",     "quantity": "1",   "unit": "tsp",   "is_optional": False},
            {"ingredient_name": "Chicken stock",  "quantity": "1.5", "unit": "litre", "is_optional": False},
        ],
    },
    {
        "recipe": {
            "name": "Kimchi Fried Rice", "cuisine": "korean",
            "description": "Tangy kimchi fried rice with pork, egg, and nori — "
                           "probiotic-rich and ready in 15 minutes.",
            "calories": 420, "protein_g": 18, "carbs_g": 62, "fat_g": 12, "fiber_g": 6,
            "prep_time_minutes": 15, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Cooked jasmine rice","quantity": "300","unit": "g",     "is_optional": False},
            {"ingredient_name": "Kimchi",            "quantity": "150","unit": "g",     "is_optional": False},
            {"ingredient_name": "Lean pork belly",   "quantity": "100","unit": "g",     "is_optional": False},
            {"ingredient_name": "Eggs",              "quantity": "2",  "unit": "large", "is_optional": False},
            {"ingredient_name": "Sesame oil",        "quantity": "1",  "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Soy sauce",         "quantity": "1",  "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Spring onions",     "quantity": "3",  "unit": "pieces","is_optional": False},
            {"ingredient_name": "Gochugaru",         "quantity": "1",  "unit": "tsp",   "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Beef Bulgogi", "cuisine": "korean",
            "description": "Thinly sliced marinated beef grilled over high heat — "
                           "sweet, savoury, and rich in iron and zinc.",
            "calories": 480, "protein_g": 38, "carbs_g": 28, "fat_g": 24, "fiber_g": 3,
            "prep_time_minutes": 30, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Beef sirloin",  "quantity": "400", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Asian pear",    "quantity": "0.5", "unit": "piece", "is_optional": False},
            {"ingredient_name": "Soy sauce",     "quantity": "4",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Sesame oil",    "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Garlic",        "quantity": "4",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Fresh ginger",  "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Brown sugar",   "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Spring onions", "quantity": "4",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Sesame seeds",  "quantity": "1",   "unit": "tsp",   "is_optional": True},
            {"ingredient_name": "Jasmine rice",  "quantity": "100", "unit": "g",     "is_optional": True},
        ],
    },
    {
        "recipe": {
            "name": "Sundubu Jjigae (Soft Tofu Stew)", "cuisine": "korean",
            "description": "Silken tofu stew with pork, mushrooms, and egg in a "
                           "spiced anchovy broth — warming and low-carb.",
            "calories": 280, "protein_g": 24, "carbs_g": 18, "fat_g": 12, "fiber_g": 4,
            "prep_time_minutes": 25, "servings": 2, "is_curated": True,
        },
        "ingredients": [
            {"ingredient_name": "Silken tofu",    "quantity": "400", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Pork mince",     "quantity": "100", "unit": "g",     "is_optional": False},
            {"ingredient_name": "Eggs",           "quantity": "2",   "unit": "large", "is_optional": False},
            {"ingredient_name": "Spring onions",  "quantity": "4",   "unit": "pieces","is_optional": False},
            {"ingredient_name": "Garlic",         "quantity": "3",   "unit": "cloves","is_optional": False},
            {"ingredient_name": "Gochugaru",      "quantity": "2",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Soy sauce",      "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Sesame oil",     "quantity": "1",   "unit": "tbsp",  "is_optional": False},
            {"ingredient_name": "Anchovy stock",  "quantity": "600", "unit": "ml",    "is_optional": False},
            {"ingredient_name": "Mushrooms",      "quantity": "100", "unit": "g",     "is_optional": False},
        ],
    },
]


# ---------------------------------------------------------------------------
# Seed runner
# ---------------------------------------------------------------------------

def _recipe_exists(name: str) -> bool:
    """Return True if a recipe with this name already exists."""
    try:
        result = service_client.table("recipes").select("id").eq("name", name).limit(1).execute()
        return bool(result.data)
    except Exception:
        return False


def seed() -> None:
    inserted = 0
    skipped  = 0

    for entry in RECIPES:
        recipe_data = entry["recipe"]
        ingredients = entry["ingredients"]

        if _recipe_exists(recipe_data["name"]):
            print(f"  skip   {recipe_data['name']}")
            skipped += 1
            continue

        try:
            result = service_client.table("recipes").insert(recipe_data).execute()
            if not result.data:
                print(f"  ERROR  {recipe_data['name']}: insert returned no data", file=sys.stderr)
                continue

            recipe_id = result.data[0]["id"]

            ing_rows = [{"recipe_id": recipe_id, **ing} for ing in ingredients]
            service_client.table("recipe_ingredients").insert(ing_rows).execute()

            print(f"  insert {recipe_data['cuisine']:10s}  {recipe_data['name']}")
            inserted += 1

        except Exception as exc:
            print(f"  ERROR  {recipe_data['name']}: {exc}", file=sys.stderr)

    print(f"\nDone — {inserted} inserted, {skipped} skipped.")


if __name__ == "__main__":
    seed()
