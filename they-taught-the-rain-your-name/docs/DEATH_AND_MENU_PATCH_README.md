# Death + Main Menu Patch

This patch adds:

- Main menu as the starting scene
- Play / Options / Quit buttons
- Options panel with fullscreen, master volume, and mouse sensitivity
- Player health
- Damage function
- Death state
- Death screen
- Restart with R or mouse click after death
- F6 debug damage key for quick testing
- Health text in the debug HUD

## Install

Unzip into:

```text
Github/Game/
```

It should overwrite/add files inside:

```text
Github/Game/they-taught-the-rain-your-name/
```

Then:

1. Close Godot.
2. Delete `.godot/` if cached errors remain.
3. Reopen `project.godot`.

## How to test death

1. Click Play from the menu.
2. Press F6 four times.
3. The death screen should appear.
4. Press R or click to restart.

## Notes

Enemies are not fully attacking yet unless wired with enemy damage behavior. This patch creates the player death system first, then the next patch can add actual enemy chase/touch damage.
