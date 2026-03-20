# 🥗 NutriLens — AI-Powered Food Calorie Tracker

An intelligent food calorie tracker that uses **Groq's Llama 4 Scout vision model** to analyze meal photos and generate detailed nutritional reports. Built with **Streamlit** for a clean, interactive UI.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-red?logo=streamlit)
![Groq](https://img.shields.io/badge/Groq-Llama_4_Scout-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- 📸 **Upload meal photos** — drag & drop or click to upload
- 🧠 **AI-powered analysis** — identifies foods, portions, and nutrients using Llama 4 Scout
- 📊 **Macro breakdown** — calories, protein, carbs, fat with donut charts
- 💊 **Micronutrient detection** — vitamins, minerals, fiber
- 📋 **Meal history** — track all analyzed meals in your session
- 📈 **Daily dashboard** — cumulative calorie timeline and daily totals
- ⚡ **Blazing fast** — powered by Groq's LPU inference engine

---

## 🏗️ Architecture

```
User uploads meal photo
        │
        ▼
┌─────────────────┐
│   Streamlit UI   │  ← Frontend (upload, display, charts)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Groq API Call   │  ← Llama 4 Scout vision model
│  (image + prompt)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  JSON Response   │  ← Structured nutrition data
│  (parse & show)  │
└─────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/nutrilens.git
cd nutrilens
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get a free Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to **API Keys** → **Create API Key**
4. Copy your key (starts with `gsk_`)

### 5. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. Enter your Groq API key in the sidebar, upload a meal photo, and click **Analyze Meal**.

---

## 📁 Project Structure

```
nutrilens/
├── app.py                    # Main Streamlit application
├── utils/
│   ├── __init__.py
│   ├── groq_client.py        # Groq API integration
│   ├── nutrition.py          # Nutrition parsing & calculations
│   └── charts.py             # Altair chart rendering
├── .streamlit/
│   └── config.toml           # Streamlit theme configuration
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── .gitignore
└── README.md
```

---

## 📚 Module Breakdown

### Module 1: Project Overview
This app demonstrates how vision-language models can be applied to nutrition tracking. The AI identifies food items from photos, estimates portion sizes, and calculates macronutrients and micronutrients — all through a single image upload.

### Module 2: Environment Setup
- **Python 3.9+** required
- **Groq** for free, fast AI inference (no GPU needed)
- **Streamlit** for the web interface
- **Pillow** for image processing
- **Altair** for interactive charts (bundled with Streamlit)

### Module 3: Streamlit Interface (`app.py`)
- Image upload with drag-and-drop support
- Meal name and portion size inputs
- Two-column layout: input panel + results panel
- Tabbed interface: Analyze Meal / Dashboard
- Sidebar with settings, daily summary, and meal history

### Module 4: AI Backend (`utils/groq_client.py`)
- Sends base64-encoded images to Groq's API
- Uses `meta-llama/llama-4-scout-17b-16e-instruct` (free multimodal model)
- Structured system prompt ensures consistent JSON output
- Images auto-resized to stay within API limits

### Module 5: Nutritional Reports (`utils/nutrition.py`)
- Robust JSON parsing with fallbacks for markdown fences
- Per-food breakdown: name, emoji, portion, calories, macros
- Daily totals aggregation across meals
- Macro percentage calculations (protein/carbs/fat split)

### Module 6: Visualization (`utils/charts.py`)
- Macro donut chart (Altair)
- Calorie timeline bar chart for daily tracking
- Interactive tooltips on all charts

### Module 7: Deployment
See the **Deploy** section below for Streamlit Community Cloud and other free options.

### Module 8: Extensions
Ideas for next steps:
- **Persistent storage**: Add SQLite or Supabase for cross-session history
- **User auth**: Streamlit's built-in authentication or Supabase auth
- **Goal tracking**: Set daily calorie/macro goals with progress bars
- **Meal planning**: Use a text LLM to suggest meals based on remaining macros
- **Export**: Download meal logs as CSV/PDF
- **Fine-tuning**: Train on food-specific datasets for better accuracy

---

## ☁️ Deploy for Free

### Option A: Streamlit Community Cloud (Recommended)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo → set `app.py` as the main file
4. Add your `GROQ_API_KEY` in **Settings → Secrets**:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
5. Deploy! You'll get a public URL like `https://your-app.streamlit.app`

### Option B: Hugging Face Spaces

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Select **Streamlit** as the SDK
3. Upload all project files
4. Add `GROQ_API_KEY` as a Secret in Space settings
5. The app deploys automatically

### Option C: Railway / Render

Both offer free tiers. Push to GitHub and connect your repo.

---

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Your Groq API key | Yes (or enter in sidebar) |

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| [Streamlit](https://streamlit.io) | Web UI framework |
| [Groq](https://groq.com) | Fast AI inference API (free tier) |
| [Llama 4 Scout](https://ai.meta.com/llama/) | Vision-language model |
| [Altair](https://altair-viz.github.io/) | Interactive charts |
| [Pillow](https://pillow.readthedocs.io/) | Image processing |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## ⚠️ Disclaimer

Nutritional estimates are AI-generated approximations based on visual analysis. They should **not** be used as medical or dietary advice. For accurate nutritional information, consult a registered dietitian or use verified food databases.
