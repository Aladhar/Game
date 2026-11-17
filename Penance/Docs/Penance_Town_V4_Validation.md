# Penance V4 town blockout

## Open the level

Open the Penance Unreal project in UE 5.7.4. In the Content Browser, open `/Game/Maps/Planning/Penance_Town_Masterplan_V4_Blockout` and choose **Play**. The level inherits the project's existing GameMode and spawns the current player at the south entrance. The map uses conventional level storage without World Partition or streaming.

The source HTML positions are stored in `Scripts/Penance_Town_V4_Layout.json`, with the source digests and original map digests. The grading and layout additions live in `Scripts/Penance_Town_V4_Design.py`. All source positions use meters with Y increasing south. The builder converts to `(X × 100, (600 − Y) × 100, Z × 100)` in Unreal centimeters. Rectangles use their centers before conversion. H01's parcel center is `(5250, 15800)` UU, and the main bridge spans the source crossing at X = 26,500 UU.

## Saved content

The map contains 16 editable terrain mesh tiles, 15 named source route surfaces, public sidewalks, separate access paths, and 34 parcel boundaries. It has 14 residential lots, 34 building pads including the sheriff annex and caretaker shed, and 28 outbuilding reserves including the caretaker shed. The build places 300 actors in the 13 requested Outliner folders. The main bridge has a 700 UU deck, physical edge barriers and abutments. The old footbridge is a blocked reserve with approaches on both banks.

Terrain and road strips are saved as Static Mesh assets, with per-triangle collision where needed. The terrain comes from a common 2 m grid, so adjacent tiles meet and road surfaces follow the same grade model. Pedestrian markings and lot outlines use the solid ground underneath. The Geometry Scripting editor plugin is needed for the build script. Opening and playing the saved level uses standard Unreal assets.

## Differences from the V4 references

- Orchard Loop's west leg moved from source X = 44 m to X = 24 m. At the source location it crossed H03's foundation and workshop. H03's dimensions and center were retained.
- The shop service alley moved from the Market Street centerline to Y = 402 m, with returns to Market Street at both ends. This gives the shops distinct rear access.
- The tower track received a short link to the northern switchback and a spur to the tower pad. The estate service road was extended toward Foster House. The Utility Station spur routes around the maintenance pad and runs to the utility apron. The pump spur ends outside the pump house pad and uses a short path to the pad.
- The park footbridge approach jogs east of the schoolhouse pad. Its south and north sections stop at separate bank barriers.
- The brief adds driveways, civic and estate walkways, cemetery gate and terraces, and outbuilding reserves where the HTML used a single outbuilding symbol. The west residential road adjustment, grading, and these local access links carry the design into playable geometry. The primary parcel boundaries and pad dimensions come from the references.
- The intended public road is split at the creek so the actual bridge deck supplies collision across the channel. The original northern approach centerline, including its portion over the bridge apron, is 321.46 m.

## Limits of the blockout

Buildings remain labeled slabs. The tower, bell tower and Foster House have temporary height proxies for view checks. The trees, fence and wall sections are prototype boundaries. Screening traces measure direct visibility to proxy tops at standing eye height. Intermediate foliage coverage, fog and final building silhouettes need a later visual review. The road hierarchy, land cut and fill, and first pass grading are part of the saved map. There are no new interiors, doors, entry triggers or story systems.

## Reproduce and verify

Run `Build_Penance_Town_V4_Blockout.py` as an Unreal PythonScript commandlet with `-EnablePlugins=GeometryScripting` in a project copy with a clean output folder. The builder refuses to overwrite an existing V4 map. Run `Verify_Penance_Town_V4.py` with `-ExecutePythonScript` in the editor. It opens the saved map, enters PIE for live collision traces, and writes JSON to `Saved/Penance_V4_Verification.json`. Set `PENANCE_V4_REPORT` to change the output path.

## Validation results

Fresh UE 5.7.4 processes reopened the saved level and started PIE with the existing `BP_PenancePlayer`. Validation was scripted and used live collision queries and injected movement input.

| Check | Result |
|---|---|
| Saved terrain bounds | 48,000 × 60,000 UU, matching the source extent |
| Road and path collision | 1,658 centerline samples across 15 routes. Cross-section traces confirmed the 700, 600 and 400 UU road widths. |
| Peak road grades sampled along centerlines | Main Street 5.23%, northern switchback 4.52%, Briar Lane 2.48%, water tower service track 8.35% |
| Terrain elevations | Civic datum 0 UU, graveyard +300, Briar Lane near end +595, Foster +1,000, church +1,200, tower +2,000, creek bed −400 |
| Pads against terrain | Sampled tops 15.4–16.7 UU above underlying ground. No road or residential lot overlap in the validation checks. |
| Main bridge | 700 UU wide, solid collision and side barriers. PIE traversed 35.99 m from the south approach to beyond the north end. |
| PIE route samples | Spawn, Main Street, civic center, H01 lot approach, Briar Lane, bridge, church access, Foster access and water tower road. The pawn remained grounded at each sampled route's end. |
| Landmark traces | 16 standing eye-height traces. All eight explicit clear or blocked targets matched the design. Partial views are recorded as simple proxy-top traces. |
| Existing maps | Persistent, V7 neighborhood and House01 Interior SHA-256 hashes match the pre-build files. Gameplay and default map configuration files are untouched. |

The route checks moved the possessed character near the selected test sections between walks. They establish local traversal and a full bridge crossing. A continuous playthrough of every street and final authored environments remains a separate review. The utility and tower service routes are open for review.

The review gallery contains 12 Unreal captures. The top and road-only views use the orthographic scene capture in Base Color mode, with north at the top and east to the left in the Unreal camera. The other views are PIE viewport screenshots.
