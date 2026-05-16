# GitHub Repair v2

This patch fixes the errors from Godot 4.6.2.

## Fix 1: Missing autoloads

Your `project.godot` was missing:

```text
[autoload]
GameState="*res://scripts/autoload/game_state.gd"
SceneBus="*res://scripts/autoload/scene_bus.gd"
AudioManager="*res://scripts/autoload/audio_manager.gd"
```

Without those, scripts throw:

```text
Identifier "SceneBus" not declared in the current scope.
Identifier "GameState" not declared in the current scope.
Identifier "AudioManager" not declared in the current scope.
```

## Fix 2: Enemy `.tscn` sub_resource ordering

Godot was throwing:

```text
Parse Error: Unknown tag 'sub_resource' in file.
```

because some enemy scenes had `[sub_resource]` blocks after `[node]` blocks. This patch moves all subresources before all nodes.

## Install

Unzip into:

```text
Github/Game/
```

It should overwrite:

```text
they-taught-the-rain-your-name/project.godot
they-taught-the-rain-your-name/scenes/enemies/*.tscn
```

Then:

1. Close Godot.
2. Delete `Github/Game/they-taught-the-rain-your-name/.godot/`.
3. Reopen `project.godot`.
