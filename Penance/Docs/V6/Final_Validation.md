# V6 validation — 18 November 2026

## Passed

- Unreal Engine **5.7.4** editor target compiled successfully, including the new HISM container. Existing player, animation and objective Blueprints compiled without reported compiler errors.
- Final saved level reload completed. Unreal map checks reported **0 errors / 0 warnings**. The final PIE physics report has an empty issue list.
- **1,292 road-center floor/capsule probes** cover all ten roads, including the 7 m bridge, graded Estate Drive and revised Tower Service. Additional dense probes cover House01 approach, park shortcut, bridge approach, church threshold, east descent, west escape and estate path.
- All 35 canonical main-site footprints clear other buildings and asphalt. Twenty are houses. Property polygons were clipped to roads and separated along shared boundaries; the host preflight reports no improper property overlaps. Eighteen detached garages were retained; three centers were adjusted into their owner's parcel.
- All **510 original building-component scales** match the baseline scale records. Original width/depth/roof-height entries match V5; no uniform town scaling occurred. Commercial roof treatments retain original peak heights.
- Hash checks cover **307 protected existing files**: maps, V5 assets, player/enemy assets, existing gameplay source and V5 generation scripts. None changed or disappeared. The V5 map hash is recorded in `Preservation_Validation.json`.
- Native PIE possession is `/Game/Player/BP_PenancePlayer.BP_PenancePlayer_C`, using `Untitled` and `ABP_PenancePlayer`.
- The actual possessed pawn continuously traversed the complete condensed opening using normal `AddMovementInput`, with collision active. There were **no checkpoint teleports**. House01 alone used its original streaming portal.
- Observed director stages: **0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8**. House01 streamed in/out, the interior silhouette appeared, the changed side-yard return worked, the park shortcut opened, the bridge and church descent were crossed, the basement encounter spawned, the west staircase was climbed, the estate gate opened and the final estate reveal checkpoint completed.
- The final restart then rechecked saved geometry and captured updated views, after the last side-road, parcel and arrival-apron changes. The earlier continuous opening walk and this final reload are separate reports, rather than a claim that every file revision received another full walkthrough.
- Foliage canopy, trunk and pine assets each have **three LODs**. HISM material-usage flags are saved. The shared engine primitives were not modified.
- Actual Unreal captures are saved for arrival, Orchard, Briar, Main Street, park, bridge, church, estate, full overhead and the possessed-player objective HUD. The overhead review camera was lowered to 180 m and foliage culling was bypassed only for the capture. This final camera-only change does not alter traversal geometry.

## Corrections made during validation

1. North bridge-bank terrain penetrated the deck: cut the terrain below the deck across both abutments.
2. Tower Service folded near a lower portion of itself, producing a height conflict: moved its final approach and water-tower platform to `(54, 192)` m, keeping the tower's dimensions and a continuous graded road.
3. A Foundry sidewalk crossed the relocated Grave Lane junction: regenerated the sidewalk with a wider junction cut.
4. The park path stood above surrounding ground: graded the lawn and path connections so the player can enter without jumping.
5. Church floor/stair joints had narrow gaps: added V6-only joint pieces while preserving both original flights.
6. Estate garden routing clipped the west wing and hedge: moved the approach south of them and shortened the hedge front.
7. Initial captures were too dark: restored readable directional/sky fill while keeping explicit sun priority and movable lighting.
8. Foliage materials needed instancing usage flags and actual LODs: saved the flags and generated LODs in the full editor.
9. Some commandlet APIs do not provide runtime physics or the Static Mesh Editor subsystem. Physics probes and LOD generation were moved into the full editor. This was an automation limitation, not a shipped game failure.

## Not verified / limitations

- **A complete human keyboard-and-mouse playthrough has not been performed.** The continuous traversal was automated on the real possessed pawn. Desktop automation observed the viewport and HUD but returned `noWindowsAvailable` when trying to send keys. A recorded position delta alone is not treated as proof of keyboard delivery. Manual testing is still needed; see the README's exact launch steps.
- This is a **procedural layout and exterior pass**, not a final art pass. Buildings, trees, vehicles and street furniture use simplified generated forms. Brick/siding materials and architectural details establish the regional direction; final modeled storefronts, convincing foliage, weathering, erosion at the washout and finer terrain blending remain art work.
- Some property fences and decorative props are intentionally visual-only. Forest instances do not provide individual tree collision; ground, roads, walls, bridge and gameplay barriers provide the tested collision.
- Existing player visual offsets and temporary crouch/jump/directional animation fallbacks were not retuned. Player animations and shoulder deformation were outside this map pass.
- Shot, crouch, sprint, jumping, inventory, AFK and objective-toggle bindings were preserved; this map pass did not individually repeat their earlier animation tests through physical keyboard input.
- The gas search remains optional and independently accessible. The continuous mandatory-route test did not assert every optional interaction.
- The player capsule was used for traversal probes. The documented 135 × 230 cm House01 opening, 320 × 420 cm church opening and 300 cm stair widths remain reserved/preserved. No unrestricted Penance pursuit or enemy-navigation test is claimed. House01 is not an enemy chase route.
- Later chapters, puzzles and expanded interiors remain reserved. Only House01 and the existing church spaces are functional interiors in this pass; the estate is not secretly a finished mansion interior.
- On a first load Unreal may generate mesh distance fields/cards and shaders. Those progress messages are not a Lightmass build failure. Allow compilation to finish before judging frame rate.

## Manual check

Open `/Game/Maps/V6/Penance_Town_V6`, choose **Selected Viewport / Default Player Start**, press Play and click the viewport. Use WASD/mouse, Shift to sprint, Ctrl/C to crouch, Space to jump, E at House01, J for inventory, T for shot reaction and O for objectives. Follow the README's opening route. No manual asset-creation step is required to play the saved level.
