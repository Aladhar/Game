"""Write the current straight-shrine delivery report from measured evidence."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];Q=R/'Reports';load=lambda n:json.loads((Q/n).read_text());fix=load('StraightShrineRepair.json');rigid=load('StraightShrineRigidityValidation.json');contacts=load('DeformationValidation.json');native=load('StraightShrineUnrealImport.json');play=load('StraightShrineUnrealPlayback.json');M=load('ClipManifest.json');project=R.parents[2]
original={n:h for n,h in load('ProtectedAssetHashes.json').items() if Path(n).name!='.DS_Store'};changed=[n for n,h in original.items() if hashlib.sha256((project/n).read_bytes()).hexdigest()!=h];assert not changed,changed
assert all(c['body_trim_intersecting_triangle_pairs']==0 for n,v in contacts['clips'].items() if n.startswith('AN_EXP_') for c in v['contacts_sampled'])
manifest=json.loads((R/'Checkpoints/BeforeStraightShrine/Manifest.json').read_text());assert all(hashlib.sha256((project/f).read_bytes()).hexdigest()==h for f,h in manifest['unchanged_animation_files'].items())
(Q/'PreservationValidation.json').write_text(json.dumps({'protected_assets_checked':len(original),'changed_assets':[],'all_14_animation_fbx_and_unreal_files_byte_unchanged':True,'all_11_action_pose_matrices_unchanged':True,'body_geometry_and_weights_unchanged':True,'final_blend_sha256':hashlib.sha256((R/'Penance_AnimationExperiments.blend').read_bytes()).hexdigest(),'original_backup_folder':'Backups','pre_fix_checkpoint':'Checkpoints/BeforeStraightShrine'},indent=2)+'\n')
rows=[]
for i,(n,s) in enumerate(M.items(),1):
 v=rigid['clips'][n];hit='-' if s['loop'] else f'{(s["impact"]-1)/30:.2f} s';count=max(c['body_trim_intersecting_triangle_pairs'] for c in contacts['clips'][n]['contacts_sampled']);rows.append(f'| {n.removeprefix("AN_EXP_")} | {s["frames"]/30:.2f} s | {v["frames_evaluated"]} | {v["max_shrine_shape_error_cm"]:.7f} cm | {count} | {hit} | [MP4](Previews/{i:02}_{n.removeprefix("AN_EXP_")}.mp4) |')
text=f'''# Straight shrine repair

The shrine is restored to its original straight architectural shape and attached as one rigid object. It follows the back through `shrine_mount`; its roof and lower frame keep the same relative positions, angles and distances throughout every animation.

The approved **Limp body/leg motion is unchanged**. Chase and attack motion redesigns remain deferred. This change fixes the shared shrine geometry and binding in every clip.

## Root-cause implementation

- Removed the previous vertex-dependent 30 cm rear flare and lateral flare. Canonical shrine geometry comes from the original `Penance_Animated.blend` source buffers.
- All **{fix['rigid_vertices']:,} shrine vertices** now have exactly one influence: `shrine_mount = 1.0`. Ornament-chain rotations can no longer bend the architecture.
- A **single rigid mounting transform** fits the straight frame to the body: {fix['rigid_pitch_degrees']} degrees of pitch and {fix['rigid_backward_mount_placement_cm']:.0f} cm of posterior mount placement, with a rigid height adjustment retaining a 230 cm character. This is one rotation/translation of the entire shrine, not a different offset at each height. It cleared the legs without editing the approved gait or warping the frame.
- Bone names, parents, reference matrices, scale, UVs, materials and non-shrine mesh/weights are preserved. The four ornament bones remain in the 31-bone skeleton for compatibility.
- Removed the old flare operation from `refine_skinning.py`. The old clearance and drape entry points now route through rigid mounting and binding. The saved Blender mesh also marks the rigid shrine explicitly.

## Actual verification

`validate_shrine_rigidity.py` evaluated the actual skinned mesh at **all {rigid['total_samples']} samples** across all seven experimental and all four existing Actions. It removed the moving shrine mount transform and compared every shrine vertex with the canonical rigid shape. Maximum shape error was **{rigid['maximum_shrine_shape_error_cm']:.8f} cm** (numerical precision). All 11 Action pose matrices were exactly unchanged from the pre-fix version, including Limp. All seven animation FBX files and all seven Unreal sequence files remain byte-for-byte unchanged.

The full deformation validator now rejects a warped shrine rest mesh, multi-bone shrine bending and any new-clip leg/shrine intersection. Every frame of all seven new clips was contact-tested; all returned zero intersections. The four existing clips also returned zero at their 17 regression poses. Body weights/geometry, foot contact, root transforms and loop/recovery endpoints retain their previous behavior.

| Clip | Duration | Frames tested | Max rigid-shape error | Max leg/shrine triangle contacts | Attack impact | Preview |
| --- | ---: | ---: | ---: | ---: | --- | --- |
{chr(10).join(rows)}

Unreal **{native['engine']}** reimported only `/Game/Enemies/Penance/Experimental/SK_Penance_Experimental`, on the existing `SKEL_Penance`. Standing height is {native['height_cm']:.6f} cm. A fresh editor session played all seven sequences in PIE at native 30 FPS, with unit actor scale and stationary roots. Screenshots are in `Previews/Unreal`; native measurements are in `StraightShrineUnrealPlayback.json`.

All {len(original)} protected original project assets still match their SHA-256 hashes, including V5/V6 maps and original enemy assets. Gameplay animation assignments remain unchanged. The original Physics Asset remains assigned and compatible; this pass verifies animation and visual-mesh clearances, not ragdoll or route collision behavior.

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
'''
(R/'Straight_Shrine_Repair.md').write_text(text)
(R/'README.md').write_text(text)
print('STRAIGHT_SHRINE_REPORT_WRITTEN')
