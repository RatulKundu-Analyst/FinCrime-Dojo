"""
╔══════════════════════════════════════════════════════════╗
║         THE FINCRIME DOJO  —  GOD MODE v1.0             ║
║   AI-Powered Financial Crime Analytics Training App      ║
║   Stack: Streamlit + Google Gemini 2.5 + SQLite          ║
╚══════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
import re
import io
import traceback
from pathlib import Path
from contextlib import redirect_stdout

# ── Optional Gemini ────────────────────────────────────────────
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# ── Optional cookie manager ────────────────────────────────────
try:
    import extra_streamlit_components as stx
    COOKIES_AVAILABLE = True
except ImportError:
    COOKIES_AVAILABLE = False


# ╔══════════════════════════════════════════════════════════════╗
# ║                   PAGE CONFIG                               ║
# ╚══════════════════════════════════════════════════════════════╝

st.set_page_config(
    page_title="FinCrime Dojo",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ╔══════════════════════════════════════════════════════════════╗
# ║              API KEY — READ FROM SECRETS FIRST              ║
# ╚══════════════════════════════════════════════════════════════╝

def resolve_api_key() -> tuple[str, str]:
    """
    Returns (api_key, source_label).
    Priority:
      1. st.secrets["GEMINI_KEY"]   ← .streamlit/secrets.toml
      2. st.secrets["gemini_key"]   ← alternate casing
      3. Session state (manual input fallback)
    """
    for secret_name in ("GEMINI_KEY", "gemini_key", "GEMINI_API_KEY", "gemini_api_key"):
        try:
            key = st.secrets[secret_name]
            if key and str(key).strip():
                return str(key).strip(), "SECRETS"
        except (KeyError, FileNotFoundError):
            continue
    # Fallback: manual input stored in session state
    manual = st.session_state.get("_manual_api_key", "")
    if manual:
        return manual, "MANUAL"
    return "", "NONE"


# ╔══════════════════════════════════════════════════════════════╗
# ║                       CSS                                   ║
# ╚══════════════════════════════════════════════════════════════╝

CYBERPUNK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&family=VT323&display=swap');

:root {
  --green:        #00ff9f;
  --green-dim:    #00cc7a;
  --green-dark:   #003d26;
  --green-glow:   rgba(0,255,159,0.15);
  --amber:        #ffb000;
  --red:          #ff3c5c;
  --blue:         #00d4ff;
  --purple:       #bf5fff;
  --bg-black:     #020c07;
  --bg-panel:     #050f0a;
  --bg-card:      #0a1a10;
  --bg-terminal:  #000a05;
  --border:       rgba(0,255,159,0.2);
  --border-hot:   rgba(0,255,159,0.6);
  --font-mono:    'Share Tech Mono', 'Courier New', monospace;
  --font-display: 'Orbitron', monospace;
  --font-vt:      'VT323', monospace;
}

html, body, .stApp {
  background-color: var(--bg-black) !important;
  color: var(--green) !important;
  font-family: var(--font-mono) !important;
}
.stApp::before {
  content: "";
  position: fixed; top:0; left:0; right:0; bottom:0;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px,
    rgba(0,0,0,0.04) 2px, rgba(0,0,0,0.04) 4px);
  pointer-events: none;
  z-index: 9999;
}

[data-testid="stSidebar"] {
  background: var(--bg-panel) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--green) !important; font-family: var(--font-mono) !important; }
[data-testid="stSidebar"] input { background: var(--bg-terminal) !important; border: 1px solid var(--border) !important; color: var(--green) !important; }

h1,h2,h3,h4 {
  font-family: var(--font-display) !important;
  color: var(--green) !important;
  text-shadow: 0 0 20px var(--green), 0 0 40px rgba(0,255,159,0.3) !important;
  letter-spacing: 2px !important;
}
p, li, label, .stMarkdown { font-family: var(--font-mono) !important; color: var(--green) !important; }
.stMarkdown code { background: var(--bg-terminal) !important; color: var(--amber) !important; border: 1px solid var(--border) !important; font-family: var(--font-mono) !important; padding: 2px 6px !important; border-radius: 3px !important; }
.stMarkdown pre { background: var(--bg-terminal) !important; border: 1px solid var(--border) !important; border-left: 3px solid var(--green) !important; color: var(--green) !important; font-family: var(--font-mono) !important; padding: 16px !important; border-radius: 4px !important; }

.stButton > button {
  background: transparent !important;
  border: 1px solid var(--green) !important;
  color: var(--green) !important;
  font-family: var(--font-display) !important;
  font-size: 0.72rem !important;
  letter-spacing: 2px !important;
  text-transform: uppercase !important;
  padding: 10px 24px !important;
  transition: all 0.2s ease !important;
  box-shadow: 0 0 10px var(--green-glow) !important;
}
.stButton > button:hover {
  background: var(--green-glow) !important;
  box-shadow: 0 0 20px var(--green), 0 0 40px rgba(0,255,159,0.2) !important;
  transform: translateY(-1px) !important;
}

.stTextArea textarea {
  background: var(--bg-terminal) !important;
  color: var(--green) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.9rem !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px !important;
  caret-color: var(--green) !important;
}
.stTextArea textarea:focus { border-color: var(--green) !important; box-shadow: 0 0 10px var(--green-glow) !important; }

.stSelectbox > div > div { background: var(--bg-terminal) !important; border: 1px solid var(--border) !important; color: var(--green) !important; }
.stDataFrame { border: 1px solid var(--border) !important; border-radius: 4px !important; }

.stTabs [data-baseweb="tab-list"] { background: var(--bg-panel) !important; border-bottom: 1px solid var(--border) !important; gap: 4px !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: var(--green-dim) !important; font-family: var(--font-display) !important; font-size: 0.68rem !important; letter-spacing: 1px !important; border: 1px solid transparent !important; border-radius: 4px 4px 0 0 !important; padding: 8px 20px !important; }
.stTabs [aria-selected="true"] { background: var(--green-dark) !important; color: var(--green) !important; border-color: var(--border-hot) !important; text-shadow: 0 0 8px var(--green) !important; }
.stTabs [data-baseweb="tab-panel"] { background: var(--bg-panel) !important; border: 1px solid var(--border) !important; border-top: none !important; padding: 20px !important; border-radius: 0 0 4px 4px !important; }

[data-testid="stMetric"] { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: 4px !important; padding: 12px !important; }
[data-testid="stMetricLabel"] { color: var(--green-dim) !important; font-family: var(--font-display) !important; font-size: 0.58rem !important; letter-spacing: 2px !important; }
[data-testid="stMetricValue"] { color: var(--green) !important; font-family: var(--font-vt) !important; font-size: 2rem !important; text-shadow: 0 0 10px var(--green) !important; }

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-black); }
::-webkit-scrollbar-thumb { background: var(--green-dark); border-radius: 3px; }

/* ── Custom components ── */
.dojo-header { text-align:center; padding:20px 0 10px 0; border-bottom:1px solid var(--border); margin-bottom:24px; }
.dojo-header h1 { font-size:1.9rem !important; letter-spacing:6px !important; margin:0 !important; }
.dojo-header .subtitle { color:var(--green-dim); font-size:0.65rem; letter-spacing:4px; margin-top:4px; }

.terminal-box { background:var(--bg-terminal); border:1px solid var(--border); border-left:3px solid var(--green); border-radius:4px; padding:16px; font-family:var(--font-mono); color:var(--green); margin:8px 0; }
.terminal-box.error  { border-left-color:var(--red);   color:var(--red);   }
.terminal-box.warning{ border-left-color:var(--amber);  color:var(--amber); }
.terminal-box.success{ border-left-color:var(--green);  box-shadow:0 0 10px rgba(0,255,159,0.08); }
.terminal-box.info   { border-left-color:var(--blue);   color:var(--blue);  }

.section-header { display:flex; align-items:center; gap:10px; margin:20px 0 12px 0; padding-bottom:6px; border-bottom:1px solid var(--border); }
.section-header span { font-family:var(--font-display); font-size:0.72rem; letter-spacing:3px; color:var(--green); text-transform:uppercase; }

.xp-badge   { display:inline-block; background:var(--green-dark); border:1px solid var(--green); color:var(--green); font-family:var(--font-display); font-size:0.62rem; letter-spacing:2px; padding:3px 10px; border-radius:2px; box-shadow:0 0 8px var(--green-glow); }
.level-badge{ display:inline-block; background:rgba(0,212,255,0.1); border:1px solid var(--blue); color:var(--blue); font-family:var(--font-display); font-size:0.62rem; letter-spacing:2px; padding:3px 10px; border-radius:2px; }

.glitch-text { animation:glitch 5s infinite; }
@keyframes glitch {
  0%,88%,100% { text-shadow:0 0 20px var(--green),0 0 40px rgba(0,255,159,0.3); }
  90%  { text-shadow:-2px 0 var(--red),2px 0 var(--blue); transform:skewX(-1deg); }
  92%  { text-shadow:2px 0 var(--red),-2px 0 var(--blue); transform:skewX(1deg); }
  94%  { text-shadow:0 0 20px var(--green),0 0 40px rgba(0,255,159,0.3); transform:none; }
}

.pulse-dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--green); box-shadow:0 0 6px var(--green); animation:pulse 1.5s infinite; margin-right:8px; vertical-align:middle; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.35;} }

.challenge-box { background:linear-gradient(135deg,var(--bg-card) 0%,rgba(0,255,159,0.03) 100%); border:1px solid var(--border-hot); border-radius:6px; padding:20px; margin:12px 0; position:relative; }
.challenge-box::before { content:"MISSION"; position:absolute; top:8px; right:12px; font-family:var(--font-display); font-size:0.52rem; letter-spacing:3px; color:rgba(0,255,159,0.3); }

.hint-box { background:rgba(255,176,0,0.05); border:1px solid rgba(255,176,0,0.4); border-left:3px solid var(--amber); border-radius:4px; padding:14px; margin:8px 0; color:var(--amber); font-family:var(--font-mono); }

.stat-bar { height:4px; background:var(--bg-card); border-radius:2px; overflow:hidden; margin:4px 0; }
.stat-bar-fill { height:100%; background:linear-gradient(90deg,var(--green-dark),var(--green)); border-radius:2px; box-shadow:0 0 6px var(--green); }

/* Key source badge colours */
.key-secrets { color:#00ff9f !important; }
.key-manual  { color:#ffb000 !important; }
.key-none    { color:#ff3c5c !important; }
</style>
"""

