"""
Chart rendering — blue/white theme.
"""

import altair as alt
import pandas as pd
from datetime import datetime
from typing import Optional


def render_macro_chart(totals: dict) -> Optional[alt.Chart]:
    protein = totals.get("protein", 0)
    carbs = totals.get("carbs", 0)
    fat = totals.get("fat", 0)
    if protein + carbs + fat == 0:
        return None

    data = pd.DataFrame({
        "Macro": ["Protein", "Carbs", "Fat"],
        "Grams": [protein, carbs, fat],
        "Calories": [protein * 4, carbs * 4, fat * 9],
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
                    range=["#2563eb", "#8b5cf6", "#f59e0b"],
                ),
                legend=alt.Legend(title=None, orient="bottom", labelColor="#64748b"),
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
    if len(meals) < 2:
        return None

    records = []
    for meal in reversed(meals):
        cals = meal.get("data", {}).get("totals", {}).get("calories", 0)
        try:
            ts = datetime.fromisoformat(meal["timestamp"])
            time_label = ts.strftime("%I:%M %p")
        except Exception:
            time_label = "?"
        records.append({
            "Time": time_label,
            "Meal": meal.get("meal_name", "Meal"),
            "Calories": cals,
            "order": len(records),
        })

    df = pd.DataFrame(records)

    bars = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, size=32)
        .encode(
            x=alt.X("order:O", axis=alt.Axis(title=None, labels=False, ticks=False)),
            y=alt.Y("Calories:Q", title="Calories"),
            color=alt.value("#2563eb"),
            tooltip=[alt.Tooltip("Meal:N"), alt.Tooltip("Time:N"), alt.Tooltip("Calories:Q")],
        )
    )

    text = (
        alt.Chart(df)
        .mark_text(dy=-14, fontSize=12, fontWeight="bold", color="#1e293b")
        .encode(x=alt.X("order:O"), y=alt.Y("Calories:Q"), text=alt.Text("Calories:Q", format=".0f"))
    )

    labels = (
        alt.Chart(df)
        .mark_text(dy=18, fontSize=10, color="#94a3b8")
        .encode(x=alt.X("order:O"), y=alt.value(0), text="Time:N")
    )

    return (
        (bars + text + labels)
        .properties(height=240)
        .configure_view(strokeWidth=0)
        .configure_axis(grid=False)
    )
