# Straight shrine repair

The shrine is restored to its original straight architectural shape and attached as one rigid object. It follows the back through `shrine_mount`; its roof and lower frame keep the same relative positions, angles and distances throughout every animation.

The approved **Limp body/leg motion is unchanged**. Chase and attack motion redesigns remain deferred. This change fixes the shared shrine geometry and binding in every clip.

## Root-cause implementation

- Removed the previous vertex-dependent 30 cm rear flare and lateral flare. Canonical shrine geometry comes from the original `Penance_Animated.blend` source buffers.
- All **82,878 shrine vertices** now have exactly one influence: `shrine_mount = 1.0`. Ornament-chain rotations can no longer bend the architecture.
- A **single rigid mounting transform** fits the straight frame to the body: 16 degrees of pitch and 16 cm of posterior mount placement, with a rigid height adjustment retaining a 230 cm character. This is one rotation/translation of the entire shrine, not a different offset at each height. It cleared the legs without editing the approved gait or warping the frame.
- Bone names, parents, reference matrices, scale, UVs, materials and non-shrine mesh/weights are preserved. The four ornament bones remain in the 31-bone skeleton for compatibility.
- Removed the old flare operation from `refine_skinning.py`. The old clearance and drape entry points now route through rigid mounting and binding. The saved Blender mesh also marks the rigid shrine explicitly.

## Actual verification

`validate_shrine_rigidity.py` evaluated the actual skinned mesh at **all 740 samples** across all seven experimental and all four existing Actions. It removed the moving shrine mount transform and compared every shrine vertex with the canonical rigid shape. Maximum shape error was **0.00005749 cm** (numerical precision). All 11 Action pose matrices were exactly unchanged from the pre-fix version, including Limp. All seven animation FBX files and all seven Unreal sequence files remain byte-for-byte unchanged.

The full deformation validator now rejects a warped shrine rest mesh, multi-bone shrine bending and any new-clip leg/shrine intersection. Every frame of all seven new clips was contact-tested; all returned zero intersections. The four existing clips also returned zero at their 17 regression poses. Body weights/geometry, foot contact, root transforms and loop/recovery endpoints retain their previous behavior.

| Clip | Duration | Frames tested | Max rigid-shape error | Max leg/shrine triangle contacts | Attack impact | Preview |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Stalk | 2.80 s | 85 | 0.0000557 cm | 0 | - | [MP4](Previews/01_Stalk.mp4) |
| Limp | 2.40 s | 73 | 0.0000565 cm | 0 | - | [MP4](Previews/02_Limp.mp4) |
| Heavy | 2.00 s | 61 | 0.0000563 cm | 0 | - | [MP4](Previews/03_Heavy.mp4) |
| Chase | 1.00 s | 31 | 0.0000552 cm | 0 | - | [MP4](Previews/04_Chase.mp4) |
| Lunge | 1.80 s | 55 | 0.0000420 cm | 0 | 0.60 s | [MP4](Previews/05_Lunge.mp4) |
| Overhead | 2.60 s | 79 | 0.0000435 cm | 0 | 1.10 s | [MP4](Previews/06_Overhead.mp4) |
| Sweep | 2.20 s | 67 | 0.0000426 cm | 0 | 0.80 s | [MP4](Previews/07_Sweep.mp4) |

Unreal **5.7.4-51494982+++UE5+Release-5.7** reimported only `/Game/Enemies/Penance/Experimental/SK_Penance_Experimental`, on the existing `SKEL_Penance`. Standing height is 229.999999 cm. A fresh editor session played all seven sequences in PIE at native 30 FPS, with unit actor scale and stationary roots. Screenshots are in `Previews/Unreal`; native measurements are in `StraightShrineUnrealPlayback.json`.

All 164 protected original project assets still match their SHA-256 hashes, including V5/V6 maps and original enemy assets. Gameplay animation assignments remain unchanged. The original Physics Asset remains assigned and compatible; this pass verifies animation and visual-mesh clearances, not ragdoll or route collision behavior.

## Watch and compare

- [Limp — approved motion, straight shrine](Previews/02_Limp.mp4)
- [Same Limp motion before/after the shrine fix](Previews/Shrine_Fix_Before_After.mp4)
- Seven numbered MP4s show front, side and three-quarter together. The 21 individual-angle MP4s are named `AN_EXP_<clip>_<view>.mp4`. All play at authored 30 FPS.
- Motion comparisons: [walking](Previews/Comparison_Walking.mp4), [attacks](Previews/Comparison_Attacks.mp4), [same overhead Action on original/refined rigs](Previews/Comparison_Rig_Deformation.mp4).
- Freshly named delivery copies: `/Users/amritladhar/Documents/ChatGPT/Penance/Advanced_Enemy_Animations/Straight_Shrine/`.

## Saved assets

- Editable rig and all 11 Actions: `Penance_AnimationExperiments.blend`.
- Updated mesh FBX: `FBX/SK_Penance_Experimental.fbx`.
- Unchanged animation FBX files: `FBX/AN_EXP_*.fbx`.
- Updated Unreal mesh: `/Game/Enemies/Penance/Experimental/SK_Penance_Experimental`.
- Unchanged sequences: `/Game/Enemies/Penance/Experimental/Animations/AN_EXP_*`.
- Showcase: `/Game/Enemies/Penance/Experimental/L_Penance_ExperimentShowcase`.
- Pre-fix bent Blender/FBX/Unreal mesh, videos and reports: `Checkpoints/BeforeStraightShrine/`.
- Original Blender backups: `Backups/`.
- Historical root-cause analysis: `Diagnostics/ShrineDeformation/Root_Cause_Report.md`.

## Reproduction and regression protection

Run `fit_rigid_shrine_mount.py` then `repair_shrine_rigidity.py` on the experimental Blender scene. The fit considers only whole-frame rigid placements and sorts candidates by upper-shrine placement change. `repair_shrine_rigidity.py` restores canonical source coordinates before applying that placement, so repeated repairs cannot accumulate a flare.

Before rendering, run `validate_shrine_rigidity.py`, `validate_deformation.py`, `audit_final_mesh.py` and `verify_straight_shrine_framing.py`. The first two now enforce shrine rigidity as an independent requirement. `render_previews.py` invalidates old frame caches when the Blender source or cameras change; encoding also invalidates stale MP4s. This prevents a corrected rig being delivered with old bent-frame previews.

`import_straight_shrine_unreal.py` imports the mesh without reimporting or changing animations. `validate_straight_shrine_unreal.py` performs the fresh-reload PIE check. Native commands use UE 5.7.4 with `-unattended -nosplash -NoSound -NoSourceControl -notracethreading -notraceserver -trace=none -stdout -FullStdOutLogOutput`.

Older reports describing a drape flare or flexible shrine weights are historical and superseded by this repair. The prior delivery report is preserved in the pre-fix checkpoint.
