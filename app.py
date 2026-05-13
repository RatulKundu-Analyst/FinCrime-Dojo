"""
╔══════════════════════════════════════════════════════════════╗
║         THE FINCRIME DOJO — GOD MODE TERMINAL                ║
║         A Gamified AML/Fraud Analytics Learning Engine       ║
║         Powered by: Streamlit + Google Gemini + SQLite       ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
import re
import sys
import io
import traceback
import random
from datetime import datetime

# ─────────────────────────────────────────────────────────────
#  PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinCrime Dojo",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
#  CYBERPUNK / TERMINAL CSS
# ─────────────────────────────────────────────────────────────
CYBER_CSS = """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600&display=swap');

/* ── Root Variables ── */
:root {
    --green:      #00ff88;
    --green-dim:  #00cc66;
    --green-dark: #003322;
    --amber:      #ffaa00;
    --red:        #ff3355;
    --cyan:       #00eeff;
    --purple:     #9b59ff;
    --bg-primary: #080c10;
    --bg-card:    #0d1117;
    --bg-panel:   #0a0f14;
    --border:     #1a2a1a;
    --border-glow:#00ff8844;
    --text-main:  #c8ffd4;
    --text-dim:   #4a7a5a;
    --font-mono:  'Share Tech Mono', monospace;
    --font-hud:   'Orbitron', monospace;
    --font-body:  'Exo 2', sans-serif;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-main) !important;
    font-family: var(--font-body) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--green-dim); border-radius: 2px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080c10 0%, #0a1208 100%) !important;
    border-right: 1px solid var(--border-glow) !important;
}
[data-testid="stSidebar"] * { color: var(--text-main) !important; }

/* ── Main Container ── */
.main .block-container {
    padding: 1rem 2rem !important;
    max-width: 1400px !important;
}

/* ── Header Banner ── */
.dojo-header {
    font-family: var(--font-hud);
    font-size: 2rem;
    font-weight: 900;
    color: var(--green);
    text-align: center;
    letter-spacing: 6px;
    text-shadow: 0 0 20px var(--green), 0 0 40px var(--green-dim);
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-glow);
    margin-bottom: 0.25rem;
}
.dojo-subheader {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--text-dim);
    text-align: center;
    letter-spacing: 4px;
    margin-bottom: 1.5rem;
}

/* ── HUD Bar ── */
.hud-bar {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1.5rem;
}
.hud-chip {
    background: var(--bg-card);
    border: 1px solid var(--border-glow);
    border-radius: 4px;
    padding: 0.3rem 0.8rem;
    font-family: var(--font-hud);
    font-size: 0.65rem;
    letter-spacing: 2px;
    color: var(--green);
    text-shadow: 0 0 8px var(--green-dim);
}
.hud-chip.amber { color: var(--amber); border-color: #ffaa0044; text-shadow: 0 0 8px var(--amber); }
.hud-chip.cyan  { color: var(--cyan);  border-color: #00eeff44; text-shadow: 0 0 8px var(--cyan);  }
.hud-chip.red   { color: var(--red);   border-color: #ff335544; text-shadow: 0 0 8px var(--red);   }

/* ── Cards ── */
.dojo-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-left: 3px solid var(--green);
    border-radius: 6px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
}
.dojo-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--green), transparent);
    opacity: 0.4;
}
.dojo-card.amber { border-left-color: var(--amber); }
.dojo-card.cyan  { border-left-color: var(--cyan);  }
.dojo-card.red   { border-left-color: var(--red);   }
.dojo-card.purple{ border-left-color: var(--purple); }

/* ── Card Titles ── */
.card-title {
    font-family: var(--font-hud);
    font-size: 0.7rem;
    letter-spacing: 3px;
    color: var(--green);
    margin-bottom: 0.8rem;
    text-shadow: 0 0 8px var(--green-dim);
}
.card-title.amber { color: var(--amber); text-shadow: 0 0 8px var(--amber); }
.card-title.cyan  { color: var(--cyan);  text-shadow: 0 0 8px var(--cyan); }
.card-title.red   { color: var(--red);   text-shadow: 0 0 8px var(--red);  }
.card-title.purple{ color: var(--purple);text-shadow: 0 0 8px var(--purple);}

