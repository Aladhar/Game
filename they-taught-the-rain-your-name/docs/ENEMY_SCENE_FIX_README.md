# Enemy Scene Fix

Godot was failing to preload these enemy scenes because the `.tscn` files used invalid inline scene syntax like:

```gdscript
mesh = BoxMesh.new()
```

Scene files need mesh resources declared as `[sub_resource]` blocks.

Copy this patch into your Godot project root and overwrite:

```text
scenes/enemies/penance_carrier.tscn
scenes/enemies/bell_saint.tscn
scenes/enemies/rain_hunter.tscn
scenes/enemies/lantern_bride.tscn
scenes/enemies/club_man.tscn
scenes/enemies/crooked_scarecrow.tscn
```

Then close Godot, delete `.godot/` if errors persist, and reopen `project.godot`.
