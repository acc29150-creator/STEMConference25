# Backend Implementation Guide
# Supporting Enhanced Usage Report Features

**Date:** November 5, 2025
**Purpose:** Implementation guide for tracking fields needed by enhanced usage report
**Status:** Ready for implementation

---

## 🎯 Overview

Your enhanced usage report now provides powerful insights into student success, but it needs three additional tracking fields in the backend to show real data instead of zeros:

1. **`wrong_responses`** - Total incorrect answers per session
2. **`calculator_used`** - Actual calculator usage count (not just AI nudges)
3. **`completed`** - Whether the problem was successfully solved

This guide provides complete implementation details for each field, plus additional backend improvement suggestions.

---

## 📊 Current vs Enhanced Tracking

### **What You're Already Tracking (✅):**
```python
session = {
    "hints_requested": 0,          # ✅ Works with report
    "why_requested": 0,            # ✅ Works with report
    "duration_seconds": None,      # ✅ Works with report
    "calculator_nudges": 0,        # ⚠️ AI suggestions, not actual use
    "module": "Unit 1",            # ✅ Works with report
    "mode": "Quick Hints",         # ✅ Works with report
    "started": "2025-11-05T...",   # ✅ Works with report
    "step_attempts": {},           # ✅ Tracks attempts per step
}
```

### **What Needs to Be Added (❌):**
```python
session = {
    # ... existing fields ...

    # NEW: Track incorrect answers
    "wrong_responses": 0,          # ❌ Not tracked yet

    # NEW: Track actual calculator usage
    "calculator_used": 0,          # ❌ Not tracked yet

    # NEW: Track completion status
    "completed": False,            # ❌ Not tracked yet
    "final_answer_correct": False, # ❌ Alternative completion indicator
}
```

---

## 🔧 Implementation 1: Wrong Responses Tracking

### **What It Tracks:**
Total number of incorrect answers given by the student during the session.

### **Why It Matters:**
- Powers "Students Needing Attention" alert (flags students with 5+ wrong)
- Calculates "Most Challenging Units" ranking
- Shows color-coded status indicators (🟢🟡🟠🔴)
- Enables early intervention for struggling students

### **How to Implement:**

#### **Option A: Aggregate from step_attempts**

If you already track attempts per step, you can derive wrong responses:

```python
# When initializing a new session:
new_session = {
    # ... existing fields ...
    "step_attempts": {},           # Already tracking this
    "wrong_responses": 0,          # NEW: Initialize to 0
}

# When student gives an incorrect answer:
def handle_incorrect_answer(session_id, step_number, student_answer):
    session = get_session(session_id)

    # Existing: Track attempts per step
    step_key = str(step_number)
    session["step_attempts"][step_key] = session["step_attempts"].get(step_key, 0) + 1

    # NEW: Increment total wrong responses
    session["wrong_responses"] = session.get("wrong_responses", 0) + 1

    save_session(session)

    return {
        "feedback": "That's not quite right. Let me help you...",
        "attempts_this_step": session["step_attempts"][step_key],
        "total_wrong": session["wrong_responses"]
    }
```

#### **Option B: Calculate on session end**

If you prefer to calculate at the end of the session:

```python
def end_session(session_id):
    session = get_session(session_id)

    # Calculate total wrong responses from step_attempts
    # Assumes first attempt = correct, subsequent = wrong
    total_wrong = 0
    for step, attempts in session.get("step_attempts", {}).items():
        if attempts > 1:
            total_wrong += (attempts - 1)  # Each retry is a wrong answer

    session["wrong_responses"] = total_wrong
    session["ended"] = datetime.now(pytz.utc).isoformat()

    save_session(session)
    return session
```

#### **Option C: Track with validator results**

If you use FastValidator or similar:

```python
from answer_validator_optimized import FastValidator

validator = FastValidator()

def check_answer(session_id, step_number, student_answer, correct_answer):
    session = get_session(session_id)

    # Validate answer
    result = validator.validate(student_answer, correct_answer)

    if not result.is_correct:
        # NEW: Increment wrong responses
        session["wrong_responses"] = session.get("wrong_responses", 0) + 1

    save_session(session)

    return {
        "correct": result.is_correct,
        "feedback": result.feedback,
        "total_wrong": session.get("wrong_responses", 0)
    }
```

