# Bell Saint v7b Blender Root-Fix Kit

This fixes the error where Blender tried to load the model from:

```text
C:\Program Files\Blender Foundation\Blender 5.1\assets\models\...
```

That happened because Blender did not know your Godot project root.

## Install

Unzip into:

```text
Github/Game/
```

You should get:

```text
they-taught-the-rain-your-name/tools/blender/bell_saint_v7b_sculpt_prep.py
```

## Best way to run

Open a terminal in the Godot project folder:

```bash
cd C:\Users\Amrit\...\Github\Game\they-taught-the-rain-your-name
blender --background --python tools/blender/bell_saint_v7b_sculpt_prep.py
```

## If using Blender UI

1. Open Blender.
2. Go to Scripting.
3. Open:

```text
tools/blender/bell_saint_v7b_sculpt_prep.py
```

4. At the top of the file, find:

```python
USER_PROJECT_ROOT = r""
```

5. Set it to your exact Godot project folder, for example:

```python
USER_PROJECT_ROOT = r"C:\Users\Amrit\OneDrive\Documents\GitHub\Game\they-taught-the-rain-your-name"
```

6. Press Run Script.

## Required file

This must exist before running:

```text
assets/models/enemies/bell_saint/bell_saint_v6_centered_artpass.glb
```

If missing, install the Bell Saint v6 patch first.

## Outputs

```text
assets/models/enemies/bell_saint/blender_work/bell_saint_v7b_sculpt_prep.blend
assets/models/enemies/bell_saint/bell_saint_v7b_sculpt_prep.glb
```
