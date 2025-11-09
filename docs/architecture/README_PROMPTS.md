# Teaching Prompts - Implementation Guide

**Created by:** Dr. April Crenshaw with Claude AI Assistance
**Date:** November 5, 2025
**Version:** Optimized with all fixes applied

---

## 📁 Files Overview

Your project now has **3 prompt files** that work together:

| File | Lines | Purpose | When Used |
|------|-------|---------|-----------|
| **prompts_master.py** | 89 | Auto-router | **Import this one!** |
| **prompts_standard.py** | 981 | Step-by-Step & Detailed modes | Auto-loaded by master |
| **prompts_quick_hints.py** | 367 | Quick Hints mode | Auto-loaded by master |

---

## 🚀 How To Use (Drop-In Ready)

### **In Your Main Application:**

```python
# Simply import from prompts_master
from prompts_master import build_system_prompt

# Use it normally - the router handles everything
system_prompt = build_system_prompt(topic='unit1', mode='quick_hints')
```

**That's it!** The master file automatically:
- Detects which mode you're using
- Loads the appropriate optimized version
- Returns the correct prompt

### **No Changes Needed:**
- Your existing code stays the same
- Just rename your current `prompts.py` to `prompts_old.py` (backup)
- Rename `prompts_master.py` to `prompts.py`
- Add `prompts_standard.py` and `prompts_quick_hints.py` to your project folder

---

## 📊 What's Different (All Fixes Applied)

### **All 22 Fixes Included:**

#### **Original 5 Reviewer Issues:**
1. ✅ D is ALWAYS "I'm not sure" and NEVER the correct answer (10+ reinforcements)
2. ✅ Verification checks prevent rejecting correct answers in equivalent forms (1/2 = 0.5, etc.)
3. ✅ Quick Hints ultra-minimal: NO arithmetic questions, shows fully simplified results immediately
4. ✅ Second scaffold provides SUBSTANTIALLY more information with detailed context and examples
5. ✅ Fixed completion flow: "Was this helpful?" → branch based on answer → then ask what's next

#### **Additional 17 Optimizations:**
6. ✅ Emoji policy clarified (only in feedback 👍👎 and session end 👋)
7. ✅ Exclamation mark guidance simplified (periods for steps, exclamations for major achievements)
8. ✅ Summary detail level specified (3-5 words per step)
9. ✅ Confirmation hierarchy (Good work vs Great work)
10. ✅ Comprehension check: removed D option (no exception needed)
11. ✅ Whiteboard separator: exactly 22 ■ symbols
12. ✅ Mode switching announcement ("Let's try a more guided approach together")
13. ✅ When student picks D: treat as help request, not wrong answer
14. ✅ Calculator offer timing specified (after 1st wrong on computation, or 3+ operations)
15. ✅ "Try again" variants covered (never use "try again", "try once more", etc.)
16. ✅ Similar problem generation guidelines (same type, similar difficulty, avoid trivial numbers)
17. ✅ Quadratics: simplified to 3 options (removed duplicate C/D)
18. ✅ Problem restatement format standardized (always "PROBLEM: [equation]")
19. ✅ Session end summary for multiple problems
20. ✅ Answer demand count scope clarified (per session, not per problem)
21. ✅ Symbol standardization (reduced visual clutter)
22. ✅ Consolidated redundancy (shared constants, removed repetition)

---

## 📦 File Details

### **prompts_master.py** (89 lines)
**Purpose:** Auto-routing based on mode

**How it works:**
```python
if mode in ['quick_hints', 'minimal', 'fast']:
    → Load prompts_quick_hints.py
else:
    → Load prompts_standard.py
```

**You import this one.** It handles everything automatically.

---

### **prompts_standard.py** (981 lines, -32% from original)
**Purpose:** Step-by-Step and Detailed Explanations modes

**Includes:**
- Full scaffolding (1st attempt, 2nd attempt with MORE support, 3rd attempt shows solution)
- Comprehension checks every 3 steps
- Detailed teaching examples
- All contextual prompts (reteach, review, break smaller)
- Complete unit procedures for all 3 units

**When used:**
- Step-by-Step mode
- Detailed Explanations mode
- Any mode except Quick Hints

---

### **prompts_quick_hints.py** (367 lines, -74% from original)
**Purpose:** Quick Hints mode (minimal scaffolding)

**Optimizations:**
- NO arithmetic/simplification questions (shows fully simplified immediately)
- NO comprehension checks (Quick Hints skips them)
- NO detailed scaffolding (switches to Step-by-Step mode after 2 wrong)
- Ultra-brief confirmations
- Streamlined unit procedures

