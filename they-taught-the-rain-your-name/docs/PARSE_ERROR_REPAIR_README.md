# Parse Error Repair Patch

This patch replaces the two scripts Godot reported as parse errors:

- `res://scripts/systems/rain_memory_controller.gd`
- `res://scripts/systems/storm_town_builder.gd`

The replacements use simpler Godot 4-safe GDScript:
- fewer inferred types
- no risky shorthand patterns
- no complex inline logic
- fewer typed assignments that can fail depending on Godot version/import state

## Install

Copy this folder into your local project root and overwrite files:

```text
Github/Game/they-taught-the-rain-your-name/
```

or wherever your Godot project root is.

The important target paths are:

```text
scripts/systems/rain_memory_controller.gd
scripts/systems/storm_town_builder.gd
```

Then in Godot:
1. Close the project.
2. Reopen `project.godot`.
3. If Godot still shows stale errors, delete the `.godot/` cache folder and reopen.