### **Testing:**

```python
# Test: Student gets 3 wrong answers in a session
session = create_session(user_token="test123", module="Unit 1")
assert session["wrong_responses"] == 0

handle_incorrect_answer(session["id"], step=1, answer="5")  # Wrong
assert get_session(session["id"])["wrong_responses"] == 1

handle_incorrect_answer(session["id"], step=1, answer="6")  # Wrong again
assert get_session(session["id"])["wrong_responses"] == 2

handle_incorrect_answer(session["id"], step=2, answer="x")  # Wrong on step 2
assert get_session(session["id"])["wrong_responses"] == 3

print("✅ Wrong responses tracking works!")
```

---

## 🔧 Implementation 2: Calculator Usage Tracking

### **What It Tracks:**
Number of times the student actually **used** the calculator (not just AI suggestions to use it).

### **Why It Matters:**
- Shows in session detail tables
- Helps understand student self-reliance
- Different from `calculator_nudges` (which tracks AI suggestions)

### **Current Issue:**
```python
# Currently you track AI suggestions to use calculator:
session["calculator_nudges"] = 0  # AI told student to use calculator

# But NOT actual usage:
session["calculator_used"] = ?  # Student actually clicked calculator
```

### **How to Implement:**

#### **Option A: Frontend event tracking**

If your frontend has a calculator component:

```javascript
// In your frontend (index.html or similar):
function onCalculatorButtonClick() {
    // Show calculator UI
    showCalculator();

    // NEW: Notify backend that calculator was used
    fetch('/api/session/calculator-used', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: currentSessionId
        })
    });
}
```

Then in your backend:

```python
@app.post("/api/session/calculator-used")
async def track_calculator_use(request: Request):
    data = await request.json()
    session_id = data.get("session_id")

    session = get_session(session_id)

    # NEW: Increment calculator usage
    session["calculator_used"] = session.get("calculator_used", 0) + 1

    save_session(session)

    return {"calculator_uses": session["calculator_used"]}
```

#### **Option B: Track in chat messages**

If calculator access is through chat commands:

```python
def handle_chat_message(session_id, user_message):
    session = get_session(session_id)

    # Check if message indicates calculator use
    if "calculator" in user_message.lower() or "calc" in user_message.lower():
        # NEW: Increment calculator usage
        session["calculator_used"] = session.get("calculator_used", 0) + 1

    # Existing: Check if AI should suggest calculator
    if should_suggest_calculator(user_message):
        session["calculator_nudges"] = session.get("calculator_nudges", 0) + 1
        response = "You might want to use a calculator for this step."
    else:
        response = generate_response(user_message)

    save_session(session)
    return response
```

#### **Option C: Detect from student work**

If you can detect calculator use from student answers:

```python
import re

def is_calculator_result(answer):
    """Detect if answer looks like calculator output."""
    # Calculator outputs often have many decimal places
    if isinstance(answer, str):
        # Match patterns like "3.14159265359" or "0.333333333"
        decimal_pattern = r'\d+\.\d{5,}'
        return bool(re.search(decimal_pattern, answer))
    return False

def check_answer(session_id, step_number, student_answer):
    session = get_session(session_id)

    # NEW: Detect calculator usage from answer format
    if is_calculator_result(student_answer):
        session["calculator_used"] = session.get("calculator_used", 0) + 1

    # ... rest of answer checking ...

    save_session(session)
```

### **Initialization:**

```python
# When creating a new session:
new_session = {
    # ... existing fields ...
    "calculator_nudges": 0,        # AI suggestions to use calculator
    "calculator_used": 0,          # NEW: Actual calculator usage
}
```

### **Testing:**