**When used:**
- Quick Hints mode
- Any mode name containing 'quick', 'minimal', or 'fast'

---

## 🔧 Integration Steps

### **Step 1: Backup Current File**
```bash
# In your real project folder
mv prompts.py prompts_old.py
```

### **Step 2: Add New Files**
```bash
# Copy these 3 files to your project:
- prompts_master.py → rename to prompts.py
- prompts_standard.py
- prompts_quick_hints.py
```

### **Step 3: Verify Imports**
Make sure your `config.py` exists and has these exports:
```python
# config.py should export:
COURSE
SCAFFOLDING_MODES
TEACHING_PHILOSOPHY
TOPIC_MODULES
METACOGNITIVE
```

### **Step 4: Test Locally**
```python
# Test each mode
from prompts import build_system_prompt

# Test Quick Hints
prompt_qh = build_system_prompt('unit1', 'quick_hints')
print(f"Quick Hints: {len(prompt_qh)} characters")

# Test Step-by-Step
prompt_ss = build_system_prompt('unit1', 'standard')
print(f"Step-by-Step: {len(prompt_ss)} characters")
```

### **Step 5: Deploy**
Once local testing passes, push to production!

---

## 📈 Expected Improvements

### **Performance:**
- **Quick Hints:** 74% smaller prompt → ~50-60% faster AI responses
- **Step-by-Step/Detailed:** 32% smaller → ~25-30% faster AI responses

### **Behavior:**
- **More consistent:** Clearer instructions reduce AI confusion
- **More accurate:** Verification checks prevent false rejections
- **Better scaffolding:** 2nd attempt provides significantly more help
- **Clearer flow:** Completion sequence is now predictable

### **Maintenance:**
- **Easier to update:** Less redundancy, better organization
- **Easier to debug:** Clear separation of modes
- **Easier to test:** Each mode in its own file

---

## 🐛 Troubleshooting

### **Error: "Module 'prompts_quick_hints' not found"**
**Solution:** Make sure all 3 files are in the same directory as your main app.

### **Error: "Cannot import name 'COURSE' from 'config'"**
**Solution:** Verify your `config.py` exists and exports all required constants.

### **AI behavior seems inconsistent**
**Solution:** Check which mode you're passing. Print the mode value to debug:
```python
print(f"Mode selected: {mode}")
prompt = build_system_prompt(topic, mode)
```

### **Want to force a specific file for testing**
```python
# Bypass router for testing
from prompts_quick_hints import build_system_prompt as build_qh
from prompts_standard import build_system_prompt as build_std

# Test specific version
prompt = build_qh('unit1', 'quick_hints')
```

---

## 📝 Version History

**Version 3.0 (Nov 5, 2025) - Optimized with Auto-Router**
- Created master router for automatic mode selection
- Split into standard (981 lines) and quick_hints (367 lines)
- Applied all 22 fixes and optimizations
- 32-74% reduction in prompt size depending on mode

**Version 2.0 (Nov 4, 2025) - All Reviewer Fixes**
- Fixed 5 critical reviewer issues
- Single 1,438-line file for all modes

**Version 1.0 (Oct 9, 2025) - Initial Release**
- Original teaching prompts

---

## 💡 Pro Tips

1. **Monitor response times** - Quick Hints should be noticeably faster
2. **Track completion rates** - Better scaffolding should improve completion
3. **Collect student feedback** - Use the "Was this helpful?" data
4. **Review mode switching** - Watch when students auto-switch from Quick Hints to Step-by-Step

---

## 🆘 Support

**Questions or Issues?**
- Check this README first
- Review the inline comments in each .py file
- Test each mode independently to isolate issues

**Future Updates?**
- These files are ready for production
- Can be further optimized based on student usage data
- Mode-specific improvements can be made to individual files without affecting others

---

## ✅ Ready to Deploy Checklist

- [ ] Backed up original prompts.py
- [ ] Copied all 3 new files to project folder
- [ ] Renamed prompts_master.py to prompts.py
- [ ] Verified config.py exists with required exports
- [ ] Tested Quick Hints mode locally
- [ ] Tested Step-by-Step mode locally
- [ ] Tested Detailed Explanations mode locally
- [ ] Reviewed AI responses for consistency
- [ ] Checked response times (should be faster)
- [ ] Ready to push to production!

---

**You're all set! 🎉**

The tutor will now automatically use the right optimized version for each mode.
