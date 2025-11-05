"""
═══════════════════════════════════════════════════════════════════════════════
MATH 1710 PRECALCULUS TUTORING SYSTEM - MAIN APPLICATION (UPDATED)
Dr. Crenshaw • Chattanooga State Community College

CHANGES IN THIS VERSION:
✅ Added wrong_responses tracking (increments on incorrect answers)
✅ Added calculator_used tracking (tracks actual button clicks)
✅ Added completed/final_answer_correct tracking (marks problem completion)
✅ Added /api/session/calculator-used endpoint for frontend tracking

Configuration is in config.py, teaching prompts in prompts.py
═══════════════════════════════════════════════════════════════════════════════
"""
# Standard Python libraries
import base64
import json
import os
import re
import sys
import threading
import time
import traceback
import uuid
import zipfile
from collections import defaultdict
from datetime import datetime
import pytz
from io import BytesIO
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, Response, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

# Our configuration and prompts
from config import COURSE, AI_SETTINGS
from prompts import (
    build_system_prompt,
    COMPREHENSION_CHECK_PROMPT,
    BRIEF_REVIEW_PROMPT,
    RETEACH_PROMPT,
    BREAK_SMALLER_PROMPT,
    SHOW_SOLUTION_PROMPT,
    VERIFICATION_PROMPT,
)

# Answer validation system
from fast_validator import FastValidator

# Mode enforcement reminders (injected as last message for recency bias)
MODE_REMINDERS = {
    "quick_hints": "🚨 QUICK HINTS MODE: Show complete simplified results. NEVER ask simplification questions like 'What is 22-7?'",
    "step_by_step": "🚨 STEP-BY-STEP MODE: Ask for operation, then ask for simplification separately. Give brief why after correct.",
    "detailed_explanations": "🚨 DETAILED MODE: Explain concept BEFORE each question. Break into tiniest steps. Ask WHY questions to check understanding. Reteach when wrong."
}

# Env
from dotenv import load_dotenv
load_dotenv()  # load .env at import time

# OpenAI SDK
try:
    from openai import AsyncOpenAI
except Exception:
    AsyncOpenAI = None  # checked at startup

# Firebase Service
from firebase_service import FirebaseTrackingService

# Backup Service
from backup_service import BackupService, AutoBackupScheduler

# Create ONE FastAPI app instance
app = FastAPI(title=f"{COURSE['code']} Learning Assistant")

# CORS on that same instance
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global client handle set at startup
client: Optional[AsyncOpenAI] = None
firebase_service: Optional[FirebaseTrackingService] = None
backup_service: Optional[BackupService] = None
auto_backup: Optional[AutoBackupScheduler] = None
cleanup_thread: Optional[threading.Thread] = None
stop_cleanup = threading.Event()

def daily_cleanup_worker():
    """Background worker to clean up old chat history daily."""
    while not stop_cleanup.is_set():
        try:
            if firebase_service and firebase_service.use_firebase:
                firebase_service.cleanup_old_chat_history(days=7)
        except Exception as e:
            print(f"[ERROR] Daily cleanup failed: {e}")

        # Sleep for 24 hours (or until stop signal)
        stop_cleanup.wait(86400)  # 86400 seconds = 24 hours

@app.on_event("startup")
def init_openai():
    """Initialize the OpenAI client and Firebase once the app process is ready."""
    global client, firebase_service, backup_service, auto_backup, cleanup_thread
    if AsyncOpenAI is None:
        raise RuntimeError("OpenAI SDK not installed. Run: pip install openai")
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable")
    # Optional model default if you read it elsewhere
    os.environ.setdefault("OPENAI_MODEL", AI_SETTINGS.get("model", "gpt-4o-mini"))
    client = AsyncOpenAI(api_key=key)

    # Initialize Firebase service
    firebase_service = FirebaseTrackingService()
    print(f"[FIREBASE] Enabled: {firebase_service.use_firebase}")

    # Load data from Firebase AFTER Firebase is initialized
    load_data()
    print(f"[STARTUP] Loaded {len(TRACKING['sessions'])} sessions from Firebase")

    # If Firebase is enabled, migrate existing JSON data
    if firebase_service.use_firebase and os.path.exists(DATA_FILE):
        migrate_json_to_firebase()

    # Clean up old chat history (7+ days old) - run once at startup
    if firebase_service and firebase_service.use_firebase:
        firebase_service.cleanup_old_chat_history(days=7)

        # Start background cleanup thread for daily cleanup
        cleanup_thread = threading.Thread(target=daily_cleanup_worker, daemon=True)
        cleanup_thread.start()
        print("[CLEANUP] Daily chat history cleanup scheduled")

    # Initialize CSV backup service
    backup_service = BackupService(backup_dir="backups")

    # Do an immediate backup on startup
    backup_service.backup_all(
        users=TRACKING["users"],
        sessions=TRACKING["sessions"],
        reports=TRACKING["reports"]
    )

    # Start automatic backups every 6 hours
    auto_backup = AutoBackupScheduler(backup_service, interval_hours=6)
    auto_backup.start(lambda: (TRACKING["users"], TRACKING["sessions"], TRACKING["reports"]))

@app.on_event("shutdown")
def shutdown_cleanup():
    """Stop the cleanup worker and backup scheduler on shutdown."""
    # Stop cleanup worker
    stop_cleanup.set()
    if cleanup_thread and cleanup_thread.is_alive():
        cleanup_thread.join(timeout=5)

    # Stop auto-backup and do final backup
    if auto_backup:
        auto_backup.stop()

    # Final backup before shutdown
    if backup_service:
        print("[BACKUP] Performing final backup before shutdown...")
        backup_service.backup_all(
            users=TRACKING["users"],
            sessions=TRACKING["sessions"],
            reports=TRACKING["reports"]
        )

# ═══════════════════════════════════════════════════════════════════════════
#                    AI HELPER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

async def call_ai(messages: List[dict]) -> str:
    """Call OpenAI API with configured settings."""
    try:
        resp = await client.chat.completions.create(
            model=AI_SETTINGS["model"],
            temperature=AI_SETTINGS["temperature"],
            max_tokens=AI_SETTINGS["max_tokens"],
            messages=messages,
            timeout=AI_SETTINGS["timeout"],
        )
        return resp.choices[0].message.content or ""
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return "I am having trouble connecting right now. Please wait a moment and resubmit your message."
# ═══════════════════════════════════════════════════════════════════════════
#                         DATA STORAGE
# ═══════════════════════════════════════════════════════════════════════════