/* ── Terminal Block ── */
.terminal-block {
    background: #020804;
    border: 1px solid #1a3a1a;
    border-radius: 4px;
    padding: 1rem 1.2rem;
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: var(--green);
    white-space: pre-wrap;
    word-break: break-all;
    min-height: 60px;
    box-shadow: inset 0 0 20px #00110011;
}
.terminal-block.error { color: var(--red); border-color: #3a1a1a; background: #080202; }
.terminal-block.amber { color: var(--amber); border-color: #3a2a00; }
.terminal-block.info  { color: var(--cyan);  border-color: #003a3a; }

/* ── Prompt line ── */
.prompt { color: var(--green-dim); }
.prompt::before { content: '┌─[DOJO@HSBC]─$ '; }

/* ── Section labels ── */
.section-label {
    font-family: var(--font-hud);
    font-size: 0.65rem;
    letter-spacing: 3px;
    color: var(--text-dim);
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}

/* ── Streamlit Widgets Overrides ── */
.stTextArea textarea, .stTextInput input, .stSelectbox select {
    background: #020804 !important;
    border: 1px solid #1a3a1a !important;
    color: var(--green) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.85rem !important;
    border-radius: 4px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--green) !important;
    box-shadow: 0 0 8px var(--green-dim) !important;
}
.stTextInput input[type="password"] { color: var(--amber) !important; }

/* ── Buttons ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--green) !important;
    color: var(--green) !important;
    font-family: var(--font-hud) !important;
    font-size: 0.65rem !important;
    letter-spacing: 2px !important;
    border-radius: 4px !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s ease !important;
    text-shadow: 0 0 6px var(--green-dim) !important;
}
.stButton > button:hover {
    background: var(--green-dark) !important;
    box-shadow: 0 0 12px var(--green-dim) !important;
}

/* ── DataFrames ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border-glow) !important;
    border-radius: 4px !important;
}
.stDataFrame { background: var(--bg-card) !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--bg-panel) !important;
    border-bottom: 1px solid var(--border-glow) !important;
    gap: 0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    font-family: var(--font-hud) !important;
    font-size: 0.65rem !important;
    letter-spacing: 2px !important;
    color: var(--text-dim) !important;
    background: transparent !important;
    border: none !important;
    padding: 0.6rem 1.2rem !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--green) !important;
    border-bottom: 2px solid var(--green) !important;
    text-shadow: 0 0 8px var(--green-dim) !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: #020804 !important;
    border: 1px solid #1a3a1a !important;
    color: var(--green) !important;
    font-family: var(--font-mono) !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    padding: 0.8rem !important;
}
[data-testid="stMetricLabel"] { font-family: var(--font-hud) !important; font-size: 0.6rem !important; color: var(--text-dim) !important; letter-spacing: 2px !important; }
[data-testid="stMetricValue"] { font-family: var(--font-hud) !important; color: var(--green) !important; text-shadow: 0 0 8px var(--green-dim) !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--font-hud) !important;
    font-size: 0.65rem !important;
    letter-spacing: 2px !important;
    color: var(--amber) !important;
}

/* ── Dividers ── */
hr { border-color: var(--border-glow) !important; margin: 1rem 0 !important; }

/* ── Spinner ── */
.stSpinner { color: var(--green) !important; }

/* ── Success / Error / Warning / Info ── */
[data-testid="stAlert"] { border-radius: 4px !important; font-family: var(--font-mono) !important; font-size: 0.82rem !important; }

/* ── Scanline Overlay ── */
.scanlines {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px);
    pointer-events: none; z-index: 9999; opacity: 0.4;
}

/* ── Blinking cursor ── */
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.cursor::after { content: '█'; animation: blink 1s infinite; color: var(--green); }

/* ── XP Progress Bar ── */
.xp-bar-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    height: 8px;
    overflow: hidden;
    margin: 0.3rem 0;
}
.xp-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--green-dim), var(--green));
    box-shadow: 0 0 8px var(--green);
    border-radius: 20px;
    transition: width 0.5s ease;
}

/* ── Glow Pulse ── */
@keyframes glow-pulse { 0%,100%{opacity:0.6} 50%{opacity:1} }
.glow-pulse { animation: glow-pulse 2s ease-in-out infinite; }