```python
# Test: Track both nudges and actual use
session = create_session(user_token="test123")
assert session["calculator_used"] == 0
assert session["calculator_nudges"] == 0

# AI suggests calculator
suggest_calculator(session["id"])
assert get_session(session["id"])["calculator_nudges"] == 1
assert get_session(session["id"])["calculator_used"] == 0  # Not used yet

# Student actually uses calculator
use_calculator(session["id"])
assert get_session(session["id"])["calculator_used"] == 1

print("✅ Calculator tracking works!")
```

---

## 🔧 Implementation 3: Session Completion Tracking

### **What It Tracks:**
Whether the student successfully completed the problem.

### **Why It Matters:**
- Powers "Mode Effectiveness Comparison" success rates
- Shows which modes lead to completion
- Helps identify if students are finishing or giving up

### **How to Implement:**

#### **Option A: Track final answer correctness**

```python
def check_final_answer(session_id, final_answer, correct_answer):
    session = get_session(session_id)
    validator = FastValidator()

    result = validator.validate(final_answer, correct_answer)

    # NEW: Mark completion status
    session["completed"] = True  # Problem was attempted to completion
    session["final_answer_correct"] = result.is_correct

    if result.is_correct:
        session["problems_solved"] = session.get("problems_solved", 0) + 1

    session["ended"] = datetime.now(pytz.utc).isoformat()

    # Calculate duration
    started = datetime.fromisoformat(session["started"])
    ended = datetime.now(pytz.utc)
    session["duration_seconds"] = int((ended - started).total_seconds())

    save_session(session)

    return {
        "correct": result.is_correct,
        "completed": True,
        "feedback": result.feedback
    }
```

#### **Option B: Track when student reaches final step**

```python
def advance_to_step(session_id, next_step, total_steps):
    session = get_session(session_id)

    session["current_step"] = next_step

    # NEW: Mark as completed when reaching final step
    if next_step >= total_steps:
        session["completed"] = True
        session["reached_final_step"] = True

    save_session(session)
    return session
```

#### **Option C: Explicit completion endpoint**

```python
@app.post("/api/session/complete")
async def complete_session(request: Request):
    data = await request.json()
    session_id = data.get("session_id")
    success = data.get("success", False)  # Did they solve it correctly?

    session = get_session(session_id)

    # NEW: Mark session as completed
    session["completed"] = True
    session["final_answer_correct"] = success
    session["ended"] = datetime.now(pytz.utc).isoformat()

    # Calculate final duration
    if session.get("started"):
        started = datetime.fromisoformat(session["started"])
        ended = datetime.now(pytz.utc)
        session["duration_seconds"] = int((ended - started).total_seconds())

    save_session(session)

    return {
        "session_id": session_id,
        "completed": True,
        "success": success
    }
```

#### **Option D: Detect abandonment**

Track both completion and abandonment:

```python
def check_session_status(session_id):
    """Check if session is completed, abandoned, or in progress."""
    session = get_session(session_id)

    # Already marked as completed?
    if session.get("completed"):
        return "completed"

    # Check for abandonment (no activity in 30+ minutes)
    last_activity = session.get("last_activity")
    if last_activity:
        idle_time = (datetime.now(pytz.utc) - datetime.fromisoformat(last_activity)).total_seconds()
        if idle_time > 1800:  # 30 minutes
            # NEW: Mark as abandoned
            session["completed"] = False
            session["abandoned"] = True
            session["abandonment_reason"] = "idle_timeout"
            save_session(session)
            return "abandoned"

    return "in_progress"

# Call this periodically or on session end
def end_session(session_id):
    session = get_session(session_id)

    status = check_session_status(session_id)

    if status == "in_progress":
        # User explicitly ended without completing
        session["completed"] = False
        session["abandoned"] = True
        session["abandonment_reason"] = "user_ended"

    session["ended"] = datetime.now(pytz.utc).isoformat()
    save_session(session)

    return session
```

### **Initialization:**

```python
# When creating a new session:
new_session = {
    # ... existing fields ...
    "completed": False,            # NEW: Has problem been completed?
    "final_answer_correct": None,  # NEW: Was final answer correct?
    "abandoned": False,            # NEW: Did student abandon session?
    "current_step": 1,             # Track progress through problem
    "last_activity": datetime.now(pytz.utc).isoformat(),  # For abandonment detection
}
```