st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║              PERSISTENCE LAYER — FILE + COOKIES             ║
# ╚══════════════════════════════════════════════════════════════╝

PROGRESS_FILE = Path("dojo_progress.json")
COOKIE_NAME   = "dojo_progress_v1"

PERSIST_KEYS = [
    "xp", "day", "streak",
    "challenges_completed", "challenges_attempted",
    "history", "current_lesson",
]

@st.cache_resource
def get_cookie_manager():
    if COOKIES_AVAILABLE:
        return stx.CookieManager(key="fincrime_dojo_cm")
    return None

cookie_manager = get_cookie_manager()


def save_to_file(state: dict):
    try:
        payload = {k: state.get(k) for k in PERSIST_KEYS}
        PROGRESS_FILE.write_text(json.dumps(payload, default=str, indent=2))
    except Exception:
        pass

def load_from_file() -> dict:
    try:
        if PROGRESS_FILE.exists():
            return json.loads(PROGRESS_FILE.read_text())
    except Exception:
        pass
    return {}

def save_to_cookie(state: dict):
    if not cookie_manager:
        return
    try:
        compact = {
            "xp":  state.get("xp", 0),
            "day": state.get("day", 0),
            "st":  state.get("streak", 0),
            "cc":  state.get("challenges_completed", 0),
            "ca":  state.get("challenges_attempted", 0),
        }
        cookie_manager.set(COOKIE_NAME, json.dumps(compact), key="cookie_save_op")
    except Exception:
        pass

