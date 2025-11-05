# Efficiency Audit Script - Complete Guide

**Created by:** Dr. April Crenshaw with Claude AI Assistance
**Date:** November 5, 2025
**Purpose:** Monitor AI tutor performance and identify optimization opportunities

---

## 🎯 What This Script Does

The Efficiency Auditor tracks:
- ⏱️  **Response times** (how long each API call takes)
- 🎯 **Token usage** (how many tokens per mode)
- 💬 **Conversation history size** (detect bloat)
- 📝 **System prompt sizes** (ensure correct file is being used)
- 🔄 **Mode switches** (when and why they happen)
- 💰 **Cost tracking** (projected costs for 100, 1000 students)
- ⚠️  **Real-time warnings** (immediate feedback on issues)

---

## 🚀 Quick Start (3 Integration Methods)

### **Method 1: Decorator (Easiest)**

Wrap your existing API call function:

```python
from efficiency_audit import audit_api_call, start_session, end_session, generate_report
import time

@audit_api_call(session_id_key="session_id", mode_key="mode")
def call_tutor_api(session_id, mode, system_prompt, messages, user_input):
    """Your existing API call function."""
    start_time = time.time()

    # Your OpenAI API call
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            *messages,
            {"role": "user", "content": user_input}
        ]
    )

    response_time = time.time() - start_time

    # Return tuple: (response_text, tokens_dict, response_time)
    return (
        response.choices[0].message.content,
        response.usage.to_dict(),
        response_time
    )

# In your main app:
start_session("student_123", "unit1", "quick_hints")

# Use your function normally - auditing happens automatically
response_text, tokens, time_taken = call_tutor_api(
    session_id="student_123",
    mode="quick_hints",
    system_prompt=system_prompt,
    messages=conversation_history,
    user_input="Solve 2x + 5 = 13"
)

end_session("student_123")

# Generate report
generate_report("efficiency_report.txt")
```

---

### **Method 2: Manual Logging (Most Control)**

Log each API call manually:

```python
from efficiency_audit import (
    start_session,
    log_api_call,
    log_mode_switch,
    log_problem_completion,
    end_session,
    generate_report
)
import time

# Start session
start_session(
    session_id="student_123",
    topic="unit1",
    mode="quick_hints",
    metadata={"student_name": "Jane Doe", "class": "MATH1710-01"}
)

# Make API call
start_time = time.time()
response = openai.ChatCompletion.create(...)
response_time = time.time() - start_time

# Log the call
log_api_call(
    session_id="student_123",
    mode="quick_hints",
    system_prompt=system_prompt,
    conversation_history=messages,
    user_message=user_input,
    response=response.choices[0].message.content,
    response_time=response_time,
    tokens_used=response.usage.to_dict(),
    success=True
)

# Log mode switch if it happens
if student_wrong_twice:
    log_mode_switch(
        session_id="student_123",
        from_mode="quick_hints",
        to_mode="step_by_step",
        reason="2 wrong attempts"
    )

# Log problem completion
log_problem_completion("student_123")

# End session
end_session("student_123")

# Generate report
generate_report()
```

---

### **Method 3: Context Manager (Clean)**

Use as a context manager for automatic tracking:

```python
from efficiency_audit import EfficiencyAuditor

auditor = EfficiencyAuditor()

with auditor.track_session("student_123", "unit1", "quick_hints"):
    # Your tutor logic here
    # Auditor automatically tracks everything
    pass

# Generate report
auditor.generate_report()
```

---

## 📊 What You Get: Sample Report

After running with students, generate a report:

```
═══════════════════════════════════════════════════════════════════════════════
EFFICIENCY AUDIT REPORT
Generated: 2025-11-05 14:32:10
═══════════════════════════════════════════════════════════════════════════════

📊 OVERALL STATISTICS
────────────────────────────────────────────────────────────────────────────────
Total API calls: 247
Total sessions: 18
Total cost: $2.3456

🎯 TOKEN USAGE BY MODE
────────────────────────────────────────────────────────────────────────────────
quick_hints:
  Average: 1,234 tokens
  Range: 890 - 1,850
  ✅ Within expected range

step_by_step:
  Average: 2,856 tokens
  Range: 2,100 - 4,200
  ⚠️  WARNING: Consider optimization (target: <3000)

⏱️  RESPONSE TIME BY MODE
────────────────────────────────────────────────────────────────────────────────
quick_hints:
  Average: 2.3s
  Range: 1.8s - 4.5s
  ✅ Excellent

step_by_step:
  Average: 4.7s
  Range: 3.2s - 8.9s
  ✅ Acceptable

📝 SYSTEM PROMPT SIZES
────────────────────────────────────────────────────────────────────────────────
quick_hints: 2,103 chars
  ✅ Correct prompt file being used

step_by_step: 5,487 chars
  ✅ Correct prompt file being used

💬 CONVERSATION HISTORY ANALYSIS
────────────────────────────────────────────────────────────────────────────────
Average history size: 4,234 chars
Maximum history size: 12,456 chars
⚠️  WARNING: Conversation history too large!
   Recommendation: Implement sliding window (keep last 6-10 messages)

🔄 MODE SWITCHING ANALYSIS
────────────────────────────────────────────────────────────────────────────────
Total mode switches: 8
  2 wrong attempts: 6 times
  Student request: 2 times

🐌 TOP 10 SLOWEST API CALLS
────────────────────────────────────────────────────────────────────────────────
1. 8.9s - step_by_step - 4,123 tokens
   Note: Large conversation history (11,234 chars)
2. 7.8s - step_by_step - 3,987 tokens
3. 6.5s - detailed_explanations - 4,567 tokens
...

💡 OPTIMIZATION RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════════════════
1. Conversation history averages 4,234 chars. Implement sliding window (keep last 6-10 messages)
2. Implement system prompt caching - build once per session, reuse for all calls
3. Set mode-specific max_tokens: Quick Hints=400, Step-by-Step=900, Detailed=1400
4. Inject contextual prompts (BREAK_SMALLER, RETEACH) as user messages, not in system prompt

💰 COST PROJECTION
────────────────────────────────────────────────────────────────────────────────
Average cost per session: $0.1303
Projected cost for 100 students: $13.03
Projected cost for 1000 students: $130.30

═══════════════════════════════════════════════════════════════════════════════
END OF REPORT
═══════════════════════════════════════════════════════════════════════════════
```

