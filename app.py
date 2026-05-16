"""
╔══════════════════════════════════════════════════════════════╗
║           THE FINCRIME DOJO  —  GOD MODE v2.0               ║
║   Multi-Provider AI  ·  SQLite  ·  Persistence  ·  Pandas   ║
╚══════════════════════════════════════════════════════════════╝
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

# ── Optional cookie manager ────────────────────────────────────
try:
    import extra_streamlit_components as stx
    COOKIES_AVAILABLE = True
except ImportError:
    COOKIES_AVAILABLE = False


# ╔══════════════════════════════════════════════════════════════╗
# ║              PROVIDER REGISTRY                              ║
# ║  To add a new provider: add one entry here. That's it.      ║
# ╚══════════════════════════════════════════════════════════════╝

PROVIDER_REGISTRY = {

    "Google Gemini": {
        "icon":          "🔵",
        "color":         "#4285F4",
        "lib":           "google-generativeai",
        "install":       "pip install google-generativeai",
        "secret_keys":   ["GEMINI_KEY", "gemini_key", "GEMINI_API_KEY"],
        "models": [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ],
        "default_model": "gemini-2.5-flash",
        "base_url":      None,   # not needed for Gemini SDK
    },

    "OpenAI": {
        "icon":          "🟢",
        "color":         "#10A37F",
        "lib":           "openai",
        "install":       "pip install openai",
        "secret_keys":   ["OPENAI_KEY", "openai_key", "OPENAI_API_KEY"],
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ],
        "default_model": "gpt-4o",
        "base_url":      None,
    },

    "Anthropic Claude": {
        "icon":          "🟡",
        "color":         "#D4A847",
        "lib":           "anthropic",
        "install":       "pip install anthropic",
        "secret_keys":   ["ANTHROPIC_KEY", "anthropic_key", "ANTHROPIC_API_KEY"],
        "models": [
            "claude-sonnet-4-6",
            "claude-haiku-4-5-20251001",
            "claude-opus-4-6",
            "claude-3-5-sonnet-20241022",
            "claude-3-haiku-20240307",
        ],
        "default_model": "claude-sonnet-4-6",
        "base_url":      None,
    },

    "Groq": {
        "icon":          "🔴",
        "color":         "#FF4F00",
        "lib":           "groq",
        "install":       "pip install groq",
        "secret_keys":   ["GROQ_KEY", "groq_key", "GROQ_API_KEY"],
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
        "default_model": "llama-3.3-70b-versatile",
        "base_url":      "https://api.groq.com/openai/v1",
    },

    "Mistral": {
        "icon":          "🟠",
        "color":         "#FF7000",
        "lib":           "mistralai",
        "install":       "pip install mistralai",
        "secret_keys":   ["MISTRAL_KEY", "mistral_key", "MISTRAL_API_KEY"],
        "models": [
            "mistral-large-latest",
            "mistral-small-latest",
            "open-mixtral-8x22b",
            "codestral-latest",
        ],
        "default_model": "mistral-large-latest",
        "base_url":      None,
    },

    "OpenRouter": {
        "icon":          "🟣",
        "color":         "#7C3AED",
        "lib":           "openai",      # OpenRouter uses OpenAI-compatible API
        "install":       "pip install openai",
        "secret_keys":   ["OPENROUTER_KEY", "openrouter_key", "OPENROUTER_API_KEY"],
        "models": [
            "meta-llama/llama-3.3-70b-instruct",
            "google/gemini-2.5-flash",
            "anthropic/claude-sonnet-4-6",
            "deepseek/deepseek-r1",
            "qwen/qwen-2.5-72b-instruct",
        ],
        "default_model": "meta-llama/llama-3.3-70b-instruct",
        "base_url":      "https://openrouter.ai/api/v1",
    },

}

# Keys that unlock providers via secrets.toml — flat lookup for sidebar
ALL_SECRET_KEYS = {
    secret: provider
    for provider, cfg in PROVIDER_REGISTRY.items()
    for secret in cfg["secret_keys"]
}


# ╔══════════════════════════════════════════════════════════════╗
# ║              UNIFIED AI CLIENT                              ║
# ╚══════════════════════════════════════════════════════════════╝

class AIClient:
    """
    Single interface for all providers.
    Usage:
        client = AIClient(provider, model, api_key, system_prompt)
        text, err = client.generate(user_prompt)
    """

    def __init__(self, provider: str, model: str, api_key: str, system_prompt: str = ""):
        self.provider      = provider
        self.model         = model
        self.api_key       = api_key
        self.system_prompt = system_prompt
        self._cfg          = PROVIDER_REGISTRY.get(provider, {})

    # ── Public ────────────────────────────────────────────────
    def generate(self, prompt: str, max_tokens: int = 2048, temperature: float = 0.7) -> tuple[str, str]:
        try:
            dispatch = {
                "Google Gemini":    self._gemini,
                "OpenAI":           self._openai_compat,
                "Anthropic Claude": self._anthropic,
                "Groq":             self._openai_compat,
                "Mistral":          self._mistral,
                "OpenRouter":       self._openai_compat,
            }
            fn = dispatch.get(self.provider)
            if fn is None:
                return "", f"Unknown provider: {self.provider}"
            return fn(prompt, max_tokens, temperature)
        except Exception as e:
            return "", f"{self.provider} error: {e}"

    def test_connection(self) -> tuple[bool, str]:
        """Quick ping to verify the key works."""
        # Use a neutral, finance-safe prompt that won't be blocked by safety filters
        text, err = self.generate(
            "What is the standard abbreviation for Anti-Money Laundering? Reply in 3 words or less.",
            max_tokens=20, temperature=0,
        )
        if err:
            return False, err
        return True, text.strip()[:60]

    # ── Provider implementations ───────────────────────────────

    def _gemini(self, prompt, max_tokens, temperature):
        try:
            import google.generativeai as genai
        except ImportError:
            return "", "google-generativeai not installed. Run: pip install google-generativeai"
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=self.system_prompt or None,
        )
        resp = model.generate_content(
            prompt,
            generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
        )
        # Safely extract text — avoid resp.text which raises if parts are empty
        # (e.g. safety filter blocked the response, or model returned no content)
        try:
            candidates = resp.candidates or []
            if not candidates:
                finish = getattr(resp, "prompt_feedback", None)
                reason = getattr(finish, "block_reason", "UNKNOWN")
                return "", f"Gemini returned no candidates. Block reason: {reason}"
            parts = candidates[0].content.parts or []
            if not parts:
                finish_reason = getattr(candidates[0], "finish_reason", "UNKNOWN")
                return "", f"Gemini candidate has no content parts. Finish reason: {finish_reason}"
            text = "".join(getattr(p, "text", "") for p in parts)
            return text, ""
        except Exception as parse_err:
            # Last-resort fallback — try the quick accessor anyway
            try:
                return resp.text, ""
            except Exception:
                return "", f"Could not parse Gemini response: {parse_err}"

    def _openai_compat(self, prompt, max_tokens, temperature):
        """Handles OpenAI, Groq, OpenRouter — all use OpenAI-compatible API."""
        try:
            from openai import OpenAI
        except ImportError:
            return "", "openai not installed. Run: pip install openai"
        kwargs = {"api_key": self.api_key}
        base_url = self._cfg.get("base_url")
        if base_url:
            kwargs["base_url"] = base_url
        client = OpenAI(**kwargs)
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content, ""

    def _anthropic(self, prompt, max_tokens, temperature):
        try:
            import anthropic
        except ImportError:
            return "", "anthropic not installed. Run: pip install anthropic"
        client = anthropic.Anthropic(api_key=self.api_key)
        kwargs = dict(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        if self.system_prompt:
            kwargs["system"] = self.system_prompt
        resp = client.messages.create(**kwargs)
        return resp.content[0].text, ""

    def _mistral(self, prompt, max_tokens, temperature):
        try:
            from mistralai import Mistral
        except ImportError:
            return "", "mistralai not installed. Run: pip install mistralai"
        client = Mistral(api_key=self.api_key)
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.complete(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content, ""


# ╔══════════════════════════════════════════════════════════════╗
# ║              SECRETS RESOLVER                               ║
# ╚══════════════════════════════════════════════════════════════╝

def resolve_key_for_provider(provider: str) -> tuple[str, str]:
    """
    Returns (api_key, source) for a given provider.
    source is one of: "SECRETS" | "MANUAL" | ""
    """
    cfg = PROVIDER_REGISTRY.get(provider, {})
    # 1. Try secrets.toml
    for secret_name in cfg.get("secret_keys", []):
        try:
            key = st.secrets[secret_name]
            if key and str(key).strip():
                return str(key).strip(), "SECRETS"
        except (KeyError, FileNotFoundError):
            continue
    # 2. Manual input stored in session state
    manual = st.session_state.get(f"_manual_key_{provider}", "")
    if manual:
        return manual, "MANUAL"
    return "", ""


def scan_available_providers() -> dict[str, str]:
    """Return {provider_name: key_source} for providers that have a key configured."""
    available = {}
    for provider in PROVIDER_REGISTRY:
        key, source = resolve_key_for_provider(provider)
        if key:
            available[provider] = source
    return available


# ╔══════════════════════════════════════════════════════════════╗
# ║                   PAGE CONFIG & CSS                         ║
# ╚══════════════════════════════════════════════════════════════╝

st.set_page_config(
    page_title="FinCrime Dojo",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

CYBERPUNK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&family=VT323&display=swap');

:root {
  --green:       #00ff9f;
  --green-dim:   #00cc7a;
  --green-dark:  #003d26;
  --green-glow:  rgba(0,255,159,0.15);
  --amber:       #ffb000;
  --red:         #ff3c5c;
  --blue:        #00d4ff;
  --purple:      #bf5fff;
  --bg-black:    #020c07;
  --bg-panel:    #050f0a;
  --bg-card:     #0a1a10;
  --bg-terminal: #000a05;
  --border:      rgba(0,255,159,0.2);
  --border-hot:  rgba(0,255,159,0.6);
  --font-mono:   'Share Tech Mono','Courier New',monospace;
  --font-display:'Orbitron',monospace;
  --font-vt:     'VT323',monospace;
}

html,body,.stApp { background-color:var(--bg-black) !important; color:var(--green) !important; font-family:var(--font-mono) !important; }

.stApp::before {
  content:""; position:fixed; top:0;left:0;right:0;bottom:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.04) 2px,rgba(0,0,0,0.04) 4px);
  pointer-events:none; z-index:9999;
}

[data-testid="stSidebar"] { background:var(--bg-panel) !important; border-right:1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color:var(--green) !important; font-family:var(--font-mono) !important; }
[data-testid="stSidebar"] input  { background:var(--bg-terminal) !important; border:1px solid var(--border) !important; color:var(--green) !important; }
[data-testid="stSidebar"] select { background:var(--bg-terminal) !important; color:var(--green) !important; }

h1,h2,h3,h4 { font-family:var(--font-display) !important; color:var(--green) !important; text-shadow:0 0 20px var(--green),0 0 40px rgba(0,255,159,0.3) !important; letter-spacing:2px !important; }
p,li,label,.stMarkdown { font-family:var(--font-mono) !important; color:var(--green) !important; }
.stMarkdown code { background:var(--bg-terminal) !important; color:var(--amber) !important; border:1px solid var(--border) !important; font-family:var(--font-mono) !important; padding:2px 6px !important; border-radius:3px !important; }
.stMarkdown pre  { background:var(--bg-terminal) !important; border:1px solid var(--border) !important; border-left:3px solid var(--green) !important; color:var(--green) !important; font-family:var(--font-mono) !important; padding:16px !important; border-radius:4px !important; }

.stButton>button { background:transparent !important; border:1px solid var(--green) !important; color:var(--green) !important; font-family:var(--font-display) !important; font-size:0.72rem !important; letter-spacing:2px !important; text-transform:uppercase !important; padding:10px 24px !important; transition:all 0.2s ease !important; box-shadow:0 0 10px var(--green-glow) !important; }
.stButton>button:hover { background:var(--green-glow) !important; box-shadow:0 0 20px var(--green),0 0 40px rgba(0,255,159,0.2) !important; transform:translateY(-1px) !important; }

.stTextArea textarea { background:var(--bg-terminal) !important; color:var(--green) !important; font-family:var(--font-mono) !important; font-size:0.9rem !important; border:1px solid var(--border) !important; border-radius:4px !important; caret-color:var(--green) !important; }
.stTextArea textarea:focus { border-color:var(--green) !important; box-shadow:0 0 10px var(--green-glow) !important; }

.stSelectbox>div>div { background:var(--bg-terminal) !important; border:1px solid var(--border) !important; color:var(--green) !important; }
.stDataFrame { border:1px solid var(--border) !important; border-radius:4px !important; }

.stTabs [data-baseweb="tab-list"]  { background:var(--bg-panel) !important; border-bottom:1px solid var(--border) !important; gap:4px !important; }
.stTabs [data-baseweb="tab"]       { background:transparent !important; color:var(--green-dim) !important; font-family:var(--font-display) !important; font-size:0.68rem !important; letter-spacing:1px !important; border:1px solid transparent !important; border-radius:4px 4px 0 0 !important; padding:8px 20px !important; }
.stTabs [aria-selected="true"]     { background:var(--green-dark) !important; color:var(--green) !important; border-color:var(--border-hot) !important; text-shadow:0 0 8px var(--green) !important; }
.stTabs [data-baseweb="tab-panel"] { background:var(--bg-panel) !important; border:1px solid var(--border) !important; border-top:none !important; padding:20px !important; border-radius:0 0 4px 4px !important; }

[data-testid="stMetric"]      { background:var(--bg-card) !important; border:1px solid var(--border) !important; border-radius:4px !important; padding:12px !important; }
[data-testid="stMetricLabel"] { color:var(--green-dim) !important; font-family:var(--font-display) !important; font-size:0.58rem !important; letter-spacing:2px !important; }
[data-testid="stMetricValue"] { color:var(--green) !important; font-family:var(--font-vt) !important; font-size:2rem !important; text-shadow:0 0 10px var(--green) !important; }

::-webkit-scrollbar       { width:6px; height:6px; }
::-webkit-scrollbar-track { background:var(--bg-black); }
::-webkit-scrollbar-thumb { background:var(--green-dark); border-radius:3px; }

.dojo-header { text-align:center; padding:20px 0 10px 0; border-bottom:1px solid var(--border); margin-bottom:24px; }
.dojo-header h1 { font-size:1.9rem !important; letter-spacing:6px !important; margin:0 !important; }
.dojo-header .subtitle { color:var(--green-dim); font-size:0.65rem; letter-spacing:4px; margin-top:4px; }

.terminal-box  { background:var(--bg-terminal); border:1px solid var(--border); border-left:3px solid var(--green); border-radius:4px; padding:16px; font-family:var(--font-mono); color:var(--green); margin:8px 0; }
.terminal-box.error   { border-left-color:var(--red);   color:var(--red);   }
.terminal-box.warning { border-left-color:var(--amber); color:var(--amber); }
.terminal-box.success { border-left-color:var(--green); box-shadow:0 0 10px rgba(0,255,159,0.08); }
.terminal-box.info    { border-left-color:var(--blue);  color:var(--blue);  }

.section-header { display:flex; align-items:center; gap:10px; margin:20px 0 12px 0; padding-bottom:6px; border-bottom:1px solid var(--border); }
.section-header span { font-family:var(--font-display); font-size:0.72rem; letter-spacing:3px; color:var(--green); text-transform:uppercase; }

.xp-badge    { display:inline-block; background:var(--green-dark); border:1px solid var(--green); color:var(--green); font-family:var(--font-display); font-size:0.62rem; letter-spacing:2px; padding:3px 10px; border-radius:2px; box-shadow:0 0 8px var(--green-glow); }
.level-badge { display:inline-block; background:rgba(0,212,255,0.1); border:1px solid var(--blue); color:var(--blue); font-family:var(--font-display); font-size:0.62rem; letter-spacing:2px; padding:3px 10px; border-radius:2px; }

.glitch-text { animation:glitch 5s infinite; }
@keyframes glitch {
  0%,88%,100%{text-shadow:0 0 20px var(--green),0 0 40px rgba(0,255,159,0.3);}
  90%{text-shadow:-2px 0 var(--red),2px 0 var(--blue);transform:skewX(-1deg);}
  92%{text-shadow:2px 0 var(--red),-2px 0 var(--blue);transform:skewX(1deg);}
  94%{text-shadow:0 0 20px var(--green),0 0 40px rgba(0,255,159,0.3);transform:none;}
}

.pulse-dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--green); box-shadow:0 0 6px var(--green); animation:pulse 1.5s infinite; margin-right:8px; vertical-align:middle; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.35;} }

.provider-card { border-radius:4px; padding:10px 12px; margin-bottom:4px; }
.challenge-box { background:linear-gradient(135deg,var(--bg-card) 0%,rgba(0,255,159,0.03) 100%); border:1px solid var(--border-hot); border-radius:6px; padding:20px; margin:12px 0; position:relative; }
.challenge-box::before { content:"MISSION"; position:absolute; top:8px; right:12px; font-family:var(--font-display); font-size:0.52rem; letter-spacing:3px; color:rgba(0,255,159,0.3); }
.hint-box { background:rgba(255,176,0,0.05); border:1px solid rgba(255,176,0,0.4); border-left:3px solid var(--amber); border-radius:4px; padding:14px; margin:8px 0; color:var(--amber); font-family:var(--font-mono); }
.stat-bar      { height:4px; background:var(--bg-card); border-radius:2px; overflow:hidden; margin:4px 0; }
.stat-bar-fill { height:100%; background:linear-gradient(90deg,var(--green-dark),var(--green)); border-radius:2px; box-shadow:0 0 6px var(--green); }
</style>
"""