### **Update last_activity on every interaction:**

```python
def update_last_activity(session_id):
    """Call this on every chat message, answer check, hint request, etc."""
    session = get_session(session_id)
    session["last_activity"] = datetime.now(pytz.utc).isoformat()
    save_session(session)

# Example usage:
def handle_chat_message(session_id, message):
    update_last_activity(session_id)  # Update activity timestamp
    # ... rest of chat handling ...
```

### **Testing:**

```python
# Test: Session completion tracking
session = create_session(user_token="test123")
assert session["completed"] == False

# Student works through problem
advance_to_step(session["id"], step=2, total_steps=3)
assert get_session(session["id"])["completed"] == False

# Student reaches final step and answers correctly
check_final_answer(session["id"], "42", "42")
final_session = get_session(session["id"])
assert final_session["completed"] == True
assert final_session["final_answer_correct"] == True

print("✅ Completion tracking works!")
```

---

## 📊 Complete Session Structure (After Implementation)

```python
{
    # === Identity & Metadata ===
    "session_id": "unique-session-id",
    "user_token": "user-unique-token",
    "module": "Unit 1",                    # Which unit/topic
    "mode": "Quick Hints",                 # Support level
    "started": "2025-11-05T10:30:00Z",    # Session start time
    "ended": "2025-11-05T10:45:00Z",      # Session end time (optional)
    "last_activity": "2025-11-05T10:44:30Z",  # Last interaction timestamp

    # === Timing ===
    "duration_seconds": 900,               # 15 minutes

    # === Help & Support Used ===
    "hints_requested": 3,                  # ✅ Already tracking
    "why_requested": 2,                    # ✅ Already tracking
    "calculator_nudges": 1,                # ✅ Already tracking (AI suggestions)
    "calculator_used": 1,                  # ❌ NEW: Actual calculator usage
    "answer_demand_count": 0,              # ✅ Already tracking

    # === Performance & Outcomes ===
    "wrong_responses": 4,                  # ❌ NEW: Total incorrect answers
    "problems_solved": 1,                  # ✅ Already tracking
    "completed": True,                     # ❌ NEW: Was problem completed?
    "final_answer_correct": True,          # ❌ NEW: Was final answer right?
    "abandoned": False,                    # ❌ NEW: Did student give up?
    "abandonment_reason": None,            # ❌ NEW: Why abandoned (if applicable)

    # === Step-by-Step Tracking ===
    "current_step": 3,                     # ✅ Already tracking
    "total_steps": 3,                      # Current problem structure
    "step_attempts": {                     # ✅ Already tracking
        "1": 2,                            # 2 attempts on step 1
        "2": 1,                            # 1 attempt on step 2
        "3": 2                             # 2 attempts on step 3
    },

    # === Conversation History ===
    "messages": [                          # ✅ Already tracking
        {"role": "user", "content": "Help me solve this..."},
        {"role": "assistant", "content": "Let's start by..."}
    ],

    # === Classification ===
    "collaborator": False,                 # ✅ Already tracking
    "collaborator_role": None,             # ✅ Already tracking
}
```

---

## 🚀 Additional Backend Improvements

Beyond the three required fields, here are suggestions to improve efficiency, clarity, and functionality:

### **1. Database Indexing**

If using Firebase or similar, add indexes for common queries:

```python
# Add composite indexes for:
# - user_token + started (for user history)
# - module + started (for unit analytics)
# - started (for time-based queries)
# - collaborator (for filtering)

# Firebase example:
# In firebase.indexes.json:
{
  "indexes": [
    {
      "collectionGroup": "sessions",
      "queryScope": "COLLECTION",
      "fields": [
        {"fieldPath": "user_token", "order": "ASCENDING"},
        {"fieldPath": "started", "order": "DESCENDING"}
      ]
    },
    {
      "collectionGroup": "sessions",
      "queryScope": "COLLECTION",
      "fields": [
        {"fieldPath": "module", "order": "ASCENDING"},
        {"fieldPath": "started", "order": "DESCENDING"}
      ]
    }
  ]
}
```

