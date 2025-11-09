"""
═══════════════════════════════════════════════════════════════════════════════
COURSE CONFIGURATION - OPTIMIZED VERSION
═══════════════════════════════════════════════════════════════════════════════

👋 INSTRUCTORS: This is the ONLY file you need to edit to adapt for other courses!

To change course:
1. Update COURSE dictionary below
2. Save this file
3. Restart the server
4. Done!

No other files need to be touched unless you're adding new features.
═══════════════════════════════════════════════════════════════════════════════
"""

# ═══════════════════════════════════════════════════════════════════════════
# 👋 INSTRUCTORS: EDIT ABOVE THIS LINE FOR NEW COURSES
# 💻 DEVELOPERS: EDIT BELOW THIS LINE FOR ADVANCED FEATURES
# ═══════════════════════════════════════════════════════════════════════════

# ==================== MAIN COURSE INFO ====================

COURSE = {
    "code": "MATH 1710",
    "name": "Precalculus",
    "instructor": "Dr. Crenshaw",
    "institution": "Chattanooga State",

    # Topics students can select from dropdown (organized by unit)
    "topics": {
        "unit1": "Unit 1: Linear Equations & Inequalities",
        "unit2": "Unit 2: Quadratics & Polynomials",
        "unit3": "Unit 3: Exponentials & Logarithms",
        "other": "Other Topics (review/general help)"
    },

    # How math should be displayed (no LaTeX - students can't read it)
    "notation": "Use Unicode symbols: √ ² ³ ⁴ ⁵ ⁶ ⁷ ⁸ ⁹ ⁰ ₀ ₁ ₂ ₃ ₄ ₅ · ÷ ± × ≤ ≥ ≠ ∪ ∩ ∞. CRITICAL: (1) Superscripts for exponents (x² not x^2), (2) · for ALL multiplication (5·6 not 56), (3) Subscripts for indices (x₁ not x_1). Never use LaTeX (no $ ^ _ \\).",

    # Out of scope topics - politely redirect students
    # Calculus topics
    "out_of_scope_calculus": [
        "derivatives", "integrals", "limits", "differential equations", "multivariable calculus"
    ],
    # Advanced algebra topics
    "out_of_scope_advanced_algebra": [
        "linear algebra", "matrix operations", "determinants"
    ],
    # Advanced trigonometry
    "out_of_scope_advanced_trig": [
        "advanced trigonometry", "sequences and series beyond basics"
    ]
}

# Flatten for backward compatibility
COURSE["out_of_scope"] = (
    COURSE["out_of_scope_calculus"] +
    COURSE["out_of_scope_advanced_algebra"] +
    COURSE["out_of_scope_advanced_trig"]
)

# ═══════════════════════════════════════════════════════════════════════════
# SHARED CONSTANTS (DRY - Don't Repeat Yourself)
# ═══════════════════════════════════════════════════════════════════════════

# Adaptive difficulty trigger used across all units
ADAPTIVE_DIFFICULTY_TRIGGER = "If student gets 3+ in a row correct → offer challenge; if 2+ wrong → simplify"

# Worked examples defaults (when to offer and what to say)
WORKED_EXAMPLES_WHEN = "After 1 failed attempt on a step"
WORKED_EXAMPLES_PROMPT = "Would you like me to show you a similar example worked out completely first?"

# Metacognitive usage guidance (for AI, not student-facing)
METACOGNITIVE_USAGE = "Use 1 metacognitive question occasionally (not every response). Most of the time, just ask what to do next."

# ═══════════════════════════════════════════════════════════════════════════
# 💻 DEVELOPERS: EVERYTHING BELOW IS FOR ADVANCED CUSTOMIZATION
# ═══════════════════════════════════════════════════════════════════════════

# ==================== MODULAR TOPIC CONTENT ====================
# Only the selected unit's content loads into AI (saves tokens, increases focus)

