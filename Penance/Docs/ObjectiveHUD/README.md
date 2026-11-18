# Penance objective tracker and playable-character setup

Open PenanceDemoUE.uproject in Unreal Engine 5.7.4 and press **Play**. The editor now opens **/Game/Maps/V5/Penance_Town_V5**. Play is configured for Selected Viewport, the default Player Start, and automatic mouse capture. BP_PenancePlayer is the spawned/possessed pawn; the camera targets that pawn. Both V5 and the original Penance_Persistent use the existing PenanceDemoGameMode. The packaged-game default map remains Penance_Persistent.

## Implemented

- **/Game/UI/WBP_ObjectiveTracker**, an actual compiled UMG Widget Blueprint, with an editable Canvas → WidthBox → TrackerPanel → ObjectiveRows designer hierarchy.
- Compact, top-right layout with 48 logical units of right margin and 40 of top margin, DPI scaling, left-aligned text and 7% charcoal tint. BackgroundOpacity and TrackerWidth are editable in the widget’s Class Defaults, along with the text colors.
- Off-white main objective, gray indented sub-objectives, dimmer optional objectives, a thin separator, hollow circles, checkmarks, chevrons, and a subtle one-pixel readability shadow. No border, solid card, notification sounds or mouse interception.
- Event-driven main/sub/optional objective updates, immediate removal, availability filtering, chapter associations 1–14, completion flags, and a three-second completed-item display. Updates fade in over 0.25 seconds; there is no objective polling or per-frame Blueprint logic in the widget.
- **O** collapses/expands the detail list using its own Enhanced Input action/context. Existing player controls and mappings remain unchanged.
- Tracker hiding during the existing V5 Penance appearances, with restoration when they end. Multiple simultaneous suppression reasons are supported.
- The old V5 screen-debug objective and the original HUD’s top-left canvas objective are replaced by this shared tracker. Stamina, interaction hints and inventory remain.
- Normal Play starts a controlled character. GameMode explicitly disables spectator starts, verifies a pawn exists, sets its camera target, and applies game-only input. Review cameras do not auto-activate.

## Connected gameplay

V5 begins with **Investigate the illuminated house** and these steps:

- Find a way inside.
- Examine the front porch.
- Optional: Search the gas station forecourt.

Two invisible, non-blocking overlap volumes complete porch inspection and the optional forecourt visit. These currently represent area visits, not a new inspection/minigame or a loot pickup. Optional completion never advances or blocks the story.

Entering House01 advances the main objective through the existing V5 director; the tracker hides for the silhouette. It returns when the encounter ends. Leaving through the existing streaming door advances to the neighborhood objective and expires the Chapter 1 optional visit at its intended chapter boundary. Subsequent existing V5 stage transitions publish concise current objectives without describing upcoming horror events.

The original progression manager also publishes through the same objective subsystem. Its existing events, pickups, gates and transitions retain their original logic. Its debug progression reset now clears the related HUD completion flags as well.

## Editing / future chapter integration

Get **Penance Objective Subsystem → Get Objective Manager**, using the local player or another runtime world object as context. Its Blueprint-callable functions include:

- SetMainObjective / AdvanceMainObjective / CompleteMainObjective.
- AddSubObjective / RemoveSubObjective / CompleteSubObjective.
- AddOptionalObjective / RemoveOptionalObjective / CompleteOptionalObjective.
- SetObjectiveAvailable, SetExpanded / ToggleExpanded.
- SetSuppressed(Reason, true/false) for cutscene or scripted-moment begin/end events. Use a different stable reason for overlapping sequences.
- CaptureSnapshot / RestoreSnapshot.

Use stable IDs such as Ch01.House.Porch and Ch01.Gas.Search. Available future-chapter optional entries stay hidden until their chapter is reached; unavailable entries stay hidden. ExpiresAfterChapter = 0 leaves expiration under explicit event control.

**PenanceObjectiveSaveGame** contains the serializable objective snapshot: main ID/title, chapter, completion state, sub/optional entries, availability, completed IDs and expanded state. Future checkpoint/save code can store CaptureSnapshot in that SaveGame and call RestoreSnapshot after restoring its world progression. This pass does not add an automatic save/checkpoint system or claim to restore the entire game world. Temporary completion-display timers and cutscene suppression are not persisted.

The UMG tree and appearance defaults are editable in the Widget Blueprint. A small native parent supplies dynamic rows and delegate/timer behavior; the supported native editor helper creates the actual designer tree because that construction is not fully exposed through the project’s Python editor interface. No arbitrary uasset binary writing is used. Saved assets are already wired; no manual editor setup is required.

## Verification and limitations

**Final result: 35 PIE checks passed, with zero failures.** Player movement, camera ownership and the actual saved WBP were verified in a fresh editor session.

See [Validation.json](Validation.json) for the final actual PIE checks and [Layout_Review.json](Layout_Review.json) for resolution measurements. Screenshots include actual gameplay with the possessed player and native UMG renders at 1080p, 1440p and 4K over both dark and bright backgrounds. Offscreen layout renders are labeled separately from the actual PIE captures.

The source compiled against the installed Unreal 5.7.4 build. Tests cover main changes, real porch/gas overlaps, optional independence, completion display/expiry, collapse/expand handlers, cutscene suppression/restoration, no idle refreshes, actual SaveGame serialization/restoration, and retained player ownership through House01 streaming. Both playable maps are tested for player possession and the active UMG HUD. Packaged builds, physical gamepad input, and a complete manual game playthrough were not tested.

Existing V5 blockout warnings about unbuilt lighting and competing directional lights remain. They do not prevent spawning or controlling the player. Debug overlays were temporarily hidden only while taking the clean HUD screenshots and then re-enabled; the warnings are retained in the editor log. No global warning suppression or unrelated lighting changes were saved.

[Gameplay screenshot](Screenshots/PIE_V5_ObjectiveTracker.png) · [Completed porch in gameplay](Screenshots/PIE_Completed_Porch.png) · [1080p dark layout](Screenshots/1080p_Dark.png) · [1080p bright layout](Screenshots/1080p_Bright.png) · [4K layout](Screenshots/4K_Dark.png)

[Created/modified file inventory](File_Inventory.json) · [Preserved asset check](Preservation.json) · [Saved asset/Play setup](Asset_Setup.json)