### **2. Session Caching**

Cache active sessions in memory to reduce database reads:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class SessionCache:
    def __init__(self):
        self.cache = {}  # session_id -> (session_data, last_updated)
        self.cache_duration = timedelta(minutes=5)

    def get(self, session_id):
        """Get session from cache or database."""
        if session_id in self.cache:
            data, last_updated = self.cache[session_id]

            # Check if cache is still fresh
            if datetime.now() - last_updated < self.cache_duration:
                return data

        # Cache miss or stale - fetch from database
        data = fetch_from_database(session_id)
        self.cache[session_id] = (data, datetime.now())
        return data

    def set(self, session_id, data):
        """Update cache and database."""
        self.cache[session_id] = (data, datetime.now())
        save_to_database(session_id, data)

    def invalidate(self, session_id):
        """Remove from cache."""
        if session_id in self.cache:
            del self.cache[session_id]

# Usage:
session_cache = SessionCache()

def get_session(session_id):
    return session_cache.get(session_id)

def save_session(session_id, data):
    session_cache.set(session_id, data)
```

### **3. Batch Analytics Calculation**

Pre-calculate common analytics to reduce report load time:

```python
from datetime import datetime, timedelta
import pytz

class AnalyticsCache:
    """Pre-calculate common analytics for faster report loading."""

    def __init__(self):
        self.last_calculated = None
        self.cache = {}
        self.cache_duration = timedelta(minutes=30)

    def should_recalculate(self):
        if not self.last_calculated:
            return True
        return datetime.now() - self.last_calculated > self.cache_duration

    def calculate(self):
        """Pre-calculate common analytics."""
        if not self.should_recalculate():
            return self.cache

        print("Calculating analytics...")

        # Fetch all recent sessions
        thirty_days_ago = datetime.now(pytz.utc) - timedelta(days=30)
        sessions = fetch_sessions_since(thirty_days_ago)

        # Calculate aggregates
        analytics = {
            "total_sessions": len(sessions),
            "total_users": len(set(s["user_token"] for s in sessions)),
            "avg_duration": sum(s.get("duration_seconds", 0) for s in sessions) / len(sessions) if sessions else 0,
            "total_hints": sum(s.get("hints_requested", 0) for s in sessions),
            "total_problems_solved": sum(s.get("problems_solved", 0) for s in sessions),

            # By unit
            "by_unit": self._aggregate_by_unit(sessions),

            # By mode
            "by_mode": self._aggregate_by_mode(sessions),

            # Completion rates
            "completion_rate": sum(1 for s in sessions if s.get("completed")) / len(sessions) if sessions else 0,

            # Success rate
            "success_rate": sum(1 for s in sessions if s.get("final_answer_correct")) / len(sessions) if sessions else 0,
        }

        self.cache = analytics
        self.last_calculated = datetime.now()

        return analytics

    def _aggregate_by_unit(self, sessions):
        by_unit = {}
        for session in sessions:
            unit = session.get("module", "Unknown")
            if unit not in by_unit:
                by_unit[unit] = {"sessions": 0, "wrong": 0, "hints": 0, "duration": 0}

            by_unit[unit]["sessions"] += 1
            by_unit[unit]["wrong"] += session.get("wrong_responses", 0)
            by_unit[unit]["hints"] += session.get("hints_requested", 0)
            by_unit[unit]["duration"] += session.get("duration_seconds", 0)

        return by_unit

    def _aggregate_by_mode(self, sessions):
        by_mode = {}
        for session in sessions:
            mode = session.get("mode", "Unknown")
            if mode not in by_mode:
                by_mode[mode] = {"sessions": 0, "completed": 0, "success": 0}

            by_mode[mode]["sessions"] += 1
            if session.get("completed"):
                by_mode[mode]["completed"] += 1
            if session.get("final_answer_correct"):
                by_mode[mode]["success"] += 1

        return by_mode