st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║              PERSISTENCE LAYER                              ║
# ╚══════════════════════════════════════════════════════════════╝

PROGRESS_FILE = Path("dojo_progress.json")
COOKIE_NAME   = "dojo_progress_v2"

PERSIST_KEYS = [
    "xp", "day", "streak",
    "challenges_completed", "challenges_attempted",
    "history", "current_lesson",
    "active_provider", "active_model",   # also persist AI config
]

def get_cookie_manager():
    # CookieManager is a Streamlit widget and must NOT be inside @st.cache_resource.
    # Guard with session state so only one instance is created per session.
    if "_cookie_manager" not in st.session_state:
        st.session_state._cookie_manager = (
            stx.CookieManager(key="fincrime_dojo_cm") if COOKIES_AVAILABLE else None
        )
    return st.session_state._cookie_manager

cookie_manager = get_cookie_manager()


def save_to_file(state: dict):
    try:
        PROGRESS_FILE.write_text(
            json.dumps({k: state.get(k) for k in PERSIST_KEYS}, default=str, indent=2)
        )
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
        cookie_manager.set(COOKIE_NAME, json.dumps({
            "xp":  state.get("xp", 0),
            "day": state.get("day", 0),
            "st":  state.get("streak", 0),
            "cc":  state.get("challenges_completed", 0),
            "ca":  state.get("challenges_attempted", 0),
            "ap":  state.get("active_provider", ""),
            "am":  state.get("active_model", ""),
        }), key="cookie_save_op")
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
                "active_provider":      c.get("ap", ""),
                "active_model":         c.get("am", ""),
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
        if key in file_data and file_data[key] is not None:
            merged[key] = file_data[key]
        elif key in cookie_data and cookie_data[key]:
            merged[key] = cookie_data[key]
    return merged


