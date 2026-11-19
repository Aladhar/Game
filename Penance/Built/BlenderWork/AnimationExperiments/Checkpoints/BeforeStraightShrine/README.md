# Penance enemy animation experiments — review delivery

Seven new editable 30 FPS animations, revised skinning and drape fit, eight FBX exports, seven Unreal sequences, an independent comparison map, three-view MP4s and original-versus-new comparisons. Gameplay animations are unchanged; these assets are ready for movement-style selection.

## Watch the animations

Each numbered MP4 shows front, side and three-quarter views together at native speed. The three camera views are also separate MP4 files named `AN_EXP_<clip>_<view>.mp4`. Locomotion repeats three times (Chase six times). Attacks play three times with a 0.8 second hold after their authored recovery; playback is never accelerated.

| Clip | Authored duration | Playback | Intended speed cm/s | Impact time / frame | Preview |
| --- | --- | --- | ---: | --- | --- |
| Stalk | 2.80 s | Loop, in place | 30 | - | [MP4](Previews/01_Stalk.mp4) |
| Limp | 2.40 s | Loop, in place | 34 | - | [MP4](Previews/02_Limp.mp4) |
| Heavy | 2.00 s | Loop, in place | 52 | - | [MP4](Previews/03_Heavy.mp4) |
| Chase | 1.00 s | Loop, in place | 115 | - | [MP4](Previews/04_Chase.mp4) |
| Lunge | 1.80 s | One shot, recovery | 0 | 0.60 s / Blender 19 / Unreal 18 | [MP4](Previews/05_Lunge.mp4) |
| Overhead | 2.60 s | One shot, recovery | 0 | 1.10 s / Blender 34 / Unreal 33 | [MP4](Previews/06_Overhead.mp4) |
| Sweep | 2.20 s | One shot, recovery | 0 | 0.80 s / Blender 25 / Unreal 24 | [MP4](Previews/07_Sweep.mp4) |

- [Walking comparison](Previews/Comparison_Walking.mp4): original walk, Stalk, Limp, Heavy and Chase, all at native speed and identical scale.
- [Attack comparison](Previews/Comparison_Attacks.mp4): original attack, Lunge, Overhead and Sweep start together, then hold their recovery poses.
- [Rig deformation comparison](Previews/Comparison_Rig_Deformation.mp4): the identical new overhead Action on the original mesh/weights and the refined mesh/weights. This isolates skinning and drape-fit changes from motion changes.
- Review pose sheets: `Previews/AN_EXP_<clip>_Review.jpg`.
- Native Unreal screenshots: `Previews/Unreal/`.
- Convenient MP4 copies: `/Users/amritladhar/Documents/ChatGPT/Penance/Advanced_Enemy_Animations/`.

## Motion and rig work

The original animated, repaired and final Blender sources were inspected independently. The starting animated/repaired mesh had 121,837 vertices, 155,282 triangles, 31 bones and normalized weights, but sharp chest/arm influence transitions, a low inner-thigh bridge, a rigid left/right split through connected rear-drape faces, and drape/leg contact under animation. Normalized weights did not make those deformations acceptable.

The final experimental file is `Penance_AnimationExperiments.blend`. It retains all four original Actions and adds all seven `AN_EXP_*` Actions. Every authored frame is keyed, with solved two-bone leg placement, sole-height correction, continuous gait targets, quaternion continuity, delayed secondary motion, and explicit anticipation/impact/recovery markers. Stalk contains a restrained head-look event; Limp uses unequal support periods and low weak-leg clearance; Heavy limits body bounce; Chase increases cadence, forward lean and arm momentum. Attacks use the existing arms and bell without introducing weapons or anatomy.

Skinning was refined by joint-local diffusion, pose-based strain optimization on welded anatomical vertices, and continuous cross-panel/two-segment drape weights. The solver tested alternative strengths instead of assuming more smoothing was better. Final weights differ at 72,100 vertices, remain normalized within 4.7e-08, use at most four influences, and leave root unweighted.

Only the lower hanging shrine/drape geometry was refitted, with a smooth rear flare and smaller lateral flare anchored below the upper structure. 52,531 vertices moved; the maximum rest-space adjustment is 30.41 cm. This is a deliberate visible silhouette change to provide actual limb clearance. Body, hands, feet, veil and bell rest geometry remain unchanged. Vertex/triangle order, UVs, packed textures and materials are retained. The 31 bone names, parents and reference transforms remain unchanged. Standing height is 229.99998 cm and both object scales are 1.

## Validation evidence

Blender evaluated all 451 new animation samples and all 289 original samples on the final rig. Actual body/leg-versus-lower-drape triangle intersections were checked at **every frame of every new clip**; all were zero. The four original clips were additionally checked at 17 collision poses each, also with zero intersections. This collision test targets the identified body/drape problem; it is not an exhaustive all-triangle self-collision proof.

| Clip | Frames evaluated/contact-tested | Body/drape intersections, max | Whole-mesh edge stretch, worst p99 | Worst individual edge stretch | Loop/recovery matrix error |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stalk | 85 | 0 | 1.282 | 2.105 | 0.000000 |
| Limp | 73 | 0 | 1.275 | 1.934 | 0.000000 |
| Heavy | 61 | 0 | 1.295 | 2.278 | 0.000000 |
| Chase | 31 | 0 | 1.324 | 2.724 | 0.000000 |
| Lunge | 55 | 0 | 1.358 | 1.848 | 0.000000 |
| Overhead | 79 | 0 | 1.383 | 2.390 | 0.000000 |
| Sweep | 67 | 0 | 1.352 | 1.928 | 0.000000 |

