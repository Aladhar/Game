# Implementation Plan

## Project goal

Build a rough playable Godot 4.x prototype proving the main horror mechanic:

> The rain records player behavior and repeats it back.

## Minimum vertical slice

1. Player enters rainy Greyhollow.
2. Player sees storm warning text.
3. Player knocks / sprints / stands still.
4. SoundEventTracker records the behavior.
5. RainMemoryController repeats it later.
6. Penance Carrier appears when the rain has learned too much.
7. Broadcast tower teases the story.

## Main systems

### SoundEventTracker
Tracks symbolic gameplay sound events:
- sprint_step
- knock
- bell_ring
- door_open
- silence_window
- puddle_step
- follow_cry
- repeat_route

### RainMemoryController
Stores sound events and replays them as rain imitation.

### RitualDirector
Controls acts, rule reveals, warning messages, and escalation.

### StormTownBuilder
Creates the temporary greybox town layout.

### EnemyDirector
Later system. For now, each enemy can be staged as a placeholder.

## First coding targets

1. Make project open with no missing files.
2. Make mouse look work.
3. Make debug HUD show event history.
4. Press E to create a knock event.
5. Sprinting creates sprint events.
6. Remaining still creates silence events.
7. Rain repeats one stored event after a delay.
8. Penance Carrier appears when memory intensity is high.

## Later targets

- actual audio files
- 3D sound positioning
- ritual bell system
- mill rhythm system
- field silence system
- emotional lure sounds
- enemy AI behaviors
- detailed Penance Carrier model
- story event timeline
