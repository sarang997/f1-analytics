---
name: f1-feature-implementer
description: Guides the addition of new features (UI components, data fields, or processing logic) to the F1 Analytics platform while maintaining layer separation.
---

# F1 Feature Implementer Skill

Use this skill when the user wants to add a new visual element, a new data point, or a new calculation to the telemetry pipeline.

## Feature Implementation Workflow

Follow these steps in order to ensure the feature is correctly integrated and cached.

### 1. Data Layer (The Foundation)
If the feature requires new data (e.g., Tire Temp, G-Force):
- **Update Model**: Modify `DriverFrame` in `src/utils/models.py` to include the new field.
- **Update Processor**: Modify `src/processor/data_manager.py`.
    - Extract the data from the FastF1 session.
    - Add an interpolation curve (`interp1d`) for the new field.
    - Map the interpolated value into the `DriverFrame` loop.
- **Refresh Cache**: Instruct the user to run `main.py` with the `--refresh` flag.

### 2. UI Layer (The Presentation)
If the feature is a visual component:
- **Create Component**: Create a new file in `src/ui/components/`.
- **Inheritance/Pattern**: Follow the existing pattern (e.g., `Leaderboard` or `TrackMap`).
    - Use a `draw(self, current_frame)` method.
    - Use constants from `src/utils/config.py` for positioning and colors.
- **Integration**: 
    - Import and instantiate in `src/ui/app.py`.
    - Call the `.draw()` method within `F1Dashboard.on_draw()`.

### 3. Verification
- Verify that the component handles frames where driver data might be missing (check `if drv in frame.drivers`).
- Ensure the UI remains responsive at 60 FPS.