DATA_FILE = "tracking_data.json"
TRACKING: Dict[str, Any] = {
    "users": {},
    "sessions": {},
    "reports": []
}

def load_data():
    """Load saved data from Firebase or fall back to local JSON."""
    global TRACKING

    if firebase_service and firebase_service.use_firebase:
        # Load from Firebase
        TRACKING["users"] = firebase_service.get_all_users()
        TRACKING["sessions"] = firebase_service.get_all_sessions()
        TRACKING["reports"] = firebase_service.get_all_reports()
        print(f"[FIREBASE] Loaded from Firebase: {len(TRACKING['users'])} users, {len(TRACKING['sessions'])} sessions")
    elif os.path.exists(DATA_FILE):
        # Fall back to JSON
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                TRACKING = json.load(f)
        except Exception:
            pass

def save_data():
    """Save data to Firebase or fall back to local JSON."""
    if firebase_service and firebase_service.use_firebase:
        # Data is saved in real-time to Firebase, no need for batch save
        pass
    else:
        # Fall back to JSON file
        try:
            readable_data = {
                "summary": generate_summary(),
                "users": TRACKING["users"],
                "sessions": TRACKING["sessions"],
                "reports": TRACKING["reports"]
            }

            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(readable_data, f, indent=2)
        except Exception:
            pass

def migrate_json_to_firebase():
    """One-time migration of existing JSON data to Firebase."""
    if not os.path.exists(DATA_FILE):
        return

    try:
        print("[MIGRATION] Migrating existing JSON data to Firebase...")
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Migrate users
        users = data.get("users", {})
        for user_token, user_data in users.items():
            firebase_service.save_user(user_token, user_data)

        # Migrate sessions
        sessions = data.get("sessions", {})
        for session_id, session_data in sessions.items():
            firebase_service.save_session(session_id, session_data)

        # Migrate reports
        reports = data.get("reports", [])
        for report in reports:
            firebase_service.save_report(report)

        print(f"[MIGRATION] Migrated {len(users)} users, {len(sessions)} sessions, {len(reports)} reports")

    except Exception as e:
        print(f"[WARNING] Migration failed: {e}")

def generate_summary():
    """Generate daily summary statistics."""
    total_users = len(TRACKING["users"])
    total_sessions = len(TRACKING["sessions"])

    # Today's activity
    today = datetime.now().date()
    today_users = set()
    today_sessions = 0

    # Module breakdown
    module_counts = defaultdict(int)
    mode_counts = defaultdict(int)

    # Time metrics
    total_duration = 0
    session_count_with_duration = 0

    # Help metrics
    total_hints = 0
    total_why = 0
    total_problems_solved = 0

    for session in TRACKING["sessions"].values():
        module_counts[session.get("module", "unknown")] += 1
        mode_counts[session.get("mode", "unknown")] += 1

        if session.get("duration_seconds"):
            total_duration += session["duration_seconds"]
            session_count_with_duration += 1

        total_hints += session.get("hints_requested", 0)
        total_why += session.get("why_requested", 0)
        total_problems_solved += session.get("problems_solved", 0)

        if session.get("started"):
            try:
                session_date = datetime.fromisoformat(session["started"]).date()
                if session_date == today:
                    today_sessions += 1
                    today_users.add(session.get("user_token"))
            except:
                pass

    avg_duration_minutes = 0
    if session_count_with_duration > 0:
        avg_duration_minutes = round((total_duration / session_count_with_duration) / 60, 1)

    module_names = {
        "unit1": "Unit 1: Linear Equations",
        "unit2": "Unit 2: Quadratics",
        "unit3": "Unit 3: Exponentials & Logs",
        "other": "Other/Review"
    }

    mode_names = {
        "light_guidance": "Light Guidance",
        "quick_start": "Quick Start",
        "full_support": "Full Support"
    }

    # Convert UTC to Eastern Time for display
    eastern = pytz.timezone('US/Eastern')
    now_et = datetime.now(pytz.utc).astimezone(eastern)

    return {
        "last_updated": now_et.strftime("%I:%M %p ET on %B %d, %Y"),
        "overview": {
            "total_unique_users": total_users,
            "total_sessions": total_sessions,
            "total_problems_solved": total_problems_solved,
            "average_session_duration_minutes": avg_duration_minutes
        },
        "today": {
            "date": now_et.strftime("%B %d, %Y"),
            "unique_users_today": len(today_users),
            "sessions_today": today_sessions
        },
        "usage_by_unit": {
            module_names.get(k, k): v for k, v in sorted(module_counts.items())
        },
        "usage_by_support_level": {
            mode_names.get(k, k): v for k, v in sorted(mode_counts.items())
        },
        "help_requests": {
            "total_hints_requested": total_hints,
            "total_why_explanations": total_why,
            "average_hints_per_session": round(total_hints / total_sessions, 1) if total_sessions > 0 else 0
        }
    }

# NOTE: load_data() is called in the startup event AFTER Firebase is initialized
# Do NOT call it here at module level!

# ═══════════════════════════════════════════════════════════════════════════
#                    UNICODE SANITIZER
# ═══════════════════════════════════════════════════════════════════════════