# Usage:
analytics_cache = AnalyticsCache()

@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Fast analytics endpoint using pre-calculated cache."""
    return analytics_cache.calculate()
```

### **4. Session Cleanup Job**

Automatically clean up old sessions:

```python
from datetime import datetime, timedelta
import pytz

async def cleanup_old_sessions():
    """Background job to archive or delete very old sessions."""

    # Archive sessions older than 90 days
    ninety_days_ago = datetime.now(pytz.utc) - timedelta(days=90)

    old_sessions = fetch_sessions_before(ninety_days_ago)

    print(f"Found {len(old_sessions)} sessions older than 90 days")

    # Option A: Move to archive collection
    for session in old_sessions:
        archive_session(session)
        delete_session(session["session_id"])

    # Option B: Delete entirely (if already exported)
    # for session in old_sessions:
    #     delete_session(session["session_id"])

    print(f"Archived {len(old_sessions)} old sessions")

# Run this as a cron job or scheduled task
# Example with APScheduler:
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_old_sessions, 'cron', hour=3)  # Run at 3 AM daily
scheduler.start()
```

### **5. Validation Layer**

Add validation for all session updates:

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class SessionUpdate(BaseModel):
    """Validate session updates to prevent bad data."""

    hints_requested: Optional[int] = Field(ge=0, description="Must be non-negative")
    wrong_responses: Optional[int] = Field(ge=0, description="Must be non-negative")
    calculator_used: Optional[int] = Field(ge=0, description="Must be non-negative")
    duration_seconds: Optional[int] = Field(ge=0, description="Must be non-negative")
    completed: Optional[bool] = None

    @validator('duration_seconds')
    def duration_reasonable(cls, v):
        if v and v > 7200:  # More than 2 hours
            raise ValueError("Duration seems unreasonably long (>2 hours)")
        return v

    @validator('wrong_responses')
    def wrong_responses_reasonable(cls, v):
        if v and v > 50:
            raise ValueError("Wrong responses seems unreasonably high (>50)")
        return v

# Usage:
@app.post("/api/session/update")
async def update_session(session_id: str, updates: SessionUpdate):
    """Update session with validation."""
    session = get_session(session_id)

    # Apply validated updates
    for field, value in updates.dict(exclude_none=True).items():
        session[field] = value

    save_session(session_id, session)
    return {"success": True}
```

### **6. Logging & Monitoring**

Add structured logging for debugging:

```python
import logging
import json
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def log_session_event(session_id, event_type, data=None):
    """Log important session events in structured format."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "event_type": event_type,
        "data": data or {}
    }

    logger.info(json.dumps(log_entry))

# Usage throughout your code:
def handle_incorrect_answer(session_id, step, answer):
    session = get_session(session_id)
    session["wrong_responses"] = session.get("wrong_responses", 0) + 1

    log_session_event(session_id, "incorrect_answer", {
        "step": step,
        "wrong_count": session["wrong_responses"]
    })

    save_session(session_id, session)

def complete_session(session_id, success):
    session = get_session(session_id)
    session["completed"] = True
    session["final_answer_correct"] = success

    log_session_event(session_id, "session_completed", {
        "success": success,
        "duration": session.get("duration_seconds"),
        "wrong_responses": session.get("wrong_responses", 0),
        "hints_used": session.get("hints_requested", 0)
    })

    save_session(session_id, session)
```

### **7. Export API Enhancement**

Add a bulk export endpoint for the usage report:

```python
from fastapi.responses import StreamingResponse
import csv
from io import StringIO