Edge ratios compare the actual deformed mesh with its final rest mesh and exclude rest edges shorter than 0.35 cm. They are diagnostics, not a claim of uniform physical strain. The extreme 24–27x drape seam stretching was removed. The remaining worst isolated ratio is under 2.73x; worst-frame whole-mesh p99 is under 1.39x. No nonfinite vertices or new open boundaries were found. Topology retains the source's coincident caps/junctions and is not presented as a newly rebuilt manifold production mesh. See `FinalMeshAudit.json` for the explicitly defined geometric-weld tolerance/counts.

Soles remain grounded to approximately 0.21 cm in the tested samples. During the flat portion of stance, intended actor-travel compensation leaves less than 0.07 cm drift per frame in every locomotion clip. Foot rolling and swing intervals are excluded from that drift statistic. Locomotion loops and attack recovery endpoints match exactly in Blender; native Unreal endpoint errors are zero within the importer tolerance. Root transforms remain stationary.

Unreal **5.7.4-51494982** imported and reloaded the final mesh and all seven clips on the original `SKEL_Penance`, with the original material and compatible Physics Asset. Native frame counts divided by duration verify 30 FPS. Full native pose evaluation covers all 451 new samples. Actual Play-in-Editor tests confirmed advancement at all seven stations, unit actor scales, stationary roots, +X facing and 230 cm bounds. `UnrealPlaybackValidation.json` contains the measured bone movements. The original four sequences are also tested on the experimental mesh in transient PIE stations; see `UnrealExistingPlaybackValidation.json`.

All 164 protected original assets still match their recorded SHA-256 hashes, including the original enemy, skeleton, sequences, Blender sources and V5/V6 map files. All three backup Blender files are byte-identical to their sources. No gameplay, AI, damage, maps or existing animation assignments were replaced.

## Unreal review

Open `Penance/PenanceDemoUE.uproject` in UE 5.7.4, then `/Game/Enemies/Penance/Experimental/L_Penance_ExperimentShowcase` and press Play. Seven experimental stations run beside three original-animation stations. Attack stations repeat for convenient review; the attack assets themselves are authored as one-shots. The mesh is `/Game/Enemies/Penance/Experimental/SK_Penance_Experimental`; the seven sequences are in `/Game/Enemies/Penance/Experimental/Animations/`.

Attack impact times are Action markers and Unreal asset metadata only. No damage event, montage integration or AI selection was added, as requested. Terrain foot IK, cloth physics and gameplay encounters remain later integration work. The retained original Physics Asset is compatible, but the refitted drape's expanded visual clearance should be considered before adopting the experimental mesh for narrow routes.

## Evaluation and recommendations

| Clip | Evaluation | Recommendation |
| --- | --- | --- |
| Stalk | Restrained upper body, deliberate support and a single head-look event. | Keep as the primary psychological-horror walk candidate. |
| Limp | Clear weak-leg drag and asymmetric support, with torso compensation. | Keep as a situational/injured variant; avoid using constantly. |
| Heavy | Longer planted support and restrained bounce convey mass. | Keep for close approaches and purposeful movement. |
| Chase | Faster cadence, stronger arms and forward posture read clearly against Stalk. | Keep for pursuit; use its authored 115 cm/s speed as the initial gameplay match. |
| Lunge | Short anticipation, abrupt reach, clear 0.60 s impact and complete recovery. | Keep as the primary quick-attack candidate. |
| Overhead | Long readable windup, coordinated torso strike and longest recovery. | Keep as the slow heavy attack; this has the largest remaining upper-body strain and deserves the closest art review if used in extreme close-ups. |
| Sweep | Broad coordinated rotation with planted feet and a distinct horizontal arc. | Keep as the wide attack candidate. |

These recommendations are for visual selection. No clip has been automatically chosen for the AI. Further terrain/contact work depends on the eventual gameplay setup, not on replacing the reviewed animation files.

## Files and reproduction

- Editable source: `Penance_AnimationExperiments.blend`.
- Untouched originals: `Backups/` (three Blender sources).
- Exports: `FBX/SK_Penance_Experimental.fbx` and seven `FBX/AN_EXP_*.fbx` files.
- Reports: `Reports/` contains source inspection, each experiment/weight trial, final mesh audit, per-frame deformation checks, native import/playback evidence, preservation hashes and video validation.
- Scripts: `Scripts/` contains the complete repeatable authoring, optimization, fitting, import, playback-test, render and encoding pipeline.
- Branch: `codex/penance-animation-experiments`.

The authoring order is `inspect_sources.py` → `author_experiments.py` → `refine_skinning.py` → `refine_shoulders.py` (the proposed anatomical shoulder field was tested and rejected) → `finalize_accessories.py` → `optimize_deformation_weights.py` → `fit_swept_clearance.py` → `repair_drape_weights.py`. Blender scripts operate on the experimental file after authoring. The numerical optimizer runs with NumPy. Do not rerun those destructive-to-experiments steps merely to view the saved assets.

For validation/rendering, run Blender with `--background Penance_AnimationExperiments.blend --python Scripts/validate_deformation.py`, then `audit_final_mesh.py`, and `render_previews.py -- videos`. The originals render from the untouched `Penance_Animated.blend` with `-- originals`. Run encoding scripts with `/usr/bin/python3` (Pillow is installed there). FFmpeg writes H.264, yuv420p, 30 FPS, fast-start MP4s.

For Unreal, run the native editor with the project and `-ExecutePythonScript=<absolute script path>`. Import with `import_unreal.py`; build the independent map once with `build_showcase.py`; fresh-reload/playback checks use `validate_unreal_playback.py` and `validate_existing_unreal.py`. The successful commands use `-unattended -nosplash -NoSound -NoSourceControl -notracethreading -notraceserver -trace=none -stdout -FullStdOutLogOutput`.
