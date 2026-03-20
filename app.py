"""
🥗 NutriLens - AI-Powered Food Calorie Tracker
Built with Streamlit + Groq (Llama 4 Scout Vision Model)
"""

import streamlit as st
import json
import base64
from datetime import datetime
from io import BytesIO
from PIL import Image

from utils.groq_client import analyze_food_image
from utils.nutrition import parse_nutrition_response, calculate_daily_totals
from utils.charts import render_macro_chart, render_calorie_timeline

# ─── Page Config ───
st.set_page_config(
    page_title="NutriLens - AI Food Calorie Tracker",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700&display=swap');

    .stApp {
        font-family: 'DM Sans', sans-serif;
    }

    .main-header {
        text-align: center;
        padding: 1.5rem 0 1rem;
    }

    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .main-header p {
        opacity: 0.5;
        font-size: 0.95rem;
        letter-spacing: 0.05em;
    }

    .nutrition-card {
        background: linear-gradient(135deg, #1a2f23 0%, #0f1f17 100%);
        border: 1px solid rgba(200, 247, 197, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.75rem 0;
    }

    .food-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.05);
    }

    .food-emoji { font-size: 1.4rem; }

    .food-name {
        flex: 1;
        font-weight: 500;
        font-size: 0.95rem;
    }

    .food-portion {
        font-size: 0.75rem;
        opacity: 0.4;
    }

    .food-calories {
        font-weight: 700;
        color: #f0c674;
        font-size: 0.95rem;
    }

    .macro-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 4px;
    }

    .micro-chip {
        display: inline-block;
        background: rgba(200, 247, 197, 0.08);
        color: #c8f7c5;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        margin: 3px;
    }

    .daily-summary {
        background: linear-gradient(135deg, #2d1f00 0%, #1a1200 100%);
        border: 1px solid rgba(240, 198, 116, 0.15);
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
    }

    .daily-cal {
        font-size: 2.5rem;
        font-weight: 700;
        color: #f0c674;
    }

    .daily-label {
        font-size: 0.8rem;
        opacity: 0.4;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    div[data-testid="stFileUploader"] {
        border: 2px dashed rgba(200, 247, 197, 0.15);
        border-radius: 16px;
        padding: 0.5rem;
    }

    .history-item {
        padding: 10px 14px;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
        margin-bottom: 8px;
    }

    .stButton > button {
        border-radius: 12px;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ───
if "meal_history" not in st.session_state:
    st.session_state.meal_history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False


def image_to_base64(uploaded_file) -> str:
    """Convert uploaded image to base64 string."""
    img = Image.open(uploaded_file)
    # Resize if too large (Groq has size limits)
    max_size = 1024
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def add_to_history(meal_name: str, result: dict):
    """Add analyzed meal to session history."""
    entry = {
        "meal_name": meal_name or "Unnamed meal",
        "timestamp": datetime.now().isoformat(),
        "data": result,
    }
    st.session_state.meal_history.insert(0, entry)
    # Keep last 50 entries
    st.session_state.meal_history = st.session_state.meal_history[:50]


# ─── Header ───
st.markdown("""
<div class="main-header">
    <h1>🥗 NutriLens</h1>
    <p>AI-Powered Food Calorie Tracker &middot; Snap, Analyze, Track</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ───
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    groq_api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Get your free API key at https://console.groq.com",
    )

    st.divider()

    model_choice = st.selectbox(
        "Vision Model",
        [
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
        ],
        index=0,
        help="Llama 4 Scout is fast & free. Maverick is more capable.",
    )

    st.divider()

    # ─── Daily Summary in Sidebar ───
    if st.session_state.meal_history:
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_meals = [
            m for m in st.session_state.meal_history
            if m["timestamp"].startswith(today_str)
        ]
        totals = calculate_daily_totals(today_meals)

        st.markdown(f"""
        <div class="daily-summary">
            <div class="daily-label">Today's Intake</div>
            <div class="daily-cal">{totals['calories']}</div>
            <div class="daily-label">kcal</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Protein", f"{totals['protein']}g")
        col2.metric("Carbs", f"{totals['carbs']}g")
        col3.metric("Fat", f"{totals['fat']}g")

        st.divider()

    # ─── History ───
    st.markdown("### 📋 Meal History")
    if st.session_state.meal_history:
        if st.button("🗑️ Clear All History", use_container_width=True):
            st.session_state.meal_history = []
            st.rerun()

        for i, entry in enumerate(st.session_state.meal_history[:15]):
            cals = entry["data"].get("totals", {}).get("calories", "?")
            ts = datetime.fromisoformat(entry["timestamp"]).strftime("%b %d, %I:%M %p")
            st.markdown(f"""
            <div class="history-item">
                <strong>{entry['meal_name']}</strong>
                <span style="float:right; color:#f0c674; font-weight:700;">{cals} kcal</span>
                <br><span style="font-size:0.75rem; opacity:0.35;">{ts}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No meals tracked yet. Upload a photo to get started!")

    st.divider()
    st.markdown(
        "<p style='text-align:center; font-size:0.7rem; opacity:0.3;'>"
        "NutriLens v1.0 • Powered by Groq + Llama 4 Vision</p>",
        unsafe_allow_html=True,
    )


# ─── Main Content ───
tab1, tab2 = st.tabs(["📸 Analyze Meal", "📊 Dashboard"])

with tab1:
    col_input, col_result = st.columns([1, 1], gap="large")

    with col_input:
        st.markdown("#### Upload Your Meal Photo")

        uploaded_file = st.file_uploader(
            "Drop a meal photo here",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
        )

        if uploaded_file:
            st.image(uploaded_file, use_container_width=True)

        meal_name = st.text_input(
            "Meal Name (optional)",
            placeholder="e.g., Lunch, Post-workout snack...",
        )

        portion_size = st.select_slider(
            "Portion Size",
            options=["Small", "Regular", "Large"],
            value="Regular",
        )

        analyze_btn = st.button(
            "🔍 Analyze Meal",
            type="primary",
            use_container_width=True,
            disabled=not uploaded_file or not groq_api_key,
        )

        if not groq_api_key:
            st.info("👈 Enter your **free** Groq API key in the sidebar to get started.")
            st.markdown(
                "Get one at [console.groq.com](https://console.groq.com) → "
                "it's free with generous rate limits."
            )

        if analyze_btn and uploaded_file and groq_api_key:
            with st.spinner("🧠 Analyzing your meal..."):
                try:
                    img_b64 = image_to_base64(uploaded_file)
                    raw_response = analyze_food_image(
                        api_key=groq_api_key,
                        image_base64=img_b64,
                        model=model_choice,
                        meal_name=meal_name,
                        portion_size=portion_size.lower(),
                    )
                    result = parse_nutrition_response(raw_response)

                    if result and "error" not in result:
                        st.session_state.current_result = result
                        st.session_state.analysis_done = True
                        add_to_history(meal_name, result)
                        st.rerun()
                    elif result and "error" in result:
                        st.error(f"⚠️ {result['error']}")
                    else:
                        st.error("Could not parse the nutritional analysis. Please try again.")

                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with col_result:
        result = st.session_state.current_result

        if result:
            st.markdown("#### 📊 Nutritional Breakdown")

            # ─── Totals ───
            totals = result.get("totals", {})
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🔥 Calories", f"{totals.get('calories', 0)} kcal")
            c2.metric("🥩 Protein", f"{totals.get('protein', 0)}g")
            c3.metric("🍞 Carbs", f"{totals.get('carbs', 0)}g")
            c4.metric("🧈 Fat", f"{totals.get('fat', 0)}g")

            # ─── Macro Chart ───
            macro_chart = render_macro_chart(totals)
            if macro_chart:
                st.altair_chart(macro_chart, use_container_width=True)

            # ─── Food Items ───
            foods = result.get("foods", [])
            if foods:
                st.markdown("##### 🍽️ Detected Items")
                for food in foods:
                    st.markdown(f"""
                    <div class="food-item">
                        <span class="food-emoji">{food.get('emoji', '🍽️')}</span>
                        <div style="flex:1;">
                            <div class="food-name">{food.get('name', 'Unknown')}</div>
                            <div class="food-portion">{food.get('portion', '1 serving')}</div>
                        </div>
                        <div>
                            <span class="food-calories">{food.get('calories', '?')} kcal</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # ─── Micronutrients ───
            micros = result.get("micronutrients", [])
            if micros:
                st.markdown("##### 💊 Key Micronutrients")
                chips_html = ""
                for m in micros:
                    chips_html += f'<span class="micro-chip">{m["name"]}: {m["amount"]}</span>'
                st.markdown(chips_html, unsafe_allow_html=True)

            # ─── Notes ───
            notes = result.get("notes", "")
            if notes:
                st.info(f"💡 **Tip:** {notes}")

        else:
            st.markdown(
                "<div style='text-align:center; padding:4rem 2rem; opacity:0.3;'>"
                "<div style='font-size:4rem; margin-bottom:1rem;'>📸</div>"
                "<p>Upload a meal photo and click <strong>Analyze</strong> to see results here</p>"
                "</div>",
                unsafe_allow_html=True,
            )


with tab2:
    st.markdown("#### 📊 Daily Dashboard")

    if not st.session_state.meal_history:
        st.info("Start tracking meals to see your dashboard here!")
    else:
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_meals = [
            m for m in st.session_state.meal_history
            if m["timestamp"].startswith(today_str)
        ]
        totals = calculate_daily_totals(today_meals)

        # ─── Daily overview ───
        st.markdown("##### Today's Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Calories", f"{totals['calories']} kcal")
        c2.metric("Total Protein", f"{totals['protein']}g")
        c3.metric("Total Carbs", f"{totals['carbs']}g")
        c4.metric("Total Fat", f"{totals['fat']}g")

        # ─── Calorie timeline ───
        if len(today_meals) >= 2:
            st.markdown("##### Calorie Timeline")
            timeline_chart = render_calorie_timeline(today_meals)
            if timeline_chart:
                st.altair_chart(timeline_chart, use_container_width=True)

        # ─── Meal breakdown table ───
        st.markdown("##### Meal Breakdown")
        for entry in today_meals:
            data = entry["data"]
            t = data.get("totals", {})
            ts = datetime.fromisoformat(entry["timestamp"]).strftime("%I:%M %p")
            with st.expander(f"🍽️ {entry['meal_name']}  —  {t.get('calories', '?')} kcal  ({ts})"):
                for food in data.get("foods", []):
                    st.write(
                        f"{food.get('emoji', '🍽️')} **{food.get('name')}** "
                        f"— {food.get('calories')} kcal "
                        f"({food.get('portion', '')})"
                    )

        # ─── All-time stats ───
        all_totals = calculate_daily_totals(st.session_state.meal_history)
        st.divider()
        st.markdown("##### All-Time Stats")
        c1, c2, c3 = st.columns(3)
        c1.metric("Meals Tracked", len(st.session_state.meal_history))
        c2.metric("Total Calories Logged", f"{all_totals['calories']} kcal")
        c3.metric("Avg Cal / Meal", f"{all_totals['calories'] // max(len(st.session_state.meal_history), 1)} kcal")
