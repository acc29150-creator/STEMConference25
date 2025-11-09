# Usage Report Updates - Custom Requirements

**Updated:** November 5, 2025
**File:** usage_report_optimized.html

---

## 📊 Changes Summary

Your usage report has been updated to match your specific requirements for time periods, columns, and user tracking.

---

## ✅ What Changed

### **1. New Table Columns**

**Before:**
- Student Name
- Unit
- Support Level
- Started
- Duration
- Hints
- "Show Why"

**After:**
| Column | Description | Data Source |
|--------|-------------|-------------|
| **Student Name** | Student's display name | `user.name` or "Anonymous" |
| **Unit** | Course unit (Unit 1, Unit 2, etc.) | `session.module` |
| **Mode** | Support level (Quick Hints, Step-by-Step, Detailed) | `session.mode` |
| **Time Spent** | Session duration in minutes | `session.duration_seconds / 60` |
| **Hints** | Number of hints requested | `session.hints_requested` or `session.hint_count` |
| **Calculator Use** | Number of times calculator was used | `session.calculator_used` or `session.calculator_count` |
| **Wrong Responses** | Number of incorrect answers given | `session.wrong_responses` or `session.incorrect_count` |

---

### **2. New Time Period Categories**

**Before:**
- 📅 Today
- 📆 This Week
- 📊 Past 30 Days
- 🎓 Student Collaborators
- 🗄️ Archived (Test Sessions)

**After:**
| Category | Time Range | Description |
|----------|------------|-------------|
| **📅 Past 7 Days** | Last 7 days | Most recent activity |
| **📆 Past 14 Days** | Last 14 days | 2-week view |
| **📊 Past 30 Days** | Last 30 days | Monthly view |
| **📈 Past 60 Days** | Last 60 days | 2-month view |
| **🎓 Student Collaborators** | All time | Test/collaborator sessions |
| **🗄️ Archived (90+ Days, Max 100)** | 90+ days old | Auto-archived old sessions (limited to 100 most recent) |

**Key Features:**
- ✅ Sessions automatically archive after 90 days
- ✅ Maximum 100 archived sessions kept (oldest pruned automatically)
- ✅ Sessions can appear in multiple time periods (e.g., a session from 5 days ago appears in both "Past 7 Days" and "Past 14 Days")

---

### **3. New User Statistics Section**

**New section added:** "👥 Active Users by Time Period"

Shows **unique user counts** for each time period:

```
📊 Active Users by Time Period
┌─────────────────┬────────────────┐
│ Past 7 Days     │ 15 users       │
│ Past 14 Days    │ 23 users       │
│ Past 30 Days    │ 42 users       │
│ Past 60 Days    │ 58 users       │
│ Archived (90+)  │ 12 users       │
└─────────────────┴────────────────┘
```

This answers: "How many different students used the tutor in the past X days?"

---

### **4. Updated CSV Export**

**New CSV columns:**
```csv
Student Name,Unit,Mode,Time Spent (min),Hints,Calculator Use,Wrong Responses,Type
```

**Example CSV output:**
```csv
"Student Name","Unit","Mode","Time Spent (min)","Hints","Calculator Use","Wrong Responses","Type"
"John Smith","Unit 1","Quick Hints","12","3","1","2","Active"
"Jane Doe","Unit 2","Step-by-Step","25","8","5","4","Active"
"Test User","Unit 1","Detailed","5","0","0","0","Collaborator"
"Old User","Unit 3","Quick Hints","15","2","0","1","Archived (90+)"
```

---

## 📋 Data Field Reference

### **Required Data in Backend**

For the report to work correctly, your backend tracking should capture:

```javascript
// Per session
{
  session_id: "unique-id",
  user_token: "user-unique-token",
  module: "Unit 1",           // or "Unit 2", "Unit 3", etc.
  mode: "Quick Hints",        // or "Step-by-Step", "Detailed Explanations"
  started: "2025-11-05T10:30:00Z",
  duration_seconds: 720,      // 12 minutes
  hints_requested: 3,         // NEW: number of hints
  calculator_used: 1,         // NEW: number of calculator uses
  wrong_responses: 2,         // NEW: number of incorrect answers
  collaborator: false,        // true for test/collaborator sessions
  collaborator_role: null     // "TA", "Instructor", etc.
}
```

**Field name variations supported:**
- Hints: `hints_requested` OR `hint_count`
- Calculator: `calculator_used` OR `calculator_count`
- Wrong responses: `wrong_responses` OR `incorrect_count`

---

## 🎯 Usage Examples

### **Example 1: Track Weekly Engagement**

Open "Past 7 Days" accordion to see:
- All students who used the tutor in the last week
- How long each session lasted
- How many hints they needed
- Whether they used the calculator
- How many mistakes they made

**Use case:** Identify students who might be struggling (high wrong responses, many hints)

---

### **Example 2: Monthly Reporting**

1. Open "Past 30 Days" accordion
2. Review all sessions from the month
3. Click "📥 Export to CSV"
4. Open in Excel/Google Sheets
5. Create pivot tables to analyze:
   - Which units have most wrong responses
   - Average time spent by mode
   - Calculator usage patterns

---

### **Example 3: Long-term Trends**

Compare user counts across time periods:
- Past 7 Days: 15 users
- Past 14 Days: 23 users
- Past 30 Days: 42 users
- Past 60 Days: 58 users

**Insight:** Growing user base over time

---

## 🔧 Technical Details

### **Automatic Archiving**

Sessions are automatically categorized based on age:

```javascript
const ninetyDaysAgo = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000);

if (sessionDate < ninetyDaysAgo) {
  // Archive (max 100 entries)
  if (archived.length < 100) {
    archived.push(session);
  }
}
```

