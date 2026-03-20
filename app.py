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

# ─── Blue & White Professional UI ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ── */
    .stApp {
        background: #f8fafc !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    #MainMenu {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent !important;}
    .block-container {padding-top: 1.5rem !important; max-width: 1200px !important;}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stMarkdown h4,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] .stMarkdown strong,
    section[data-testid="stSidebar"] label {
        color: #1e293b !important;
    }
    section[data-testid="stSidebar"] .stCaption p { color: #94a3b8 !important; }

    /* ── Hero Bar ── */
    .hero-bar {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .hero-brand {
        display: flex; align-items: center; gap: 14px;
    }
    .hero-icon {
        width: 48px; height: 48px;
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.5rem;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
    }
    .hero-text h1 {
        font-size: 1.6rem; font-weight: 800; color: #1e293b;
        letter-spacing: -0.02em; margin: 0; line-height: 1.2;
    }
    .hero-text p {
        color: #94a3b8; font-size: 0.82rem;
        font-weight: 400; margin: 2px 0 0 0;
    }
    .hero-stats {
        display: flex; gap: 2rem;
    }
    .hero-stat { text-align: center; }
    .hero-stat-val {
        font-size: 1.5rem; font-weight: 800; color: #2563eb;
        line-height: 1.2;
    }
    .hero-stat-lbl {
        font-size: 0.62rem; font-weight: 600; color: #94a3b8;
        text-transform: uppercase; letter-spacing: 0.1em;
    }

    /* ── Stat Cards ── */
    .stat-grid {
        display: grid; grid-template-columns: repeat(4, 1fr);
        gap: 12px; margin: 1rem 0;
    }
    .stat-card {
        background: #ffffff; border: 1px solid #e2e8f0;
        border-radius: 14px; padding: 18px 16px; text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .stat-icon { font-size: 1.4rem; margin-bottom: 6px; }
    .stat-value {
        font-size: 1.7rem; font-weight: 800;
        letter-spacing: -0.02em; line-height: 1.2;
    }
    .stat-label {
        font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.08em; color: #94a3b8; margin-top: 4px;
    }
    .stat-cal .stat-value { color: #ea580c; }
    .stat-pro .stat-value { color: #2563eb; }
    .stat-carb .stat-value { color: #7c3aed; }
    .stat-fat .stat-value { color: #d97706; }

    /* ── Food Items ── */
    .food-item {
        display: flex; align-items: center; gap: 14px;
        padding: 14px 16px; background: #ffffff;
        border: 1px solid #e2e8f0; border-radius: 12px;
        margin-bottom: 8px; transition: all 0.15s ease;
    }
    .food-item:hover {
        border-color: #bfdbfe;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.06);
    }
    .food-emoji { font-size: 1.5rem; }
    .food-details { flex: 1; min-width: 0; }
    .food-name { font-weight: 600; font-size: 0.95rem; color: #1e293b; }
    .food-portion { font-size: 0.78rem; color: #94a3b8; margin-top: 2px; }
    .food-macros { display: flex; gap: 6px; margin-top: 5px; }
    .food-macro-tag {
        font-size: 0.65rem; font-weight: 600; padding: 2px 8px;
        border-radius: 6px; letter-spacing: 0.02em;
    }
    .tag-p { background: #eff6ff; color: #2563eb; }
    .tag-c { background: #f5f3ff; color: #7c3aed; }
    .tag-f { background: #fffbeb; color: #d97706; }
    .food-cals {
        font-weight: 800; font-size: 1rem; color: #ea580c;
        white-space: nowrap;
    }
    .food-cals-unit { font-size: 0.7rem; font-weight: 500; color: #94a3b8; }

    /* ── Micro Chips ── */
    .micro-chip {
        display: inline-block; background: #eff6ff; color: #1d4ed8;
        padding: 6px 14px; border-radius: 20px; font-size: 0.78rem;
        font-weight: 500; margin: 3px; border: 1px solid #dbeafe;
    }

    /* ── Upload Zone ── */
    div[data-testid="stFileUploader"] {
        border: 2px dashed #cbd5e1; border-radius: 16px;
        padding: 0.5rem; background: #ffffff;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #2563eb; background: #f8faff;
    }

    /* ── Primary Button ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important; border: none !important;
        border-radius: 12px !important; padding: 0.7rem 1.5rem !important;
        font-weight: 700 !important; font-size: 0.95rem !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.4) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button {
        border-radius: 10px !important; font-weight: 600 !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px; background: #ffffff; border-radius: 12px;
        padding: 4px; border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; padding: 10px 28px;
        font-weight: 600; color: #94a3b8; font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background: #2563eb !important; color: white !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }

    /* ── Metrics ── */
    div[data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e2e8f0;
        border-radius: 12px; padding: 16px;
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important; font-weight: 600 !important;
        font-size: 0.72rem !important; text-transform: uppercase !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #1e293b !important; font-weight: 700 !important;
    }

    /* ── Inputs ── */
    .stTextInput input {
        border-radius: 10px !important; border-color: #e2e8f0 !important;
        background: #ffffff !important; color: #1e293b !important;
    }
    .stTextInput input:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }

    /* ── Text Colors ── */
    .stMarkdown p, .stMarkdown li, .stMarkdown span,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown h5 { color: #1e293b !important; }
    .stCaption p { color: #94a3b8 !important; }
    .stSlider label, .stSelectbox label, .stTextInput label { color: #1e293b !important; }

    /* ── Health Score ── */
    .health-score {
        background: linear-gradient(135deg, #1e3a5f, #1e293b);
        border-radius: 14px; padding: 20px; text-align: center;
        margin: 1rem 0;
    }
    .health-score-val { font-size: 2.5rem; font-weight: 800; color: #60a5fa; line-height: 1; }
    .health-score-label {
        font-size: 0.7rem; font-weight: 600; color: rgba(255,255,255,0.5);
        text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px;
    }
    .health-score-desc { font-size: 0.82rem; color: rgba(255,255,255,0.7); margin-top: 8px; }

    /* ── Section Title ── */
    .section-title {
        font-size: 1rem; font-weight: 700; color: #1e293b;
        margin: 1.5rem 0 0.75rem; display: flex;
        align-items: center; gap: 8px;
    }

    /* ── Tip Box ── */
    .tip-box {
        background: #eff6ff; border: 1px solid #dbeafe;
        border-left: 4px solid #2563eb; border-radius: 10px;
        padding: 14px 18px; margin-top: 12px;
        font-size: 0.88rem; color: #1e40af;
    }

    /* ── Sidebar Items ── */
    .history-item {
        padding: 10px 14px; background: #f8fafc;
        border: 1px solid #e2e8f0; border-radius: 10px;
        margin-bottom: 6px; color: #1e293b;
    }
    .history-item strong { color: #1e293b; }
    .history-cal { color: #ea580c; font-weight: 700; }

    .daily-summary {
        background: linear-gradient(135deg, #eff6ff, #dbeafe);
        border: 1px solid #bfdbfe; border-radius: 14px;
        padding: 1.25rem; text-align: center;
    }
    .daily-cal { font-size: 2.2rem; font-weight: 800; color: #2563eb; line-height: 1.1; }
    .daily-label {
        font-size: 0.7rem; font-weight: 600; color: #3b82f6;
        text-transform: uppercase; letter-spacing: 0.1em;
    }

    /* ── Empty State ── */
    .empty-state { text-align: center; padding: 3.5rem 2rem; }
    .empty-state-icon { font-size: 3.5rem; margin-bottom: 1rem; opacity: 0.4; }
    .empty-state p { font-size: 0.95rem; color: #94a3b8; }

    .app-footer {
        text-align: center; padding: 2rem 0 1rem;
        font-size: 0.75rem; color: #cbd5e1;
    }

    @media (max-width: 768px) {
        .stat-grid { grid-template-columns: repeat(2, 1fr); }
        .hero-bar { flex-direction: column; text-align: center; gap: 1rem; }
        .hero-stats { justify-content: center; }
    }
</style>
""", unsafe_allow_html=True)


# ─── Session State ───
if "meal_history" not in st.session_state:
    st.session_state.meal_history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None


def get_api_key() -> str:
    try:
        return st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    key = os.environ.get("GROQ_API_KEY", "")
    return key if key else ""


def image_to_base64(uploaded_file) -> str:
    """Convert any image format to base64 JPEG — handles PNG/RGBA safely."""
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P", "LA", "PA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    max_size = 1024
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        img = img.resize((int(img.size[0] * ratio), int(img.size[1] * ratio)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def calc_health_score(result: dict) -> tuple:
    totals = result.get("totals", {})
    p, c, f = totals.get("protein", 0), totals.get("carbs", 0), totals.get("fat", 0)
    pc, cc, fc = p * 4, c * 4, f * 9
    total = pc + cc + fc
    if total == 0:
        return 50, "No macro data"
    pp, cp, fp = pc / total * 100, cc / total * 100, fc / total * 100
    score = 100
    if pp < 10: score -= 20
    elif pp > 40: score -= 10
    if fp > 45: score -= 20
    elif fp > 35: score -= 10
    if cp > 70: score -= 15
    if len(result.get("foods", [])) >= 4: score += 5
    score = max(20, min(100, score))
    if score >= 80: desc = "Well-balanced meal with good macro distribution"
    elif score >= 60: desc = "Decent balance — could use more protein or fiber"
    else: desc = "Consider adding more protein or reducing fat/carbs"
    return score, desc


def add_to_history(meal_name: str, result: dict):
    st.session_state.meal_history.insert(0, {
        "meal_name": meal_name or "Unnamed meal",
        "timestamp": datetime.now().isoformat(),
        "data": result,
    })
    st.session_state.meal_history = st.session_state.meal_history[:50]


groq_api_key = get_api_key()

# ─── Hero Bar ───
today_count, today_cals = 0, 0
if st.session_state.meal_history:
    td = datetime.now().strftime("%Y-%m-%d")
    ti = [m for m in st.session_state.meal_history if m["timestamp"].startswith(td)]
    today_count = len(ti)
    today_cals = sum(m.get("data", {}).get("totals", {}).get("calories", 0) for m in ti)

st.markdown(f"""
<div class="hero-bar">
    <div class="hero-brand">
        <div class="hero-icon">🥗</div>
        <div class="hero-text">
            <h1>NutriLens</h1>
            <p>AI-Powered Food Calorie Tracker</p>
        </div>
    </div>
    <div class="hero-stats">
        <div class="hero-stat">
            <div class="hero-stat-val">{today_count}</div>
            <div class="hero-stat-lbl">Meals Today</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-val">{today_cals}</div>
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
        groq_api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
        st.caption("Free key → [console.groq.com](https://console.groq.com)")
    else:
        st.success("API key loaded", icon="🔑")
    st.divider()
    model_choice = st.selectbox(
        "Vision Model",
        ["meta-llama/llama-4-scout-17b-16e-instruct", "meta-llama/llama-4-maverick-17b-128e-instruct"],
        index=0,
        format_func=lambda x: "⚡ Llama 4 Scout (Fast)" if "scout" in x else "🧠 Llama 4 Maverick (Accurate)",
    )
    st.divider()
    if st.session_state.meal_history:
        td = datetime.now().strftime("%Y-%m-%d")
        tm = [m for m in st.session_state.meal_history if m["timestamp"].startswith(td)]
        tots = calculate_daily_totals(tm)
        st.markdown(f"""
        <div class="daily-summary">
            <div class="daily-label">Today's Intake</div>
            <div class="daily-cal">{tots['calories']}</div>
            <div class="daily-label">kcal</div>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Protein", f"{tots['protein']}g")
        c2.metric("Carbs", f"{tots['carbs']}g")
        c3.metric("Fat", f"{tots['fat']}g")
        st.divider()
    st.markdown("#### 📋 Meal History")
    if st.session_state.meal_history:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.meal_history = []
            st.rerun()
        for entry in st.session_state.meal_history[:15]:
            cals = entry["data"].get("totals", {}).get("calories", "?")
            ts = datetime.fromisoformat(entry["timestamp"]).strftime("%b %d, %I:%M %p")
            st.markdown(f"""
            <div class="history-item">
                <strong>{entry['meal_name']}</strong>
                <span style="float:right;" class="history-cal">{cals} kcal</span>
                <br><span style="font-size:0.72rem; color:#94a3b8;">{ts}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No meals tracked yet.")
    st.divider()
    st.markdown('<p style="text-align:center; font-size:0.7rem; color:#cbd5e1;">NutriLens v1.0</p>', unsafe_allow_html=True)

# ─── Main ───
tab1, tab2 = st.tabs(["📸  Analyze Meal", "📊  Dashboard"])

with tab1:
    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.markdown('<div class="section-title">📷 Upload Your Meal Photo</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload", type=["jpg","jpeg","png","webp"], label_visibility="collapsed")
        if uploaded:
            st.image(uploaded, use_container_width=True)
        meal_name = st.text_input("Meal Name (optional)", placeholder="e.g., Lunch, Breakfast, Dinner...")
        portion = st.select_slider("Portion Size", options=["Small","Regular","Large"], value="Regular")
        btn = st.button("🔍  Analyze Meal", type="primary", use_container_width=True, disabled=not uploaded or not groq_api_key)

        if not groq_api_key:
            st.warning("Open sidebar → enter your free Groq API key to start.")

        if btn and uploaded and groq_api_key:
            with st.spinner("🧠 Analyzing your meal..."):
                try:
                    raw = analyze_food_image(
                        api_key=groq_api_key,
                        image_base64=image_to_base64(uploaded),
                        model=model_choice,
                        meal_name=meal_name,
                        portion_size=portion.lower(),
                    )
                    result = parse_nutrition_response(raw)
                    if result and "error" not in result:
                        st.session_state.current_result = result
                        add_to_history(meal_name, result)
                        st.rerun()
                    elif result and "error" in result:
                        st.error(f"⚠️ {result['error']}")
                    else:
                        st.error("Could not parse the analysis. Try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with col_out:
        result = st.session_state.current_result
        if result:
            st.markdown('<div class="section-title">📊 Nutritional Breakdown</div>', unsafe_allow_html=True)
            t = result.get("totals", {})
            st.markdown(f"""
            <div class="stat-grid">
                <div class="stat-card stat-cal"><div class="stat-icon">🔥</div><div class="stat-value">{t.get('calories',0)}</div><div class="stat-label">Calories</div></div>
                <div class="stat-card stat-pro"><div class="stat-icon">🥩</div><div class="stat-value">{t.get('protein',0)}g</div><div class="stat-label">Protein</div></div>
                <div class="stat-card stat-carb"><div class="stat-icon">🌾</div><div class="stat-value">{t.get('carbs',0)}g</div><div class="stat-label">Carbs</div></div>
                <div class="stat-card stat-fat"><div class="stat-icon">🧈</div><div class="stat-value">{t.get('fat',0)}g</div><div class="stat-label">Fat</div></div>
            </div>
            """, unsafe_allow_html=True)

            sc, desc = calc_health_score(result)
            st.markdown(f"""
            <div class="health-score">
                <div class="health-score-val">{sc}/100</div>
                <div class="health-score-label">Meal Health Score</div>
                <div class="health-score-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

            mc = render_macro_chart(t)
            if mc: st.altair_chart(mc, use_container_width=True)

            foods = result.get("foods", [])
            if foods:
                st.markdown('<div class="section-title">🍽️ Detected Items</div>', unsafe_allow_html=True)
                for fd in foods:
                    st.markdown(f"""
                    <div class="food-item">
                        <span class="food-emoji">{fd.get('emoji','🍽️')}</span>
                        <div class="food-details">
                            <div class="food-name">{fd.get('name','Unknown')}</div>
                            <div class="food-portion">{fd.get('portion','1 serving')}</div>
                            <div class="food-macros">
                                <span class="food-macro-tag tag-p">P: {fd.get('protein','?')}g</span>
                                <span class="food-macro-tag tag-c">C: {fd.get('carbs','?')}g</span>
                                <span class="food-macro-tag tag-f">F: {fd.get('fat','?')}g</span>
                            </div>
                        </div>
                        <div style="text-align:right;">
                            <div class="food-cals">{fd.get('calories','?')}</div>
                            <div class="food-cals-unit">kcal</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            micros = result.get("micronutrients", [])
            if micros:
                st.markdown('<div class="section-title">💊 Key Micronutrients</div>', unsafe_allow_html=True)
                st.markdown("".join(f'<span class="micro-chip">{m["name"]}: {m["amount"]}</span>' for m in micros), unsafe_allow_html=True)

            notes = result.get("notes", "")
            if notes:
                st.markdown(f'<div class="tip-box">💡 <strong>Tip:</strong> {notes}</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📸</div>
                <p><strong>Upload a meal photo</strong> and click <strong>Analyze</strong><br>to see your nutritional breakdown here</p>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="section-title">📊 Daily Dashboard</div>', unsafe_allow_html=True)
    if not st.session_state.meal_history:
        st.info("Start tracking meals to see your dashboard!")
    else:
        td = datetime.now().strftime("%Y-%m-%d")
        tm = [m for m in st.session_state.meal_history if m["timestamp"].startswith(td)]
        tots = calculate_daily_totals(tm)
        st.markdown(f"""
        <div class="stat-grid">
            <div class="stat-card stat-cal"><div class="stat-icon">🔥</div><div class="stat-value">{tots['calories']}</div><div class="stat-label">Total Calories</div></div>
            <div class="stat-card stat-pro"><div class="stat-icon">🥩</div><div class="stat-value">{tots['protein']}g</div><div class="stat-label">Total Protein</div></div>
            <div class="stat-card stat-carb"><div class="stat-icon">🌾</div><div class="stat-value">{tots['carbs']}g</div><div class="stat-label">Total Carbs</div></div>
            <div class="stat-card stat-fat"><div class="stat-icon">🧈</div><div class="stat-value">{tots['fat']}g</div><div class="stat-label">Total Fat</div></div>
        </div>
        """, unsafe_allow_html=True)
        if len(tm) >= 2:
            tl = render_calorie_timeline(tm)
            if tl: st.altair_chart(tl, use_container_width=True)
        st.markdown('<div class="section-title">🍽️ Meal Breakdown</div>', unsafe_allow_html=True)
        for entry in tm:
            d = entry["data"]
            tt = d.get("totals", {})
            ts = datetime.fromisoformat(entry["timestamp"]).strftime("%I:%M %p")
            with st.expander(f"🍽️ {entry['meal_name']}  —  {tt.get('calories','?')} kcal  ({ts})"):
                for fd in d.get("foods", []):
                    st.write(f"{fd.get('emoji','🍽️')} **{fd.get('name')}** — {fd.get('calories')} kcal ({fd.get('portion','')})")
        at = calculate_daily_totals(st.session_state.meal_history)
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Meals Tracked", len(st.session_state.meal_history))
        c2.metric("Total Calories", f"{at['calories']} kcal")
        c3.metric("Avg Cal/Meal", f"{at['calories'] // max(len(st.session_state.meal_history),1)} kcal")

st.markdown('<div class="app-footer">Built with ❤️ using Streamlit + Groq · Nutritional estimates are AI-generated approximations</div>', unsafe_allow_html=True)
