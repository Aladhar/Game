# Bell Saint v7 Blender Sculpt-Prep Kit

This kit prepares the Bell Saint v6 model for a real Blender sculpt/art pass.

## What this script does

It runs inside Blender and:

- imports `bell_saint_v6_centered_artpass.glb`
- recenters the model
- organizes pieces into named collections
- assigns AAA-oriented material placeholders
- adds bevels and weighted normals
- adds procedural cloth/metal/noise displacement
- adds guide markers for weak points
- adds preview lights and camera
- saves a `.blend`
- exports a Godot-ready `bell_saint_v7_sculpt_prep.glb`

## Required before running

Make sure this file exists:

```text
they-taught-the-rain-your-name/assets/models/enemies/bell_saint/bell_saint_v6_centered_artpass.glb
```

If it does not, install the Bell Saint v6 patch first.

## How to run in Blender

Option A: Blender UI

1. Open Blender.
2. Go to `Scripting`.
3. Open this file:

```text
they-taught-the-rain-your-name/tools/blender/bell_saint_v7_sculpt_prep.py
```

4. Press `Run Script`.

Option B: command line

From the Godot project root:

```bash
blender --background --python tools/blender/bell_saint_v7_sculpt_prep.py
```

## Outputs

After running, you should get:

```text
assets/models/enemies/bell_saint/blender_work/bell_saint_v7_sculpt_prep.blend
assets/models/enemies/bell_saint/bell_saint_v7_sculpt_prep.glb
```

## Godot integration

To test the v7 GLB in Godot, update:

```text
scenes/enemies/bell_saint.tscn
```

Change the model path from:

```text
res://assets/models/enemies/bell_saint/bell_saint_v6_centered_artpass.glb
```

to:

```text
res://assets/models/enemies/bell_saint/bell_saint_v7_sculpt_prep.glb
```

## Important

This is not the final AAA model yet. It is the prepared Blender file where you begin the real AAA work:

- sculpt real cloth folds
- sculpt bell dents/chips
- add better chains
- retopologize
- UV unwrap
- bake normal/AO/curvature
- texture in Blender/Substance/ArmorPaint
- export LOD0/LOD1/LOD2