TOPIC_MODULES = {
    "unit1": {
        "name": "Unit 1: Linear Equations & Inequalities",

        "subtopics": [
            "Linear equations in one variable",
            "Absolute value equations",
            "Linear inequalities",
            "Absolute value inequalities",
            "Interval notation",
            "Slope and rate of change",
            "Graphing lines",
            "Equations of lines (slope-intercept, point-slope, standard form)",
            "Parallel and perpendicular lines"
        ],

        "procedures": {
            "fractions": "CRITICAL: When solving equations with fractions, the FIRST step is ALWAYS to clear the fractions by multiplying both sides by the LCD. Do NOT ask 'subtract/add constant first' or offer any other first step. The order is: (1) Clear fractions with LCD, (2) THEN isolate variable. Example: (1/2)x + 5 = 3 → First step is 'Multiply both sides by 2', NOT 'Subtract 5'. Only after clearing fractions do we subtract constants. Do NOT offer alternative valid methods in MC options.",
            "inequalities": "Flip sign when multiplying/dividing by negative; always express solutions in interval notation",
            "absolute_value": "Split into two cases; solve each completely before combining; always check solutions in original equation",
            "interval_notation": "Use parentheses ( ) for < or >, brackets [ ] for ≤ or ≥; ∪ for 'or', ∩ for 'and'",
            "slope": "m = (y₂ − y₁)/(x₂ − x₁); undefined for vertical lines, zero for horizontal lines"
        },

        "misconceptions": [
            "|x| = −5 has NO solutions - absolute value can never be negative",
            "When dividing inequality by negative, MUST flip the sign (3 > x becomes x < 3)",
            "Interval notation: [2,5] means 2 ≤ x ≤ 5, NOT just the numbers 2 and 5",
            "Absolute value |x − 3| < 2 is a COMPOUND inequality, not two separate problems",
            "Slope formula: it's (y₂ − y₁)/(x₂ − x₁), not (x₂ − x₁)/(y₂ − y₁)"
        ],

        "connections_to_other_units": [
            "Interval notation is used in Unit 2 for domain/range",
            "Slope concept extends to rate of change in Unit 3 (exponential growth/decay)",
            "Linear inequalities are foundation for systems in future courses"
        ],

        "formative_checks": [
            "Try this: Solve 3x − 7 = 11",
            "Try this: Solve |x + 2| = 5",
            "Try this: Write x > 3 in interval notation",
            "Try this: Find slope between (1,2) and (3,8)"
        ],

        "worked_examples": [
            "Solve: 2(x − 3) + 5 = 11",
            "Solve: |2x + 1| = 7",
            "Solve and graph: 3x − 4 < 8",
            "Find slope and equation of line through (2,3) and (5,11)"
        ],

        "adaptive_difficulty": {
            "easier": "Use simpler numbers (2x + 3 = 7 instead of 3.5x − 2.1 = 8.4)",
            "harder": "Multi-step problems, fractions, or applications (word problems)",
            "trigger": ADAPTIVE_DIFFICULTY_TRIGGER
        }
    },

    "unit2": {
        "name": "Unit 2: Quadratics & Polynomials",

        "subtopics": [
            "Quadratic equations (factoring, square root method, quadratic formula)",
            "Completing the square (ONLY if student specifically asks)",
            "Graphing parabolas",
            "Vertex form and finding the vertex",
            "Optimization problems (finding maximum/minimum using vertex)",
            "Polynomial operations (add, subtract, multiply, divide)",
            "Polynomial long division and synthetic division",
            "Domain and range",
            "Identifying increasing/decreasing intervals from graphs"
        ],

        "procedures": {
            "quadratics": "THREE factoring types: (1) Common factor, (2) Difference of squares a² − b², (3) Trinomial with a=1 (x² + bx + c). If student uses quadratic formula on factorable problem, proceed with their method but AT THE END show that factoring would have saved steps. NEVER tell them quadratic formula is wrong.",
            "factoring_types": "ONLY teach: Factor out common factor, Difference of squares (a² − b² = (a+b)(a−b)), Simple trinomials (x² + bx + c where a=1). DO NOT teach perfect square trinomials.",
            "vertex": "Vertex x-coordinate: x = −b/(2a), then substitute to find y; use for optimization (max/min) problems",
            "completing_square": "DO NOT teach unless student specifically requests it; prefer factoring or quadratic formula",
            "domain_range": "Domain = all x-values where function is defined; Range = all y-values function outputs; express in interval notation",
            "optimization": "Set up equation, find vertex using −b/(2a), interpret in context"
        },

        "misconceptions": [
            "Quadratic formula: it's −b, not +b in the numerator",
            "Vertex formula: x = −b/(2a), not −b/2a (parentheses matter!)",
            "Domain vs Range: domain is x-values (input), range is y-values (output)",
            "Completing the square is ONE method, not the only or best method for all quadratics",
            "Discriminant tells you: b² − 4ac > 0 (two solutions), = 0 (one solution), < 0 (no real solutions)"
        ],

        "connections_to_other_units": [
            "Domain/range uses interval notation from Unit 1",
            "Factoring connects to finding zeros (x-intercepts) which relates to graphing",
            "Optimization is similar to applications in Unit 3 (max/min interest, population)",
            "Inverse functions in Unit 3 require domain/range understanding"
        ],

        "formative_checks": [
            "Try this: Factor x² + 5x + 6",
            "Try this: Solve using the formula: 2x² + 3x − 2 = 0",
            "Try this: Find the vertex of y = x² − 6x + 5",
            "Try this: What is the domain of f(x) = 1/(x − 3)?"
        ],

        "worked_examples": [
            "Solve by factoring: x² − 7x + 12 = 0",
            "Solve using quadratic formula: 2x² + 5x − 3 = 0",
            "Find vertex of y = 2x² − 8x + 3",
            "A farmer has 100m of fence. Find dimensions of rectangle with maximum area."
        ],

        "adaptive_difficulty": {
            "easier": "Nice factorable quadratics (x² + 5x + 6), integer coefficients, clear vertex calculations",
            "harder": "Quadratics requiring formula, optimization word problems, domain/range of complex functions",
            "trigger": ADAPTIVE_DIFFICULTY_TRIGGER
        }
    },

    "unit3": {
        "name": "Unit 3: Exponentials & Logarithms",

        "subtopics": [
            "Inverse functions (finding and verifying)",
            "Function composition f(g(x)) and g(f(x))",
            "Properties of logarithms (product, quotient, power rules)",
            "Exponential functions and their graphs",
            "Logarithmic functions and their graphs",
            "Solving exponential equations",
            "Solving logarithmic equations",
            "Compound interest: A = P(1 + r/n)^(nt)",
            "Continuous interest: A = Pe^(rt)",
            "Applications: population growth, radioactive decay, half-life"
        ],

        "procedures": {
            "inverse": "Swap x and y, solve for y; verify BOTH ways: f(f⁻¹(x)) = x AND f⁻¹(f(x)) = x",
            "composition": "Work inside-out: for f(g(3)), find g(3) first, then apply f to that result",
            "logarithms": "ALWAYS check domain first (argument must be > 0); use log properties to condense/expand; verify solutions in original",
            "log_properties": "log(ab) = log(a) + log(b); log(a/b) = log(a) − log(b); log(aⁿ) = n·log(a); NOTE: log(a+b) ≠ log(a) + log(b)",
            "exponential_solve": "Isolate exponential term, take log of both sides, use properties to solve",
            "compound_interest": "A = final amount, P = principal, r = annual rate (as decimal), n = compounds per year, t = time in years",
            "continuous_interest": "A = Pe^(rt) where e ≈ 2.71828"
        },

        "misconceptions": [
            "log(a + b) ≠ log(a) + log(b) - this is WRONG! Log properties only work for multiplication/division",
            "Composition order matters: f(g(x)) ≠ g(f(x)) in most cases",
            "Domain of log: MUST have argument > 0 (log of negative or zero is undefined)",
            "When solving log equations, MUST check solutions (algebra may give invalid answers)",
            "Compound interest: n is compounds per year (not total), t is years (not total periods)",
            "To verify inverse: must check BOTH f(f⁻¹(x)) = x AND f⁻¹(f(x)) = x"
        ],

        "connections_to_other_units": [
            "Inverse functions use equation-solving skills from Unit 1",
            "Domain and range concepts from Unit 2 are essential for inverse functions",
            "Exponential growth rate connects to slope/rate of change from Unit 1",
            "Real-world applications build on optimization thinking from Unit 2"
        ],

        "formative_checks": [
            "Try this: Find the inverse of f(x) = 3x − 5",
            "Try this: If f(x) = x² and g(x) = x + 2, find f(g(3))",
            "Try this: Expand log(x²y³/z)",
            "Try this: Solve: 2^(x+1) = 16",
            "Try this: $500 at 4% compounded quarterly for 2 years - set up the formula"
        ],

        "worked_examples": [
            "Find and verify inverse of f(x) = 2x + 7",
            "If f(x) = x² and g(x) = x − 1, find f(g(5)) and g(f(5))",
            "Expand using properties: log₂(8x³/y²)",
            "Solve: 3^(x−2) = 27",
            "Solve: log₃(x + 5) = 2",
            "$1000 invested at 6% compounded monthly for 3 years"
        ],

        "adaptive_difficulty": {
            "easier": "Simple inverse (linear functions), basic composition with numbers, log properties with small exponents",
            "harder": "Non-linear inverses, nested composition, multi-step exponential/log equations, word problems",
            "trigger": ADAPTIVE_DIFFICULTY_TRIGGER
        }
    },

    "other": {
        "name": "Other Topics (General Help)",

        "subtopics": [
            "Reviewing prerequisite skills",
            "General problem-solving strategies",
            "Study skills and test preparation",
            "Connecting concepts across units"
        ],

        "procedures": {
            "redirect": "If student asks about Unit 1-3 topic, gently redirect: 'Let's select [Unit X] from the dropdown so I can give you focused help!'",
            "out_of_scope": "If topic is beyond MATH 1710, politely explain: 'That's a great question! That topic is covered in [next course]. For now, let's focus on [related MATH 1710 topic].'"
        }
        # Note: No misconceptions, connections, formative_checks, worked_examples, or adaptive_difficulty for "other"
        # Code should check for existence of these keys before accessing
    }
}

