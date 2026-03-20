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

# ─── Modern Warm UI ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ── */
    .stApp {
        background: #faf9f7 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    #MainMenu {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent !important;}
    .block-container {padding-top: 1.5rem !important; max-width: 1200px !important;}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #f0ebe4 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stMarkdown h4,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] .stMarkdown strong,
    section[data-testid="stSidebar"] label {
        color: #3d3229 !important;
    }
    section[data-testid="stSidebar"] .stCaption p { color: #9a8e82 !important; }

    /* ── Hero ── */
    .hero-bar {
        background: linear-gradient(135deg, #2d2118 0%, #4a3728 60%, #5c3d1e 100%);
        border-radius: 20px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 24px rgba(45, 33, 24, 0.12);
        position: relative;
        overflow: hidden;
    }
    .hero-bar::before {
        content: '';
        position: absolute;
        top: -50%; right: -20%;
        width: 60%; height: 200%;
        background: radial-gradient(ellipse, rgba(255,180,80,0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-left { position: relative; z-index: 1; }
    .hero-brand {
        display: flex; align-items: center; gap: 12px; margin-bottom: 6px;
    }
    .hero-icon {
        width: 44px; height: 44px;
        background: linear-gradient(135deg, #ff9f43, #f0932b);
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.4rem;
        box-shadow: 0 3px 12px rgba(255, 159, 67, 0.3);
    }
    .hero-title {
        font-size: 1.8rem; font-weight: 800; color: #ffffff;
        letter-spacing: -0.02em; margin: 0;
    }
    .hero-sub {
        color: rgba(255,255,255,0.5); font-size: 0.85rem;
        font-weight: 400; letter-spacing: 0.02em;
    }
    .hero-right {
        display: flex; gap: 2rem; position: relative; z-index: 1;
    }
    .hero-stat { text-align: center; }
    .hero-stat-val {
        font-size: 1.6rem; font-weight: 800; color: #ff9f43;
        line-height: 1.2;
    }
    .hero-stat-lbl {
        font-size: 0.65rem; font-weight: 600; color: rgba(255,255,255,0.4);
        text-transform: uppercase; letter-spacing: 0.1em;
    }

    /* ── Cards ── */
    .card {
        background: #ffffff;
        border: 1px solid #f0ebe4;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }

    /* ── Stat Cards ── */
    .stat-grid {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 12px; margin: 1rem 0;
    }
    .stat-card {
        background: #ffffff; border: 1px solid #f0ebe4;
        border-radius: 16px; padding: 18px 16px; text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    }
    .stat-icon { font-size: 1.4rem; margin-bottom: 6px; }
    .stat-value {
        font-size: 1.7rem; font-weight: 800;
        letter-spacing: -0.02em; line-height: 1.2;
    }
    .stat-label {
        font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.08em; color: #9a8e82; margin-top: 4px;
    }
    .stat-cal .stat-value { color: #f0932b; }
    .stat-pro .stat-value { color: #0984e3; }
    .stat-carb .stat-value { color: #6c5ce7; }
    .stat-fat .stat-value { color: #e17055; }

    /* ── Food Items ── */
    .food-item {
        display: flex; align-items: center; gap: 14px;
        padding: 14px 16px; background: #faf9f7;
        border: 1px solid #f0ebe4; border-radius: 14px;
        margin-bottom: 8px; transition: all 0.15s ease;
    }
    .food-item:hover {
        background: #f5f0eb;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .food-emoji { font-size: 1.5rem; }
    .food-details { flex: 1; min-width: 0; }
    .food-name { font-weight: 600; font-size: 0.95rem; color: #2d2118; }
    .food-portion { font-size: 0.78rem; color: #9a8e82; margin-top: 2px; }
    .food-macros {
        display: flex; gap: 8px; margin-top: 4px;
    }
    .food-macro-tag {
        font-size: 0.65rem; font-weight: 600; padding: 2px 8px;
        border-radius: 6px; letter-spacing: 0.02em;
    }
    .tag-p { background: #e8f4fd; color: #0984e3; }
    .tag-c { background: #f0ecff; color: #6c5ce7; }
    .tag-f { background: #fef0ec; color: #e17055; }
    .food-cals {
        font-weight: 800; font-size: 1rem; color: #f0932b;
        white-space: nowrap;
    }
    .food-cals-unit {
        font-size: 0.7rem; font-weight: 500; color: #9a8e82;
    }

    /* ── Micro Chips ── */
    .micro-chip {
        display: inline-block; background: #faf5f0; color: #8b6914;
        padding: 6px 14px; border-radius: 20px; font-size: 0.78rem;
        font-weight: 500; margin: 3px; border: 1px solid #f0e4d0;
    }

    /* ── Upload Zone ── */
    div[data-testid="stFileUploader"] {
        border: 2px dashed #ddd5ca; border-radius: 16px;
        padding: 0.5rem; background: #fdfcfa;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #f0932b; background: #fef9f3;
    }

    /* ── Primary Button ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ff9f43 0%, #f0932b 100%) !important;
        color: white !important; border: none !important;
        border-radius: 14px !important; padding: 0.7rem 1.5rem !important;
        font-weight: 700 !important; font-size: 0.95rem !important;
        box-shadow: 0 3px 12px rgba(240, 147, 43, 0.3) !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.01em !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(240, 147, 43, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button {
        border-radius: 12px !important; font-weight: 600 !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px; background: #ffffff; border-radius: 14px;
        padding: 5px; border: 1px solid #f0ebe4;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px; padding: 10px 28px;
        font-weight: 600; color: #9a8e82; font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2d2118, #4a3728) !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }

    /* ── Metrics ── */
    div[data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #f0ebe4;
        border-radius: 14px; padding: 16px;
    }
    div[data-testid="stMetric"] label {
        color: #9a8e82 !important; font-weight: 600 !important;
        font-size: 0.72rem !important; text-transform: uppercase !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #2d2118 !important; font-weight: 700 !important;
    }

    /* ── Inputs ── */
    .stTextInput input {
        border-radius: 12px !important; border-color: #e5ddd4 !important;
        background: #ffffff !important; color: #2d2118 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .stTextInput input:focus {
        border-color: #f0932b !important;
        box-shadow: 0 0 0 3px rgba(240, 147, 43, 0.12) !important;
    }

    /* ── Text Colors ── */
    .stMarkdown p, .stMarkdown li, .stMarkdown span,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown h5 { color: #2d2118 !important; }
    .stCaption p { color: #9a8e82 !important; }
    .stSlider label { color: #2d2118 !important; }
    .stSelectbox label { color: #2d2118 !important; }
    .stTextInput label { color: #2d2118 !important; }

    /* ── Sidebar History ── */
    .history-item {
        padding: 10px 14px; background: #faf9f7;
        border: 1px solid #f0ebe4; border-radius: 12px;
        margin-bottom: 6px; color: #3d3229;
    }
    .history-item strong { color: #2d2118; }
    .history-cal { color: #f0932b; font-weight: 700; }

    .daily-summary {
        background: linear-gradient(135deg, #fff8ed, #fff3e0);
        border: 1px solid #fde5c0; border-radius: 16px;
        padding: 1.25rem; text-align: center;
    }
    .daily-cal { font-size: 2.2rem; font-weight: 800; color: #f0932b; line-height: 1.1; }
    .daily-label {
        font-size: 0.7rem; font-weight: 600; color: #c47f17;
        text-transform: uppercase; letter-spacing: 0.1em;
    }

    /* ── Section Title ── */
    .section-title {
        font-size: 1rem; font-weight: 700; color: #2d2118;
        margin: 1.5rem 0 0.75rem; display: flex;
        align-items: center; gap: 8px;
    }

    /* ── Tip Box ── */
    .tip-box {
        background: #fff8ed; border: 1px solid #fde5c0;
        border-left: 4px solid #f0932b; border-radius: 12px;
        padding: 14px 18px; margin-top: 12px;
        font-size: 0.88rem; color: #8b6914;
    }

    /* ── Health Score ── */
    .health-score {
        background: linear-gradient(135deg, #2d2118, #4a3728);
        border-radius: 16px; padding: 20px; text-align: center;
        margin: 1rem 0;
    }
    .health-score-val {
        font-size: 2.8rem; font-weight: 800; color: #ff9f43;
        line-height: 1;
    }
    .health-score-label {
        font-size: 0.72rem; font-weight: 600; color: rgba(255,255,255,0.5);
        text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px;
    }
    .health-score-desc {
        font-size: 0.82rem; color: rgba(255,255,255,0.7);
        margin-top: 8px;
    }

    /* ── Empty State ── */
    .empty-state { text-align: center; padding: 3.5rem 2rem; }
    .empty-state-icon { font-size: 3.5rem; margin-bottom: 1rem; opacity: 0.4; }
    .empty-state p { font-size: 0.95rem; color: #9a8e82; }

    .app-footer {
        text-align: center; padding: 2rem 0 1rem;
        font-size: 0.75rem; color: #c4b8aa;
    }

    /* ── Responsive ── */
    @media (max-width: 768px) {
        .stat-grid { grid-template-columns: repeat(2, 1fr); }
        .hero-bar { flex-direction: column; text-align: center; gap: 1rem; }
        .hero-right { justify-content: center; }
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
    """Convert uploaded image to base64 — handles PNG (RGBA), JPEG, WebP."""
    img = Image.open(uploaded_file)
    # Convert RGBA/P mode to RGB (JPEG doesn't support transparency)
    if img.mode in ("RGBA", "P", "LA", "PA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")
    # Resize if too large
    max_size = 1024
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def calculate_health_score(result: dict) -> tuple:
    """Calculate a simple health score based on macro balance."""
    totals = result.get("totals", {})
    cal = totals.get("calories", 0)
    protein = totals.get("protein", 0)
    carbs = totals.get("carbs", 0)
    fat = totals.get("fat", 0)
    if cal == 0:
        return 0, "No data"
    protein_cal = protein * 4
    carbs_cal = carbs * 4
    fat_cal = fat * 9
    total_macro_cal = protein_cal + carbs_cal + fat_cal
    if total_macro_cal == 0:
        return 50, "Balanced"
    p_pct = protein_cal / total_macro_cal * 100
    c_pct = carbs_cal / total_macro_cal * 100
    f_pct = fat_cal / total_macro_cal * 100
    # Score: balanced = higher, extreme = lower
    score = 100
    if p_pct < 10:
        score -= 20
    elif p_pct > 40:
        score -= 10
    if f_pct > 45:
        score -= 20
    elif f_pct > 35:
        score -= 10
    if c_pct > 70:
        score -= 15
    items = len(result.get("foods", []))
    if items >= 4:
        score += 5  # variety bonus
    score = max(20, min(100, score))
    if score >= 80:
        desc = "Well-balanced meal with good macro distribution"
    elif score >= 60:
        desc = "Decent balance — could use more protein or fiber"
    else:
        desc = "Consider adding more protein or reducing fat/carbs"
    return score, desc


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

# ─── Hero Header ───
today_meals_count = 0
today_calories = 0
if st.session_state.meal_history:
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_items = [m for m in st.session_state.meal_history if m["timestamp"].startswith(today_str)]
    today_meals_count = len(today_items)
    today_calories = sum(m.get("data", {}).get("totals", {}).get("calories", 0) for m in today_items)

st.markdown(f"""
<div class="hero-bar">
    <div class="hero-left">
        <div class="hero-brand">
            <div class="hero-icon">🥗</div>
            <h1 class="hero-title">NutriLens</h1>
        </div>
        <p class="hero-sub">AI-Powered Food Calorie Tracker</p>
    </div>
    <div class="hero-right">
        <div class="hero-stat">
            <div class="hero-stat-val">{today_meals_count}</div>
            <div class="hero-stat-lbl">Meals Today</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-val">{today_calories}</div>
            <div class="hero-stat-lbl">Kcal Today</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-val">{len(st.session_state.meal_history)}</div>
            <div class="hero-stat-lbl">Total Logged</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ───
with st.sidebar:
    st.markdown("#### ⚙️ Settings")

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
        format_func=lambda x: "⚡ Llama 4 Scout (Fast)" if "scout" in x else "🧠 Llama 4 Maverick (Accurate)",
    )

    st.divider()

    if st.session_state.meal_history:
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_meals = [m for m in st.session_state.meal_history if m["timestamp"].startswith(today_str)]
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
                <br><span style="font-size:0.72rem; color:#9a8e82;">{ts}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No meals tracked yet.")

    st.divider()
    st.markdown(
        '<p style="text-align:center; font-size:0.7rem; color:#c4b8aa;">'
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

        meal_name = st.text_input("Meal Name (optional)", placeholder="e.g., Lunch, Breakfast, Dinner...")

        portion_size = st.select_slider("Portion Size", options=["Small", "Regular", "Large"], value="Regular")

        analyze_btn = st.button(
            "🔍  Analyze Meal",
            type="primary",
            use_container_width=True,
            disabled=not uploaded_file or not groq_api_key,
        )

        if not groq_api_key:
            st.warning("Open the sidebar and enter your Groq API key to start.")
            st.markdown("Get a **free** key at [console.groq.com](https://console.groq.com)")

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

            # Health Score
            score, desc = calculate_health_score(result)
            st.markdown(f"""
            <div class="health-score">
                <div class="health-score-val">{score}/100</div>
                <div class="health-score-label">Meal Health Score</div>
                <div class="health-score-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

            # Macro Chart
            macro_chart = render_macro_chart(totals)
            if macro_chart:
                st.altair_chart(macro_chart, use_container_width=True)

            # Food Items with per-item macros
            foods = result.get("foods", [])
            if foods:
                st.markdown('<div class="section-title">🍽️ Detected Items</div>', unsafe_allow_html=True)
                for food in foods:
                    p = food.get('protein', '?')
                    c = food.get('carbs', '?')
                    f = food.get('fat', '?')
                    st.markdown(f"""
                    <div class="food-item">
                        <span class="food-emoji">{food.get('emoji', '🍽️')}</span>
                        <div class="food-details">
                            <div class="food-name">{food.get('name', 'Unknown')}</div>
                            <div class="food-portion">{food.get('portion', '1 serving')}</div>
                            <div class="food-macros">
                                <span class="food-macro-tag tag-p">P: {p}g</span>
                                <span class="food-macro-tag tag-c">C: {c}g</span>
                                <span class="food-macro-tag tag-f">F: {f}g</span>
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div class="food-cals">{food.get('calories', '?')}</div>
                            <div class="food-cals-unit">kcal</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Micronutrients
            micros = result.get("micronutrients", [])
            if micros:
                st.markdown('<div class="section-title">💊 Key Micronutrients</div>', unsafe_allow_html=True)
                chips = "".join(f'<span class="micro-chip">{m["name"]}: {m["amount"]}</span>' for m in micros)
                st.markdown(chips, unsafe_allow_html=True)

            # Tip
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
        today_meals = [m for m in st.session_state.meal_history if m["timestamp"].startswith(today_str)]
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