@app.get("/api/sessions/export")
async def export_sessions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    module: Optional[str] = None,
    mode: Optional[str] = None
):
    """Export sessions to CSV with optional filtering."""

    # Build query based on filters
    query = {}
    if start_date:
        query["started"] = {">=": start_date}
    if end_date:
        if "started" not in query:
            query["started"] = {}
        query["started"]["<="] = end_date
    if module:
        query["module"] = module
    if mode:
        query["mode"] = mode

    # Fetch filtered sessions
    sessions = fetch_sessions(query)

    # Create CSV
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "session_id", "user_token", "module", "mode",
        "started", "duration_seconds",
        "hints_requested", "calculator_used", "wrong_responses",
        "completed", "final_answer_correct",
        "problems_solved"
    ])

    writer.writeheader()
    for session in sessions:
        writer.writerow({
            "session_id": session.get("session_id"),
            "user_token": session.get("user_token"),
            "module": session.get("module"),
            "mode": session.get("mode"),
            "started": session.get("started"),
            "duration_seconds": session.get("duration_seconds"),
            "hints_requested": session.get("hints_requested", 0),
            "calculator_used": session.get("calculator_used", 0),
            "wrong_responses": session.get("wrong_responses", 0),
            "completed": session.get("completed", False),
            "final_answer_correct": session.get("final_answer_correct", False),
            "problems_solved": session.get("problems_solved", 0)
        })

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sessions_export.csv"}
    )
```

### **8. Error Handling & Recovery**

Add robust error handling:

```python
from functools import wraps
import traceback

