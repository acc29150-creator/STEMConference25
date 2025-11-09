"""
═══════════════════════════════════════════════════════════════════════════════
TEACHING PROMPTS - MASTER ROUTER
═══════════════════════════════════════════════════════════════════════════════

This file automatically selects the appropriate prompt version based on mode.

AUTOMATIC MODE DETECTION:
- Quick Hints mode → Uses prompts_quick_hints.py (ultra-streamlined, 367 lines)
- Step-by-Step mode → Uses prompts_standard.py (optimized, 981 lines)
- Detailed Explanations mode → Uses prompts_standard.py (optimized, 981 lines)

NO MANUAL SELECTION REQUIRED - Just call build_system_prompt() as usual.
═══════════════════════════════════════════════════════════════════════════════
"""

def build_system_prompt(topic: str, mode: str) -> str:
    """
    Automatically route to the correct prompt file based on mode.

    This function detects the scaffolding mode and loads the appropriate
    optimized prompt file:
    - Quick Hints → prompts_quick_hints.py (minimal scaffolding)
    - Step-by-Step/Detailed → prompts_standard.py (full scaffolding)

    Args:
        topic (str): Which unit (e.g., "unit1", "unit2", "unit3", "other")
        mode (str): Scaffolding level (e.g., "quick_hints", "standard", "detailed")

    Returns:
        str: Complete prompt optimized for the selected mode
    """

    # Detect Quick Hints mode
    if mode == 'quick_hints' or mode == 'minimal' or mode == 'fast':
        # Import Quick Hints version (ultra-streamlined)
        from prompts_quick_hints import build_system_prompt as build_quick_hints
        return build_quick_hints(topic, mode)

    else:
        # Import Standard version (for Step-by-Step and Detailed modes)
        from prompts_standard import build_system_prompt as build_standard
        return build_standard(topic, mode)


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXTUAL PROMPTS (can be imported by other modules if needed)
# ═══════════════════════════════════════════════════════════════════════════

COMPREHENSION_CHECK_PROMPT = """
COMPREHENSION CHECK DUE (every 3 steps)

Pause and ask:
"How are you feeling about what we've done so far?"
A) I'm following along
B) Mostly following, but a bit unsure
C) I'm lost

Wait for their response before continuing.
"""

BRIEF_REVIEW_PROMPT = """
Student is mostly following.

1. Restate: PROBLEM: [equation]
2. Briefly review the last 3 steps with emphasis on WHY we did them
3. Then ask: 'Does that make more sense now? (A) Yes (B) Still unsure' before continuing
"""

RETEACH_PROMPT = """
RETEACH MODE ACTIVATED - Student is struggling with comprehension.

1. Restate: PROBLEM: [equation]
2. Say: "No problem - let's go back through this together."
3. Re-explain everything we've done so far with:
   - Simpler language
   - Emphasis on WHY each step makes sense
   - Smaller micro-steps
4. After reteaching, ask: "Does this approach make more sense now?"
   A) Yes, let's continue
   B) Still confused
   C) I'm not sure
5. If B or C, break into even smaller steps and reteach again
"""

# ═══════════════════════════════════════════════════════════════════════════
# Created by Dr. April Crenshaw w/ Claude AI Assistance
# Date: 2025-11-05
#
# Version: Master Router (auto-selects optimized version based on mode)
# ═══════════════════════════════════════════════════════════════════════════