def sanitize_to_unicode(text: str) -> str:
    """
    Remove LaTeX formatting and convert to Unicode.
    Students can't read LaTeX - we want plain text.

    NOTE: This function is a FALLBACK for when the AI generates LaTeX.
    The AI should be generating Unicode symbols directly (√, ·, ÷, etc.)
    based on the notation instructions in config.py.
    """
    if not text:
        return text

    # Remove LaTeX delimiters
    text = re.sub(r'\$+|\\\[|\\\]|\\\(|\\\)', '', text)
    text = re.sub(r'\\text\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\(left|right)\s*', '', text)

    # Convert LaTeX symbols to Unicode (fallback)
    replacements = {
        r'\\times': '×', r'\\cdot': '·', r'\\div': '÷',
        r'\\leq': '≤', r'\\geq': '≥', r'\\neq': '≠', r'\\pm': '±'
    }
    for latex, unicode_char in replacements.items():
        text = text.replace(latex, unicode_char)

    # Convert LaTeX structures to Unicode (fallback)
    text = re.sub(r'\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}', r'(\1) ÷ (\2)', text)
    text = re.sub(r'\{([^{}]+)\}\s*\{([^{}]+)\}', r'[\1] ÷ [\2]', text)  # Handle {numerator}{denominator} format
    text = re.sub(r'\\sqrt\s*\{([^{}]+)\}', r'√(\1)', text)

    # Fix imaginary unit notation: √(n)·i or √(n) · i → i√(n)
    text = re.sub(r'√\(([^)]+)\)\s*[·•]\s*i', r'i√(\1)', text)

    # Subscripts and superscripts - IMPROVED to handle all numbers, variables, and complex expressions
    sub_map = str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉')

    # Superscript mappings for numbers, letters, operators, and parentheses
    super_number_map = str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')
    super_letter_map = str.maketrans(
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖ ʳˢᵗᵘᵛʷˣʸᶻᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᵠᴿˢᵀᵁⱽᵂˣʸᶻ'
    )
    super_operator_map = str.maketrans('+-=*/()[]{}', '⁺⁻⁼ˣ*⁽⁾[]{}')

    def to_superscript(text: str) -> str:
        """Convert text to Unicode superscript characters."""
        result = []
        for char in text:
            if char in '0123456789':
                result.append(char.translate(super_number_map))
            elif char.lower() in 'abcdefghijklmnopqrstuvwxyz':
                result.append(char.translate(super_letter_map))
            elif char in '+-=()':
                result.append(char.translate(super_operator_map))
            else:
                result.append(char)
        return ''.join(result)

    # Convert subscripts: x_1, x_{12}, etc.
    text = re.sub(r'_\{?([0-9]+)\}?', lambda m: ''.join(c.translate(sub_map) for c in m.group(1)), text)

    # Convert complex superscripts: ^(x+1), ^x, ^{2n+3}, ^2, etc.
    # Handle expressions in parentheses first: ^(...) - include the parentheses in the superscript
    text = re.sub(r'\^\(([^)]+)\)', lambda m: to_superscript('(' + m.group(1) + ')'), text)

    # Handle expressions in braces: ^{...} - don't include braces in superscript
    text = re.sub(r'\^\{([^}]+)\}', lambda m: to_superscript(m.group(1)), text)

    # Handle single character or simple expressions: ^x, ^n, ^2
    text = re.sub(r'\^([a-zA-Z0-9])', lambda m: to_superscript(m.group(1)), text)

    # Clean up remaining LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    text = re.sub(r'[ \t]+\n', '\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)

    return text.strip()

# ═══════════════════════════════════════════════════════════════════════════
#                    REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str = ""
    session_id: Optional[str] = None
    user_token: Optional[str] = None
    user_name: Optional[str] = None
    module: str = "other"
    image_data: Optional[str] = None
    mode: str = "standard"

class ReportRequest(BaseModel):
    user_token: Optional[str] = None
    session_id: Optional[str] = None
    category: Optional[str] = None
    report: Optional[str] = None

# ═══════════════════════════════════════════════════════════════════════════
#                    SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def get_or_create_session(req: ChatRequest, response: Response) -> dict:
    """Get existing session or create new one with tracking."""

    # Anonymous user
    if not req.user_token:
        req.user_token = f"anon_{uuid.uuid4().hex[:12]}"
        response.headers["X-User-Token"] = req.user_token

    # Get or create user
    if firebase_service and firebase_service.use_firebase:
        user = firebase_service.get_user(req.user_token)
        if not user:
            user = {
                "created": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "name": None,
                "sessions": [],
                "total_interactions": 0
            }
    else:
        user = TRACKING["users"].setdefault(req.user_token, {
            "created": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat(),
            "name": None,
            "sessions": [],
            "total_interactions": 0
        })

    user["last_seen"] = datetime.now().isoformat()
    user["total_interactions"] += 1

    # Update name if provided
    if req.user_name:
        user["name"] = req.user_name

    # Save user to Firebase or local storage
    if firebase_service and firebase_service.use_firebase:
        firebase_service.save_user(req.user_token, user)
        TRACKING["users"][req.user_token] = user  # Keep in memory for /stats endpoint
    else:
        TRACKING["users"][req.user_token] = user

    # Session
    if not req.session_id:
        req.session_id = f"sess_{uuid.uuid4().hex[:8]}"
        user["sessions"].append(req.session_id)

        new_session = {
            "user_token": req.user_token,
            "module": req.module,
            "mode": req.mode,
            "started": datetime.now(pytz.utc).isoformat(),
            "last_activity": datetime.now(pytz.utc).isoformat(),
            "ended": None,
            "duration_seconds": None,
            "messages": [],
            "original_problem": None,
            "problem_completed": False,
            "steps_completed": 0,
            "current_step": 0,
            "step_attempts": {},
            "comprehension_checks": [],
            "steps_since_check": 0,
            "needs_reteach": False,
            "questions_asked": 0,
            "hints_requested": 0,
            "why_requested": 0,
            "calculator_nudges": 0,
            "problems_solved": 0,
            "answer_demand_count": 0,
            "last_correct_position": None,  # Track MC answer position rotation
            "question_count": 0,  # Count questions asked in this session
            "waiting_for_feedback": False,  # Track if we're waiting for feedback response
            "feedback_given": [],  # List of feedback entries with full context
            "expected_answer": None,  # Expected answer for current question (from AI declaration)
            "last_question": None,  # Last question text for validation
            "last_options": None,  # Last MC options for validation

            # ✅ NEW TRACKING FIELDS
            "wrong_responses": 0,          # Total incorrect answers
            "calculator_used": 0,          # Actual calculator usage (not just AI suggestions)
            "completed": False,            # Was problem successfully completed?
            "final_answer_correct": None,  # Was final answer correct? (True/False/None)
        }

        if firebase_service and firebase_service.use_firebase:
            firebase_service.save_session(req.session_id, new_session)
            firebase_service.save_user(req.user_token, user)  # Update user's session list
            TRACKING["sessions"][req.session_id] = new_session
        else:
            TRACKING["sessions"][req.session_id] = new_session

    # Get session
    if firebase_service and firebase_service.use_firebase:
        session = firebase_service.get_session(req.session_id)
        if not session:
            session = TRACKING["sessions"].get(req.session_id, {})
    else:
        session = TRACKING["sessions"][req.session_id]

    session["mode"] = req.mode
    session["module"] = req.module
    session["last_activity"] = datetime.now(pytz.utc).isoformat()

    # Save updated session
    if firebase_service and firebase_service.use_firebase:
        firebase_service.save_session(req.session_id, session)
        TRACKING["sessions"][req.session_id] = session

    return session

