# Penance Demo Unreal Import

This project is a clean Unreal Engine import target for the Godot blockout in:

`../they-taught-the-rain-your-name`

The import is intentionally editable blockout geometry, not a baked mesh. It reconstructs Godot boxes, cylinders, lights, player start, event areas, and interactable markers as Unreal actors.

## What Imports

- Outdoor neighborhood loop, arrival street, park, cul-de-sac, church/community center, basement/storm-drain tunnel geometry, final house silhouette.
- Multi-story graybox houses and route-control blockers.
- Basic material colors for wet roads, concrete, rotten wood, rusted metal, cloth/water, candles/photos, warm windows/spill light.
- Point/spot/directional lights exported from the Godot scene.
- Scripted-event and interactable volumes as visible marker cubes.
- Player start converted from Godot meters to Unreal centimeters.

## What Does Not Import Automatically

- Godot GDScript gameplay/state logic.
- Godot UI, AudioManager, rain particle controller, and one-shot event code.
- Final detailed Penance assets beyond whatever is represented in the current blockout primitives.

Those systems should be rebuilt natively in Unreal after the blockout arrives.

## Native Unreal Gameplay Added

- `APenancePlayerCharacter` ports the Godot player rules into native Unreal C++: grounded first-person movement, no jump/fly, sprint stamina, low-stamina sprint speed, crouch camera/capsule changes, mouse look, and Blueprint events for stamina, crouch, and player noise.
- `APenanceDemoGameMode` is configured as the default game mode so Play-in-Editor spawns the grounded player pawn instead of Unreal's default floating pawn.

## Import Native Unreal Assets

The blockout importer handles level geometry. Enemy art assets are imported separately from the Godot asset folder:

```sh
"/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "/Users/amritladhar/Documents/GitHub/Game/they-taught-the-rain-your-name-ue/PenanceDemoUE.uproject" -run=pythonscript -script="/Users/amritladhar/Documents/GitHub/Game/they-taught-the-rain-your-name-ue/Scripts/import_penance_assets.py" -unattended -nop4 -NoSourceControl -stdout -FullStdOutLogOutput
```

Then verify imported assets:

```sh
"/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "/Users/amritladhar/Documents/GitHub/Game/they-taught-the-rain-your-name-ue/PenanceDemoUE.uproject" -run=pythonscript -script="/Users/amritladhar/Documents/GitHub/Game/they-taught-the-rain-your-name-ue/Scripts/verify_penance_assets.py" -unattended -nop4 -NoSourceControl -stdout -FullStdOutLogOutput
```

## Refresh Import

From the Godot project:

```sh
/Applications/Godot.app/Contents/MacOS/Godot --headless --path ../they-taught-the-rain-your-name --script res://scripts/blockout/export_unreal_blockout_data.gd
```

Then run the Unreal importer:

```sh
"/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "/Users/amritladhar/Documents/GitHub/Game/they-taught-the-rain-your-name-ue/PenanceDemoUE.uproject" -run=pythonscript -script="/Users/amritladhar/Documents/GitHub/Game/they-taught-the-rain-your-name-ue/Scripts/import_penance_blockout.py" -unattended -nop4
```

The imported level is:

`/Game/Maps/Penance_Suburban_Blockout`

## Verify Import

```sh
"/Users/Shared/Epic Games/UE_5.7/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor" "/Users/amritladhar/Documents/GitHub/Game/they-taught-the-rain-your-name-ue/PenanceDemoUE.uproject" -run=pythonscript -script="/Users/amritladhar/Documents/GitHub/Game/they-taught-the-rain-your-name-ue/Scripts/verify_penance_import.py" -unattended -nop4
```

The latest verification report is written to:

`Saved/PenanceImportVerify.txt`