def load_from_cookie() -> dict:
    if not cookie_manager:
        return {}
    try:
        raw = cookie_manager.get(COOKIE_NAME)
        if raw:
            c = json.loads(raw)
            return {
                "xp":                   c.get("xp", 0),
                "day":                  c.get("day", 0),
                "streak":               c.get("st", 0),
                "challenges_completed": c.get("cc", 0),
                "challenges_attempted": c.get("ca", 0),
            }
    except Exception:
        pass
    return {}

def save_progress():
    state = dict(st.session_state)
    save_to_file(state)
    save_to_cookie(state)

def load_progress() -> dict:
    file_data   = load_from_file()
    cookie_data = load_from_cookie()
    merged = {}
    for key in PERSIST_KEYS:
        if key in file_data:
            merged[key] = file_data[key]
        elif key in cookie_data:
            merged[key] = cookie_data[key]
    return merged


# ╔══════════════════════════════════════════════════════════════╗
# ║                   SESSION STATE INIT                        ║
# ╚══════════════════════════════════════════════════════════════╝

DEFAULTS = {
    "xp": 0, "day": 0, "streak": 0,
    "challenges_completed": 0, "challenges_attempted": 0,
    "current_lesson": None, "current_df": None,
    "sql_result": None, "python_output": None,
    "hint_sql": None, "hint_python": None,
    "last_sql_correct": None, "last_python_correct": None,
    "last_sql_input": "", "last_python_input": "",
    "last_sql_error": "", "last_python_error": "",
    "history": [],
    "_progress_loaded": False,
    "_manual_api_key": "",
}

if not st.session_state.get("_progress_loaded", False):
    saved = load_progress()
    for k, default_val in DEFAULTS.items():
        if k.startswith("_"):
            st.session_state[k] = default_val
            continue
        if k in saved and saved[k] is not None:
            st.session_state[k] = saved[k]
        elif k not in st.session_state:
            st.session_state[k] = default_val

    # Re-hydrate DataFrame if a lesson was saved
    if st.session_state.get("current_lesson"):
        _code = st.session_state.current_lesson.get("data_setup", "")
        if _code:
            try:
                _ns = {}
                exec(compile(_code, "<restore>", "exec"),
                     {"pd": pd, "__builtins__": __builtins__}, _ns)
                st.session_state.current_df = _ns.get("df")
            except Exception:
                st.session_state.current_df = None

    st.session_state._progress_loaded = True


# ╔══════════════════════════════════════════════════════════════╗
# ║                   CONSTANTS & PROMPTS                       ║
# ╚══════════════════════════════════════════════════════════════╝

LEVEL_CONFIG = {
    "🎖️ Cadet (Basics)": {
        "id": "cadet", "color": "#00ff9f",
        "topics": [
            "SQL SELECT and WHERE on transaction tables",
            "Python variables and data types for banking data",
            "SQL ORDER BY and LIMIT for top suspicious transactions",
            "Python if/else conditions for transaction threshold alerts",
            "SQL COUNT and SUM aggregations on transaction records",
            "Python for loops iterating over customer watchlists",
            "SQL BETWEEN and IN operators for date range and country filters",
            "Python lists and dictionaries for storing watchlist data",
            "SQL DISTINCT for unique customer and account analysis",
            "Python string operations for normalizing customer names",
        ],
    },
    "🔬 Analyst (Data)": {
        "id": "analyst", "color": "#00d4ff",
        "topics": [
            "Pandas DataFrame loading and inspection of bank transaction records",
            "SQL INNER JOIN linking customer accounts to transactions",
            "SQL LEFT JOIN to find customers with missing KYC documents",
            "Pandas groupby for customer transaction volume aggregation",
            "SQL GROUP BY with HAVING for flagging high-volume accounts",
            "Pandas fillna and dropna for cleaning dirty transaction data",
            "SQL CASE WHEN for dynamic risk tier classification",
            "Pandas merge to combine customer profiles and transaction tables",
            "SQL Common Table Expressions for multi-step AML analysis",
            "Pandas pivot_table for monthly transaction pattern heatmaps",
        ],
    },
    "🕵️ Investigator (Patterns)": {
        "id": "investigator", "color": "#bf5fff",
        "topics": [
            "Detecting cash structuring and smurfing with SQL HAVING COUNT",
            "Writing Python functions to flag suspicious transaction patterns",
            "SQL Window Functions LAG and LEAD for transaction velocity analysis",
            "Detecting dormant account reactivation with date-delta logic",
            "Fuzzy name matching for PEP and sanctions list screening",
            "SQL self-joins for detecting fund layering chains",
            "Python Z-score anomaly detection for peer group outlier analysis",
            "Geographic risk scoring with FATF country risk classification",
            "SQL ROW_NUMBER and deduplication for alert management",
            "Building a weighted rule-based AML risk scoring engine",
        ],
    },
    "🤖 Architect (ML)": {
        "id": "architect", "color": "#ffb000",
        "topics": [
            "Feature engineering from raw transaction data for fraud ML models",
            "Logistic Regression for binary fraud yes/no classification",
            "Random Forest ensemble model for financial crime detection",
            "Handling imbalanced fraud datasets with SMOTE and class weights",
            "Isolation Forest for unsupervised transaction anomaly detection",
            "XGBoost gradient boosting for production-grade fraud prediction",
            "Model evaluation with confusion matrix, ROC-AUC, and F1-score",
            "SHAP values for explainable and regulator-ready AML model decisions",
            "Cross-validation and GridSearchCV hyperparameter tuning",
            "Building a full end-to-end AML machine learning pipeline",
        ],
    },
}

SYSTEM_PROMPT = """You are FinCrime_Architect, a Senior Financial Crime Analytics Expert at HSBC and an expert Python/SQL instructor. You EXCLUSIVELY generate training modules for Financial Crime Analytics roles.

ALL problems, datasets, and scenarios must involve:
- AML (Anti-Money Laundering) transaction monitoring
- KYC (Know Your Customer) compliance
- Fraud detection, structuring/smurfing, layering
- PEP and sanctions screening
- Suspicious Activity Reports (SARs)

Use these domain variable names (never x, y, z):
- transaction_id, cust_id, account_id, amount, txn_date
- cust_risk_score, country_code, beneficiary_country
- is_flagged, alert_id, sar_filed, kyc_status
- product_type, channel, currency, txn_type

Respond ONLY with valid JSON. No markdown, no explanation outside JSON."""

