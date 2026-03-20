"""
Chart rendering utilities for the NutriLens dashboard.
Uses Altair (built into Streamlit) for visualization.
"""

import altair as alt
import pandas as pd
from datetime import datetime
from typing import Optional


def render_macro_chart(totals: dict) -> Optional[alt.Chart]:
    """
    Render a donut chart showing macro distribution.

    Args:
        totals: Dict with protein, carbs, fat values in grams

    Returns:
        Altair chart object or None
    """
    protein = totals.get("protein", 0)
    carbs = totals.get("carbs", 0)
    fat = totals.get("fat", 0)

    if protein + carbs + fat == 0:
        return None

    data = pd.DataFrame({
        "Macro": ["Protein", "Carbs", "Fat"],
        "Grams": [protein, carbs, fat],
        "Calories": [protein * 4, carbs * 4, fat * 9],
        "Color": ["#81d4fa", "#ce93d8", "#ef9a9a"],
    })

    chart = (
        alt.Chart(data)
        .mark_arc(innerRadius=50, outerRadius=90, cornerRadius=4)
        .encode(
            theta=alt.Theta("Calories:Q"),
            color=alt.Color(
                "Macro:N",
                scale=alt.Scale(
                    domain=["Protein", "Carbs", "Fat"],
                    range=["#81d4fa", "#ce93d8", "#ef9a9a"],
                ),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip("Macro:N"),
                alt.Tooltip("Grams:Q", format=".0f", title="Grams"),
                alt.Tooltip("Calories:Q", format=".0f", title="Calories"),
            ],
        )
        .properties(height=220)
        .configure_view(strokeWidth=0)
    )

    return chart


def render_calorie_timeline(meals: list) -> Optional[alt.Chart]:
    """
    Render a timeline of calorie intake throughout the day.

    Args:
        meals: List of meal entries (today only)

    Returns:
        Altair chart object or None
    """
    if len(meals) < 2:
        return None

    records = []
    cumulative = 0
    for meal in reversed(meals):  # oldest first
        cals = meal.get("data", {}).get("totals", {}).get("calories", 0)
        cumulative += cals
        try:
            ts = datetime.fromisoformat(meal["timestamp"])
            time_label = ts.strftime("%I:%M %p")
        except Exception:
            time_label = "?"

        records.append({
            "Time": time_label,
            "Meal": meal.get("meal_name", "Meal"),
            "Calories": cals,
            "Cumulative": cumulative,
            "order": len(records),
        })

    df = pd.DataFrame(records)

    bars = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=28)
        .encode(
            x=alt.X("order:O", axis=alt.Axis(title=None, labels=False, ticks=False)),
            y=alt.Y("Calories:Q", title="Calories"),
            color=alt.value("#4a7c59"),
            tooltip=[
                alt.Tooltip("Meal:N"),
                alt.Tooltip("Time:N"),
                alt.Tooltip("Calories:Q"),
            ],
        )
    )

    text = (
        alt.Chart(df)
        .mark_text(dy=-12, fontSize=11, fontWeight="bold", color="#c8f7c5")
        .encode(
            x=alt.X("order:O"),
            y=alt.Y("Calories:Q"),
            text=alt.Text("Calories:Q", format=".0f"),
        )
    )

    labels = (
        alt.Chart(df)
        .mark_text(dy=16, fontSize=10, color="#888")
        .encode(
            x=alt.X("order:O"),
            y=alt.value(0),
            text="Time:N",
        )
    )

    chart = (
        (bars + text + labels)
        .properties(height=220)
        .configure_view(strokeWidth=0)
        .configure_axis(grid=False)
    )

    return chart
