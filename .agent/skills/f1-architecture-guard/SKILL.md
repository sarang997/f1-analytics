---
name: f1-architecture-guard
description: Ensures that code changes adhere to the decoupled architecture of the F1 Analytics platform, preventing circular dependencies and layer leakage.
---

# F1 Architecture Guard Skill

Use this skill to validate that any proposed changes maintain the separation of concerns between Data Processing and Visualization.

## Architectural Principles

### 1. Separation of Layers
- **Processor Layer (`src/processor/`)**: Only handles data fetching, math, and interpolation. 
    - **NO** imports from `arcade` or `src/ui/`.
    - **NO** screen coordinates or pixel logic.
- **UI Layer (`src/ui/`)**: Only handles rendering and user input.
    - **NO** calls to `fastf1` directly.
    - **NO** heavy math or interpolation (this should happen in the processor and be cached).
    - Data must be accessed via the pre-computed `SessionData` / `Frame` objects.

### 2. Shared Source of Truth
- All shared data types must be defined in `src/utils/models.py`.
- All magic numbers (colors, offsets, sizes) must live in `src/utils/config.py`.

### 3. Caching Integrity
- Any change to the `Frame` model MUST be accompanied by an instruction to the user to `--refresh` their cache.
- The `DataManager` should remain the sole owner of the cache lifecycle.

## Checklist for Reviewing Changes
- [ ] Does this change add a UI import to a processor file? (Fail)
- [ ] Does this change add a `fastf1` import to a UI file? (Fail)
- [ ] Are new colors defined as inline hex codes? (Fail - Move to `config.py`)
- [ ] Is heavy interpolation happening in the `on_update` loop? (Fail - Move to `DataManager`)