LESSON_PROMPT = """Generate a Financial Crime Analytics training module for a {level}-level student.
Topic: "{topic}"

Return EXACTLY this JSON (no markdown fences):
{{
  "topic": "concise topic name",
  "theory": "3-4 sentences using real AML/fraud terminology. Explain why it matters for investigators.",
  "data_setup": "complete runnable Python code creating a Pandas DataFrame called df with 8-12 rows. Must start with: import pandas as pd",
  "challenge": "specific task framed as a real investigator scenario. Reference exact column names from data_setup.",
  "solution_sql": "correct SQLite SQL. Table name must be: transactions",
  "solution_python": "correct Python/Pandas using df. Store answer in result and print it."
}}"""

HINT_PROMPT = """A {level}-level Financial Crime Analytics student is stuck.
Topic: "{topic}"
Challenge: {challenge}
Their code: {code}
Error: {error}

Give ONE targeted hint (2-3 sentences). Be encouraging. Don't reveal the answer. Plain text only."""


# ╔══════════════════════════════════════════════════════════════╗
# ║                   GEMINI FUNCTIONS                          ║
# ╚══════════════════════════════════════════════════════════════╝

def init_gemini(api_key: str):
    if not GEMINI_AVAILABLE:
        return None, "google-generativeai not installed."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
        )
        return model, None
    except Exception as e:
        return None, str(e)

def generate_lesson(model, level: str, topic: str):
    try:
        resp = model.generate_content(
            LESSON_PROMPT.format(level=level, topic=topic),
            generation_config={"temperature": 0.7, "max_output_tokens": 2048},
        )
        raw = re.sub(r"^```json\s*|^```\s*|\s*```$", "", resp.text.strip())
        return json.loads(raw), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"
    except Exception as e:
        return None, str(e)

def get_ai_hint(model, level, topic, challenge, code, error):
    try:
        resp = model.generate_content(
            HINT_PROMPT.format(level=level, topic=topic,
                               challenge=challenge, code=code or "(empty)",
                               error=error or "no output"),
            generation_config={"temperature": 0.5, "max_output_tokens": 200},
        )
        return resp.text.strip()
    except Exception as e:
        return f"Could not generate hint: {e}"


# ╔══════════════════════════════════════════════════════════════╗
# ║                   EXECUTION ENGINE                          ║
# ╚══════════════════════════════════════════════════════════════╝

def exec_data_setup(code: str):
    ns = {}
    try:
        exec(compile(code, "<data_setup>", "exec"),
             {"pd": pd, "__builtins__": __builtins__}, ns)
        df = ns.get("df")
        return (df, "") if df is not None else (None, "data_setup must create a variable named 'df'")
    except Exception:
        return None, traceback.format_exc()

def exec_sql(sql: str, df: pd.DataFrame):
    try:
        conn = sqlite3.connect(":memory:")
        df.to_sql("transactions", conn, index=False, if_exists="replace")
        result = pd.read_sql_query(sql, conn)
        conn.close()
        return result, ""
    except Exception as e:
        return None, str(e)

SAFE_BUILTINS = {
    b: __builtins__[b] if isinstance(__builtins__, dict) else getattr(__builtins__, b, None)
    for b in ("print","len","range","list","dict","set","tuple","int","float","str",
              "bool","sum","min","max","abs","round","sorted","enumerate","zip",
              "map","filter","isinstance","type","repr","__import__")
    if (isinstance(__builtins__, dict) and b in __builtins__) or hasattr(__builtins__, b)
}

def exec_python(code: str, df: pd.DataFrame):
    buf = io.StringIO()
    ns  = {"df": df.copy(), "pd": pd, "__builtins__": SAFE_BUILTINS}
    try:
        with redirect_stdout(buf):
            exec(compile(code, "<student>", "exec"), ns)
        output = buf.getvalue()
        if "result" in ns and not output.strip():
            val = ns["result"]
            output = val.to_string() if isinstance(val, pd.DataFrame) else repr(val)
        return output or "(No output — use print() or assign to 'result')", ""
    except Exception:
        return "", traceback.format_exc()


# ╔══════════════════════════════════════════════════════════════╗
# ║                   UI HELPERS                                ║
# ╚══════════════════════════════════════════════════════════════╝

def tb(content: str, box_type: str = "success", title: str = ""):
    t = (f'<div style="font-size:0.62rem;letter-spacing:3px;opacity:0.6;'
         f'margin-bottom:8px;font-family:var(--font-display)">{title}</div>') if title else ""
    st.markdown(
        f'<div class="terminal-box {box_type}">{t}'
        f'<pre style="margin:0;font-family:var(--font-mono);background:none;border:none;'
        f'padding:0;color:inherit;white-space:pre-wrap;word-break:break-all">{content}</pre></div>',
        unsafe_allow_html=True,
    )

def sh(icon: str, title: str):
    st.markdown(
        f'<div class="section-header"><span>{icon} {title}</span></div>',
        unsafe_allow_html=True,
    )

def progress_html(val: int, maxv: int = 100):
    p = min(100, int(val / maxv * 100)) if maxv else 0
    st.markdown(
        f'<div class="stat-bar"><div class="stat-bar-fill" style="width:{p}%"></div></div>',
        unsafe_allow_html=True,
    )


# ╔══════════════════════════════════════════════════════════════╗
# ║                   RESOLVE API KEY                           ║
# ╚══════════════════════════════════════════════════════════════╝

api_key, key_source = resolve_api_key()


# ╔══════════════════════════════════════════════════════════════╗
# ║                       SIDEBAR                               ║
# ╚══════════════════════════════════════════════════════════════╝