# ═══════════════════════════════════════════════════════════════════════════
#                    ADAPTIVE SCAFFOLDING HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def check_comprehension_due(session: dict) -> bool:
    """Check if it's time for comprehension check (every 3 steps)."""
    return session.get("steps_since_check", 0) >= 3

def should_reteach(session: dict, response: str) -> bool:
    """
    Determine if full reteach is needed.
    Triggers: 2 consecutive "mostly", "mostly" then "no", or any "no"
    """
    checks = session.get("comprehension_checks", [])
    if response == "no":
        return True
    if len(checks) >= 1:
        last = checks[-1]
        if last == "mostly" and response in ["mostly", "no"]:
            return True
    return False

def needs_more_scaffolding(session: dict) -> Optional[str]:
    """Check if intervention needed based on wrong answers."""
    current_step = session.get("current_step", 0)
    attempts = session.get("step_attempts", {}).get(str(current_step), 0)
    if attempts >= 3:
        return "SHOW_SOLUTION"
    elif attempts >= 2:
        return "BREAK_SMALLER"
    return None

# ═══════════════════════════════════════════════════════════════════════════
#                    WEB ROUTES
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
def root():
    """Serve student interface."""
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": f"{COURSE['code']} API is running"})

@app.get("/evaluation-dashboard.html")
def evaluation_dashboard():
    """Serve evaluation dashboard (production version)."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "evaluation-dashboard.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    raise HTTPException(status_code=404, detail="Evaluation dashboard not found")

@app.get("/evaluation-dashboard-commented.html")
def evaluation_dashboard_commented():
    """Serve evaluation dashboard (commented version for non-coders)."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "evaluation-dashboard-commented.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    raise HTTPException(status_code=404, detail="Commented evaluation dashboard not found")

@app.get("/usage-report.html")
def usage_report():
    """Serve usage report with formatted statistics."""
    report_path = os.path.join(os.path.dirname(__file__), "usage-report.html")
    if os.path.exists(report_path):
        return FileResponse(report_path)
    raise HTTPException(status_code=404, detail="Usage report not found")

@app.get("/tracking_data.json")
def tracking_data():
    """Serve raw tracking data for usage report."""
    if os.path.exists(DATA_FILE):
        return FileResponse(DATA_FILE)
    raise HTTPException(status_code=404, detail="Tracking data not found")

@app.get("/debug.html")
def debug_page():
    """Serve debug page to check data structure."""
    debug_path = os.path.join(os.path.dirname(__file__), "debug.html")
    if os.path.exists(debug_path):
        return FileResponse(debug_path)
    raise HTTPException(status_code=404, detail="Debug page not found")

@app.get("/firebase-test.html")
def firebase_test():
    """Serve Firebase connection test page."""
    test_path = os.path.join(os.path.dirname(__file__), "firebase-test.html")
    if os.path.exists(test_path):
        return FileResponse(test_path)
    raise HTTPException(status_code=404, detail="Firebase test page not found")

@app.get("/firebase-check-all.html")
def firebase_check_all():
    """Serve Firebase raw data dump page."""
    test_path = os.path.join(os.path.dirname(__file__), "firebase-check-all.html")
    if os.path.exists(test_path):
        return FileResponse(test_path)
    raise HTTPException(status_code=404, detail="Firebase check page not found")

@app.get("/health")
def health():
    """System health check."""
    return {
        "status": "ok",
        "course": f"{COURSE['code']} - {COURSE['name']}",
        "institution": COURSE["institution"],
        "users": len(TRACKING["users"]),
        "active_sessions": len(TRACKING["sessions"]),
        "reports_received": len(TRACKING["reports"])
    }

@app.get("/health/data")
def check_data_integrity():
    """
    Data integrity health check - detects potential data loss.

    Returns warnings if:
    - No recent sessions (possible data overwrite)
    - Session count decreased significantly
    - All sessions older than expected
    """
    sessions = TRACKING["sessions"]

    if not sessions:
        return {
            "status": "WARNING",
            "message": "No sessions found in database",
            "total_sessions": 0,
            "recommendation": "Check if Firebase connection is working"
        }

    # Get current date components for comparison
    from datetime import datetime, timedelta
    now = datetime.now()
    current_month = now.strftime("%Y-%m")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")

    # Analyze session dates
    session_dates = []
    recent_sessions = 0
    this_month_sessions = 0

    for session in sessions.values():
        started = session.get('started', '')
        if started:
            session_dates.append(started[:10])

            # Count recent sessions (last 7 days)
            if started[:10] >= week_ago:
                recent_sessions += 1

            # Count this month's sessions
            if started[:7] == current_month:
                this_month_sessions += 1

    # Get earliest and latest session dates
    earliest = min(session_dates) if session_dates else None
    latest = max(session_dates) if session_dates else None

    # Check for anomalies
    warnings = []

    # WARNING: No recent sessions (possible data overwrite)
    if recent_sessions == 0 and len(sessions) > 0:
        warnings.append({
            "type": "NO_RECENT_ACTIVITY",
            "message": f"All {len(sessions)} sessions are older than 7 days",
            "details": f"Latest session: {latest}",
            "possible_cause": "Data may have been overwritten with old backup"
        })

    # WARNING: No sessions from current month
    if this_month_sessions == 0 and latest and latest < current_month:
        warnings.append({
            "type": "OLD_DATA_ONLY",
            "message": f"No sessions from {current_month}",
            "details": f"Latest session: {latest}",
            "possible_cause": "Database may contain only archived/old data"
        })

    # WARNING: Very few total sessions (suspicious for production system)
    if len(sessions) < 10:
        warnings.append({
            "type": "LOW_SESSION_COUNT",
            "message": f"Only {len(sessions)} total sessions",
            "details": "Unusually low for a system in use",
            "possible_cause": "Data loss or recent database reset"
        })

    # Determine overall status
    if warnings:
        status = "WARNING"
        message = f"{len(warnings)} data integrity issue(s) detected"
    else:
        status = "OK"
        message = "Data looks healthy"

    return {
        "status": status,
        "message": message,
        "total_sessions": len(sessions),
        "recent_sessions_7d": recent_sessions,
        "this_month_sessions": this_month_sessions,
        "date_range": {
            "earliest": earliest,
            "latest": latest
        },
        "warnings": warnings,
        "recommendation": "Check DATA_LOSS_ROOT_CAUSE_REPORT.md if warnings present"
    }