/* ── Badge ── */
.badge {
    display: inline-block;
    background: var(--green-dark);
    border: 1px solid var(--green);
    color: var(--green);
    font-family: var(--font-hud);
    font-size: 0.55rem;
    letter-spacing: 2px;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    text-shadow: 0 0 6px var(--green-dim);
    margin-right: 0.3rem;
}
.badge.amber { background: #1a1000; border-color: var(--amber); color: var(--amber); }
.badge.red   { background: #1a0008; border-color: var(--red); color: var(--red); }
.badge.cyan  { background: #001a1a; border-color: var(--cyan); color: var(--cyan); }
</style>
<div class="scanlines"></div>
"""

# ─────────────────────────────────────────────────────────────
#  LEVEL CONFIG
# ─────────────────────────────────────────────────────────────
LEVELS = {
    "🎖️ Cadet (Basics)": {
        "code": "CADET",
        "color": "green",
        "xp_per_challenge": 100,
        "topics": [
            "Python Variables & Data Types in Banking",
            "SQL SELECT & WHERE for Transaction Filtering",
            "Python Conditionals for AML Threshold Rules",
            "SQL ORDER BY & DISTINCT for Watchlist Screening",
            "Python Loops for Batch Transaction Processing",
        ],
        "description": "Python variables/loops, SQL SELECT/WHERE, basic transaction filtering",
    },
    "🔬 Analyst (Data)": {
        "code": "ANALYST",
        "color": "cyan",
        "xp_per_challenge": 200,
        "topics": [
            "Pandas DataFrames for Transaction Ledger Analysis",
            "SQL JOINs for Customer-KYC Cross-Referencing",
            "SQL GROUP BY & HAVING for Aggregated Suspicious Activity",
            "Cleaning Dirty Bank Data with Pandas",
            "SQL Window Functions for Customer Transaction Ranking",
        ],
        "description": "Pandas DataFrames, SQL Joins/Aggregations, cleaning dirty bank data",
    },
    "🕵️ Investigator (Patterns)": {
        "code": "INVESTIGATOR",
        "color": "amber",
        "xp_per_challenge": 350,
        "topics": [
            "Detecting Structuring & Smurfing with SQL",
            "Python Functions for Multi-Rule AML Flagging",
            "Velocity Checks using SQL LAG() and LEAD()",
            "Dormant Account Reactivation Pattern Detection",
            "Fuzzy Name Matching for PEP/Sanctions Screening",
        ],
        "description": "Flagging suspicious patterns, SQL Window Functions, rule-based AML engines",
    },
    "🤖 Architect (ML)": {
        "code": "ARCHITECT",
        "color": "purple",
        "xp_per_challenge": 500,
        "topics": [
            "Isolation Forest for Unsupervised Fraud Detection",
            "Random Forest Classifier for AML Risk Scoring",
            "Logistic Regression for Binary Fraud Prediction",
            "Handling Imbalanced Fraud Data with SMOTE",
            "XGBoost for Production-Grade SAR Prediction",
        ],
        "description": "Scikit-Learn, Random Forests, Isolation Forest, Logistic Regression for fraud ML",
    },
}

BADGES = {
    50:   ("🌱", "FIRST_BLOOD",    "First query executed"),
    200:  ("⚡", "SYNTAX_HUNTER",  "5 challenges completed"),
    500:  ("🎯", "FLAG_MASTER",    "First correct solution"),
    1000: ("🔥", "AML_ANALYST",    "500 XP earned"),
    2000: ("💀", "GHOST_PROTOCOL", "1000 XP milestone"),
    3500: ("🏆", "DOJO_MASTER",    "Architect level reached"),
}

# ─────────────────────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "xp": 0,
        "day": 0,
        "streak": 0,
        "challenges_done": 0,
        "correct_solutions": 0,
        "current_lesson": None,
        "current_df": None,
        "sql_result": None,
        "py_result": None,
        "sql_feedback": "",
        "py_feedback": "",
        "hint_text": "",
        "badges_earned": [],
        "last_active": datetime.now().strftime("%Y-%m-%d"),
        "history": [],
        "sql_code": "",
        "py_code": "",
        "lesson_loading": False,
        "topic_index": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ─────────────────────────────────────────────────────────────
#  GEMINI HELPERS
# ─────────────────────────────────────────────────────────────
def get_gemini_client(api_key: str):
    """Return configured Gemini model or None."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model
    except ImportError:
        st.error("❌ `google-generativeai` not installed. Run: pip install google-generativeai")
        return None
    except Exception as e:
        st.error(f"❌ Gemini init error: {e}")
        return None


SYSTEM_CONTEXT = """
You are FinCrime_Architect, a Senior Financial Crime Analytics expert at HSBC.
You ONLY generate problems related to:
- Anti-Money Laundering (AML)
- Know Your Customer (KYC)
- Transaction Monitoring
- Suspicious Activity Reporting (SAR)
- Fraud Detection
- Sanctions/PEP Screening
- Structuring / Smurfing detection
- Shell company / layering detection

All variable names must be realistic banking fields:
transaction_id, customer_id, account_number, amount, currency,
transaction_date, beneficiary_country, cust_risk_score, is_flagged,
alert_type, kyc_status, transaction_type, channel, ip_address, etc.

All datasets must simulate real bank transaction data.
Never use generic examples like 'x', 'y', 'foo', 'bar'.
"""


def build_lesson_prompt(level_code: str, topic: str, day: int) -> str:
    return f"""
{SYSTEM_CONTEXT}

Generate a Day {day} Financial Crime Analytics lesson for level: {level_code}
Topic: {topic}

Return ONLY a valid JSON object with NO markdown fencing, NO extra text.
The JSON must have EXACTLY these keys:

{{
  "topic": "short topic title (max 60 chars)",
  "theory": "2-3 paragraph explanation of the concept with real AML/banking context. Explain WHY this matters for catching criminals.",
  "data_setup": "Python code string that creates a variable named `df` — a pandas DataFrame with 8-12 rows of realistic banking transaction data relevant to this topic. Include realistic customer names, amounts, countries, risk scores. Import pandas as pd inside the code.",
  "challenge": "A specific, clearly worded challenge question asking the user to write SQL or Python to solve a financial crime detection problem using the dataset above.",
  "sql_table_name": "name of the SQL table to register the DataFrame as (snake_case, e.g. transactions)",
  "solution_sql": "The correct SQL query that solves the challenge (SELECT ... FROM {'{sql_table_name}'} ...)",
  "solution_python": "The correct Python/Pandas code using `df` variable that solves the challenge",
  "expected_output_description": "One sentence describing what the correct output should show",
  "hints": ["hint 1 (vague)", "hint 2 (more specific)", "hint 3 (nearly gives it away)"]
}}

Level guidelines:
- CADET: Simple SELECT/WHERE, basic Python variables and loops
- ANALYST: JOINs, GROUP BY, HAVING, Pandas groupby/merge/filter
- INVESTIGATOR: Window functions LAG/LEAD/RANK, multi-rule Python functions, pattern detection
- ARCHITECT: Machine learning with scikit-learn, feature engineering from transaction data

Current level: {level_code}
Current topic: {topic}

Generate the JSON now:
"""


def build_hint_prompt(challenge: str, user_code: str, error_msg: str, hint_level: int) -> str:
    return f"""
{SYSTEM_CONTEXT}

A student is working on this Financial Crime Analytics challenge:
CHALLENGE: {challenge}

Their code attempt:
```
{user_code}
```

Error / Wrong result:
{error_msg}

Generate hint level {hint_level} of 3 (1=vague, 3=almost the answer).
Keep it under 80 words. Be encouraging. Use banking/AML terminology.
Return ONLY the hint text, no JSON, no markdown.
"""


def call_gemini(model, prompt: str) -> str | None:
    """Call Gemini and return text response."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"🔴 Gemini API error: {e}")
        return None


def parse_lesson_json(raw: str) -> dict | None:
    """Extract and parse JSON from Gemini response."""
    # Strip markdown fences if present
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON object
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        return None


# ─────────────────────────────────────────────────────────────
#  SQLITE EXECUTION ENGINE
# ─────────────────────────────────────────────────────────────
def run_sql(query: str, df: pd.DataFrame, table_name: str) -> tuple[pd.DataFrame | None, str | None]:
    """Execute SQL against in-memory SQLite loaded with df."""
    try:
        conn = sqlite3.connect(":memory:")
        df.to_sql(table_name, conn, index=False, if_exists="replace")
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result, None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────
#  PYTHON SAFE EXEC ENGINE
# ─────────────────────────────────────────────────────────────
def run_python(code: str, df: pd.DataFrame) -> tuple[str, str | None]:
    """
    Safely exec user Python code in a sandboxed namespace.
    Returns (stdout_output, error_or_None).
    """
    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    namespace = {
        "df": df.copy(),
        "pd": pd,
        "print": print,
    }
    # Allow common libs
    try:
        import numpy as np
        namespace["np"] = np
    except ImportError:
        pass
    try:
        import sklearn
        namespace["sklearn"] = sklearn
    except ImportError:
        pass

    error = None
    try:
        exec(code, namespace)  # noqa: S102
    except Exception:
        error = traceback.format_exc()
    finally:
        sys.stdout = old_stdout

    output = buffer.getvalue()

    # If user assigned result variable, show it
    for var in ["result", "flagged", "output", "suspicious", "model_output", "predictions"]:
        if var in namespace:
            val = namespace[var]
            if isinstance(val, pd.DataFrame):
                output += f"\n[DataFrame '{var}']:\n{val.to_string()}"
            elif isinstance(val, (list, dict)):
                output += f"\n{var} = {val}"
            elif val is not None:
                output += f"\n{var} = {val}"

    return output.strip(), error


# ─────────────────────────────────────────────────────────────
#  DATA SETUP EXECUTOR
# ─────────────────────────────────────────────────────────────
def execute_data_setup(code: str) -> tuple[pd.DataFrame | None, str | None]:
    """Run the AI-generated data_setup code and return the df."""
    namespace = {"pd": pd}
    try:
        import numpy as np
        namespace["np"] = np
    except ImportError:
        pass
    try:
        exec(code, namespace)  # noqa: S102
        df = namespace.get("df")
        if df is None or not isinstance(df, pd.DataFrame):
            return None, "data_setup code did not create a variable named `df`."
        return df, None
    except Exception:
        return None, traceback.format_exc()


# ─────────────────────────────────────────────────────────────
#  XP & BADGE SYSTEM
# ─────────────────────────────────────────────────────────────
def award_xp(amount: int):
    st.session_state.xp += amount
    # Check badges
    for xp_threshold, (icon, name, desc) in BADGES.items():
        if st.session_state.xp >= xp_threshold and name not in st.session_state.badges_earned:
            st.session_state.badges_earned.append(name)
            st.balloons()
            st.success(f"🏅 BADGE UNLOCKED: {icon} **{name}** — {desc}")


def xp_to_level_progress() -> float:
    """Return 0.0–1.0 progress within current XP band."""
    thresholds = list(BADGES.keys())
    xp = st.session_state.xp
    for i, t in enumerate(thresholds):
        if xp < t:
            prev = thresholds[i - 1] if i > 0 else 0
            return (xp - prev) / (t - prev)
    return 1.0


# ─────────────────────────────────────────────────────────────
#  FALLBACK OFFLINE LESSON (no API key)
# ─────────────────────────────────────────────────────────────
OFFLINE_LESSON = {
    "topic": "SQL SELECT & WHERE — Transaction Filtering",
    "theory": (
        "In financial crime analytics, the first weapon in your arsenal is the ability to "
        "retrieve and filter transaction data. SQL's SELECT statement lets you specify which "
        "columns you want, while WHERE acts as your filter gate.\n\n"
        "At HSBC, compliance analysts run thousands of queries daily to isolate suspicious "
        "transactions. A common first step is filtering by amount threshold — transactions "
        "just under the $10,000 regulatory reporting limit (known as 'structuring') are "
        "prime targets.\n\n"
        "Today's mission: learn SELECT + WHERE to pull transactions that deserve a second look."
    ),
    "data_setup": """import pandas as pd
df = pd.DataFrame({
    'transaction_id': ['TXN_001','TXN_002','TXN_003','TXN_004','TXN_005',
                       'TXN_006','TXN_007','TXN_008'],
    'customer_name':  ['Mehta Traders','GlobalFin Ltd','Shah Ent.','Ravi Exports',
                       'Delta Corp','Apex Holdings','Sunrise FX','NovaBridge'],
    'amount':         [9800, 4200, 9500, 500, 15000, 9900, 3200, 9750],
    'currency':       ['USD','USD','USD','INR','USD','USD','GBP','USD'],
    'beneficiary_country': ['Pakistan','UAE','India','India','Russia','Pakistan','UK','Nigeria'],
    'transaction_type': ['CASH','WIRE','CASH','WIRE','WIRE','CASH','WIRE','CASH'],
    'is_flagged': [False, False, False, False, True, False, False, False]
})""",
    "challenge": (
        "Your compliance manager suspects structuring activity. "
        "Write a SQL query to find all CASH transactions where amount > 9000 "
        "from the `transactions` table. "
        "Order results by amount descending."
    ),
    "sql_table_name": "transactions",
    "solution_sql": "SELECT * FROM transactions WHERE transaction_type = 'CASH' AND amount > 9000 ORDER BY amount DESC;",
    "solution_python": (
        "result = df[(df['transaction_type'] == 'CASH') & (df['amount'] > 9000)]\n"
        "result = result.sort_values('amount', ascending=False)\n"
        "print(result)"
    ),
    "expected_output_description": "3 cash transactions with amounts 9900, 9800, 9750 from high-risk countries.",
    "hints": [
        "Think about what two conditions you need to check simultaneously.",
        "Use AND to combine transaction_type filter with an amount filter in your WHERE clause.",
        "WHERE transaction_type = 'CASH' AND amount > 9000 — then add ORDER BY amount DESC.",
    ],
}


# ─────────────────────────────────────────────────────────────
#  UI COMPONENTS
# ─────────────────────────────────────────────────────────────
def render_header():
    st.markdown(CYBER_CSS, unsafe_allow_html=True)
    st.markdown('<div class="dojo-header">⬡ THE FINCRIME DOJO ⬡</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dojo-subheader">HSBC FINANCIAL CRIME ANALYTICS TRAINING ENGINE — GOD MODE ACTIVE</div>',
        unsafe_allow_html=True,
    )


def render_hud(level_name: str, level_cfg: dict):
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("⚡ XP", f"{st.session_state.xp:,}")
    with col2:
        st.metric("📅 DAY", st.session_state.day)
    with col3:
        st.metric("🔥 STREAK", f"{st.session_state.streak}d")
    with col4:
        st.metric("✅ SOLVED", st.session_state.correct_solutions)
    with col5:
        st.metric("🏅 BADGES", len(st.session_state.badges_earned))

    # XP bar
    progress = xp_to_level_progress()
    st.markdown(
        f"""
        <div class="section-label">XP PROGRESS ── NEXT MILESTONE</div>
        <div class="xp-bar-container">
          <div class="xp-bar-fill" style="width:{int(progress*100)}%"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Badges row
    if st.session_state.badges_earned:
        badges_html = "".join(
            f'<span class="badge">{b}</span>'
            for b in st.session_state.badges_earned
        )
        st.markdown(badges_html, unsafe_allow_html=True)


def render_theory(lesson: dict, level_cfg: dict):
    color = level_cfg["color"]
    st.markdown(
        f"""
        <div class="dojo-card {color}">
          <div class="card-title {color}">▸ 01 / CONCEPT DOWNLOAD</div>
          <div style="font-family:var(--font-body); line-height:1.8; font-size:0.9rem; color:#b8e8c8;">
            {lesson['theory'].replace(chr(10), '<br>')}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_data_viewer(df: pd.DataFrame, level_cfg: dict):
    color = level_cfg["color"]
    st.markdown(
        f'<div class="card-title {color}">▸ 02 / LIVE BANK DATA — INVESTIGATION DATASET</div>',
        unsafe_allow_html=True,
    )
    st.dataframe(
        df.style.set_properties(**{
            "background-color": "#0d1117",
            "color": "#00ff88",
            "border": "1px solid #1a3a1a",
            "font-family": "Share Tech Mono, monospace",
            "font-size": "0.8rem",
        }),
        use_container_width=True,
        height=300,
    )
    st.markdown(
        f'<div class="terminal-block info">▶ {len(df)} records loaded │ {len(df.columns)} columns │ '
        f'Table: <b>{st.session_state.current_lesson.get("sql_table_name","transactions")}</b></div>',
        unsafe_allow_html=True,
    )


def render_challenge(lesson: dict, level_cfg: dict):
    color = level_cfg["color"]
    st.markdown(
        f"""
        <div class="dojo-card {color}">
          <div class="card-title {color}">▸ 03 / ACTIVE CASE — YOUR MISSION</div>
          <div style="font-family:var(--font-mono); font-size:0.88rem; color:#ffe080; line-height:1.7;">
            {lesson['challenge']}
          </div>
          <div style="margin-top:0.8rem; font-family:var(--font-mono); font-size:0.75rem; color:var(--text-dim);">
            EXPECTED ▸ {lesson.get('expected_output_description', '')}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_terminal(lesson: dict, df: pd.DataFrame, level_cfg: dict, model):
    table_name = lesson.get("sql_table_name", "transactions")
    color = level_cfg["color"]

    st.markdown(
        f'<div class="card-title {color}">▸ 04 / DOJO TERMINAL — SUBMIT YOUR SOLUTION</div>',
        unsafe_allow_html=True,
    )

    tab_sql, tab_py, tab_solution = st.tabs(["  💾 SQL TERMINAL  ", "  🐍 PYTHON TERMINAL  ", "  🔐 REVEAL SOLUTION  "])

    # ── SQL Tab ──────────────────────────────────────────────
    with tab_sql:
        st.markdown(
            f'<div class="terminal-block" style="margin-bottom:0.5rem;">'
            f'┌─[DOJO@HSBC:SQL]─$ SELECT * FROM {table_name}...<br>'
            f'└─ Table loaded ✓ │ Write your query below</div>',
            unsafe_allow_html=True,
        )
        sql_input = st.text_area(
            label="SQL Query",
            value=st.session_state.sql_code,
            height=140,
            placeholder=f"SELECT ... FROM {table_name} WHERE ...",
            key="sql_input_area",
            label_visibility="collapsed",
        )
        col_run, col_hint, col_reset = st.columns([2, 2, 1])
        with col_run:
            run_sql_btn = st.button("▶  EXECUTE SQL", key="run_sql", use_container_width=True)
        with col_hint:
            hint_sql_btn = st.button("💡  REQUEST HINT", key="hint_sql", use_container_width=True)
        with col_reset:
            if st.button("↺", key="reset_sql"):
                st.session_state.sql_code = ""
                st.session_state.sql_result = None
                st.session_state.sql_feedback = ""
                st.rerun()

        if run_sql_btn and sql_input.strip():
            st.session_state.sql_code = sql_input
            award_xp(5)  # Micro XP for trying
            result_df, err = run_sql(sql_input, df, table_name)
            if err:
                st.session_state.sql_result = None
                st.session_state.sql_feedback = f"🔴 SQL ERROR:\n{err}"
                # AI hint on error
                if model:
                    with st.spinner("GEMINI ANALYZING ERROR..."):
                        hint = call_gemini(
                            model,
                            build_hint_prompt(lesson["challenge"], sql_input, err, 2),
                        )
                        if hint:
                            st.session_state.sql_feedback += f"\n\n💡 AI MENTOR:\n{hint}"
            else:
                st.session_state.sql_result = result_df
                st.session_state.sql_feedback = f"✅ QUERY EXECUTED — {len(result_df)} rows returned."
                st.session_state.correct_solutions += 1
                award_xp(level_cfg["xp_per_challenge"])
                st.session_state.challenges_done += 1

        if hint_sql_btn and model:
            with st.spinner("REQUESTING INTEL..."):
                hint_level = min(3, (st.session_state.challenges_done % 3) + 1)
                hint = call_gemini(
                    model,
                    build_hint_prompt(
                        lesson["challenge"],
                        sql_input or "(no code yet)",
                        "User requested hint",
                        hint_level,
                    ),
                )
                if hint:
                    st.session_state.hint_text = hint

        # Output
        if st.session_state.sql_feedback:
            is_error = "ERROR" in st.session_state.sql_feedback or "🔴" in st.session_state.sql_feedback
            css_cls = "error" if is_error else ""
            st.markdown(
                f'<div class="terminal-block {css_cls}">{st.session_state.sql_feedback}</div>',
                unsafe_allow_html=True,
            )
        if st.session_state.sql_result is not None:
            st.markdown('<div class="section-label">QUERY RESULT</div>', unsafe_allow_html=True)
            st.dataframe(st.session_state.sql_result, use_container_width=True)

        if st.session_state.hint_text:
            st.markdown(
                f'<div class="terminal-block amber">💡 INTEL RECEIVED:\n{st.session_state.hint_text}</div>',
                unsafe_allow_html=True,
            )

    # ── Python Tab ───────────────────────────────────────────
    with tab_py:
        st.markdown(
            '<div class="terminal-block" style="margin-bottom:0.5rem;">'
            '┌─[DOJO@HSBC:PYTHON]─$ df is preloaded ✓<br>'
            '└─ pandas as pd │ numpy as np │ sklearn available</div>',
            unsafe_allow_html=True,
        )
        py_input = st.text_area(
            label="Python Code",
            value=st.session_state.py_code,
            height=180,
            placeholder="# Use `df` variable — it's already loaded\nresult = df[df['amount'] > 9000]\nprint(result)",
            key="py_input_area",
            label_visibility="collapsed",
        )
        col_run2, col_hint2, col_reset2 = st.columns([2, 2, 1])
        with col_run2:
            run_py_btn = st.button("▶  EXECUTE PYTHON", key="run_py", use_container_width=True)
        with col_hint2:
            hint_py_btn = st.button("💡  REQUEST HINT", key="hint_py", use_container_width=True)
        with col_reset2:
            if st.button("↺", key="reset_py"):
                st.session_state.py_code = ""
                st.session_state.py_result = None
                st.session_state.py_feedback = ""
                st.rerun()

        if run_py_btn and py_input.strip():
            st.session_state.py_code = py_input
            award_xp(5)
            output, err = run_python(py_input, df)
            if err:
                st.session_state.py_result = None
                st.session_state.py_feedback = f"🔴 PYTHON TRACEBACK:\n{err}"
                if model:
                    with st.spinner("GEMINI DEBUGGING..."):
                        hint = call_gemini(
                            model,
                            build_hint_prompt(lesson["challenge"], py_input, err, 2),
                        )
                        if hint:
                            st.session_state.py_feedback += f"\n\n💡 AI MENTOR:\n{hint}"
            else:
                st.session_state.py_result = output
                st.session_state.py_feedback = "✅ CODE EXECUTED SUCCESSFULLY"
                st.session_state.correct_solutions += 1
                award_xp(level_cfg["xp_per_challenge"])
                st.session_state.challenges_done += 1

        if hint_py_btn and model:
            with st.spinner("REQUESTING INTEL..."):
                hint = call_gemini(
                    model,
                    build_hint_prompt(
                        lesson["challenge"],
                        py_input or "(no code yet)",
                        "User requested hint",
                        2,
                    ),
                )
                if hint:
                    st.session_state.hint_text = hint
                    st.rerun()

        if st.session_state.py_feedback:
            is_error = "TRACEBACK" in st.session_state.py_feedback or "🔴" in st.session_state.py_feedback
            css_cls = "error" if is_error else ""
            st.markdown(
                f'<div class="terminal-block {css_cls}">{st.session_state.py_feedback}</div>',
                unsafe_allow_html=True,
            )
        if st.session_state.py_result:
            st.markdown(
                f'<div class="terminal-block">{st.session_state.py_result}</div>',
                unsafe_allow_html=True,
            )

    # ── Solution Tab (locked feel) ────────────────────────────
    with tab_solution:
        with st.expander("⚠️  REVEAL SOLUTION — Try yourself first! This costs 50 XP.", expanded=False):
            if st.button("🔓 UNLOCK SOLUTION (-50 XP)", key="unlock_sol"):
                st.session_state.xp = max(0, st.session_state.xp - 50)

            st.markdown("**📝 SQL Solution:**")
            st.code(lesson.get("solution_sql", "N/A"), language="sql")
            st.markdown("**🐍 Python Solution:**")
            st.code(lesson.get("solution_python", "N/A"), language="python")


def render_history():
    if st.session_state.history:
        with st.expander("📜 SESSION LOG", expanded=False):
            for entry in reversed(st.session_state.history[-10:]):
                st.markdown(
                    f'<div class="terminal-block" style="margin-bottom:0.3rem; font-size:0.75rem;">'
                    f'{entry}</div>',
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
def render_sidebar() -> tuple[str | None, dict, str]:
    with st.sidebar:
        st.markdown(
            '<div style="font-family:\'Orbitron\',monospace; font-size:0.7rem; '
            'letter-spacing:3px; color:#00ff88; text-shadow:0 0 8px #00cc66; '
            'margin-bottom:1rem;">⬡ DOJO CONFIG</div>',
            unsafe_allow_html=True,
        )

        # Check if the key is in the "Vault" (Secrets) first
    if "GEMINI_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_KEY"]
        st.sidebar.success("🟢 API Key Loaded from Secrets")
    else:
        # If not found, ask the user to type it in manually
        api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")


        if api_key:
            st.markdown(
                '<div class="terminal-block" style="font-size:0.72rem; padding:0.4rem 0.8rem;">'
                '✅ API KEY LOADED<br>🟢 AI TUTOR: ONLINE</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="terminal-block amber" style="font-size:0.72rem; padding:0.4rem 0.8rem;">'
                '⚠️ NO API KEY<br>🟡 OFFLINE MODE: DEMO LESSON</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        level_name = st.selectbox(
            "DIFFICULTY LEVEL",
            list(LEVELS.keys()),
            index=0,
        )
        level_cfg = LEVELS[level_name]

        st.markdown(
            f'<div class="terminal-block info" style="font-size:0.72rem; padding:0.5rem 0.8rem;">'
            f'LEVEL: {level_cfg["code"]}<br>'
            f'XP/CHALLENGE: +{level_cfg["xp_per_challenge"]}<br>'
            f'{level_cfg["description"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            '<div style="font-family:\'Orbitron\',monospace; font-size:0.65rem; '
            'letter-spacing:2px; color:#4a7a5a; margin-bottom:0.5rem;">COMMANDS</div>',
            unsafe_allow_html=True,
        )

        cmd_map = {
            "START DAY": "Load first lesson",
            "NEXT":      "Next challenge",
            "HINT":      "Request AI hint",
            "RESET XP":  "Reset your progress",
        }
        for cmd, desc in cmd_map.items():
            st.markdown(
                f'<div style="font-family:\'Share Tech Mono\',monospace; font-size:0.72rem; '
                f'color:#4a7a5a; margin:0.15rem 0;">'
                f'<span style="color:#00ff88;">{cmd}</span> — {desc}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        if st.button("🔄  RESET ALL PROGRESS", key="reset_all"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_session()
            st.rerun()

        # Earned badges
        if st.session_state.badges_earned:
            st.markdown("---")
            st.markdown(
                '<div style="font-family:\'Orbitron\',monospace; font-size:0.65rem; '
                'letter-spacing:2px; color:#4a7a5a; margin-bottom:0.5rem;">BADGES EARNED</div>',
                unsafe_allow_html=True,
            )
            for b in st.session_state.badges_earned:
                for _, (icon, name, desc) in BADGES.items():
                    if name == b:
                        st.markdown(
                            f'<div class="badge amber">{icon} {name}</div><br>',
                            unsafe_allow_html=True,
                        )

        st.markdown("---")
        st.markdown(
            '<div style="font-family:\'Share Tech Mono\',monospace; font-size:0.65rem; '
            'color:#2a4a2a; text-align:center; line-height:1.6;">'
            'FinCrime Dojo v1.0<br>Built for HSBC-style<br>AML Analytics Training</div>',
            unsafe_allow_html=True,
        )

    return api_key or None, level_cfg, level_name


# ─────────────────────────────────────────────────────────────
#  LESSON LOADER
# ─────────────────────────────────────────────────────────────
def load_lesson(model, level_cfg: dict, level_name: str):
    """Fetch a new lesson from Gemini or use offline fallback."""
    # Pick topic
    topics = level_cfg["topics"]
    idx = st.session_state.topic_index.get(level_name, 0)
    topic = topics[idx % len(topics)]
    st.session_state.topic_index[level_name] = idx + 1

    lesson = None
    if model:
        with st.spinner(f"⚡ GEMINI GENERATING LESSON: {topic}..."):
            raw = call_gemini(model, build_lesson_prompt(level_cfg["code"], topic, st.session_state.day))
            if raw:
                lesson = parse_lesson_json(raw)
                if lesson is None:
                    st.warning("⚠️ JSON parse failed — using offline lesson.")

    if lesson is None:
        lesson = OFFLINE_LESSON.copy()
        lesson["topic"] = topic if not model else lesson["topic"]

    # Execute data setup
    df, err = execute_data_setup(lesson["data_setup"])
    if err or df is None:
        st.error(f"Data setup error: {err}")
        # Build minimal fallback df
        df = pd.DataFrame({
            "transaction_id": ["TXN_001", "TXN_002", "TXN_003"],
            "amount": [9800, 4200, 15000],
            "customer_name": ["Mehta Traders", "GlobalFin", "Shah Ent."],
            "is_flagged": [False, False, True],
        })

    # Update state
    st.session_state.current_lesson = lesson
    st.session_state.current_df = df
    st.session_state.sql_result = None
    st.session_state.py_result = None
    st.session_state.sql_feedback = ""
    st.session_state.py_feedback = ""
    st.session_state.hint_text = ""
    st.session_state.sql_code = ""
    st.session_state.py_code = ""
    st.session_state.day += 1
    st.session_state.challenges_done += 1

    # Log to history
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.history.append(
        f"[{ts}] DAY {st.session_state.day} LOADED ─ {lesson['topic']} ─ LEVEL: {level_cfg['code']}"
    )

    award_xp(10)  # Micro XP for starting
    st.rerun()


# ─────────────────────────────────────────────────────────────
#  WELCOME SCREEN
# ─────────────────────────────────────────────────────────────
def render_welcome():
    st.markdown(
        """
        <div class="dojo-card" style="text-align:center; padding:3rem 2rem;">
          <div style="font-family:'Orbitron',monospace; font-size:3rem; color:#00ff88;
                      text-shadow:0 0 30px #00cc66, 0 0 60px #00880033; margin-bottom:1rem;">
            ⬡
          </div>
          <div style="font-family:'Orbitron',monospace; font-size:1rem; color:#00ff88;
                      letter-spacing:4px; margin-bottom:1.5rem;">
            SYSTEM READY — AWAITING OPERATIVE
          </div>
          <div style="font-family:'Share Tech Mono',monospace; font-size:0.85rem;
                      color:#4a7a5a; line-height:2; max-width:600px; margin:0 auto 2rem;">
            ┌── MISSION BRIEF ────────────────────────────┐<br>
            │ Train to detect: AML · KYC · Fraud · SARs  │<br>
            │ Weapons: Python · SQL · Pandas · Scikit-ML  │<br>
            │ Target: HSBC-grade Financial Crime Analyst  │<br>
            └─────────────────────────────────────────────┘
          </div>
          <div style="font-family:'Share Tech Mono',monospace; font-size:0.8rem; color:#2a5a3a;">
            → Enter your Gemini API key in the sidebar for AI-powered lessons<br>
            → Or click START DAY for an offline demo lesson<br>
            → Select your difficulty level and begin
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────────────────────
def main():
    render_header()
    api_key, level_cfg, level_name = render_sidebar()

    # Init Gemini model
    model = get_gemini_client(api_key) if api_key else None

    # HUD
    render_hud(level_name, level_cfg)
    st.markdown("---")

    # Control buttons
    col_start, col_next, col_spacer = st.columns([2, 2, 6])
    with col_start:
        start_btn = st.button(
            "▶  START DAY" if st.session_state.day == 0 else "▶  NEW LESSON",
            key="start_btn",
            use_container_width=True,
        )
    with col_next:
        next_btn = st.button("⏭  NEXT CHALLENGE", key="next_btn", use_container_width=True)

    if start_btn or next_btn:
        load_lesson(model, level_cfg, level_name)

    # Main content
    if st.session_state.current_lesson is None:
        render_welcome()
    else:
        lesson = st.session_state.current_lesson
        df = st.session_state.current_df

        # Day banner
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
              <div style="font-family:'Orbitron',monospace; font-size:0.65rem;
                          letter-spacing:3px; color:var(--text-dim);">
                DAY {st.session_state.day}
              </div>
              <div style="font-family:'Orbitron',monospace; font-size:1rem;
                          color:#00ff88; text-shadow:0 0 10px #00cc66; letter-spacing:2px;">
                {lesson['topic'].upper()}
              </div>
              <span class="badge {level_cfg['color']}">{level_cfg['code']}</span>
              <span class="badge amber">+{level_cfg['xp_per_challenge']} XP</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Layout: left = theory + data, right = terminal
        left_col, right_col = st.columns([4, 6], gap="medium")

        with left_col:
            render_theory(lesson, level_cfg)
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            render_data_viewer(df, level_cfg)
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            render_challenge(lesson, level_cfg)

        with right_col:
            render_terminal(lesson, df, level_cfg, model)

        st.markdown("---")
        render_history()

    # Footer
    st.markdown(
        """
        <div style="text-align:center; font-family:'Share Tech Mono',monospace;
                    font-size:0.65rem; color:#1a3a1a; margin-top:2rem; letter-spacing:2px;">
          FINCRIME DOJO ── HSBC ANALYTICS DIVISION ── ALL TRANSACTIONS SIMULATED ── NO REAL DATA
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