**What happens when 101st archived session arrives?**
- Only the 100 most recent archived sessions are kept
- Oldest archived sessions are automatically pruned
- This prevents unlimited growth of archived data

---

### **Unique User Counting**

```javascript
getUniqueUserCount(sessions) {
  const uniqueTokens = new Set(sessions.map(s => s.user_token));
  return uniqueTokens.size;
}
```

**How it works:**
- Extracts all `user_token` values from sessions
- Uses JavaScript `Set` to automatically remove duplicates
- Returns count of unique tokens

**Example:**
- Session 1: user_token = "abc123"
- Session 2: user_token = "abc123" (same user)
- Session 3: user_token = "xyz789" (different user)
- **Result:** 2 unique users

---

### **Session Overlap in Multiple Periods**

A session from 5 days ago appears in:
- ✅ Past 7 Days (because 5 < 7)
- ✅ Past 14 Days (because 5 < 14)
- ✅ Past 30 Days (because 5 < 30)
- ✅ Past 60 Days (because 5 < 60)

This is intentional and allows you to see:
- "Past 7 Days" = Activity in last week
- "Past 30 Days" = All activity in last month (includes the last week)

---

## 📊 Report Structure

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Usage Report                                              │
│ MATH 1710 Precalculus Learning Assistant (Optimized)       │
├─────────────────────────────────────────────────────────────┤
│ [🔄 Refresh] [📥 Export CSV] [☑ Auto-refresh] [🔍 Search]  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 📈 Overview                                                  │
│ ├─ Total Users: 58                                          │
│ ├─ Total Sessions: 142                                      │
│ ├─ Problems Solved: 324                                     │
│ └─ Avg Session Time: 18 min                                 │
│                                                              │
│ 👥 Active Users by Time Period                              │
│ ├─ Past 7 Days: 15 users                                    │
│ ├─ Past 14 Days: 23 users                                   │
│ ├─ Past 30 Days: 42 users                                   │
│ ├─ Past 60 Days: 58 users                                   │
│ └─ Archived (90+): 12 users                                 │
│                                                              │
│ 📚 Usage by Unit                                             │
│ 📊 (table)                                                   │
│                                                              │
│ 🎯 Usage by Support Level                                   │
│ 📊 (table)                                                   │
│                                                              │
│ 💡 Help Features Used                                        │
│ ├─ Total Hints: 456                                         │
│ ├─ "Show Me Why" Clicks: 123                                │
│ └─ Avg Hints/Session: 3.2                                   │
│                                                              │
│ 📝 Session History                                           │
│ ├─ 📅 Past 7 Days (15 sessions) ▼                          │
│ │   [Table with columns: Name, Unit, Mode, Time, Hints...] │
│ ├─ 📆 Past 14 Days (23 sessions) ▶                         │
│ ├─ 📊 Past 30 Days (42 sessions) ▶                         │
│ ├─ 📈 Past 60 Days (58 sessions) ▶                         │
│ ├─ 🎓 Student Collaborators (5 sessions) ▶                 │
│ └─ 🗄️ Archived (90+ Days, Max 100) (12 sessions) ▶        │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Verification Checklist

After deploying the updated report, verify:

### **Display:**
- [ ] "Active Users by Time Period" section shows 5 stat cards
- [ ] Session History has 6 accordions (Past 7/14/30/60, Collaborators, Archived)
- [ ] Table columns: Name, Unit, Mode, Time Spent, Hints, Calculator Use, Wrong Responses

### **Functionality:**
- [ ] Click accordion → table loads with correct columns
- [ ] Search works across student names and units
- [ ] Export CSV → downloads with new column headers
- [ ] Auto-refresh checkbox → updates data every 30s
- [ ] Unique user counts display correctly

### **Data:**
- [ ] Calculator Use column shows numbers (not all zeros)
- [ ] Wrong Responses column shows numbers
- [ ] Time periods show expected session counts
- [ ] Archived shows max 100 sessions

---

## 🔍 Troubleshooting

### **Issue: Calculator Use and Wrong Responses show all zeros**

**Cause:** Backend not tracking these fields yet

**Solution:** Update your backend session tracking to capture:
```javascript
calculator_used: countCalculatorClicks(),
wrong_responses: countIncorrectAnswers()
```

**Temporary workaround:** Fields will show 0 until backend is updated

---

### **Issue: Archived section empty**

**This is normal if:**
- No sessions older than 90 days exist
- All sessions are recent

**To test:** Manually create test sessions with dates > 90 days ago

---

### **Issue: User counts don't match session counts**

**This is correct!**
- User count = number of **unique** students
- Session count = number of **total** sessions

**Example:**
- John has 3 sessions
- Jane has 2 sessions
- **User count:** 2
- **Session count:** 5

---

## 📈 Next Steps

1. **Deploy updated report:**
   ```bash
   cp usage_report_optimized.html usage_report.html
   ```

2. **Update backend tracking** (if not already done):
   - Add `calculator_used` field
   - Add `wrong_responses` field

3. **Test with real data:**
   - Verify all columns populate correctly
   - Check user counts make sense
   - Export CSV and review in Excel

4. **Use for insights:**
   - Track weekly engagement trends
   - Identify struggling students (high wrong responses)
   - Analyze calculator usage patterns
   - Monitor time spent by mode

---

## 🎉 Summary

**Your usage report now provides:**

✅ **Time-based tracking** - Past 7, 14, 30, 60 days, plus 90+ archive
✅ **New metrics** - Calculator use and wrong responses
✅ **User counting** - Unique users per time period
✅ **Detailed sessions** - 7 columns of actionable data
✅ **CSV export** - All data exportable for analysis
✅ **Auto-archiving** - Old sessions automatically archived (max 100)
✅ **All optimizations** - Fast, cached, searchable, auto-refresh

**Ready to deploy! 🚀**
