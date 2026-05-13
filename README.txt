╔══════════════════════════════════════════════════════════════╗
║         THE FINCRIME DOJO — SETUP GUIDE                      ║
╚══════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PREREQUISITES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✔ Python 3.10 or higher
  ✔ pip (comes with Python)
  ✔ Google Gemini API key (free at aistudio.google.com)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — CLONE / PLACE FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Place app.py and requirements.txt in the same folder.
  
  fincrime_dojo/
  ├── app.py
  └── requirements.txt

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — CREATE VIRTUAL ENVIRONMENT (Recommended)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # Windows
  python -m venv venv
  venv\Scripts\activate

  # macOS / Linux
  python3 -m venv venv
  source venv/bin/activate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3 — INSTALL DEPENDENCIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  pip install -r requirements.txt

  ⚡ Minimum install (fastest start):
  pip install streamlit pandas google-generativeai

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4 — GET GEMINI API KEY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Go to: https://aistudio.google.com/app/apikey
  2. Sign in with Google
  3. Click "Create API Key"
  4. Copy the key (starts with "AIza...")
  ★ It's FREE — no credit card needed for standard usage

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 5 — RUN THE APP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  streamlit run app.py

  The app opens automatically at: http://localhost:8501

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 6 — USING THE APP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Paste your Gemini API key in the sidebar (masked)
  2. Select your difficulty level:
     → Cadet     : Python basics + simple SQL
     → Analyst   : Pandas + JOINs + GROUP BY
     → Investigator: AML pattern detection, Window functions
     → Architect : ML models (Random Forest, Isolation Forest)
  3. Click "START DAY" to generate your first AI-powered lesson
  4. Read the theory, inspect the live data
  5. Write your SQL in the SQL Terminal tab
  6. Write your Python in the Python Terminal tab
  7. Click "Execute" — the app runs your code in real-time
  8. Stuck? Click "Request Hint" for AI-powered guidance
  9. Click "Next Challenge" for a fresh lesson

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OFFLINE MODE (No API Key)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  The app works without a Gemini key!
  It loads a built-in AML/SQL demo lesson so you can
  explore the interface immediately.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Issue: ModuleNotFoundError
  Fix:   pip install <module_name>

  Issue: Gemini API error 403
  Fix:   Check your API key is valid and has quota

  Issue: App won't start
  Fix:   Ensure Python 3.10+ with: python --version

  Issue: Fonts not loading (offline environment)
  Fix:   The app still works, Google Fonts are cosmetic only

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARCHITECTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  app.py
  ├── CSS Layer        → Cyberpunk terminal aesthetic
  ├── Gemini Engine    → Generates infinite AML lessons in JSON
  ├── SQLite Engine    → Executes user SQL against in-memory DB
  ├── Python Exec      → Safely runs user pandas/ML code
  ├── XP System        → Tracks progress + unlocks badges
  └── Session State    → Persists everything across reruns

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Every SAR filed starts with someone who knew
 how to write the query." — FinCrime_Architect
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