with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:16px 0;border-bottom:1px solid rgba(0,255,159,0.2);margin-bottom:16px">'
        '<div style="font-family:\'Orbitron\',monospace;font-size:1.1rem;color:#00ff9f;'
        'text-shadow:0 0 15px #00ff9f;letter-spacing:4px">FINCRIME</div>'
        '<div style="font-family:\'Orbitron\',monospace;font-size:0.58rem;color:#00cc7a;'
        'letter-spacing:6px;margin-top:2px">D O J O</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── API KEY STATUS PANEL ───────────────────────────────────
    st.markdown(
        '<div style="font-size:0.62rem;letter-spacing:3px;color:#00cc7a;margin-bottom:6px">◈ AI ENGINE</div>',
        unsafe_allow_html=True,
    )

    if key_source == "SECRETS":
        # Key loaded automatically — show locked indicator, no input needed
        masked = api_key[:8] + "•" * 10 + api_key[-4:]
        st.markdown(
            f'<div style="background:rgba(0,255,159,0.05);border:1px solid rgba(0,255,159,0.3);'
            f'border-radius:4px;padding:10px 12px;">'
            f'<div style="font-size:0.65rem;color:#00ff9f;margin-bottom:4px">'
            f'🔐 AUTO-LOADED FROM SECRETS</div>'
            f'<div style="font-size:0.6rem;color:#00cc7a;font-family:\'Share Tech Mono\',monospace">'
            f'{masked}</div>'
            f'<div style="font-size:0.55rem;color:rgba(0,204,122,0.5);margin-top:4px">'
            f'gemini-2.5-flash  ·  always active</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        # No secret found — show manual input as fallback
        st.markdown(
            '<div style="font-size:0.6rem;color:#ffb000;margin-bottom:4px">'
            '⚠ No secret found — enter key manually</div>',
            unsafe_allow_html=True,
        )
        manual_key = st.text_input(
            "API Key", type="password",
            label_visibility="collapsed",
            placeholder="AIza...",
            value=st.session_state._manual_api_key,
            help="Or add GEMINI_KEY to .streamlit/secrets.toml",
        )
        if manual_key != st.session_state._manual_api_key:
            st.session_state._manual_api_key = manual_key
            api_key, key_source = manual_key, "MANUAL" if manual_key else "NONE"
            st.rerun()

        if not api_key:
            st.markdown(
                '<div style="font-size:0.6rem;color:#ff3c5c;margin-top:4px">'
                '● OFFLINE — add secrets.toml for auto-login</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="font-size:0.6rem;color:#ffb000;margin-top:4px">'
                '● MANUAL KEY ACTIVE</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── DIFFICULTY ────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.62rem;letter-spacing:3px;color:#00cc7a;margin-bottom:4px">◈ DIFFICULTY</div>',
        unsafe_allow_html=True,
    )
    difficulty = st.selectbox("Difficulty", list(LEVEL_CONFIG.keys()), label_visibility="collapsed")
    level_data = LEVEL_CONFIG[difficulty]

    st.markdown("<br>", unsafe_allow_html=True)

    # ── STATS ─────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.62rem;letter-spacing:3px;color:#00cc7a;margin-bottom:12px">◈ AGENT STATS</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    c1.metric("XP",     f"{st.session_state.xp:,}")
    c2.metric("DAY",    st.session_state.day)
    c3, c4 = st.columns(2)
    c3.metric("STREAK", f"🔥{st.session_state.streak}")
    _acc = int(st.session_state.challenges_completed /
               st.session_state.challenges_attempted * 100) \
        if st.session_state.challenges_attempted else 0
    c4.metric("ACC%", f"{_acc}%")

    st.markdown(
        '<div style="font-size:0.58rem;letter-spacing:2px;color:#00cc7a;margin-top:8px">XP TO NEXT RANK</div>',
        unsafe_allow_html=True,
    )
    progress_html(st.session_state.xp % 100, 100)
    st.markdown(
        f'<div style="font-size:0.58rem;color:#00cc7a;text-align:right">'
        f'{st.session_state.xp % 100}/100</div>',
        unsafe_allow_html=True,
    )

    # ── SAVE STATUS ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    _layers = []
    if PROGRESS_FILE.exists(): _layers.append("FILE")
    if COOKIES_AVAILABLE:      _layers.append("COOKIE")
    _save_label = " + ".join(_layers) if _layers else "SESSION ONLY"
    _save_color = "#00ff9f" if PROGRESS_FILE.exists() else "#ffb000"
    st.markdown(
        f'<div style="background:rgba(0,0,0,0.3);border:1px solid rgba(0,255,159,0.15);'
        f'border-radius:3px;padding:8px 10px;">'
        f'<div style="font-size:0.55rem;letter-spacing:2px;color:#00cc7a;margin-bottom:3px">SAVE STATUS</div>'
        f'<div style="font-size:0.65rem;color:{_save_color}">● {_save_label}</div>'
        f'<div style="font-size:0.52rem;color:rgba(0,204,122,0.5);margin-top:2px">'
        f'{"Auto-saved · Refresh-safe" if PROGRESS_FILE.exists() else "Start a lesson to begin saving"}'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # ── HISTORY ───────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.history:
        st.markdown(
            '<div style="font-size:0.62rem;letter-spacing:3px;color:#00cc7a;margin-bottom:6px">◈ HISTORY</div>',
            unsafe_allow_html=True,
        )
        for h in st.session_state.history[-5:]:
            icon = "✅" if h.get("completed") else "⚠️"
            st.markdown(
                f'<div style="font-size:0.62rem;color:#00cc7a;padding:2px 0">'
                f'{icon} Day {h["day"]} — {h["topic"][:24]}...</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⚡ RESET DOJO", use_container_width=True):
        try:
            if PROGRESS_FILE.exists():
                PROGRESS_FILE.unlink()
        except Exception:
            pass
        if cookie_manager:
            try:
                cookie_manager.delete(COOKIE_NAME, key="cookie_del")
            except Exception:
                pass
        for k, v in DEFAULTS.items():
            st.session_state[k] = v
        st.session_state._progress_loaded = True
        st.rerun()


# ╔══════════════════════════════════════════════════════════════╗
# ║                   MAIN HEADER                               ║
# ╚══════════════════════════════════════════════════════════════╝

st.markdown(
    '<div class="dojo-header">'
    '<h1 class="glitch-text">THE FINCRIME DOJO</h1>'
    '<div class="subtitle">AI-POWERED FINANCIAL CRIME ANALYTICS TRAINING — GOD MODE ACTIVE</div>'
    '</div>',
    unsafe_allow_html=True,
)

# Status bar
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.markdown(
        f'<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a">LEVEL</div>'
        f'<div style="font-size:0.8rem;color:#00d4ff">{difficulty.split("(")[0].strip()}</div>',
        unsafe_allow_html=True,
    )
with s2:
    _n = len(level_data["topics"])
    _d = (st.session_state.day % _n) + 1
    st.markdown(
        f'<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a">PROGRESS</div>'
        f'<div style="font-size:0.8rem;color:#00ff9f">{_d}/{_n} topics</div>',
        unsafe_allow_html=True,
    )
with s3:
    _st = "LESSON ACTIVE" if st.session_state.current_lesson else "STANDBY"
    _sc = "#00ff9f" if st.session_state.current_lesson else "#ffb000"
    st.markdown(
        f'<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a">STATUS</div>'
        f'<div style="font-size:0.8rem;color:{_sc}">● {_st}</div>',
        unsafe_allow_html=True,
    )
with s4:
    _kc = {"SECRETS": "#00ff9f", "MANUAL": "#ffb000", "NONE": "#ff3c5c"}[key_source]
    _kt = {"SECRETS": "● GEMINI  🔐 SECRETS", "MANUAL": "● GEMINI  ✎ MANUAL", "NONE": "● OFFLINE"}[key_source]
    st.markdown(
        f'<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a">AI ENGINE</div>'
        f'<div style="font-size:0.8rem;color:{_kc}">{_kt}</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

if not api_key:
    tb(
        "⚠  GEMINI OFFLINE — No API key found.\n\n"
        "  OPTION 1 (Recommended): Add to .streamlit/secrets.toml:\n"
        "    GEMINI_KEY = \"AIza...\"\n\n"
        "  OPTION 2: Paste the key manually in the sidebar.\n\n"
        "  Demo mode is active below while you set this up.",
        "warning", "SYSTEM NOTICE",
    )
    st.markdown("<br>", unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║                   ACTION BUTTONS                            ║
# ╚══════════════════════════════════════════════════════════════╝

b1, b2, b3, b4 = st.columns([2, 2, 2, 2])
with b1:
    start_clicked = st.button(
        "▶ START DAY" if not st.session_state.current_lesson else "⟳ NEW LESSON",
        use_container_width=True, disabled=not bool(api_key),
    )
with b2:
    next_clicked = st.button("⏭ NEXT TOPIC", use_container_width=True, disabled=not bool(api_key))
with b3:
    hint_sql_btn = st.button("💡 HINT (SQL)", use_container_width=True,
                              disabled=not bool(api_key and st.session_state.current_lesson))
with b4:
    hint_py_btn  = st.button("💡 HINT (Python)", use_container_width=True,
                              disabled=not bool(api_key and st.session_state.current_lesson))


# ── Generate lesson ───────────────────────────────────────────
def load_lesson(advance: bool = False):
    model, err = init_gemini(api_key)
    if err:
        st.error(f"Gemini init failed: {err}")
        return
    if advance:
        st.session_state.day += 1
    topic_idx = st.session_state.day % len(level_data["topics"])
    topic     = level_data["topics"][topic_idx]
    with st.spinner(f"⟳ GENERATING: {topic}..."):
        lesson, err = generate_lesson(model, level_data["id"], topic)
    if lesson:
        st.session_state.current_lesson = lesson
        df, df_err = exec_data_setup(lesson["data_setup"])
        st.session_state.current_df = df
        if df_err:
            st.warning(f"Data setup warning:\n{df_err}")
        for k in ["sql_result","python_output","hint_sql","hint_python",
                  "last_sql_correct","last_python_correct",
                  "last_sql_input","last_python_input",
                  "last_sql_error","last_python_error"]:
            st.session_state[k] = None if any(x in k for x in ("result","output","correct")) else ""
        if not advance:
            st.session_state.day += 1
        st.session_state.streak += 1
        save_progress()
    else:
        st.error(f"Lesson generation failed: {err}")


if start_clicked:
    load_lesson(advance=False)
    st.rerun()

if next_clicked:
    if st.session_state.current_lesson:
        done = bool(st.session_state.last_sql_correct or st.session_state.last_python_correct)
        st.session_state.history.append({
            "day":   st.session_state.day,
            "topic": st.session_state.current_lesson.get("topic", ""),
            "completed": done,
        })
        if done:
            st.session_state.xp += 100
            st.session_state.challenges_completed += 1
        save_progress()
    load_lesson(advance=True)
    st.rerun()

if hint_sql_btn and st.session_state.current_lesson and api_key:
    model, _ = init_gemini(api_key)
    if model:
        with st.spinner("GENERATING HINT..."):
            h = get_ai_hint(model, level_data["id"],
                            st.session_state.current_lesson.get("topic",""),
                            st.session_state.current_lesson.get("challenge",""),
                            st.session_state.last_sql_input,
                            st.session_state.last_sql_error or "No submission yet")
        st.session_state.hint_sql = h
    st.rerun()

if hint_py_btn and st.session_state.current_lesson and api_key:
    model, _ = init_gemini(api_key)
    if model:
        with st.spinner("GENERATING HINT..."):
            h = get_ai_hint(model, level_data["id"],
                            st.session_state.current_lesson.get("topic",""),
                            st.session_state.current_lesson.get("challenge",""),
                            st.session_state.last_python_input,
                            st.session_state.last_python_error or "No submission yet")
        st.session_state.hint_python = h
    st.rerun()


# ╔══════════════════════════════════════════════════════════════╗
# ║                   LESSON DISPLAY                            ║
# ╚══════════════════════════════════════════════════════════════╝

if st.session_state.current_lesson:
    lesson = st.session_state.current_lesson
    df     = st.session_state.current_df

    # ── Theory ────────────────────────────────────────────────
    sh("🧠", f"DAY {st.session_state.day}  —  {lesson.get('topic','LESSON').upper()}")
    tc, bc = st.columns([5, 1])
    with tc:
        st.markdown(
            f'<div class="terminal-box success">'
            f'<div style="font-size:0.6rem;letter-spacing:3px;color:#00cc7a;margin-bottom:8px">▸ INTELLIGENCE BRIEFING</div>'
            f'{lesson.get("theory","")}</div>',
            unsafe_allow_html=True,
        )
    with bc:
        st.markdown(
            f'<div style="text-align:center;padding-top:16px">'
            f'<div class="xp-badge">+100 XP</div><br><br>'
            f'<div class="level-badge">{level_data["id"].upper()}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Live data ─────────────────────────────────────────────
    sh("📊", "LIVE BANK DATA — TABLE: transactions")
    if df is not None:
        st.markdown(
            f'<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a;margin-bottom:6px">'
            f'⬡ ROWS: {len(df)}  |  COLS: {len(df.columns)}  |  {list(df.columns)}</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(df, use_container_width=True, height=min(320, 60 + len(df) * 38))
        with st.expander("⟫ SCHEMA / COLUMN TYPES"):
            schema = "\n".join(f"  {c:<32}{str(t)}" for c, t in df.dtypes.items())
            tb(f"TABLE: transactions\n{'─'*50}\n  {'COLUMN':<32}TYPE\n{'─'*50}\n{schema}", "info", "SCHEMA")
    else:
        tb("⚠ DataFrame not loaded. Check data_setup.", "error")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Challenge ─────────────────────────────────────────────
    sh("🕵️", "YOUR MISSION")
    st.markdown(
        f'<div class="challenge-box">'
        f'<div style="font-size:0.62rem;letter-spacing:3px;color:#00ff9f;margin-bottom:10px">▸ CASE FILE — ACTIVE INVESTIGATION</div>'
        f'<div style="font-size:0.95rem;line-height:1.75">{lesson.get("challenge","")}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Terminal tabs ─────────────────────────────────────────
    sh("💻", "THE TERMINAL")
    tab_sql, tab_py, tab_sol = st.tabs([
        "  ⬡ SQL TERMINAL  ", "  ⬡ PYTHON TERMINAL  ", "  ⬡ SOLUTIONS  "
    ])

    # ── SQL tab ───────────────────────────────────────────────
    with tab_sql:
        st.markdown(
            '<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a;margin-bottom:6px">'
            '> SQL query runs against in-memory SQLite — table name: transactions</div>',
            unsafe_allow_html=True,
        )
        sql_in = st.text_area("SQL", height=150,
                              placeholder="SELECT ...\nFROM transactions\nWHERE ...",
                              label_visibility="collapsed", key="sql_input_area")
        rc1, _ = st.columns([2, 7])
        with rc1:
            run_sql = st.button("▶ EXECUTE SQL", key="exec_sql_btn", use_container_width=True)

        if run_sql:
            st.session_state.challenges_attempted += 1
            st.session_state.last_sql_input = sql_in
            if not sql_in.strip():
                st.warning("⚠ Write a SQL query first.")
            elif df is None:
                st.error("⚠ No data loaded.")
            else:
                res_df, sql_err = exec_sql(sql_in, df)
                if sql_err:
                    st.session_state.last_sql_error  = sql_err
                    st.session_state.last_sql_correct = False
                    tb(f"SQLiteError: {sql_err}\n\nTip: Check column names in the schema viewer above.",
                       "error", "EXECUTION ERROR")
                    if api_key:
                        model, _ = init_gemini(api_key)
                        if model:
                            with st.spinner("Generating AI hint..."):
                                h = get_ai_hint(model, level_data["id"],
                                                lesson.get("topic",""), lesson.get("challenge",""),
                                                sql_in, sql_err)
                            st.session_state.hint_sql = h
                else:
                    st.session_state.sql_result  = res_df
                    st.session_state.last_sql_error = ""
                    if res_df is not None and len(res_df) > 0:
                        st.session_state.last_sql_correct = True
                        st.session_state.xp += 25
                        save_progress()
                        tb(f"✓ QUERY EXECUTED SUCCESSFULLY\n"
                           f"  Rows returned : {len(res_df)}\n"
                           f"  Columns       : {list(res_df.columns)}\n"
                           f"  +25 XP AWARDED", "success", "OUTPUT")
                    else:
                        st.session_state.last_sql_correct = False
                        tb("⚠ Query ran but returned 0 rows.\nCheck your WHERE/HAVING conditions.",
                           "warning", "OUTPUT")
                st.rerun()

        if st.session_state.sql_result is not None:
            st.markdown(
                f'<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a;margin:12px 0 6px">'
                f'⬡ RESULT SET — {len(st.session_state.sql_result)} rows</div>',
                unsafe_allow_html=True,
            )
            st.dataframe(st.session_state.sql_result, use_container_width=True)

        if st.session_state.hint_sql:
            st.markdown(
                f'<div class="hint-box">⚡ AI HINT<br><br>{st.session_state.hint_sql}</div>',
                unsafe_allow_html=True,
            )

    # ── Python tab ────────────────────────────────────────────
    with tab_py:
        st.markdown(
            '<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a;margin-bottom:6px">'
            '> DataFrame available as: df  |  pandas available as: pd</div>',
            unsafe_allow_html=True,
        )
        py_in = st.text_area("Python", height=160,
                             placeholder="result = df[df['amount'] > 9000]\nprint(result)",
                             label_visibility="collapsed", key="py_input_area")
        pc1, _ = st.columns([2, 7])
        with pc1:
            run_py = st.button("▶ RUN PYTHON", key="exec_py_btn", use_container_width=True)

        if run_py:
            st.session_state.challenges_attempted += 1
            st.session_state.last_python_input = py_in
            if not py_in.strip():
                st.warning("⚠ Write some Python first.")
            elif df is None:
                st.error("⚠ No data loaded.")
            else:
                out, py_err = exec_python(py_in, df)
                st.session_state.last_python_error = py_err
                if py_err:
                    st.session_state.last_python_correct = False
                    tb(py_err, "error", "RUNTIME ERROR")
                    if api_key:
                        model, _ = init_gemini(api_key)
                        if model:
                            with st.spinner("Generating AI hint..."):
                                h = get_ai_hint(model, level_data["id"],
                                                lesson.get("topic",""), lesson.get("challenge",""),
                                                py_in, py_err)
                            st.session_state.hint_python = h
                else:
                    st.session_state.python_output   = out
                    st.session_state.last_python_correct = True
                    st.session_state.xp += 25
                    save_progress()
                    tb(f"✓ EXECUTION SUCCESSFUL  |  +25 XP\n{'─'*44}\n{out}", "success", "PROGRAM OUTPUT")
                st.rerun()

        if st.session_state.python_output:
            tb(st.session_state.python_output, "success", "LAST OUTPUT")

        if st.session_state.hint_python:
            st.markdown(
                f'<div class="hint-box">⚡ AI HINT<br><br>{st.session_state.hint_python}</div>',
                unsafe_allow_html=True,
            )

    # ── Solutions tab ─────────────────────────────────────────
    with tab_sol:
        st.markdown(
            '<div style="font-size:0.68rem;letter-spacing:2px;color:#ff3c5c;margin-bottom:16px">'
            '⚠ Try on your own first. Viewing solutions does not award XP.</div>',
            unsafe_allow_html=True,
        )
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(
                '<div style="font-size:0.62rem;letter-spacing:3px;color:#00cc7a;margin-bottom:6px">SQL SOLUTION</div>',
                unsafe_allow_html=True,
            )
            st.code(lesson.get("solution_sql", "-- Not available"), language="sql")
            if df is not None and st.button("✓ VERIFY SQL", key="verify_sql_btn"):
                r, e = exec_sql(lesson.get("solution_sql",""), df)
                tb(f"✓ Returns {len(r)} rows." if not e else f"Error: {e}",
                   "success" if not e else "error")
        with sc2:
            st.markdown(
                '<div style="font-size:0.62rem;letter-spacing:3px;color:#00cc7a;margin-bottom:6px">PYTHON SOLUTION</div>',
                unsafe_allow_html=True,
            )
            st.code(lesson.get("solution_python", "# Not available"), language="python")
            if df is not None and st.button("✓ VERIFY PYTHON", key="verify_py_btn"):
                o, e = exec_python(lesson.get("solution_python",""), df)
                tb(f"✓ Output:\n{o}" if not e else f"Error: {e}",
                   "success" if not e else "error")

    with st.expander("⟫ VIEW AI-GENERATED DATA SETUP CODE"):
        st.code(lesson.get("data_setup","# Not available"), language="python")


# ── Empty state ───────────────────────────────────────────────
else:
    st.markdown(
        '<div class="terminal-box" style="text-align:center;padding:56px 40px">'
        '<div style="font-family:\'VT323\',monospace;font-size:3.5rem;color:#00ff9f;margin-bottom:12px">◈</div>'
        '<div style="font-family:\'Orbitron\',monospace;font-size:0.9rem;letter-spacing:4px;color:#00ff9f;margin-bottom:12px">DOJO TERMINAL STANDING BY</div>'
        '<div style="font-size:0.8rem;color:#00cc7a;line-height:2">'
        '① API key loaded automatically from secrets.toml<br>'
        '② Select your difficulty level in the sidebar<br>'
        '③ Click ▶ START DAY to generate your AI-powered lesson'
        '</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    sh("⚡", "DEMO MODE — PRACTICE WITHOUT A LESSON")

    demo_df = pd.DataFrame({
        "transaction_id": ["TXN_001","TXN_002","TXN_003","TXN_004","TXN_005","TXN_006"],
        "cust_id":        ["C_101","C_102","C_103","C_101","C_104","C_102"],
        "amount":         [9800.0, 14500.0, 500.0, 9500.0, 23000.0, 8900.0],
        "country_code":   ["PK","AE","IN","PK","NG","AE"],
        "txn_type":       ["CASH_DEP","WIRE","CASH_DEP","CASH_DEP","WIRE","CASH_DEP"],
        "cust_risk_score":[8, 6, 2, 8, 9, 6],
        "is_flagged":     [False, True, False, False, True, False],
    })

    tb(
        "DEMO CHALLENGE\n══════════════\n"
        "A compliance alert fired. Find all CASH deposits over $9,000\n"
        "from customers with a risk score above 5.\n\n"
        "SQL hint  : WHERE amount > 9000 AND txn_type = 'CASH_DEP' AND cust_risk_score > 5\n"
        "Python hint: df[(df['amount'] > 9000) & (df['txn_type'] == 'CASH_DEP')]",
        "info", "DEMO CASE",
    )
    st.dataframe(demo_df, use_container_width=True)

    d1, d2 = st.columns(2)
    with d1:
        demo_sql = st.text_area("SQL demo:", height=90,
                                placeholder="SELECT * FROM transactions WHERE ...",
                                key="demo_sql_input")
        if st.button("▶ RUN DEMO SQL", key="demo_sql_run"):
            if demo_sql.strip():
                r, e = exec_sql(demo_sql, demo_df)
                tb(f"Error: {e}" if e else f"✓ {len(r)} rows returned",
                   "error" if e else "success", "OUTPUT")
                if not e:
                    st.dataframe(r, use_container_width=True)
            else:
                st.warning("Write a query first.")
    with d2:
        demo_py = st.text_area("Python demo:", height=90,
                               placeholder="result = df[df['amount'] > 9000]\nprint(result)",
                               key="demo_py_input")
        if st.button("▶ RUN DEMO PYTHON", key="demo_py_run"):
            if demo_py.strip():
                out, err = exec_python(demo_py, demo_df)
                tb(err if err else out, "error" if err else "success", "OUTPUT")
            else:
                st.warning("Write some code first.")


# ╔══════════════════════════════════════════════════════════════╗
# ║                       FOOTER                                ║
# ╚══════════════════════════════════════════════════════════════╝
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center;padding:16px;border-top:1px solid rgba(0,255,159,0.12);'
    'font-size:0.58rem;letter-spacing:3px;color:rgba(0,255,159,0.25)">'
    'FINCRIME DOJO v1.0  ·  GEMINI 2.5 FLASH  ·  FINANCIAL CRIME ANALYTICS TRAINING  ·  ALL DATA SYNTHETIC'
    '</div>',
    unsafe_allow_html=True,
)
