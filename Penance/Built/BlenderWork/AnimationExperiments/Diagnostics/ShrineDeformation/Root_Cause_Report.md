# Shrine deformation root cause — historical diagnosis

This records the bent version before the straight-shrine repair. See [the implemented fix](../../Straight_Shrine_Repair.md) for the current asset and validation.

The lower rear shrine was treated as flexible drape instead of preserving the rigid architectural frame. Two independent effects combine: a permanent rest-mesh flare introduced during the experimental collision-clearance pass, plus ornament-chain animation acting on the lower architectural surface. The upper roof remains rigid.

## 1. Permanent rest-geometry change

`Scripts/refine_skinning.py:50` moved every `part == 1` vertex below Z142 cm backward by a smooth falloff, up to 12 cm, and sideways by up to 5 cm. `Scripts/fit_swept_clearance.py:16` used the same broad region and `:39` applied another 18 cm rear displacement, selected by intersection count. Together these moved 52,531 of the 82,878 shrine-region vertices, with a maximum 30 cm backward / 30.41 cm total offset. This creates the S-shaped back profile even with **all animation transforms reset**. The bend fades between Z80 and Z142 cm; geometry above Z142 cm was not moved.

This is a regression introduced by the previous experiment pass. The collision objective accepted bending the architectural frame to eliminate leg contact. Zero contact did not establish preservation of the intended shrine shape.

[Original versus current neutral geometry](Rest_Shape_Comparison.png)

## 2. Animated lower frame follows flexible ornament chains

Current shrine-region influences are `shrine_mount`, `ornament_01_l/r`, and `ornament_02_l/r`. `Scripts/repair_drape_weights.py:7` uses the entire `part == 1` region and a height-based attachment transition over Z112–162 cm. The lower-segment transition is Z69–97 cm. This does not distinguish hard architectural ribs/columns from genuinely hanging trim. The smoothing repaired tearing at the left/right split, but did not restore architectural rigidity.

`Scripts/author_experiments.py:111` drives primary ornament pitch near 10 degrees for Stalk/Limp/Heavy and 17 degrees for Chase, with oscillation and lateral spread. `:148` uses 8–25 degrees for all three attacks, plus delayed lower-chain counterrotation. These bones therefore bend/swing the lower shrine relative to its roof. Ordinary torso lean makes the silhouette more obvious, but is not the intrinsic cause: the measurements below remove the full moving `shrine_mount` transform.

This dynamic issue also reproduces using the older source geometry and older source weights under the same new motions. Source versus current peak dynamic displacements are approximately 39.8 versus 40.7 cm for Chase, and 51.6 versus 51.2 cm for attacks. Therefore the last smoothing pass is **not the sole cause**, and reverting only those weights would not solve it. The inherited lower-shrine ownership plus the authored chain motion must be corrected together.

## 3. Controlled evidence

All tests are transient. No Blender source, FBX, Unreal asset, animation keyframe, or delivered MP4 was changed.

- Neutral original geometry versus neutral current geometry proves the permanent flare exists before animation/export.
- Chase frame 9 with original geometry restored, current weights retained: the permanent flare disappears, but chain-driven bending remains.
- Chase frame 9 with ornament transforms neutralized relative to the mount, current geometry retained: dynamic bending disappears, but the permanent S-shaped flare remains.
- Original geometry plus a rigid shrine attachment: the rigid profile returns. This is a diagnostic control, **not a production repair**; it can intersect limbs because hard frame and actual hanging trim still need separate ownership/clearance handling.
- Removing relative ornament transforms reduces dynamic shrine-space deformation to numerical noise (under 0.000001 cm). The upper shrine's dynamic deviation is under 0.00002 cm across all clips.
- The CPU deformation model matched actual Blender evaluation within 0.000048 cm before rendering controls.

[Four-way control comparison](Cause_Controls.png)

## 4. All seven experimental animations

All seven share the same permanent 30 cm backward rest-shape modification. The following is the **additional maximum vertex displacement relative to the moving shrine mount**, compared with the current rest mesh. Every shrine vertex and all 451 authored samples were evaluated. These values exclude whole-body translation/rotation; they are neither actor travel nor edge stretch. Static and dynamic maxima should not be added as scalars.

| Clip | Additional pose-induced shrine displacement | Peak Blender frame |
| --- | ---: | ---: |
| Stalk | 26.0 cm | 30 |
| Limp | 26.0 cm | 26 |
| Heavy | 26.0 cm | 21 |
| Chase | 40.7 cm | 11 |
| Lunge | 51.2 cm | 22 |
| Overhead | 51.2 cm | 37 |
| Sweep | 51.2 cm | 28 |

Stalk, Limp and Heavy use almost identical secondary-chain motion, so their dynamic issue is the same despite different gaits. Chase uses a larger primary tilt, amplifying it. All three attacks share the same 8–25 degree secondary envelope, hence almost identical peak deformation magnitudes. Their torso/arm motions differ and remain separate artistic issues.

The Limp gait can be kept exactly as approved. It is affected by the shared shrine mesh/rig problem even though its body/leg motion is preferred.

[All seven side-view comparisons](All_Animations_Comparison.png)

## 5. Existing animations on the experimental mesh

These inherit the same rest-shape problem **when played on the experimental mesh**. Their original saved assets remain untouched.

| Existing clip | Additional pose-induced shrine displacement |
| --- | ---: |
| Idle | 7.6 cm |
| StalkWalk | 27.5 cm |
| Chase | 37.8 cm |
| Attack | 32.5 cm |

## 6. Correct repair direction, for a later change

1. Restore the original rigid shrine's rest shape instead of retaining the 30 cm flare.
2. Identify hard architectural frame/roof/columns independently from truly hanging cloth, chains, bells and trim. The existing broad part ID and height-only rules are insufficient.
3. Give the rigid frame one rigid mount transform; reserve secondary chains for genuinely flexible/hanging pieces.
4. Recheck leg clearance with the original rigid silhouette. Resolve actual mount placement or appropriate part articulation without bending architectural members or changing the approved Limp gait to hide the problem.
5. Validate rigid-frame point distances/shape under every clip, separately from cloth contact and skin-weight normalization. The prior checks omitted this necessary rigidity constraint.

No chase/attack redesign or rig repair was applied in this diagnostic pass. `RootCauseMetrics.json`, `ActionEvaluation.json`, `DiagnosticRenderVerification.json`, and the scripts preserve reproducible evidence.
