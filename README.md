# AI Release Radar

Setup
    pip install -r requirements.txt
    Edit .env (GEMINI_API_KEY, RESEND_API_KEY; PostgreSQL DATABASE_URL for production, SQLite for local)
    cd backend
    uvicorn main:app --reload
    Open http://localhost:8000

Tests
- Startup: server logs show the scheduler running; http://localhost:8000/docs loads.
- Signup/login: use the UI or POST /api/signup and /api/login.
- Discovery: within about a minute the Sources page shows last-checked times and Releases fills in.
- Verification: items off a company's official domain are marked REJECTED.
- Gemini: set GEMINI_API_KEY; summaries and categories appear (keyword fallback without a key).
- Relevance and email: pick interests, set RESEND_API_KEY; Notifications page shows history (SKIPPED_NO_KEY without a key).
- Duplicates: restart the server; counts do not grow for the same URLs.
- X discovery: set X_DISCOVERY_ENABLED=true and X_BEARER_TOKEN.
- Feedback: open a release and submit a rating.

Notes
- Anthropic, xAI, Meta AI and DeepSeek have no RSS feed configured yet; they show "No feed configured".
- The ~10-15 minute alert time is a target, not a guarantee.