---

## ⚠️  Real-Time Warnings

The auditor provides immediate feedback during runtime:

```
⚠️  [AUDIT] WARNING: Conversation history is 11,456 chars!
   💡 TIP: Implement sliding window (keep last 6-10 messages)

⚠️  [AUDIT] WARNING: Slow response (8.9s)
   💡 TIP: Check if conversation history is too large or prompt too complex

⚠️  [AUDIT] WARNING: High token usage (4,567 tokens)
   💡 TIP: Reduce conversation history or use shorter prompts

⚠️  [AUDIT] WARNING: Quick Hints prompt is 5,234 chars
   💡 TIP: Quick Hints should use prompts_quick_hints.py (~2500 chars)
```

---

## 🔧 Integration Examples

### **Example 1: Flask Web App**

```python
from flask import Flask, request, session
from efficiency_audit import start_session, log_api_call, end_session, generate_report
import time

app = Flask(__name__)

@app.route("/start_tutoring", methods=["POST"])
def start_tutoring():
    session_id = session.get("session_id")
    topic = request.json["topic"]
    mode = request.json["mode"]

    # Start audit tracking
    start_session(session_id, topic, mode, metadata={"user_id": session.get("user_id")})

    return {"status": "started"}

@app.route("/ask_tutor", methods=["POST"])
def ask_tutor():
    session_id = session.get("session_id")
    user_input = request.json["message"]

    # Get conversation state
    system_prompt = get_system_prompt(session["topic"], session["mode"])
    messages = get_conversation_history(session_id)

    # Make API call
    start_time = time.time()
    response = call_openai_api(system_prompt, messages, user_input)
    response_time = time.time() - start_time

    # Log for audit
    log_api_call(
        session_id=session_id,
        mode=session["mode"],
        system_prompt=system_prompt,
        conversation_history=messages,
        user_message=user_input,
        response=response["content"],
        response_time=response_time,
        tokens_used=response["usage"],
        success=True
    )

    return {"response": response["content"]}

@app.route("/admin/efficiency_report")
def efficiency_report():
    """Admin endpoint to view efficiency report."""
    report = generate_report()
    return {"report": report}
```

---

### **Example 2: Streamlit App**

```python
import streamlit as st
from efficiency_audit import start_session, log_api_call, generate_report
import time

# Initialize session
if "audit_started" not in st.session_state:
    start_session(
        session_id=st.session_state.get("session_id", "default"),
        topic=st.selectbox("Topic", ["unit1", "unit2", "unit3"]),
        mode=st.selectbox("Mode", ["quick_hints", "step_by_step", "detailed_explanations"])
    )
    st.session_state.audit_started = True

# User input
user_input = st.text_input("Enter problem:")

if st.button("Submit"):
    # Make API call
    start_time = time.time()
    response = call_tutor(...)
    response_time = time.time() - start_time

    # Log for audit
    log_api_call(...)

    st.write(response)

# Admin section
if st.sidebar.button("Generate Efficiency Report"):
    report = generate_report()
    st.sidebar.download_button("Download Report", report, "efficiency_report.txt")
```

---

### **Example 3: Command-Line Testing**

```python
from efficiency_audit import start_session, log_api_call, end_session, generate_report
import time

def test_tutor_efficiency(num_problems=10):
    """Test tutor with N problems and generate efficiency report."""

    session_id = "test_session"
    start_session(session_id, "unit1", "quick_hints")

    test_problems = [
        "Solve 2x + 5 = 13",
        "Solve 3x - 7 = 11",
        "Solve x/2 + 3 = 7",
        # ... more test problems
    ]

    for i, problem in enumerate(test_problems[:num_problems]):
        print(f"Testing problem {i+1}/{num_problems}: {problem}")

        # Simulate API call
        start_time = time.time()
        response = call_tutor_api(session_id, "quick_hints", problem)
        response_time = time.time() - start_time

        # Log
        log_api_call(
            session_id=session_id,
            mode="quick_hints",
            system_prompt=get_system_prompt("unit1", "quick_hints"),
            conversation_history=get_history(session_id),
            user_message=problem,
            response=response["content"],
            response_time=response_time,
            tokens_used=response["usage"]
        )

        time.sleep(1)  # Rate limiting

    end_session(session_id)

    # Generate report
    report = generate_report("test_efficiency_report.txt")
    print("\n" + "="*80)
    print("EFFICIENCY TEST COMPLETE")
    print("="*80)
    print(report)

if __name__ == "__main__":
    test_tutor_efficiency(num_problems=20)
```

