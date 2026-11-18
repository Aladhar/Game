# Penance V5 — independent playable world blockout

Open `PenanceDemoUE.uproject` in Unreal Engine 5.7.4, open **/Game/Maps/V5/Penance_Town_V5**, and press **Play** from the default Player Start. The project’s default map remains Penance_Persistent. No existing map, player asset, House01 interior, door source, or previous progression manager was replaced.

Use the existing player controls: WASD movement, mouse look, Left Shift sprint, Space jump, E interaction, and T shot reaction. Left Ctrl or C crouches; J opens the inventory. Walk up to the illuminated house’s west door and press E. Its existing streamed interior is reused. Leave through its front door to return to the new side yard.

The condensed opening preview follows this order:

1. Arrival / gas station → warm House01 window.
2. Enter House01: a brief stationary Penance appears in the hall. No free-roaming AI.
3. Leave through the same streaming door: the changed side-yard return and a moved car establish the memory change.
4. Follow Orchard Loop to the neighborhood checkpoint; the park shortcut opens.
5. Cross the park, creek bridge and old ridge road to the church.
6. Inside the nave, use the east stair. Reach the basement encounter point, then leave by the west stair.
7. The estate path gate opens. Follow the garden path around the west wing to the Foster House reveal.

Objectives appear at the top of the screen. This is a compressed geography/playability preview, not fourteen completed chapters. The basement Penance is a scripted animated actor following a fixed path: **no damage, sensing, resource system, or enemy AI** is attached. You may explore exterior locations, but out-of-order checkpoint visits do not advance the opening story. Restart Play to reset the preview.

Final automated result: **0 blocking check failures and 1 local driveway-grade warning**. See [the final validation summary](Final_Validation.md) for measurements and test limits.

## Saved construction

- 480 × 440 m site, east +X and north +Y; all authoring measurements convert at 100 UU per meter.
- Rolling terrain, curved incised creek, sloped banks, graded public/residential/service roads, sidewalks and drives.
- 14 different homes, each with an outbuilding and yard boundaries; civic, commercial, school, park, graveyard, fire station, gas and utility sites.
- Church nave, bell tower and spire; estate wings and portico; a water tower on high ground.
- Real walkable church basement, two service stairs and escape landing.
- Main road bridge, visibly closed older footbridge, 552 simple trees in combined meshes, retaining walls and everyday-life placeholders.
- Existing possessed BP_PenancePlayer, ABP_PenancePlayer and Untitled mesh, plus the unmodified House01 streaming implementation.
- Only new V5 classes were added: PenanceV5WorldDirector.h/.cpp. It has editable checkpoints, objectives, animation references and a scripted path. Existing progression code is untouched.

Superseded V5 geometry is disabled in **V5/99_Trash_Archive**. Incomplete build backups are outside Content in Built/WorldCheckpoints. They do not participate in gameplay.

## Deliverables

- [Interactive companion map](Penance_Town_V5_Interactive.html): zoom, pan, selectable buildings, layers, dimensions, chapter routes and sightlines.
- [Labeled masterplan](Penance_V5_Masterplan.png), generated from the same layout data as the 3D build.
- [Fourteen-chapter graph and beats](Penance_V5_Chapter_Graph.md): start, objective, required path, survival encounter, optional branches, restriction, unlock, exit and return shortcut for each chapter.
- [Implementation data](Penance_V5_Implementation.json): buildings, roads, elevations, paths, drives, checkpoints, chapter regions and review cameras.
- [Exact saved Unreal actor placements](Unreal_Actor_Placements.json): all actor transforms, classes, tags and mesh references, including actual modular wings, props and disabled archives.
- [Native validation measurements](Penance_V5_Validation.json), [preservation hashes](Preservation_Check.json), and [footprint review](Placement_Review.json).
- [File inventory](File_Inventory.json).
- Native Unreal views: [Arrival](Views/Arrival.png), [Residential](Views/Residential.png), [Park](Views/Park.png), [Main Street](Views/MainStreet.png), [Graveyard](Views/Graveyard.png), [Creek crossing](Views/CreekCrossing.png), [Church approach](Views/ChurchApproach.png), [Foster approach](Views/FosterApproach.png), [Overhead](Views/Overhead.png), [World](Views/World.png).

## V4 versus V5

V4 was a conceptual/foundation planning layout with landmark proxy masses. V5 is a separate reconstructed world: a smaller 480 × 440 m footprint, a curving creek instead of a straight divider, roads shaped by the mill crossing and hillside grades, irregular cottage and postwar districts, and recognizable building shells. Its church and Foster estate share the opposite ridge. The town’s history explains why those routes exist.

V5 adds physical yards, garages, roofs, windows, street furniture, roads, cover and a traversable basement. It reuses one proven interior rather than changing the existing streaming system. Early scripted encounters are rare; the first clear Penance sighting remains inside House01. Later chapter threats and interior production are explicitly reserved.

## Scope and remaining work

This is editable blockout geometry, not final environment art. Most ordinary houses, civic buildings and Foster House are closed exterior shells. Church offices/archive and later interiors remain expansion spaces. No claim is made that fourteen chapters, puzzles, pickups, optional documents, final ending or survival balancing are implemented.

The Foster driveway junction has a short local travel-surface grade of about 12%, above the 10% service-road target. It is reserved for a later apron-smoothing pass; the main public roads measured below 6%.

The early silhouette lasts nine seconds. The basement actor follows a fixed route with no collision/damage; animation travel speed is provisional and may slide. Full player-driven playthrough, encounter timing, controller feel, alternate routes, creek recovery, sustained performance and navigation-mesh generation still need human gameplay testing. No unrestricted enemy AI or Recast navigation build was added. Roads and wide service stairs reserve space for a 230 cm enemy; the narrow House01 door is for the player.

Use the native validation JSON to distinguish actual automated checks from these untested areas. Progression checks move the possessed pawn to checkpoints to verify order and triggers; they do not represent an uninterrupted manual walk through the entire route. The basic actual-movement and streaming checks are separate.

The existing enemy animation pass was closed before map work. Four Blender Actions, FBXs, native animation sequences and its showcase remain saved. Accessory clipping and provisional hidden-face texture mapping remain as accepted. See Built/BlenderWork/Penance_Animation_Validation.md for that pass.

## Issues corrected during implementation

The first generated ground had reversed surface orientation under the new north/east coordinate convention; this caused the player to fall through and was corrected. Thin generated meshes now also use two-sided query collision. Road/building overlaps, cemetery access, fence ends across Mill Road, raised sidewalks through intersections, the tower-road overlap, a basement landing gap, and the estate path through a wing were corrected. Superseded geometry is archived rather than destroyed. Review lighting and the church/estate cameras were corrected after inspecting native captures.

The new native director compiled successfully after correcting an Unreal header include. No existing player or progression source was changed. Unreal emitted non-blocking editor icon, audio-device and connectivity warnings on this machine; no launch-blocking project error was ignored.
