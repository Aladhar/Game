# Penance V6 — playable compact town

Open `PenanceDemoUE.uproject` with Unreal Engine **5.7.4**. The Editor Startup Map is now `/Game/Maps/V6/Penance_Town_V6`. If another map is open, open that level explicitly. Choose **Play → Selected Viewport**, with **Spawn Player At → Default Player Start**. Click the viewport to capture the mouse. Stop with Escape.

V6 is a separate, playable level derived from V5. The original maps, player assets, enemy assets and existing gameplay source were preserved. The packaged game default map remains `Penance_Persistent`; this pass changes the editor startup level only.

## What is saved

| | V5 | V6 |
|---|---:|---:|
| Town bounds | 480 × 440 m | 400 × 350 m |
| Land area | 211,200 m² | 140,000 m² |
| Main sites | 29 | 35 |
| Houses | 14 | 20 |
| Named roads | 10 | 10 |

Land area falls **33.7%**. Every original building retains its canonical width, depth and roof height; copied building parts retain their original scale. Buildings were repositioned individually. Commercial gables were replaced **in V6 only** by parapets at the original peak heights. Church nave, basement, both staircases and estate wings were moved as intact groups.

- Rebuilt graded terrain, creek, 7 m × 37 m road bridge and closed old footbridge.
- Compact Orchard Loop and Briar Rise; six different house footprints, porches, a hip roof and dormers. Individual non-overlapping parcels, fences, mailboxes and detached garages.
- Brick commercial frontage, parapets, storefront glazing, signs and rear service alley; consistent brick/siding palette for civic and residential buildings.
- Arrival washout, barricade, guardrails, drainage, welcome sign, utilities and overhead wires. Gas canopy, pumps, parking, bins and stranded car. Bus shelter, bench, schedule, suitcase and bicycle.
- Clustered tree forms and shrubs using six HISM components, three foliage LODs and 180–320 m distance culling.
- Readable blue-hour dynamic lighting. One directional light has priority 2 and atmosphere-sun status; fills have priority 0. Static baking is disabled only in this level.
- Existing House01 portal, objectives, changed car, shortcut barrier, enemy sightings, church encounter and estate gate use relocated V6 properties. The original `V5_*` gameplay tags are intentionally retained because the shared director already uses them.
- Future shop, civic, church and estate interior volumes are documented reservations, not finished rooms or later chapters.

The only new native class is `PenanceV6InstancedSet`: a persistent HISM container with no ticking, AI or gameplay logic. Existing gameplay classes and Blueprints were not rewritten.

## Controls

| Input | Existing action |
|---|---|
| WASD / mouse | Move / look |
| Left Shift held | Sprint |
| Space | Jump |
| Left Ctrl or C held | Crouch |
| E | Interact; enter/leave House01 |
| J | Inventory |
| T | Shot reaction |
| O | Expand/collapse objectives |
| 30 seconds without activity | Scared animation |

These reuse the existing Enhanced Input setup and possessed `BP_PenancePlayer`, `Untitled` mesh and `ABP_PenancePlayer`. This map pass does not change player animation quality or previously documented temporary player poses.

## Opening route

Arrival → gas station → bus shelter → illuminated House01. Use E at its west-facing front door; enter, then leave through the existing interior exit. The return is the side yard. Follow Orchard Loop to its north-west bend, then the opened park shortcut. Cross the park and creek bridge, follow Ridge Road to the church, descend the east service stair, then escape up the west stair. The estate gate opens; follow the garden path around the west wing to the Foster forecourt.

The main director owns mandatory progression. The gas search is optional. The fourteen-chapter graph retains its order; only the condensed opening is playable. Later puzzles, enemy AI, damage, unrestricted pursuit and narrative conclusions are **not implemented**.

## Evidence and editable data

The plan follows the native Unreal overhead display: **+X left, +Y up**. Inspector values remain the actual world coordinates. The overhead capture temporarily disables foliage distance culling in PIE to show the entire woodland; saved gameplay culling remains 180–320 m.

- [Interactive plan](Penance_Town_V6_Interactive.html): wheel zoom, drag pan, click buildings for dimensions.
- [Implementation coordinates](Penance_V6_Implementation.json) and [actual Unreal actor placements](Unreal_Actor_Placements.json).
- [Parcel boundaries](Parcels.json) and [garage adjustments](Garage_Adjustments.json).
- [Original-part scale proof](Original_Building_Scale_Proof.json) and [preservation hashes](Preservation_Validation.json).
- [Saved-world physics validation](Penance_V6_Saved_Validation.json), [continuous PIE walkthrough](Penance_V6_Gameplay_Validation.json) and [final restart check](Penance_V6_Final_Reload.json).
- [Future interior reservations](Future_Interior_Reservations.json), [foliage LODs](Foliage_LODs.json), and [file manifest](File_Manifest.json).
- `Views/`: native Unreal player-height arrival, Orchard, Briar, Main Street, park, bridge, church and Foster captures; full overhead and possessed-player HUD capture.
- [Validation and limitations](Final_Validation.md).

## Construction and validation

Authoritative design: `Scripts/Penance_Town_V6_Design.py`. Host preparation/presentation scripts require Shapely and Pillow. Unreal construction uses Geometry Scripting to save ordinary Static Mesh assets; that plugin is not needed to play the generated level.

Construction stages are retained for review: `Build_Penance_Town_V6.py`, `Refine_Penance_V6_Access.py`, `Finish_Penance_V6.py`, `Finalize_Penance_V6_Parcels.py`. Do not regenerate over a completed level; use a separate reviewed repair script for further changes. `Complete_Penance_V6_Foliage.py` runs in the full editor because the Static Mesh Editor subsystem is unavailable to commandlets.

`Verify_Penance_V6_Play.py` opens the saved map in a fresh full editor and drives the actual possessed pawn continuously with `AddMovementInput`; it does not teleport between checkpoints. House01 uses its original streaming portal. The separate saved-world probe file must run **inside PIE**, since editor-only commandlet worlds do not provide authoritative runtime collision. The report explicitly distinguishes this automated walk from a human manual playthrough.

Local baseline backup: `Built/Checkpoints/BeforeV6/Penance_Town_V5.umap`. Original baseline commit: `123f54f962d60e8cad99e9b429ee12f01edf9639`. The intervening `cf28c9e` V6map and `86fe272` Run commits are preserved; subsequent fixes are a follow-up on the same branch.
