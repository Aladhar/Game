# Final native V5 validation

Result: **0 blocking check failures; 1 grading warning.**

Unreal 5.7.4 loaded the saved map in a fresh editor and entered Play-in-Editor. The new C++ module compiled successfully. No existing player Blueprint or animation asset was modified in this map pass.

Actual possessed-player movement: 210.4 cm. House01 streamed in and returned the same controlled pawn to the side yard. Out-of-order checkpoint visits were rejected. Stages 3–8 advanced, the basement actor spawned, and the preview reached its end.

59 original files passed before/after hash comparisons. The original Penance.blend also matches its original Git LFS content hash.

The route checks sampled actual PIE collision floors on the park, church approach, descent, basement escape and estate reveal. They found no missing floor or unmanageable sample-height step after correction. Road capsule samples found no blocking obstruction. These are geometry samples, not a full uninterrupted manual walkthrough.

| Road | Width (m) | Measured maximum travel-surface grade |
|---|---:|---:|
| Mill Road | 7.0 | 5.64% |
| Main Street | 7.0 | 1.54% |
| Orchard Loop | 5.6 | 3.31% |
| Briar Rise | 5.8 | 4.93% |
| Foundry Cut | 5.8 | 3.59% |
| School Lane | 5.6 | 0.94% |
| Grave Lane | 4.0 | 2.47% |
| Ridge Road | 6.5 | 5.90% |
| Estate Drive | 4.0 | 11.97% |
| Tower Service | 4.0 | 10.08% |

The estate driveway junction reaches 11.97% locally against a 10% service-road target. Its short apron should be smoothed in the next layout pass. It did not obstruct the sampled player capsule.

Door reservations: House01 135 × 230 cm, church 320 × 420 cm, service stairs 300 cm wide. The 230 cm enemy is not expected to pursue through House01. Recast/navmesh, enemy AI, packaged builds, sustained performance and a complete manual playthrough remain untested.

Ten native screenshots are saved in Views, including all eight requested eye-height locations. The interactive companion map JavaScript passed a syntax check.

Engine warnings observed: missing optional editor icons, audio-device timeouts and a connectivity probe timeout. No project launch error remained.
