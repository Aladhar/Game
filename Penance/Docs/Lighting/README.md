# V5 lighting repair

The prior editor session logged `Failed to build lighting!!! Lighting build failed`, with five lights and 833 primitives left unbuilt. It also reported a missing Lightmass importance volume. The Lightmass worker logs stopped after `Building static lighting...`; they did not provide a specific solver error. The newly supplied pasted log was startup output rather than the failed build session.

V5 is an editable blockout, so its lighting is now consistently **dynamic**. This repair deliberately removes V5's dependence on a Lightmass bake; it does not claim that the Lightmass solver itself was repaired or that static lightmaps were successfully baked.

Changes saved through Unreal's command-line Python APIs:

- All eight V5 light components use Movable mobility.
- V5's World Settings enable Force No Precomputed Lighting.
- V5_Afternoon_Light has forward-shading priority 2 and is the sole atmosphere sun. The two fill directionals retain priority 0 and their existing intensities/colors.
- Actor transforms and building geometry are unchanged.
- The V5 generation helper creates future lights with the same dynamic configuration, preventing this setup error from returning on regeneration.
- Warning overlays are enabled. This fix does not hide lighting errors with a console suppression setting.

Backups are in `Built/Checkpoints/BeforeV5LightingFix`. The original persistent map, House01 interior, player and enemy assets are hash-checked separately and unchanged. Global static-lighting support is retained for other maps.

To apply the idempotent repair again from a terminal, close the saved editor session and run:

```sh
PYTHONPYCACHEPREFIX=/private/tmp/PenanceLighting/pycache \
'/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/Mac/UnrealEditor' \
'/Users/amritladhar/Documents/GitHub/Game/Penance/PenanceDemoUE.uproject' \
-unattended -nop4 -run=pythonscript \
-script='/Users/amritladhar/Documents/GitHub/Game/Penance/Scripts/Fix_Penance_V5_Lighting.py'
```

V5 no longer needs Build Lighting to be playable. Keep new V5 lights Movable. A future baked-lighting art pass would require deliberately restoring a static-lighting configuration, preparing lightmap UVs, bounding the bake with an importance volume, and validating the Lightmass pipeline separately.

Validation records: [saved repair](V5_Lighting_Repair.json), [initial settings](Initial_Light_Settings.json), [rendered verification](Rendered_Validation.json), [preservation check](Preservation.json), [gameplay screenshot](V5_Lighting_Gameplay.png).

During automation, two commandlet-only limitations were corrected: a Play-session query requiring the full editor, and a map-check command attempting to open a Slate results window. The final repair uses a headless-safe map check and exits normally.

Final result: the repaired commandlet run exited normally. Fresh rendered-editor checks found **0 lights and 0 primitives with unbuilt interactions**, and map checks reported **0 errors and 0 warnings**. All eight rendered/PIE checks passed, including player possession, camera, objective HUD and actual movement. Unreal was left open on the corrected level.