# ╔══════════════════════════════════════════════════════════════╗
# ║                   SESSION STATE INIT                        ║
# ╚══════════════════════════════════════════════════════════════╝

_first_provider = next(iter(PROVIDER_REGISTRY))

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
    "active_provider": _first_provider,
    "active_model":    PROVIDER_REGISTRY[_first_provider]["default_model"],
    "_progress_loaded": False,
}

if not st.session_state.get("_progress_loaded", False):
    saved = load_progress()
    for k, default_val in DEFAULTS.items():
        if k == "_progress_loaded":
            st.session_state[k] = False
            continue
        st.session_state[k] = saved.get(k, default_val) if k in saved and saved[k] is not None else default_val

    # Re-hydrate DataFrame from saved lesson
    if st.session_state.get("current_lesson"):
        try:
            _ns = {}
            exec(compile(st.session_state.current_lesson.get("data_setup",""),
                         "<restore>", "exec"),
                 {"pd": pd, "__builtins__": __builtins__}, _ns)
            st.session_state.current_df = _ns.get("df")
        except Exception:
            st.session_state.current_df = None

    st.session_state._progress_loaded = True


# ╔══════════════════════════════════════════════════════════════╗
# ║                   CURRICULUM CONSTANTS                      ║
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
            "SQL CTEs for multi-step AML analysis",
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