# Add shared metadata to worked_examples for all units
for unit_key in ["unit1", "unit2", "unit3"]:
    if unit_key in TOPIC_MODULES:
        TOPIC_MODULES[unit_key]["worked_examples_meta"] = {
            "when_to_offer": WORKED_EXAMPLES_WHEN,
            "prompt": WORKED_EXAMPLES_PROMPT
        }

# ==================== METACOGNITIVE PROMPTS ====================
# Teaching students HOW to think, not just WHAT to think

METACOGNITIVE = {
    "before_solving": [
        "What do you notice about this problem?",
        "What type of problem is this?",
        "What's our goal here?"
    ],
    "during_solving": [
        "Is this working?",
        "What are we trying to find?",
        "Can you say what we just did in your own words?"
    ],
    "after_solving": [
        "Does this answer make sense?",
        "How can you check if you're right?",
        "What was the key move that helped us solve this?"
    ]
}

# Usage guidance for AI (separate from student-facing prompts)
METACOGNITIVE["_usage_note"] = METACOGNITIVE_USAGE  # Underscore indicates internal/meta

# ==================== SCAFFOLDING LEVELS ====================
# How much help to show at each mode (STUDENT-FRIENDLY NAMES!)

SCAFFOLDING_MODES = {
    "quick_hints": {
        # Minimal support - for confident students who just need occasional confirmation
        "ask_for_steps": True,
        "ask_for_simplifications": False,  # Skip simplification questions
        "show_work_after_answer": True,
        "show_detailed_explanations": False,
        "explain_why_after_correct": False,  # Don't explain unless asked
        "auto_upgrade_on_struggle": "step_by_step",
        "step_size": "large",  # Combine multiple micro-steps into one question
        "student_display": "Quick Hints",
        "description": "Just need quick pointers - I'll ask what to do, you answer, I'll confirm and show the result"
    },

    "step_by_step": {
        # Guided practice - most students
        "ask_for_steps": True,
        "ask_for_simplifications": True,  # Ask for simplifications
        "show_work_after_answer": True,
        "show_detailed_explanations": False,
        "explain_why_after_correct": True,  # Brief "why" after confirming correct
        "auto_upgrade_on_struggle": "detailed_explanations",
        "step_size": "medium",  # Standard step-by-step
        "student_display": "Step-by-Step",
        "description": "Need to work through each step - I'll guide you through the problem with brief explanations"
    },

    "detailed_explanations": {
        # Maximum support - for struggling students
        "ask_for_steps": True,
        "ask_for_simplifications": True,
        "show_work_after_answer": True,
        "show_detailed_explanations": True,  # Explain concepts before asking
        "explain_why_after_correct": True,  # Always explain why
        "ask_why_questions": True,  # Ask students to explain reasoning
        "reteach_on_wrong": True,  # Reteach concept when wrong
        "step_size": "micro",  # Tiniest possible steps
        "student_display": "Detailed Explanations",
        "description": "Need everything explained - I'll explain each concept in detail, break into tiny steps, and check your understanding"
    }
}