@app.get("/debug/firebase-env")
def debug_firebase_env():
    """Debug endpoint to check Firebase environment variable."""
    firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    if not firebase_json:
        return {
            "status": "NOT_SET",
            "message": "FIREBASE_SERVICE_ACCOUNT_JSON environment variable is not set or is empty"
        }

    try:
        cred_dict = json.loads(firebase_json)
        return {
            "status": "VALID",
            "message": "Firebase credentials JSON is valid",
            "length": len(firebase_json),
            "type": cred_dict.get("type"),
            "project_id": cred_dict.get("project_id"),
            "client_email": cred_dict.get("client_email"),
            "has_private_key": "private_key" in cred_dict
        }
    except json.JSONDecodeError as e:
        return {
            "status": "INVALID_JSON",
            "message": f"Failed to parse JSON: {str(e)}",
            "length": len(firebase_json),
            "first_100_chars": firebase_json[:100]
        }

@app.get("/stats")
def get_stats():
    """Get organized usage statistics with summaries (excludes archived sessions)."""
    # Filter out archived sessions
    active_sessions = {sid: s for sid, s in TRACKING["sessions"].items() if not s.get("archived", False)}

    # Calculate summaries - only count users with active sessions
    active_user_tokens = set(s.get("user_token") for s in active_sessions.values() if s.get("user_token"))
    total_users = len(active_user_tokens)
    total_sessions = len(active_sessions)

    # Today's activity (use Eastern Time for "today")
    eastern = pytz.timezone('US/Eastern')
    now_et = datetime.now(pytz.utc).astimezone(eastern)
    today_et = now_et.date()

    today_users = set()
    today_sessions = 0

    # Module breakdown
    module_counts = defaultdict(int)
    mode_counts = defaultdict(int)

    # Time metrics
    total_duration = 0
    session_count_with_duration = 0

    # Help metrics
    total_hints = 0
    total_why = 0
    total_problems_solved = 0

    for session_id, session in active_sessions.items():
        # Module stats
        module_counts[session.get("module", "unknown")] += 1
        mode_counts[session.get("mode", "unknown")] += 1

        # Duration stats
        if session.get("duration_seconds"):
            total_duration += session["duration_seconds"]
            session_count_with_duration += 1

        # Help stats
        total_hints += session.get("hints_requested", 0)
        total_why += session.get("why_requested", 0)
        total_problems_solved += session.get("problems_solved", 0)

        # Today's activity (convert UTC timestamps to Eastern)
        if session.get("started"):
            try:
                session_dt_utc = datetime.fromisoformat(session["started"].replace('Z', '+00:00'))
                if not session_dt_utc.tzinfo:
                    session_dt_utc = session_dt_utc.replace(tzinfo=pytz.utc)
                session_date_et = session_dt_utc.astimezone(eastern).date()
                if session_date_et == today_et:
                    today_sessions += 1
                    today_users.add(session.get("user_token"))
            except:
                pass

    # Average duration
    avg_duration_minutes = 0
    if session_count_with_duration > 0:
        avg_duration_minutes = round((total_duration / session_count_with_duration) / 60, 1)

    # Format module names
    module_names = {
        "unit1": "Unit 1: Linear Equations & Inequalities",
        "unit2": "Unit 2: Quadratics & Polynomials",
        "unit3": "Unit 3: Exponentials & Logarithms",
        "other": "Other/Review"
    }

    mode_names = {
        "light_guidance": "Light Guidance",
        "quick_start": "Quick Start",
        "full_support": "Full Support"
    }

    return {
        "generated_at": now_et.strftime("%I:%M %p ET on %B %d, %Y"),

        "summary": {
            "total_unique_users": total_users,
            "total_sessions": total_sessions,
            "total_problems_solved": total_problems_solved,
            "average_session_minutes": avg_duration_minutes,
        },

        "today": {
            "date": now_et.strftime("%B %d, %Y"),
            "unique_users": len(today_users),
            "sessions": today_sessions
        },

        "by_unit": {
            module_names.get(k, k): v for k, v in module_counts.items()
        },

        "by_support_level": {
            mode_names.get(k, k): v for k, v in mode_counts.items()
        },

        "help_usage": {
            "total_hints_requested": total_hints,
            "total_why_requested": total_why,
            "average_hints_per_session": round(total_hints / total_sessions, 1) if total_sessions > 0 else 0
        }
    }

@app.get("/tracking_data_live")
def get_tracking_data_live():
    """Serve live tracking data from Firebase (or memory).

    Note: This endpoint returns ALL sessions including archived ones.
    The frontend (usage-report.html) handles filtering archived sessions for display.
    """
    return {
        "users": TRACKING["users"],
        "sessions": TRACKING["sessions"],
        "reports": TRACKING["reports"]
    }

@app.post("/reload_data")
def reload_data_endpoint():
    """Manually reload all data from Firebase."""
    load_data()
    return {
        "success": True,
        "users_loaded": len(TRACKING["users"]),
        "sessions_loaded": len(TRACKING["sessions"]),
        "reports_loaded": len(TRACKING["reports"])
    }

@app.post("/archive_sessions")
def archive_sessions_endpoint(session_ids: list[str]):
    """
    Archive multiple sessions at once.
    Marks sessions as archived so they don't appear in usage stats.
    """
    if not firebase_service or not firebase_service.use_firebase:
        return {"error": "Firebase not enabled"}

    archived_count = 0
    errors = []

    for session_id in session_ids:
        try:
            # Get session from Firebase
            session = firebase_service.get_session(session_id)
            if session:
                # Mark as archived
                session['archived'] = True
                session['archived_at'] = datetime.now(pytz.utc).isoformat()

                # Save back to Firebase
                firebase_service.save_session(session_id, session)

                # Update in-memory tracking
                if session_id in TRACKING["sessions"]:
                    TRACKING["sessions"][session_id] = session

                archived_count += 1
            else:
                errors.append(f"Session {session_id} not found")
        except Exception as e:
            errors.append(f"Error archiving {session_id}: {str(e)}")

    return {
        "success": True,
        "archived_count": archived_count,
        "total_requested": len(session_ids),
        "errors": errors if errors else None
    }