---

## 📈 Interpreting Results

### **Token Usage:**

| Mode | Target | Warning Level | Action |
|------|--------|---------------|--------|
| Quick Hints | <1,500 | >2,000 | Switch to prompts_quick_hints.py |
| Step-by-Step | <3,000 | >3,500 | Check conversation history size |
| Detailed | <4,000 | >5,000 | Implement sliding window |

### **Response Time:**

| Speed | Rating | User Experience |
|-------|--------|-----------------|
| <3s | ✅ Excellent | Students happy |
| 3-5s | ✅ Acceptable | Minor wait |
| 5-8s | ⚠️  Slow | Students notice |
| >8s | 🚨 Too slow | Students frustrated |

### **Conversation History:**

| Size | Status | Action |
|------|--------|--------|
| <3,000 chars | ✅ Good | No action needed |
| 3,000-6,000 | ⚠️  Growing | Monitor |
| >6,000 | 🚨 Too large | Implement sliding window NOW |

---

## 🎯 Optimization Checklist

After running the audit, use this checklist:

### **High Priority:**
- [ ] Implement conversation history sliding window (if >6,000 chars)
- [ ] Switch to mode-specific prompt files (if using wrong file)
- [ ] Cache system prompts (if rebuilding every call)
- [ ] Set mode-specific max_tokens

### **Medium Priority:**
- [ ] Inject contextual prompts as user messages
- [ ] Review mode switching frequency
- [ ] Optimize prompt sizes if possible
- [ ] Add request debouncing/rate limiting

### **Low Priority:**
- [ ] Fine-tune temperature settings
- [ ] Implement prompt compression techniques
- [ ] Set up monitoring dashboard
- [ ] Add cost alerts ($X per day threshold)

---

## 💾 Data Storage

The auditor saves data to `efficiency_audit.json`:

```json
{
  "sessions": {
    "session_123": {
      "session_id": "session_123",
      "topic": "unit1",
      "initial_mode": "quick_hints",
      "current_mode": "step_by_step",
      "start_time": "2025-11-05T14:30:00",
      "end_time": "2025-11-05T14:45:00",
      "api_calls": [...],
      "mode_switches": [...],
      "total_tokens": 12456,
      "total_cost": 0.1234,
      "problems_attempted": 3
    }
  },
  "summary": {
    "total_api_calls": 247,
    "total_sessions": 18,
    "total_mode_switches": 8,
    "last_updated": "2025-11-05T15:00:00"
  }
}
```

---

## 🔒 Privacy & Security

**Important Notes:**

1. **No student content stored** - Only metadata (sizes, times, tokens)
2. **Session IDs are opaque** - Use hashed IDs, not student names
3. **Store audit data securely** - Keep `efficiency_audit.json` out of public repos
4. **GDPR/FERPA compliance** - No PII in logs

**Recommended `.gitignore`:**
```
efficiency_audit.json
efficiency_report.txt
test_efficiency_report.txt
```

---

## 🐛 Troubleshooting

### **Issue: "Session not started" warning**

```python
# Problem: Logging before starting session
log_api_call(session_id="xyz", ...)  # Warning!

# Solution: Always start session first
start_session("xyz", "unit1", "quick_hints")
log_api_call(session_id="xyz", ...)  # Works
```

### **Issue: Report shows 0 calls**

```python
# Problem: Not logging calls
response = call_api(...)  # No logging

# Solution: Log every call
response = call_api(...)
log_api_call(...)  # Add this
```

### **Issue: Token usage not tracked**

```python
# Problem: Wrong tokens_used format
log_api_call(..., tokens_used=response.usage)  # Wrong

# Solution: Convert to dict
log_api_call(..., tokens_used=response.usage.to_dict())  # Correct
```

---

## 🚀 Next Steps

1. **Integrate** the auditor into your app (pick a method above)
2. **Run** with 10-20 test sessions
3. **Generate** your first report
4. **Review** recommendations
5. **Implement** top 3 optimizations
6. **Re-test** to measure improvement
7. **Deploy** to production with monitoring

---

## 📞 Support

**Found an issue?** Check the troubleshooting section above.

**Want to extend?** The `EfficiencyAuditor` class is easily customizable:
- Add custom metrics
- Create custom visualizations
- Export to CSV/Excel
- Integration with monitoring tools (Datadog, New Relic, etc.)

---

**You're ready to audit! 🎉**

Start with Method 1 (decorator) for easiest integration, then work through the optimization checklist based on your report.
