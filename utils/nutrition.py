"""
Utilities for parsing and calculating nutritional data.
"""

import json
import re
from typing import Optional


def parse_nutrition_response(raw_text: str) -> Optional[dict]:
    """
    Parse the JSON nutritional data from the model's raw response.
    Handles common issues like markdown fences, extra text, etc.

    Args:
        raw_text: Raw text response from the vision model

    Returns:
        Parsed dictionary or None if parsing fails
    """
    if not raw_text:
        return None

    # Strip markdown code fences if present
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON object from the text
    try:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
    except json.JSONDecodeError:
        pass

    return None


def calculate_daily_totals(meals: list) -> dict:
    """
    Calculate total macros from a list of meal entries.

    Args:
        meals: List of meal history entries with 'data' field

    Returns:
        Dictionary with summed totals
    """
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}

    for meal in meals:
        data = meal.get("data", {})
        meal_totals = data.get("totals", {})
        for key in totals:
            try:
                totals[key] += int(meal_totals.get(key, 0))
            except (ValueError, TypeError):
                pass

    return totals


def format_macro_percentage(totals: dict) -> dict:
    """
    Calculate macro percentages from totals.

    Args:
        totals: Dictionary with protein, carbs, fat in grams

    Returns:
        Dictionary with percentage values
    """
    protein_cal = totals.get("protein", 0) * 4
    carbs_cal = totals.get("carbs", 0) * 4
    fat_cal = totals.get("fat", 0) * 9
    total_cal = protein_cal + carbs_cal + fat_cal

    if total_cal == 0:
        return {"protein_pct": 0, "carbs_pct": 0, "fat_pct": 0}

    return {
        "protein_pct": round(protein_cal / total_cal * 100, 1),
        "carbs_pct": round(carbs_cal / total_cal * 100, 1),
        "fat_pct": round(fat_cal / total_cal * 100, 1),
    }