@app.post("/mark_collaborator")
def mark_collaborator_sessions(data: dict):
    """
    Mark sessions as collaborator sessions.
    Adds collaborator flag to distinguish from regular student sessions.

    Expected data:
    {
        "session_ids": [...],
        "collaborator_name": "Name",
        "collaborator_role": "Student Collaborator"
    }
    """
    if not firebase_service or not firebase_service.use_firebase:
        return {"error": "Firebase not enabled"}

    session_ids = data.get('session_ids', [])
    collaborator_name = data.get('collaborator_name', 'Unknown')
    collaborator_role = data.get('collaborator_role', 'Collaborator')

    marked_count = 0
    errors = []

    for session_id in session_ids:
        try:
            # Get session from Firebase
            session = firebase_service.get_session(session_id)
            if session:
                # Mark as collaborator session
                session['collaborator'] = True
                session['collaborator_name'] = collaborator_name
                session['collaborator_role'] = collaborator_role
                session['marked_collaborator_at'] = datetime.now(pytz.utc).isoformat()

                # Save back to Firebase
                firebase_service.save_session(session_id, session)

                # Update in-memory tracking
                if session_id in TRACKING["sessions"]:
                    TRACKING["sessions"][session_id] = session

                marked_count += 1
            else:
                errors.append(f"Session {session_id} not found")
        except Exception as e:
            errors.append(f"Error marking {session_id}: {str(e)}")

    return {
        "success": True,
        "marked_count": marked_count,
        "total_requested": len(session_ids),
        "collaborator_name": collaborator_name,
        "collaborator_role": collaborator_role,
        "errors": errors if errors else None
    }

@app.post("/report_problem")
def report_problem(req: ReportRequest):
    """Handle student issue reports."""
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "user_token": req.user_token,
        "session_id": req.session_id,
        "category": req.category,
        "report": req.report
    }

    if firebase_service and firebase_service.use_firebase:
        firebase_service.save_report(report_data)
        TRACKING["reports"].append(report_data)
    else:
        TRACKING["reports"].append(report_data)
        save_data()

    return {"status": "received", "message": "Thank you for helping us improve!"}

# ═══════════════════════════════════════════════════════════════════════════
#  ✅ NEW ENDPOINT: CALCULATOR USAGE TRACKING
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/session/calculator-used")
async def track_calculator_use(request: Request):
    """
    Track when student actually uses the calculator button.

    Frontend should call this endpoint when calculator button is clicked:

    fetch('/api/session/calculator-used', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId })
    });
    """
    try:
        data = await request.json()
        session_id = data.get("session_id")

        if not session_id:
            return {"error": "session_id required"}

        # Get session
        if firebase_service and firebase_service.use_firebase:
            session = firebase_service.get_session(session_id)
            if not session:
                session = TRACKING["sessions"].get(session_id)
        else:
            session = TRACKING["sessions"].get(session_id)

        if not session:
            return {"error": "Session not found"}

        # ✅ Increment calculator usage counter
        session["calculator_used"] = session.get("calculator_used", 0) + 1

        # Save updated session
        if firebase_service and firebase_service.use_firebase:
            firebase_service.save_session(session_id, session)
            TRACKING["sessions"][session_id] = session
        else:
            TRACKING["sessions"][session_id] = session
            save_data()

        return {
            "success": True,
            "calculator_uses": session["calculator_used"]
        }

    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════