def handle_session_errors(func):
    """Decorator to handle session-related errors gracefully."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except KeyError as e:
            logger.error(f"Session field missing: {e}")
            return {"error": "Session data incomplete", "field": str(e)}
        except ValueError as e:
            logger.error(f"Invalid session data: {e}")
            return {"error": "Invalid data", "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}\n{traceback.format_exc()}")
            return {"error": "Internal server error"}
    return wrapper

# Usage:
@app.post("/api/session/update")
@handle_session_errors
async def update_session(session_id: str, updates: dict):
    session = get_session(session_id)

    # This will be safely handled if anything goes wrong
    session.update(updates)
    save_session(session_id, session)

    return {"success": True}
```

---

## 📋 Implementation Checklist

Use this checklist to track your implementation progress:

### **Phase 1: Core Tracking Fields**
- [ ] Add `wrong_responses` field to session schema
- [ ] Implement wrong responses increment on incorrect answers
- [ ] Test wrong responses tracking with multiple scenarios
- [ ] Add `calculator_used` field to session schema
- [ ] Implement calculator usage tracking (frontend event or detection)
- [ ] Test calculator usage tracking
- [ ] Add `completed` field to session schema
- [ ] Add `final_answer_correct` field to session schema
- [ ] Implement completion tracking when problem is solved
- [ ] Test completion tracking for both success and failure cases

### **Phase 2: Testing & Verification**
- [ ] Create test session with known values
- [ ] Verify usage report shows correct data (not all zeros)
- [ ] Check "Students Needing Attention" flags correctly (5+ wrong)
- [ ] Verify color-coded indicators work (green/yellow/orange/red)
- [ ] Verify "Most Challenging Units" ranks correctly
- [ ] Verify "Mode Effectiveness" shows success rates
- [ ] Export CSV and verify all columns have data

### **Phase 3: Additional Improvements** (Optional)
- [ ] Implement session caching for performance
- [ ] Add database indexes for common queries
- [ ] Implement analytics pre-calculation
- [ ] Add session cleanup job for old data
- [ ] Add validation layer for session updates
- [ ] Enhance logging and monitoring
- [ ] Create bulk export API endpoint
- [ ] Add error handling and recovery

---

## 🧪 Testing Examples

### **Test 1: Complete Session Flow**

```python
# Create a test session with all tracking
def test_complete_session_flow():
    # Start session
    session = create_session(
        user_token="test_user_123",
        module="Unit 1",
        mode="Step-by-Step"
    )

    assert session["wrong_responses"] == 0
    assert session["calculator_used"] == 0
    assert session["completed"] == False

    # Student attempts step 1 (wrong)
    handle_incorrect_answer(session["id"], step=1, answer="5")
    session = get_session(session["id"])
    assert session["wrong_responses"] == 1

    # Student attempts step 1 again (correct this time)
    handle_correct_answer(session["id"], step=1, answer="10")
    session = get_session(session["id"])
    assert session["wrong_responses"] == 1  # Doesn't increment on correct

    # Student uses calculator
    track_calculator_use(session["id"])
    session = get_session(session["id"])
    assert session["calculator_used"] == 1

    # Student attempts step 2 (wrong)
    handle_incorrect_answer(session["id"], step=2, answer="x")
    session = get_session(session["id"])
    assert session["wrong_responses"] == 2

    # Student completes problem successfully
    complete_session(session["id"], success=True)
    session = get_session(session["id"])

    assert session["completed"] == True
    assert session["final_answer_correct"] == True
    assert session["wrong_responses"] == 2
    assert session["calculator_used"] == 1
    assert session["duration_seconds"] > 0

    print("✅ Complete session flow works!")
```

### **Test 2: Report Integration**

```python
# Test that usage report receives correct data
def test_usage_report_integration():
    # Create 3 test sessions with varying difficulty

    # Easy session (1 wrong)
    session1 = create_test_session(wrong=1, calculator=0, completed=True, success=True)

    # Medium session (3 wrong)
    session2 = create_test_session(wrong=3, calculator=1, completed=True, success=True)

    # Hard session (8 wrong - should trigger alert)
    session3 = create_test_session(wrong=8, calculator=2, completed=False, success=False)

    # Fetch report data
    report_data = fetch_report_data()

    # Verify "Students Needing Attention" flags session3
    assert session3["id"] in report_data["students_needing_attention"]

    # Verify color coding
    assert get_status_color(session1) == "green"   # 1 wrong = green
    assert get_status_color(session2) == "yellow"  # 3 wrong = yellow
    assert get_status_color(session3) == "red"     # 8 wrong = red

    # Verify mode effectiveness calculation
    mode_stats = report_data["mode_effectiveness"]["Step-by-Step"]
    assert mode_stats["completion_rate"] == 2/3  # 2 out of 3 completed
    assert mode_stats["success_rate"] == 2/3     # 2 out of 3 successful

    print("✅ Report integration works!")
```

---

## 🎯 Priority Implementation Order

1. **Start with wrong_responses** (30 min)
   - Highest impact for "Students Needing Attention"
   - Enables color-coded indicators
   - Powers "Most Challenging Units"

2. **Add completion tracking** (20 min)
   - Enables "Mode Effectiveness" success rates
   - Shows which modes lead to completion

3. **Add calculator_used** (20 min)
   - Completes all required fields
   - Less critical than above, but needed for full data

4. **Test everything** (30 min)
   - Verify report shows real data
   - Check all new features work correctly

5. **Optional improvements** (ongoing)
   - Add caching, logging, cleanup, etc. as needed

---

## 📞 Support & Questions

### **If wrong_responses shows all zeros:**
- Verify you're incrementing the field on each incorrect answer
- Check that the field name matches (`wrong_responses` or `incorrect_count`)
- Test with a known session that had wrong answers

### **If calculator_used shows all zeros:**
- Verify frontend is calling the tracking endpoint
- Check that events are being captured correctly
- Try manual test by calling endpoint directly

### **If completion tracking isn't working:**
- Verify you're marking `completed = True` when problem is solved
- Check that end-of-session logic is running
- Ensure `final_answer_correct` is set appropriately

### **Performance concerns:**
- Implement session caching (see Additional Improvements #2)
- Add database indexes (see Additional Improvements #1)
- Use analytics pre-calculation (see Additional Improvements #3)

---

## ✅ Summary

**Three fields to add:**
1. `wrong_responses` - Total incorrect answers
2. `calculator_used` - Actual calculator usage
3. `completed` - Whether problem was finished

**Why they matter:**
- Enable "Students Needing Attention" alerts
- Power "Most Challenging Units" ranking
- Show color-coded status indicators
- Calculate mode effectiveness and success rates

**Implementation time:**
- Core tracking: ~1.5 hours
- Testing: ~30 minutes
- Optional improvements: ongoing

**After implementation:**
Your usage report will transform from showing zeros to showing actionable insights that help you identify struggling students, understand which topics are challenging, and measure tutoring effectiveness.

**Ready to implement! 🚀**
