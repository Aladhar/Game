# THEY TAUGHT THE RAIN YOUR NAME

Godot 4.x rough-draft project for a psychological folk-horror game.

## Core hook

In Greyhollow, rain does not just fall. It repeats people.

Every person who died there left behind a pattern in the rain:

- footsteps
- knocking
- breathing
- crying
- whispering
- door-opening
- dragging
- prayer
- bell ringing

At first, it sounds like ambience.

Then it copies the dead.

Eventually, it copies you.

## Current prototype goal

This ZIP is a fresh Godot starter project with the full folder structure and rough systems for:

- first-person player movement
- debug ritual HUD
- SoundEventTracker
- RainMemoryController
- RitualDirector
- StormTownBuilder
- placeholder ritual enemy scenes
- playable prototype scene

The first playable target is simple:

> The player enters Greyhollow, makes a sound, and the rain repeats it later.

## Open in Godot

1. Open Godot 4.x.
2. Click **Import**.
3. Select:

```text
they-taught-the-rain-your-name/project.godot
```

4. Import and run.

## Controls

- WASD = move
- Mouse = look
- Shift = sprint
- E = interact / knock test
- Esc = unlock/lock mouse
- Left click = recapture mouse

## Suggested repo placement

Put this folder inside your repo as a new project folder:

```text
Roblox/
  they-taught-the-rain-your-name/
    project.godot
    scenes/
    scripts/
    assets/
    docs/
```

This avoids breaking the old `dont-look-home` Godot folder.