@app.get("/backup")
def manual_backup():
    """
    Trigger a manual backup of all data to CSV files.
    Returns paths to created backup files.
    """
    if not backup_service:
        raise HTTPException(status_code=500, detail="Backup service not initialized")

    try:
        # Perform backup
        backup_files = backup_service.backup_all(
            users=TRACKING["users"],
            sessions=TRACKING["sessions"],
            reports=TRACKING["reports"]
        )

        return {
            "status": "success",
            "message": "Backup completed successfully",
            "timestamp": datetime.now().isoformat(),
            "files": backup_files,
            "backup_directory": str(backup_service.backup_dir.absolute()),
            "download_url": "/backup/download"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@app.get("/backup/download")
def download_backups():
    """
    Download all current backup CSV files as a ZIP archive.
    Returns a ZIP file containing today's backups.
    """
    if not backup_service:
        raise HTTPException(status_code=500, detail="Backup service not initialized")

    try:
        # Get today's date prefix
        date_prefix = datetime.now().strftime("%Y-%m-%d")

        # Find all CSV files for today
        backup_files = list(backup_service.backup_dir.glob(f"{date_prefix}_*.csv"))

        if not backup_files:
            raise HTTPException(status_code=404, detail="No backup files found for today")

        # Create ZIP file in memory
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for csv_file in backup_files:
                # Add file to ZIP with just the filename (not full path)
                zip_file.write(csv_file, arcname=csv_file.name)

        # Seek to beginning of buffer
        zip_buffer.seek(0)

        # Return as downloadable file
        filename = f"math1710_backup_{date_prefix}.zip"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/backup/list")
def list_backups():
    """
    List all available backup files.
    Returns information about all backup CSV files.
    """
    if not backup_service:
        raise HTTPException(status_code=500, detail="Backup service not initialized")

    try:
        # Get all CSV files
        all_files = list(backup_service.backup_dir.glob("*.csv"))

        # Group by date
        backups_by_date = {}
        for filepath in all_files:
            # Extract date from filename (YYYY-MM-DD_type.csv)
            parts = filepath.stem.split("_")
            if len(parts) >= 2:
                date = parts[0]
                file_type = "_".join(parts[1:])

                if date not in backups_by_date:
                    backups_by_date[date] = []

                # Get file info
                stat = filepath.stat()
                backups_by_date[date].append({
                    "type": file_type,
                    "filename": filepath.name,
                    "size_bytes": stat.st_size,
                    "size_kb": round(stat.st_size / 1024, 1),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        # Sort dates descending (newest first)
        sorted_backups = {
            date: sorted(files, key=lambda x: x["type"])
            for date, files in sorted(backups_by_date.items(), reverse=True)
        }

        return {
            "status": "success",
            "backup_directory": str(backup_service.backup_dir.absolute()),
            "total_dates": len(sorted_backups),
            "backups": sorted_backups
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")

@app.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    """Handle image uploads."""
    try:
        contents = await file.read()
        encoded = base64.b64encode(contents).decode("utf-8")
        return {"status": "success", "image_data": encoded}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/chat")
async def chat(req: ChatRequest, response: Response):
    """
    ═══════════════════════════════════════════════════════════════════════
    MAIN TUTORING ENDPOINT
    ═══════════════════════════════════════════════════════════════════════
    """

    # Initialize session
    session = get_or_create_session(req, response)

    # Build user message
    user_content = []
    if req.message:
        user_content.append({"type": "text", "text": req.message})
    if req.image_data:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{req.image_data}"}
        })
    if not user_content:
        user_content = [{"type": "text", "text": ""}]

    user_message = {"role": "user", "content": user_content}
    session["messages"].append(user_message)

    # Save user message to Firebase chat history
    if firebase_service and firebase_service.use_firebase:
        firebase_service.save_chat_message(req.session_id, {
            "role": "user",
            "content": req.message,
            "timestamp": datetime.now(pytz.utc).isoformat()
        })

    # Track special requests
    msg_lower = req.message.lower()
    if "hint" in msg_lower:
        session["hints_requested"] = session.get("hints_requested", 0) + 1
    if "why" in msg_lower:
        session["why_requested"] = session.get("why_requested", 0) + 1

    # Detect answer demands
    answer_demand_phrases = [
        "just give me the answer",
        "tell me the answer",
        "what is the answer",
        "give me answer",
        "show me the answer",
        "just tell me",
        "just show me"
    ]
    if any(phrase in msg_lower for phrase in answer_demand_phrases):
        session["answer_demand_count"] = session.get("answer_demand_count", 0) + 1

    # Build AI context
    messages = []
    system_prompt = build_system_prompt(session["module"], session["mode"])
    messages.append({"role": "system", "content": system_prompt})

    # ─────── Answer Position Rotation Enforcement ───────
    last_position = session.get("last_correct_position")
    if last_position:
        # Enforce rotation - never repeat same position
        position_rotation = {
            "A": "B or C",
            "B": "C or A",
            "C": "A or B",
            "D": "A or B"
        }
        next_positions = position_rotation.get(last_position, "B or C")
        messages.append({
            "role": "system",
            "content": f"🚨 CRITICAL ROTATION ENFORCEMENT 🚨\n\nYour LAST multiple-choice question had the correct answer at position {last_position}.\n\nThis question MUST have the correct answer at position: {next_positions}\n\nYou CANNOT use position {last_position} again.\n\nThis is REQUIRED to prevent students from pattern-guessing."
        })
    else:
        # First question of session
        messages.append({
            "role": "system",
            "content": "🚨 CRITICAL ROTATION ENFORCEMENT 🚨\n\nThis is the first multiple-choice question of this session.\n\nThe correct answer MUST be at position B or C (NEVER A for first question).\n\nThis prevents students from always choosing A."
        })

    # ─────── Comprehension Check Logic ───────
    if check_comprehension_due(session) and not session.get("waiting_for_comprehension"):
        messages.append({"role": "system", "content": COMPREHENSION_CHECK_PROMPT})
        session["waiting_for_comprehension"] = True

    if session.get("waiting_for_comprehension"):
        student_response = req.message.strip().upper()

        if student_response == "A":
            session["comprehension_checks"].append("yes")
            session["steps_since_check"] = 0
            session["waiting_for_comprehension"] = False

        elif student_response == "B":
            session["comprehension_checks"].append("mostly")
            if should_reteach(session, "mostly"):
                session["needs_reteach"] = True
            else:
                messages.append({"role": "system", "content": BRIEF_REVIEW_PROMPT})
            session["steps_since_check"] = 0
            session["waiting_for_comprehension"] = False

        elif student_response in ["C", "D"]:
            session["comprehension_checks"].append("no")
            session["needs_reteach"] = True
            session["steps_since_check"] = 0
            session["waiting_for_comprehension"] = False

    # ─────── Reteach if Needed ───────
    if session.get("needs_reteach"):
        messages.append({"role": "system", "content": RETEACH_PROMPT})
        session["needs_reteach"] = False

    # ─────── Scaffolding Intervention ───────
    intervention = needs_more_scaffolding(session)
    if intervention == "BREAK_SMALLER":
        messages.append({"role": "system", "content": BREAK_SMALLER_PROMPT})
    elif intervention == "SHOW_SOLUTION":
        messages.append({"role": "system", "content": SHOW_SOLUTION_PROMPT})
        session["step_attempts"] = {}
        session["current_step"] = 0

    # ─────── Answer Demand Tracking ───────
    demand_count = session.get("answer_demand_count", 0)
    if demand_count > 0:
        messages.append({
            "role": "system",
            "content": f"Student has demanded answer {demand_count} time(s) in this session. Follow the answer demand protocol in the system prompt."
        })

    # ─────── Add Conversation History ───────
    recent_history = session["messages"][-20:]
    messages.extend(recent_history)

    # ─────── FAST PROGRAMMATIC VALIDATION ───────
    # If student sent A/B/C/D and we have the last question, validate it
    student_choice = req.message.strip().upper()
    if student_choice in ["A", "B", "C", "D"] and session.get("last_question") and session.get("last_options"):
        # Try fast validation (for arithmetic questions)
        is_correct = FastValidator.validate(
            student_choice,
            session["last_question"],
            session["last_options"]
        )

        if is_correct is not None:
            # We successfully validated - inject clear result
            if is_correct:
                validation_msg = """🟢 STUDENT IS CORRECT - Confirm positively and continue."""
            else:
                validation_msg = """🔴 STUDENT IS WRONG - Say "Let's reconsider your response" and give a hint. DO NOT praise their wrong answer."""

                # ✅ INCREMENT WRONG RESPONSES
                session["wrong_responses"] = session.get("wrong_responses", 0) + 1

            messages.append({"role": "system", "content": validation_msg})
            print(f"[VALIDATION] Student: {student_choice}, Correct: {is_correct}, Wrong count: {session.get('wrong_responses', 0)}")

            # Track attempts
            current_step = str(session.get("current_step", 1))
            if not is_correct:
                session["step_attempts"][current_step] = session["step_attempts"].get(current_step, 0) + 1
            else:
                session["step_attempts"][current_step] = 0

            # Clear stored question
            session["last_question"] = None
            session["last_options"] = None
        else:
            # Couldn't validate programmatically - fall back to AI validation
            messages.append({"role": "system", "content": VERIFICATION_PROMPT})
            current_step = str(session.get("current_step", 1))
            session["step_attempts"][current_step] = session["step_attempts"].get(current_step, 0) + 1

            # ✅ Assume wrong if we can't validate (conservative approach)
            session["wrong_responses"] = session.get("wrong_responses", 0) + 1

            print(f"[VALIDATION] Falling back to AI validation, incrementing wrong count: {session.get('wrong_responses', 0)}")
    elif req.message.strip().upper() in ["A", "B", "C", "D"]:
        # No stored question - use AI validation
        messages.append({"role": "system", "content": VERIFICATION_PROMPT})
        current_step = str(session.get("current_step", 1))
        session["step_attempts"][current_step] = session["step_attempts"].get(current_step, 0) + 1

        # ✅ Assume wrong if we can't validate
        session["wrong_responses"] = session.get("wrong_responses", 0) + 1

    # ─────── Mode Enforcement Reminder ───────
    if req.mode in MODE_REMINDERS:
        messages.append({"role": "system", "content": MODE_REMINDERS[req.mode]})

    # ─────── Call AI ───────
    ai_text = await call_ai(messages)
    ai_text = sanitize_to_unicode(ai_text)

    # ─────── Extract MC Options for Next Validation ───────
    options = FastValidator.extract_mc_options(ai_text)
    if options:
        # Store question and options for validation when student responds
        session["last_question"] = ai_text
        session["last_options"] = options
        print(f"[OPTIONS] Extracted {len(options)} options for next validation")

    # ─────── Feedback Detection ───────
    # Detect if AI is asking for feedback
    ai_lower = ai_text.lower()
    if "was this helpful?" in ai_lower and ("👍" in ai_text or "👎" in ai_text):
        session["waiting_for_feedback"] = True

    # Detect if student is responding to feedback question
    if session.get("waiting_for_feedback") and req.message.strip().upper() in ["A", "B"]:
        student_choice = req.message.strip().upper()
        feedback_response = "positive" if student_choice == "A" else "negative"

        # Capture the full interaction (problem + all messages)
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "problem": session.get("original_problem", ""),
            "feedback": feedback_response,
            "full_conversation": [
                {
                    "role": msg.get("role"),
                    "content": msg.get("content") if isinstance(msg.get("content"), str) else str(msg.get("content"))
                }
                for msg in session.get("messages", [])
            ],
            "module": session.get("module"),
            "mode": session.get("mode"),
            "steps_completed": session.get("steps_completed", 0),
            "hints_requested": session.get("hints_requested", 0),
            "why_requested": session.get("why_requested", 0)
        }

        # Add to session's feedback list
        if "feedback_given" not in session:
            session["feedback_given"] = []
        session["feedback_given"].append(feedback_entry)

        # Reset waiting flag
        session["waiting_for_feedback"] = False

    # ─────── Track Metrics ───────
    if "calculator" in ai_text.lower():
        session["calculator_nudges"] = session.get("calculator_nudges", 0) + 1
    if "?" in ai_text:
        session["questions_asked"] = session.get("questions_asked", 0) + 1

    # ✅ DETECT PROBLEM COMPLETION
    completion_phrases = [
        "here's what we did",
        "would you like to",
        "we've solved",
        "we've found",
        "great job! you've completed",
        "excellent work! we've finished",
        "perfect! you've successfully"
    ]
    if any(phrase in ai_text.lower() for phrase in completion_phrases):
        session["problem_completed"] = True
        session["problems_solved"] = session.get("problems_solved", 0) + 1

        # ✅ MARK AS COMPLETED
        session["completed"] = True

        # ✅ DETERMINE IF FINAL ANSWER WAS CORRECT
        # If they completed with few wrong responses, likely correct
        wrong_count = session.get("wrong_responses", 0)
        if wrong_count <= 2:
            session["final_answer_correct"] = True
        else:
            # More ambiguous - could be they got it after multiple tries
            # Conservative: mark as completed but with struggle
            session["final_answer_correct"] = False

        print(f"[COMPLETION] Problem completed! Wrong: {wrong_count}, Final correct: {session.get('final_answer_correct')}")

    if any(word in req.message.lower() for word in ["solve", "find", "calculate"]) or "=" in req.message:
        if not session.get("original_problem"):
            session["original_problem"] = req.message
            session["current_step"] = 1
    if "?" in ai_text and "correct" in ai_text.lower():
        session["current_step"] = session.get("current_step", 0) + 1
        session["steps_completed"] = session.get("steps_completed", 0) + 1
        session["steps_since_check"] = session.get("steps_since_check", 0) + 1

    # ─────── Save and Return ───────
    assistant_message = {"role": "assistant", "content": ai_text}
    session["messages"].append(assistant_message)

    # Save assistant message to Firebase chat history
    if firebase_service and firebase_service.use_firebase:
        firebase_service.save_chat_message(req.session_id, {
            "role": "assistant",
            "content": ai_text,
            "timestamp": datetime.now(pytz.utc).isoformat()
        })

    # Update session duration (time from start to last activity)
    if session.get("started"):
        start_time = datetime.fromisoformat(session["started"])
        current_time = datetime.now(pytz.utc)
        session["duration_seconds"] = int((current_time - start_time).total_seconds())

    # Save session with updated position tracking
    if firebase_service and firebase_service.use_firebase:
        firebase_service.save_session(req.session_id, session)
        TRACKING["sessions"][req.session_id] = session

    save_data()

    return {
        "response": ai_text,
        "session_id": req.session_id,
        "user_token": req.user_token,
        "mode": session["mode"],
        "original_problem": session.get("original_problem")
    }

# ═══════════════════════════════════════════════════════════════════════════
#                         START SERVER
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", 8000))  # Use Railway's PORT or default to 8000

    print(f"Starting {COURSE['code']} Learning Assistant...")
    print(f"Instructor: {COURSE['instructor']}")
    print(f"Institution: {COURSE['institution']}")
    print(f"Port: {port}")
    print("✅ NEW: Enhanced session tracking enabled (wrong_responses, calculator_used, completed)")

    uvicorn.run(app, host="0.0.0.0", port=port)
