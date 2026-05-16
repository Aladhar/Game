# Folder Guide

```text
assets/
  audio/
    ambience/      Rain beds, thunder, wind
    enemies/       Enemy motifs and movement cues
    rituals/       Bells, prayers, chimes, knocks
    broadcasts/    Emergency warning system voice clips
  models/
    enemies/       GLB/OBJ enemy models
    environment/   Town, church, mill, tower assets
  textures/        PBR textures
  materials/       Shared Godot materials
  fonts/           UI/story fonts

docs/
  Story and implementation documents

resources/
  enemy_configs/   Future enemy tuning Resource files
  ritual_rules/    Future ritual rule definitions
  story_events/    Future event definitions

scenes/
  main/            Main playable prototype scenes
  player/          Player scene
  ui/              HUD/debug UI scenes
  enemies/         Enemy scenes
  environment/     Reusable environment pieces
  interactables/   Bells, doors, radios, notes, tower console

scripts/
  autoload/        Global state/signal managers
  player/          Movement and camera
  ui/              HUD controllers
  systems/         Main gameplay systems
  enemies/         Enemy controllers
  interactables/   Interactable object scripts
  environment/     Environment scripts
```
