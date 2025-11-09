# Archive

This folder contains duplicate and variant files that are not currently used in production but are preserved for reference.

## Duplicate Files (Identical to Production)

- **app_updated.py** - Duplicate of `app.py`
- **firebase_service_fixed.py** - Duplicate of `firebase_service.py`

## Variant Files (Not Currently Used)

### Prompts Variants
- **prompts_master.py** - Router system for mode-based prompt selection
- **prompts_optimized.py** - Optimized prompts variant
- **prompts_quick_hints.py** - Quick Hints only variant
- **prompts_standard.py** - Step-by-Step/Detailed variant

**Note:** The production system uses `prompts.py` which contains all modes in one file.

### Other Variants
- **config_optimized.py** - Alternative configuration file
- **answer_validator_optimized.py** - Old validator (missing FastValidator class that was added to production)

---

## Why Archive These?

These files were created during development and optimization but were superseded by the current production files. They're kept here for:
- Historical reference
- Alternative implementation ideas
- Future optimization experiments
- Documentation of development evolution

**Production files are in the root directory.**
