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
- Godot UI, stamina/crouch controller, AudioManager, rain particle controller, and one-shot event code.
- Final detailed Penance assets beyond whatever is represented in the current blockout primitives.

Those systems should be rebuilt natively in Unreal after the blockout arrives.

## Windows UE 5.6 Rebuild

This checkout is configured for the installed Windows engine at:

`C:\Program Files\Epic Games\UE_5.6`

To rebuild the Unreal content from the exported JSON, verify the imported level, and package a Win64 development build:

```powershell
.\Scripts\Build_Unreal_Windows.ps1
```

The packaged build is written to:

`Builds\Win64`

To open the project in Unreal Editor after the import has been rebuilt:

```powershell
.\Scripts\Open_Unreal_Editor.ps1
```

The imported level is:

`/Game/Maps/Penance_Suburban_Blockout`

## Refresh Import From Godot

From the Godot project:

```sh
/Applications/Godot.app/Contents/MacOS/Godot --headless --path ../they-taught-the-rain-your-name --script res://scripts/blockout/export_unreal_blockout_data.gd
```

Then run the Unreal importer:

```powershell
.\Scripts\Build_Unreal_Windows.ps1 -SkipPackage
```

The imported level is:

`/Game/Maps/Penance_Suburban_Blockout`

## Verify Import

```powershell
& "C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" `
  ".\PenanceDemoUE.uproject" `
  -run=pythonscript `
  -script=".\Scripts\verify_penance_import.py" `
  -unattended -nop4 -NullRHI -NoSplash -DDC-ForceMemoryCache
```

The latest verification report is written to:

`Saved/PenanceImportVerify.txt`