ALL problems must involve: AML transaction monitoring, KYC compliance, fraud detection, structuring/smurfing, PEP/sanctions screening, or SARs.

Use domain variable names (never x, y, z): transaction_id, cust_id, account_id, amount, txn_date, cust_risk_score, country_code, beneficiary_country, is_flagged, alert_id, sar_filed, kyc_status, product_type, channel, currency, txn_type.

Respond ONLY with valid JSON. No markdown, no text outside JSON."""

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
# ║              LESSON + HINT HELPERS                          ║
# ╚══════════════════════════════════════════════════════════════╝

def _clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*",     "", raw)
    raw = re.sub(r"\s*```$",     "", raw)
    return raw.strip()

def generate_lesson(client: AIClient, level: str, topic: str):
    text, err = client.generate(LESSON_PROMPT.format(level=level, topic=topic))
    if err:
        return None, err
    try:
        return json.loads(_clean_json(text)), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}\n\nRaw response:\n{text[:400]}"

def get_ai_hint(client: AIClient, level, topic, challenge, code, error):
    text, err = client.generate(
        HINT_PROMPT.format(level=level, topic=topic,
                           challenge=challenge, code=code or "(empty)",
                           error=error or "no output"),
        max_tokens=200, temperature=0.5,
    )
    return text.strip() if not err else f"Could not generate hint: {err}"


# ╔══════════════════════════════════════════════════════════════╗
# ║              EXECUTION ENGINE                               ║
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

_SAFE = {b: getattr(__builtins__, b, None) for b in
         ("print","len","range","list","dict","set","tuple","int","float","str",
          "bool","sum","min","max","abs","round","sorted","enumerate","zip",
          "map","filter","isinstance","type","repr","__import__")
         if hasattr(__builtins__, b)}

def exec_python(code: str, df: pd.DataFrame):
    buf = io.StringIO()
    ns  = {"df": df.copy(), "pd": pd, "__builtins__": _SAFE}
    try:
        with redirect_stdout(buf):
            exec(compile(code, "<student>", "exec"), ns)
        out = buf.getvalue()
        if "result" in ns and not out.strip():
            val = ns["result"]
            out = val.to_string() if isinstance(val, pd.DataFrame) else repr(val)
        return out or "(No output — use print() or assign to 'result')", ""
    except Exception:
        return "", traceback.format_exc()


# ╔══════════════════════════════════════════════════════════════╗
# ║              UI HELPERS                                     ║
# ╚══════════════════════════════════════════════════════════════╝

def tb(content, box_type="success", title=""):
    t = (f'<div style="font-size:0.62rem;letter-spacing:3px;opacity:0.6;margin-bottom:8px;'
         f'font-family:var(--font-display)">{title}</div>') if title else ""
    st.markdown(
        f'<div class="terminal-box {box_type}">{t}'
        f'<pre style="margin:0;font-family:var(--font-mono);background:none;border:none;'
        f'padding:0;color:inherit;white-space:pre-wrap;word-break:break-all">{content}</pre></div>',
        unsafe_allow_html=True,
    )

def sh(icon, title):
    st.markdown(f'<div class="section-header"><span>{icon} {title}</span></div>', unsafe_allow_html=True)

def progress_html(val, maxv=100):
    p = min(100, int(val / maxv * 100)) if maxv else 0
    st.markdown(f'<div class="stat-bar"><div class="stat-bar-fill" style="width:{p}%"></div></div>',
                unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════╗
# ║                       SIDEBAR                               ║
# ╚══════════════════════════════════════════════════════════════╝

with st.sidebar:

    # ── Logo ─────────────────────────────────────────────────
    st.markdown(
        '<div style="text-align:center;padding:14px 0;border-bottom:1px solid rgba(0,255,159,0.2);margin-bottom:14px">'
        '<div style="font-family:\'Orbitron\',monospace;font-size:1.1rem;color:#00ff9f;text-shadow:0 0 15px #00ff9f;letter-spacing:4px">FINCRIME</div>'
        '<div style="font-family:\'Orbitron\',monospace;font-size:0.58rem;color:#00cc7a;letter-spacing:6px;margin-top:2px">D O J O</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════
    # AI PROVIDER CONFIG
    # ══════════════════════════════════════════════════════════
    st.markdown('<div style="font-size:0.62rem;letter-spacing:3px;color:#00cc7a;margin-bottom:8px">◈ AI PROVIDER</div>', unsafe_allow_html=True)

    # Scan which providers have keys ready
    available_providers = scan_available_providers()

    # Build display labels with status dots
    def provider_label(name):
        src = available_providers.get(name, "")
        dot = {"SECRETS": "🟢", "MANUAL": "🟡"}.get(src, "🔴")
        return f"{dot} {PROVIDER_REGISTRY[name]['icon']} {name}"

    provider_options = list(PROVIDER_REGISTRY.keys())
    provider_labels  = [provider_label(p) for p in provider_options]

    # Restore previously saved provider if valid
    saved_provider = st.session_state.get("active_provider", provider_options[0])
    saved_idx = provider_options.index(saved_provider) if saved_provider in provider_options else 0

    selected_label = st.selectbox(
        "Provider", provider_labels,
        index=saved_idx,
        label_visibility="collapsed",
        key="provider_selectbox",
    )
    active_provider = provider_options[provider_labels.index(selected_label)]
    provider_cfg    = PROVIDER_REGISTRY[active_provider]

    # Update session if provider changed
    if active_provider != st.session_state.get("active_provider"):
        st.session_state.active_provider = active_provider
        st.session_state.active_model    = provider_cfg["default_model"]

    # ── Model selector ────────────────────────────────────────
    st.markdown('<div style="font-size:0.58rem;letter-spacing:2px;color:#00cc7a;margin:6px 0 4px">MODEL</div>', unsafe_allow_html=True)

    model_options = provider_cfg["models"] + ["✎ Custom..."]
    saved_model   = st.session_state.get("active_model", provider_cfg["default_model"])

    # If saved model is in the known list, select it; otherwise show custom
    if saved_model in provider_cfg["models"]:
        model_idx = provider_cfg["models"].index(saved_model)
    else:
        model_idx = len(provider_cfg["models"])   # "Custom" entry

    model_choice = st.selectbox("Model", model_options, index=model_idx, label_visibility="collapsed", key="model_selectbox")

    if model_choice == "✎ Custom...":
        custom_model = st.text_input(
            "Custom model", value=saved_model if saved_model not in provider_cfg["models"] else "",
            placeholder="e.g. my-fine-tuned-model",
            label_visibility="collapsed",
            key="custom_model_input",
        )
        active_model = custom_model.strip() or provider_cfg["default_model"]
    else:
        active_model = model_choice

    if active_model != st.session_state.get("active_model"):
        st.session_state.active_model = active_model

    # ── API Key status for selected provider ──────────────────
    api_key, key_source = resolve_key_for_provider(active_provider)
    st.markdown('<div style="font-size:0.58rem;letter-spacing:2px;color:#00cc7a;margin:8px 0 4px">API KEY</div>', unsafe_allow_html=True)

    if key_source == "SECRETS":
        masked = api_key[:6] + "•" * 8 + api_key[-4:]
        st.markdown(
            f'<div style="background:rgba(0,255,159,0.05);border:1px solid rgba(0,255,159,0.25);'
            f'border-radius:3px;padding:8px 10px;font-size:0.62rem;">'
            f'<div style="color:#00ff9f">🔐 AUTO — secrets.toml</div>'
            f'<div style="color:#00cc7a;margin-top:2px;font-family:\'Share Tech Mono\',monospace">{masked}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        hint_key = provider_cfg["secret_keys"][0]
        manual_val = st.session_state.get(f"_manual_key_{active_provider}", "")
        new_val = st.text_input(
            "API Key",
            value=manual_val,
            type="password",
            placeholder=f"Paste key  (or add {hint_key} to secrets.toml)",
            label_visibility="collapsed",
            key=f"manual_key_input_{active_provider}",
        )
        if new_val != manual_val:
            st.session_state[f"_manual_key_{active_provider}"] = new_val
            api_key, key_source = new_val, "MANUAL" if new_val else ""
            st.rerun()
        status_color = "#ffb000" if api_key else "#ff3c5c"
        status_text  = "● MANUAL KEY" if api_key else "● NO KEY"
        st.markdown(f'<div style="font-size:0.6rem;color:{status_color};margin-top:4px">{status_text}</div>', unsafe_allow_html=True)

    # ── Test connection button ────────────────────────────────
    if api_key:
        if st.button("⟳ TEST CONNECTION", use_container_width=True, key="test_conn_btn"):
            with st.spinner("Testing..."):
                client = AIClient(active_provider, active_model, api_key, "")
                ok, msg = client.test_connection()
            if ok:
                st.success(f"✓ Connected: {msg[:40]}")
            else:
                st.error(f"✗ {msg[:80]}")

    # ── Available providers summary ───────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.58rem;letter-spacing:2px;color:#00cc7a;margin-bottom:6px">ALL PROVIDERS</div>', unsafe_allow_html=True)
    for pname, pcfg in PROVIDER_REGISTRY.items():
        src = available_providers.get(pname, "")
        dot = {"SECRETS": "🟢", "MANUAL": "🟡"}.get(src, "⚫")
        src_label = {"SECRETS": "secrets", "MANUAL": "manual", "": "no key"}.get(src, "")
        active_marker = " ◀" if pname == active_provider else ""
        st.markdown(
            f'<div style="font-size:0.58rem;color:{"#00ff9f" if pname == active_provider else "#00804d"};'
            f'padding:2px 0">{dot} {pcfg["icon"]} {pname}  '
            f'<span style="opacity:0.5">({src_label})</span>{active_marker}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Difficulty ────────────────────────────────────────────
    st.markdown('<div style="font-size:0.62rem;letter-spacing:3px;color:#00cc7a;margin-bottom:4px">◈ DIFFICULTY</div>', unsafe_allow_html=True)
    difficulty = st.selectbox("Difficulty", list(LEVEL_CONFIG.keys()), label_visibility="collapsed")
    level_data = LEVEL_CONFIG[difficulty]

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Stats ─────────────────────────────────────────────────
    st.markdown('<div style="font-size:0.62rem;letter-spacing:3px;color:#00cc7a;margin-bottom:10px">◈ AGENT STATS</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("XP",     f"{st.session_state.xp:,}")
    c2.metric("DAY",    st.session_state.day)
    c3, c4 = st.columns(2)
    c3.metric("STREAK", f"🔥{st.session_state.streak}")
    _acc = int(st.session_state.challenges_completed /
               st.session_state.challenges_attempted * 100) if st.session_state.challenges_attempted else 0
    c4.metric("ACC%", f"{_acc}%")

    st.markdown('<div style="font-size:0.55rem;letter-spacing:2px;color:#00cc7a;margin-top:6px">XP TO NEXT RANK</div>', unsafe_allow_html=True)
    progress_html(st.session_state.xp % 100)
    st.markdown(f'<div style="font-size:0.55rem;color:#00cc7a;text-align:right">{st.session_state.xp % 100}/100</div>', unsafe_allow_html=True)

    # ── Save status ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    _layers = (["FILE"] if PROGRESS_FILE.exists() else []) + (["COOKIE"] if COOKIES_AVAILABLE else [])
    _sc = "#00ff9f" if PROGRESS_FILE.exists() else "#ffb000"
    st.markdown(
        f'<div style="background:rgba(0,0,0,0.3);border:1px solid rgba(0,255,159,0.12);border-radius:3px;padding:8px 10px;">'
        f'<div style="font-size:0.55rem;letter-spacing:2px;color:#00cc7a;margin-bottom:2px">SAVE STATUS</div>'
        f'<div style="font-size:0.62rem;color:{_sc}">● {" + ".join(_layers) or "SESSION ONLY"}</div>'
        f'<div style="font-size:0.5rem;color:rgba(0,204,122,0.4);margin-top:2px">'
        f'{"Refresh-safe · auto-saved" if PROGRESS_FILE.exists() else "Start a lesson to begin saving"}'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # ── History ───────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.history:
        st.markdown('<div style="font-size:0.62rem;letter-spacing:3px;color:#00cc7a;margin-bottom:6px">◈ HISTORY</div>', unsafe_allow_html=True)
        for h in st.session_state.history[-5:]:
            st.markdown(
                f'<div style="font-size:0.58rem;color:#00cc7a;padding:2px 0">'
                f'{"✅" if h.get("completed") else "⚠️"} Day {h["day"]} — {h["topic"][:22]}...</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⚡ RESET DOJO", use_container_width=True):
        try:
            if PROGRESS_FILE.exists(): PROGRESS_FILE.unlink()
        except Exception:
            pass
        if cookie_manager:
            try: cookie_manager.delete(COOKIE_NAME, key="cookie_del")
            except Exception: pass
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
    _color = provider_cfg["color"]
    st.markdown(
        f'<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a">AI PROVIDER</div>'
        f'<div style="font-size:0.8rem;color:{_color}">'
        f'{provider_cfg["icon"]} {active_provider}</div>',
        unsafe_allow_html=True,
    )
with s2:
    st.markdown(
        f'<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a">MODEL</div>'
        f'<div style="font-size:0.75rem;color:#00d4ff;word-break:break-all">{active_model}</div>',
        unsafe_allow_html=True,
    )
with s3:
    _kc = {"SECRETS": "#00ff9f", "MANUAL": "#ffb000", "": "#ff3c5c"}[key_source]
    _kt = {"SECRETS": "🔐 FROM SECRETS", "MANUAL": "✎ MANUAL KEY", "": "⚠ NO KEY"}[key_source]
    st.markdown(
        f'<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a">KEY STATUS</div>'
        f'<div style="font-size:0.8rem;color:{_kc}">{_kt}</div>',
        unsafe_allow_html=True,
    )
with s4:
    _n = len(level_data["topics"])
    _d = (st.session_state.day % _n) + 1
    st.markdown(
        f'<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a">PROGRESS</div>'
        f'<div style="font-size:0.8rem;color:#00ff9f">Day {st.session_state.day}  ·  {_d}/{_n}</div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

if not api_key:
    tb(
        f"⚠  {active_provider.upper()} OFFLINE — No API key found.\n\n"
        f"  OPTION 1 (recommended): Add to .streamlit/secrets.toml:\n"
        f"    {provider_cfg['secret_keys'][0]} = \"your-key-here\"\n\n"
        f"  OPTION 2: Paste your key in the sidebar API KEY field.\n\n"
        f"  Install library if needed: {provider_cfg['install']}",
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


def make_client() -> AIClient:
    return AIClient(active_provider, active_model, api_key, SYSTEM_PROMPT)


def load_lesson(advance: bool = False):
    if advance:
        st.session_state.day += 1
    topic_idx = st.session_state.day % len(level_data["topics"])
    topic     = level_data["topics"][topic_idx]
    with st.spinner(f"⟳ [{active_provider} / {active_model}] Generating: {topic}..."):
        lesson, err = generate_lesson(make_client(), level_data["id"], topic)
    if lesson:
        st.session_state.current_lesson = lesson
        df, df_err = exec_data_setup(lesson["data_setup"])
        st.session_state.current_df = df
        if df_err:
            st.warning(f"Data setup warning:\n{df_err}")
        for k in ["sql_result","python_output","hint_sql","hint_python",
                  "last_sql_correct","last_python_correct",
                  "last_sql_input","last_python_input","last_sql_error","last_python_error"]:
            st.session_state[k] = None if any(x in k for x in ("result","output","correct")) else ""
        if not advance:
            st.session_state.day += 1
        st.session_state.streak += 1
        st.session_state.active_provider = active_provider
        st.session_state.active_model    = active_model
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
            "day": st.session_state.day,
            "topic": st.session_state.current_lesson.get("topic",""),
            "completed": done,
            "provider": active_provider,
            "model":    active_model,
        })
        if done:
            st.session_state.xp += 100
            st.session_state.challenges_completed += 1
        save_progress()
    load_lesson(advance=True)
    st.rerun()

if hint_sql_btn and st.session_state.current_lesson and api_key:
    with st.spinner("Generating hint..."):
        h = get_ai_hint(make_client(), level_data["id"],
                        st.session_state.current_lesson.get("topic",""),
                        st.session_state.current_lesson.get("challenge",""),
                        st.session_state.last_sql_input,
                        st.session_state.last_sql_error or "No submission yet")
    st.session_state.hint_sql = h
    st.rerun()

if hint_py_btn and st.session_state.current_lesson and api_key:
    with st.spinner("Generating hint..."):
        h = get_ai_hint(make_client(), level_data["id"],
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
            f'<div class="level-badge">{level_data["id"].upper()}</div><br>'
            f'<div style="font-size:0.5rem;color:{provider_cfg["color"]};letter-spacing:1px;margin-top:4px">'
            f'{provider_cfg["icon"]} {active_model.split("/")[-1]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

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
    sh("🕵️", "YOUR MISSION")
    st.markdown(
        f'<div class="challenge-box">'
        f'<div style="font-size:0.62rem;letter-spacing:3px;color:#00ff9f;margin-bottom:10px">▸ CASE FILE — ACTIVE INVESTIGATION</div>'
        f'<div style="font-size:0.95rem;line-height:1.75">{lesson.get("challenge","")}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    sh("💻", "THE TERMINAL")
    tab_sql, tab_py, tab_sol = st.tabs(["  ⬡ SQL TERMINAL  ", "  ⬡ PYTHON TERMINAL  ", "  ⬡ SOLUTIONS  "])

    with tab_sql:
        st.markdown('<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a;margin-bottom:6px">> SQL runs against in-memory SQLite — table: transactions</div>', unsafe_allow_html=True)
        sql_in = st.text_area("SQL", height=150, placeholder="SELECT ...\nFROM transactions\nWHERE ...", label_visibility="collapsed", key="sql_input_area")
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
                    tb(f"SQLiteError: {sql_err}\n\nTip: Check column names in the schema viewer above.", "error", "EXECUTION ERROR")
                    if api_key:
                        with st.spinner("Generating hint..."):
                            st.session_state.hint_sql = get_ai_hint(
                                make_client(), level_data["id"], lesson.get("topic",""),
                                lesson.get("challenge",""), sql_in, sql_err)
                else:
                    st.session_state.sql_result     = res_df
                    st.session_state.last_sql_error = ""
                    if res_df is not None and len(res_df) > 0:
                        st.session_state.last_sql_correct = True
                        st.session_state.xp += 25
                        save_progress()
                        tb(f"✓ QUERY EXECUTED SUCCESSFULLY\n  Rows     : {len(res_df)}\n  Columns  : {list(res_df.columns)}\n  +25 XP AWARDED", "success", "OUTPUT")
                    else:
                        st.session_state.last_sql_correct = False
                        tb("⚠ Query ran but returned 0 rows.\nCheck your WHERE/HAVING conditions.", "warning", "OUTPUT")
                st.rerun()

        if st.session_state.sql_result is not None:
            st.markdown(f'<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a;margin:12px 0 6px">⬡ RESULT — {len(st.session_state.sql_result)} rows</div>', unsafe_allow_html=True)
            st.dataframe(st.session_state.sql_result, use_container_width=True)
        if st.session_state.hint_sql:
            st.markdown(f'<div class="hint-box">⚡ AI HINT<br><br>{st.session_state.hint_sql}</div>', unsafe_allow_html=True)

    with tab_py:
        st.markdown('<div style="font-size:0.62rem;letter-spacing:2px;color:#00cc7a;margin-bottom:6px">> DataFrame: df  |  Pandas: pd</div>', unsafe_allow_html=True)
        py_in = st.text_area("Python", height=160, placeholder="result = df[df['amount'] > 9000]\nprint(result)", label_visibility="collapsed", key="py_input_area")
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
                        with st.spinner("Generating hint..."):
                            st.session_state.hint_python = get_ai_hint(
                                make_client(), level_data["id"], lesson.get("topic",""),
                                lesson.get("challenge",""), py_in, py_err)
                else:
                    st.session_state.python_output       = out
                    st.session_state.last_python_correct = True
                    st.session_state.xp += 25
                    save_progress()
                    tb(f"✓ EXECUTION SUCCESSFUL  |  +25 XP\n{'─'*44}\n{out}", "success", "PROGRAM OUTPUT")
                st.rerun()

        if st.session_state.python_output:
            tb(st.session_state.python_output, "success", "LAST OUTPUT")
        if st.session_state.hint_python:
            st.markdown(f'<div class="hint-box">⚡ AI HINT<br><br>{st.session_state.hint_python}</div>', unsafe_allow_html=True)

    with tab_sol:
        st.markdown('<div style="font-size:0.68rem;letter-spacing:2px;color:#ff3c5c;margin-bottom:16px">⚠ Try on your own first. Viewing solutions does not award XP.</div>', unsafe_allow_html=True)
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown('<div style="font-size:0.62rem;letter-spacing:3px;color:#00cc7a;margin-bottom:6px">SQL SOLUTION</div>', unsafe_allow_html=True)
            st.code(lesson.get("solution_sql","-- Not available"), language="sql")
            if df is not None and st.button("✓ VERIFY SQL", key="verify_sql_btn"):
                r, e = exec_sql(lesson.get("solution_sql",""), df)
                tb(f"✓ Returns {len(r)} rows." if not e else f"Error: {e}", "success" if not e else "error")
        with sc2:
            st.markdown('<div style="font-size:0.62rem;letter-spacing:3px;color:#00cc7a;margin-bottom:6px">PYTHON SOLUTION</div>', unsafe_allow_html=True)
            st.code(lesson.get("solution_python","# Not available"), language="python")
            if df is not None and st.button("✓ VERIFY PYTHON", key="verify_py_btn"):
                o, e = exec_python(lesson.get("solution_python",""), df)
                tb(f"✓ Output:\n{o}" if not e else f"Error: {e}", "success" if not e else "error")

    with st.expander("⟫ VIEW AI-GENERATED DATA SETUP CODE"):
        st.code(lesson.get("data_setup","# Not available"), language="python")

else:
    # Empty state
    st.markdown(
        '<div class="terminal-box" style="text-align:center;padding:56px 40px">'
        '<div style="font-family:\'VT323\',monospace;font-size:3.5rem;color:#00ff9f;margin-bottom:12px">◈</div>'
        '<div style="font-family:\'Orbitron\',monospace;font-size:0.9rem;letter-spacing:4px;color:#00ff9f;margin-bottom:12px">DOJO TERMINAL STANDING BY</div>'
        '<div style="font-size:0.8rem;color:#00cc7a;line-height:2">'
        '① Select your AI Provider + Model in the sidebar<br>'
        '② Select difficulty level<br>'
        '③ Click ▶ START DAY to generate your lesson'
        '</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    sh("⚡", "DEMO MODE — PRACTICE WITHOUT A LESSON")

    demo_df = pd.DataFrame({
        "transaction_id": ["TXN_001","TXN_002","TXN_003","TXN_004","TXN_005","TXN_006"],
        "cust_id":        ["C_101","C_102","C_103","C_101","C_104","C_102"],
        "amount":         [9800.0,14500.0,500.0,9500.0,23000.0,8900.0],
        "country_code":   ["PK","AE","IN","PK","NG","AE"],
        "txn_type":       ["CASH_DEP","WIRE","CASH_DEP","CASH_DEP","WIRE","CASH_DEP"],
        "cust_risk_score":[8,6,2,8,9,6],
        "is_flagged":     [False,True,False,False,True,False],
    })
    tb("DEMO CHALLENGE\n══════════════\nFind all CASH deposits > $9,000 from customers with risk score > 5.\nSQL hint   : WHERE amount > 9000 AND txn_type = 'CASH_DEP' AND cust_risk_score > 5\nPython hint: df[(df['amount']>9000) & (df['txn_type']=='CASH_DEP')]", "info", "DEMO CASE")
    st.dataframe(demo_df, use_container_width=True)
    d1, d2 = st.columns(2)
    with d1:
        demo_sql = st.text_area("SQL:", height=80, placeholder="SELECT * FROM transactions WHERE ...", key="demo_sql_input")
        if st.button("▶ RUN DEMO SQL"):
            if demo_sql.strip():
                r, e = exec_sql(demo_sql, demo_df)
                tb(f"Error: {e}" if e else f"✓ {len(r)} rows", "error" if e else "success", "OUTPUT")
                if not e: st.dataframe(r, use_container_width=True)
    with d2:
        demo_py = st.text_area("Python:", height=80, placeholder="result = df[df['amount']>9000]\nprint(result)", key="demo_py_input")
        if st.button("▶ RUN DEMO PYTHON"):
            if demo_py.strip():
                out, err = exec_python(demo_py, demo_df)
                tb(err if err else out, "error" if err else "success", "OUTPUT")

# ── Footer ─────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    f'<div style="text-align:center;padding:16px;border-top:1px solid rgba(0,255,159,0.12);'
    f'font-size:0.58rem;letter-spacing:3px;color:rgba(0,255,159,0.25)">'
    f'FINCRIME DOJO v2.0  ·  {provider_cfg["icon"]} {active_provider} / {active_model.split("/")[-1]}'
    f'  ·  FINANCIAL CRIME ANALYTICS  ·  ALL DATA SYNTHETIC'
    f'</div>',
    unsafe_allow_html=True,
)
