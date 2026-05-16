# Penance Carrier Blockout v1

This patch adds a real Godot-ready geometric blockout model for the Penance Carrier.

## Files included

```text
assets/models/enemies/penance_carrier/penance_carrier_blockout_v1.glb
scenes/enemies/penance_carrier.tscn
scripts/enemies/penance_carrier_controller.gd
docs/PENANCE_CARRIER_BLOCKOUT_README.md
```

## Install

Unzip into your repo root:

```text
Github/Game/
```

It should merge into:

```text
Github/Game/they-taught-the-rain-your-name/
```

## What this is

This is the correct first production step toward a AAA enemy:

```text
geometric blockout → readable silhouette → Godot import → controller → later sculpt/textures/animations
```

The model uses simple mesh shapes to define:

- hunched humanoid body
- giant shrine load
- slanted roof
- hanging face mask
- large hand bell
- radios / speakers / clocks / cassettes
- candles / warm glow markers
- chains / ropes / dangling bells
- wet cloth / wood / rusted metal / brass material colors

## Godot scene

Use:

```text
res://scenes/enemies/penance_carrier.tscn
```

The scene contains:

- CharacterBody3D root
- GLB model instance
- CollisionShape3D
- audio player placeholders
- candle light
- weak point markers
- idle sway/facing script

## Next upgrade pass

After this works in-game, the next model pass should replace the blockout pieces with:

1. Blender sculpted body
2. proper wood shrine planks
3. actual bell/radio/clock models
4. UV unwraps
5. 2K/4K PBR textures
6. LOD0/LOD1/LOD2 exports
