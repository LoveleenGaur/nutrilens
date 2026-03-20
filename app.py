"""
🥗 NutriLens - AI-Powered Food Calorie Tracker
Built with Streamlit + Groq (Llama 4 Scout Vision Model)
"""

import streamlit as st
import json
import base64
import os
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
    initial_sidebar_state="collapsed",
)

# ─── Professional Light Theme CSS ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');

    /* ── Global ── */
    .stApp {
        background: linear-gradient(160deg, #f8faf9 0%, #eef5f1 40%, #f5f0eb 100%) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    #MainMenu {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent !important;}
    .block-container {padding-top: 2rem !important; max-width: 1200px !important;}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e8ece9 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stMarkdown h4,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] .stMarkdown strong,
    section[data-testid="stSidebar"] label {
        color: #2d3b33 !important;
    }
    section[data-testid="stSidebar"] .stCaption p { color: #8a9a90 !important; }

    /* ── Hero ── */
    .hero-header { text-align: center; padding: 1rem 0 2rem; }
    .hero-logo {
        display: inline-flex; align-items: center; gap: 14px; margin-bottom: 8px;
    }
    .hero-logo-icon {
        width: 52px; height: 52px;
        background: linear-gradient(135deg, #34a853, #2d8f48);
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.6rem;
        box-shadow: 0 4px 16px rgba(52, 168, 83, 0.2);
    }
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 2.4rem; font-weight: 700; color: #1a2e22;
        letter-spacing: -0.02em; margin: 0;
    }
    .hero-subtitle {
        color: #7a8f82; font-size: 0.95rem; font-weight: 400;
        letter-spacing: 0.03em; margin-top: 2px;
    }

    /* ── Stat Cards ── */
    .stat-grid {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 12px; margin: 1rem 0;
    }
    .stat-card {
        background: #ffffff; border: 1px solid #e4ebe7;
        border-radius: 14px; padding: 16px 18px; text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.02);
    }
    .stat-icon { font-size: 1.3rem; margin-bottom: 4px; }
    .stat-value {
        font-size: 1.6rem; font-weight: 800;
        letter-spacing: -0.02em; line-height: 1.2;
    }
    .stat-label {
        font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.08em; color: #8a9a90; margin-top: 2px;
    }
    .stat-cal .stat-value { color: #e8850c; }
    .stat-pro .stat-value { color: #2563eb; }
    .stat-carb .stat-value { color: #9333ea; }
    .stat-fat .stat-value { color: #e11d48; }

    /* ── Food Items ── */
    .food-item {
        display: flex; align-items: center; gap: 14px;
        padding: 14px 16px; background: #f8faf9;
        border: 1px solid #edf1ee; border-radius: 12px;
        margin-bottom: 8px; transition: background 0.15s ease;
    }
    .food-item:hover { background: #f0f5f2; }
    .food-emoji { font-size: 1.5rem; }
    .food-details { flex: 1; min-width: 0; }
    .food-name { font-weight: 600; font-size: 0.95rem; color: #1a2e22; }
    .food-portion { font-size: 0.78rem; color: #8a9a90; margin-top: 1px; }
    .food-cals { font-weight: 700; font-size: 0.95rem; color: #e8850c; white-space: nowrap; }

    /* ── Micro Chips ── */
    .micro-chip {
        display: inline-block; background: #eef5f1; color: #2d6a3e;
        padding: 5px 12px; border-radius: 20px; font-size: 0.78rem;
        font-weight: 500; margin: 3px; border: 1px solid #d5e8da;
    }

    /* ── Upload Zone ── */
    div[data-testid="stFileUploader"] {
        border: 2px dashed #c8d9ce; border-radius: 16px;
        padding: 0.5rem; background: #f8faf9;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #34a853; background: #f2f8f4;
    }

    /* ── Primary Button ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #34a853 0%, #2d8f48 100%) !important;
        color: white !important; border: none !important;
        border-radius: 12px !important; padding: 0.65rem 1.5rem !important;
        font-weight: 600 !important; font-size: 0.95rem !important;
        box-shadow: 0 2px 8px rgba(52, 168, 83, 0.25) !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 16px rgba(52, 168, 83, 0.35) !important;
    }
    .stButton > button { border-radius: 10px !important; font-weight: 500 !important; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0; background: #ffffff; border-radius: 12px;
        padding: 4px; border: 1px solid #e4ebe7;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; padding: 8px 24px;
        font-weight: 500; color: #7a8f82;
    }
    .stTabs [aria-selected="true"] {
        background: #34a853 !important; color: white !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }

    /* ── Metrics ── */
    div[data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e4ebe7;
        border-radius: 12px; padding: 14px 16px;
    }
    div[data-testid="stMetric"] label {
        color: #7a8f82 !important; font-weight: 600 !important;
        font-size: 0.75rem !important; text-transform: uppercase !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #1a2e22 !important; font-weight: 700 !important;
    }

    /* ── Inputs ── */
    .stTextInput input {
        border-radius: 10px !important; border-color: #d5ddd8 !important;
        background: #ffffff !important; color: #1a2e22 !important;
    }
    .stTextInput input:focus {
        border-color: #34a853 !important;
        box-shadow: 0 0 0 2px rgba(52, 168, 83, 0.15) !important;
    }

    /* ── Text Colors ── */
    .stMarkdown p, .stMarkdown li, .stMarkdown span,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown h5 { color: #1a2e22 !important; }
    .stCaption p { color: #8a9a90 !important; }
    .stSlider label { color: #1a2e22 !important; }
    .stSelectbox label { color: #1a2e22 !important; }
    .stTextInput label { color: #1a2e22 !important; }

    /* ── Sidebar History ── */
    .history-item {
        padding: 10px 14px; background: #f8faf9;
        border: 1px solid #e8ece9; border-radius: 10px;
        margin-bottom: 6px; color: #2d3b33;
    }
    .history-item strong { color: #1a2e22; }
    .history-cal { color: #e8850c; font-weight: 700; }

    .daily-summary {
        background: linear-gradient(135deg, #fff8ed, #fff3e0);
        border: 1px solid #fde5c0; border-radius: 14px;
        padding: 1.25rem; text-align: center;
    }
    .daily-cal { font-size: 2.2rem; font-weight: 800; color: #e8850c; line-height: 1.1; }
    .daily-label {
        font-size: 0.72rem; font-weight: 600; color: #b8860b;
        text-transform: uppercase; letter-spacing: 0.1em;
    }

    /* ── Section Title ── */
    .section-title {
        font-size: 1.05rem; font-weight: 700; color: #1a2e22;
        margin: 1.5rem 0 0.75rem; display: flex; align-items: center; gap: 8px;
    }

    /* ── Tip Box ── */
    .tip-box {
        background: #f0f8f3; border: 1px solid #c8e6cf;
        border-left: 4px solid #34a853; border-radius: 10px;
        padding: 14px 18px; margin-top: 12px;
        font-size: 0.88rem; color: #2d6a3e;
    }

    /* ── Empty State ── */
    .empty-state { text-align: center; padding: 3.5rem 2rem; color: #8a9a90; }
    .empty-state-icon { font-size: 3.5rem; margin-bottom: 1rem; opacity: 0.5; }
    .empty-state p { font-size: 0.95rem; color: #8a9a90; }

    .app-footer {
        text-align: center; padding: 2rem 0 1rem;
        font-size: 0.75rem; color: #a3b3a9;
    }
</style>
""", unsafe_allow_html=True)


# ─── Session State ───
if "meal_history" not in st.session_state:
    st.session_state.meal_history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False


def get_api_key() -> str:
    """Get Groq API key: secrets → env → sidebar fallback."""
    try:
        return st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        return key
    return ""


def image_to_base64(uploaded_file) -> str:
    img = Image.open(uploaded_file)
    max_size = 1024
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def add_to_history(meal_name: str, result: dict):
    entry = {
        "meal_name": meal_name or "Unnamed meal",
        "timestamp": datetime.now().isoformat(),
        "data": result,
    }
    st.session_state.meal_history.insert(0, entry)
    st.session_state.meal_history = st.session_state.meal_history[:50]


# ─── Get API Key ───
groq_api_key = get_api_key()

# ─── Header ───
st.markdown("""
<div class="hero-header">
    <div class="hero-logo">
        <div class="hero-logo-icon">🥗</div>
        <h1 class="hero-title">NutriLens</h1>
    </div>
    <p class="hero-subtitle">AI-Powered Food Calorie Tracker &middot; Snap, Analyze, Track</p>
</div>
""", unsafe_allow_html=True)


# ─── Sidebar ───
with st.sidebar:
    st.markdown("#### ⚙️ Configuration")

    if not groq_api_key:
        groq_api_key = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
            help="Get your free API key at https://console.groq.com",
        )
        st.caption("Get a free key at [console.groq.com](https://console.groq.com)")
    else:
        st.success("API key loaded", icon="🔑")

    st.divider()

    model_choice = st.selectbox(
        "Vision Model",
        [
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
        ],
        index=0,
        format_func=lambda x: "Llama 4 Scout (Fast)" if "scout" in x else "Llama 4 Maverick (Accurate)",
    )

    st.divider()

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

    st.markdown("#### 📋 Meal History")
    if st.session_state.meal_history:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.meal_history = []
            st.rerun()

        for i, entry in enumerate(st.session_state.meal_history[:15]):
            cals = entry["data"].get("totals", {}).get("calories", "?")
            ts = datetime.fromisoformat(entry["timestamp"]).strftime("%b %d, %I:%M %p")
            st.markdown(f"""
            <div class="history-item">
                <strong>{entry['meal_name']}</strong>
                <span style="float:right;" class="history-cal">{cals} kcal</span>
                <br><span style="font-size:0.72rem; color:#8a9a90;">{ts}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No meals tracked yet.")

    st.divider()
    st.markdown(
        '<p style="text-align:center; font-size:0.7rem; color:#a3b3a9;">'
        'NutriLens v1.0 &middot; Powered by Groq + Llama 4</p>',
        unsafe_allow_html=True,
    )


# ─── Main Content ───
tab1, tab2 = st.tabs(["📸  Analyze Meal", "📊  Dashboard"])

with tab1:
    col_input, col_result = st.columns([1, 1], gap="large")

    with col_input:
        st.markdown('<div class="section-title">📷 Upload Your Meal Photo</div>', unsafe_allow_html=True)

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
            "🔍  Analyze Meal",
            type="primary",
            use_container_width=True,
            disabled=not uploaded_file or not groq_api_key,
        )

        if not groq_api_key:
            st.warning("Open the sidebar (top-left arrow) and enter your Groq API key.")
            st.markdown(
                "Get a **free** key at [console.groq.com](https://console.groq.com)"
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
                        st.error("Could not parse the analysis. Please try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with col_result:
        result = st.session_state.current_result

        if result:
            st.markdown('<div class="section-title">📊 Nutritional Breakdown</div>', unsafe_allow_html=True)

            totals = result.get("totals", {})
            st.markdown(f"""
            <div class="stat-grid">
                <div class="stat-card stat-cal">
                    <div class="stat-icon">🔥</div>
                    <div class="stat-value">{totals.get('calories', 0)}</div>
                    <div class="stat-label">Calories</div>
                </div>
                <div class="stat-card stat-pro">
                    <div class="stat-icon">🥩</div>
                    <div class="stat-value">{totals.get('protein', 0)}g</div>
                    <div class="stat-label">Protein</div>
                </div>
                <div class="stat-card stat-carb">
                    <div class="stat-icon">🌾</div>
                    <div class="stat-value">{totals.get('carbs', 0)}g</div>
                    <div class="stat-label">Carbs</div>
                </div>
                <div class="stat-card stat-fat">
                    <div class="stat-icon">🧈</div>
                    <div class="stat-value">{totals.get('fat', 0)}g</div>
                    <div class="stat-label">Fat</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            macro_chart = render_macro_chart(totals)
            if macro_chart:
                st.altair_chart(macro_chart, use_container_width=True)

            foods = result.get("foods", [])
            if foods:
                st.markdown('<div class="section-title">🍽️ Detected Items</div>', unsafe_allow_html=True)
                for food in foods:
                    st.markdown(f"""
                    <div class="food-item">
                        <span class="food-emoji">{food.get('emoji', '🍽️')}</span>
                        <div class="food-details">
                            <div class="food-name">{food.get('name', 'Unknown')}</div>
                            <div class="food-portion">{food.get('portion', '1 serving')}</div>
                        </div>
                        <div class="food-cals">{food.get('calories', '?')} kcal</div>
                    </div>
                    """, unsafe_allow_html=True)

            micros = result.get("micronutrients", [])
            if micros:
                st.markdown('<div class="section-title">💊 Key Micronutrients</div>', unsafe_allow_html=True)
                chips = "".join(f'<span class="micro-chip">{m["name"]}: {m["amount"]}</span>' for m in micros)
                st.markdown(chips, unsafe_allow_html=True)

            notes = result.get("notes", "")
            if notes:
                st.markdown(f'<div class="tip-box">💡 <strong>Tip:</strong> {notes}</div>', unsafe_allow_html=True)

        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📸</div>
                <p><strong>Upload a meal photo</strong> and click <strong>Analyze</strong><br>
                to see your nutritional breakdown here</p>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-title">📊 Daily Dashboard</div>', unsafe_allow_html=True)

    if not st.session_state.meal_history:
        st.info("Start tracking meals to see your dashboard here!")
    else:
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_meals = [
            m for m in st.session_state.meal_history
            if m["timestamp"].startswith(today_str)
        ]
        totals = calculate_daily_totals(today_meals)

        st.markdown(f"""
        <div class="stat-grid">
            <div class="stat-card stat-cal">
                <div class="stat-icon">🔥</div>
                <div class="stat-value">{totals['calories']}</div>
                <div class="stat-label">Total Calories</div>
            </div>
            <div class="stat-card stat-pro">
                <div class="stat-icon">🥩</div>
                <div class="stat-value">{totals['protein']}g</div>
                <div class="stat-label">Total Protein</div>
            </div>
            <div class="stat-card stat-carb">
                <div class="stat-icon">🌾</div>
                <div class="stat-value">{totals['carbs']}g</div>
                <div class="stat-label">Total Carbs</div>
            </div>
            <div class="stat-card stat-fat">
                <div class="stat-icon">🧈</div>
                <div class="stat-value">{totals['fat']}g</div>
                <div class="stat-label">Total Fat</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if len(today_meals) >= 2:
            st.markdown('<div class="section-title">⏱️ Calorie Timeline</div>', unsafe_allow_html=True)
            timeline_chart = render_calorie_timeline(today_meals)
            if timeline_chart:
                st.altair_chart(timeline_chart, use_container_width=True)

        st.markdown('<div class="section-title">🍽️ Meal Breakdown</div>', unsafe_allow_html=True)
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

        all_totals = calculate_daily_totals(st.session_state.meal_history)
        st.divider()
        st.markdown('<div class="section-title">📈 All-Time Stats</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Meals Tracked", len(st.session_state.meal_history))
        c2.metric("Total Calories", f"{all_totals['calories']} kcal")
        c3.metric("Avg Cal / Meal", f"{all_totals['calories'] // max(len(st.session_state.meal_history), 1)} kcal")

st.markdown("""
<div class="app-footer">
    Built with ❤️ using Streamlit + Groq &middot; Nutritional estimates are AI-generated approximations
</div>
""", unsafe_allow_html=True)