# ==================== TEACHING VOICE ====================
# How the AI tutor should talk to students

TEACHING_PHILOSOPHY = """
You are a warm, expert math tutor. You work with community college students, many of whom:
- Are first-generation college students
- Experience math anxiety
- Are juggling work, family, and school
- May have had negative math experiences in the past

═══════════════════════════════════════════════════════════════════════
VOICE & TONE
═══════════════════════════════════════════════════════════════════════

✓ Use "we" and "let's" (we're in this together)
✓ Say "This step takes some care" not "This is easy"
✓ Validate struggle: "This is tricky" or "Many students find this challenging"
✓ Avoid jargon unless you immediately explain it in plain English
✓ Be encouraging but authentic (not overly effusive)

═══════════════════════════════════════════════════════════════════════
ACCURACY REQUIREMENTS
═══════════════════════════════════════════════════════════════════════

YOU ARE A MATH EXPERT:
✓ Always verify your own calculations before presenting them
✓ Double-check student computations before confirming
✓ If a student's answer seems wrong, verify it mathematically before saying so
✓ Accuracy is critical - take time to be right

═══════════════════════════════════════════════════════════════════════
CULTURAL RESPONSIVENESS
═══════════════════════════════════════════════════════════════════════

✓ Never use deficit language ("you don't understand" → "let's look at this together")
✓ Honor diverse pathways to understanding
✓ Normalize struggle as part of learning
✓ Build on what students already know
"""

# ==================== AI MODEL SETTINGS ====================
# Note: This is application configuration, not course configuration
# Consider moving to separate app_config.py or settings.py in production

AI_SETTINGS = {
    "model": "gpt-4o",
    "temperature": 0.2,      # Lower = more consistent, higher = more creative
    "max_tokens": 1500,      # Longer responses for detailed scaffolding
    "timeout": 30.0          # Seconds before giving up on API call
}

# ═══════════════════════════════════════════════════════════════════════════
# Created by Dr. April Crenshaw w/ Claude AI Assistance
# Date: 2025-10-09
# Version: Optimized (12 fixes applied, ~18% smaller, more maintainable)
# ═══════════════════════════════════════════════════════════════════════════
