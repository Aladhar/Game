from pathlib import Path

import unreal


LEVEL_PATH = "/Game/Maps/Penance_Suburban_Blockout"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TRIGGER_NAMES = [
    "Event_FirstHouse_FrontApproach",
    "Event_FirstHouse_Entry",
    "Event_FirstHouse_HallwayStretch",
    "Event_FirstHouse_DoorAppearsInWall",
    "Interact_FirstHouse_BlankPhoto",
    "Event_Park_LightsFlicker",
    "Event_CulDeSac_LightningPenanceAngle",
    "Event_Church_Threshold",
    "Interact_Church_InternalHandlingNotice",
    "Event_Church_BasementEntrance",
    "Event_Tunnel_PressureStarts",
    "Event_TunnelExit_FinalHouseBecomesReachable",
    "Event_FosterHouse_FinalApproach",
    "Event_RoadsLoop_NorthExit_TeleportBeforeUnlock",
]

REQUIRED_IMPORTED_NAMES = [
    "RouteGate_ToPark_BlockedUntilHouse",
    "RouteGate_ToCulDeSac_BlockedUntilPark",
    "RouteGate_ToChurch_BlockedUntilCulDeSac",
    "RouteGate_ToBasement_BlockedUntilChurch",
    "Church_RustedDoorBlocker_LockedUntilCulDeSac",
    "FirstHouse_FalseWall_BecomesDoor",
    "FirstHouse_NewDoor_AppearsWhereWallWas",
    "FinalHouse_RustedGate_BlocksEarlyRoute",
    "FinalHouse_RoadExtension_AppearsLater",
]


def class_name(actor):
    return actor.get_class().get_name()


def imported_name(actor):
    for tag in actor.tags:
        value = str(tag)
        if value.startswith("ImportedName_"):
            return value[len("ImportedName_") :]
    return ""


def actors_by_imported_name(actors):
    result = {}
    for actor in actors:
        name = imported_name(actor)
        if name:
            result.setdefault(name, []).append(actor)
    return result


def actor_collision_enabled(actor):
    try:
        return bool(actor.get_actor_enable_collision())
    except Exception:
        return False


def named_collision_enabled(named_actors, name):
    matches = named_actors.get(name, [])
    if not matches:
        raise AssertionError(f"Missing imported actor: {name}")
    return any(actor_collision_enabled(actor) for actor in matches)


def assert_state(manager, expected, label, failures):
    actual = str(manager.get_progression_state_name())
    if actual != expected:
        failures.append(f"{label}: expected state {expected}, got {actual}")


def assert_bool(actual, expected, label, failures):
    if bool(actual) != bool(expected):
        failures.append(f"{label}: expected {expected}, got {actual}")


def assert_gate(named_actors, name, expected_collision, label, failures):
    try:
        actual = named_collision_enabled(named_actors, name)
    except AssertionError as exc:
        failures.append(str(exc))
        return
    if actual != expected_collision:
        failures.append(f"{label}: {name} collision expected {expected_collision}, got {actual}")


def fire(manager, event_name):
    manager.debug_fire_event(unreal.Name(event_name))


def pickup(manager, pickup_name):
    manager.debug_pickup(unreal.Name(pickup_name))


def verify_initial_world_state(manager, named_actors, failures):
    manager.debug_reset_progression()
    assert_state(manager, "START", "initial reset", failures)
    assert_bool(manager.is_final_house_unlocked(), False, "initial final house unlock", failures)
    assert_bool(manager.is_church_notice_inspected(), False, "initial church notice", failures)
    assert_gate(named_actors, "RouteGate_ToPark_BlockedUntilHouse", True, "initial", failures)
    assert_gate(named_actors, "RouteGate_ToCulDeSac_BlockedUntilPark", True, "initial", failures)
    assert_gate(named_actors, "RouteGate_ToChurch_BlockedUntilCulDeSac", True, "initial", failures)
    assert_gate(named_actors, "RouteGate_ToBasement_BlockedUntilChurch", True, "initial", failures)
    assert_gate(named_actors, "FinalHouse_RustedGate_BlocksEarlyRoute", True, "initial", failures)
    assert_gate(named_actors, "FinalHouse_RoadExtension_AppearsLater", False, "initial", failures)
    assert_gate(named_actors, "FirstHouse_FalseWall_BecomesDoor", True, "initial", failures)
    assert_gate(named_actors, "FirstHouse_NewDoor_AppearsWhereWallWas", False, "initial", failures)


def verify_skip_resistance(manager, failures):
    manager.debug_reset_progression()
    for event_name in [
        "Event_Park_LightsFlicker",
        "Event_CulDeSac_LightningPenanceAngle",
        "Event_Church_Threshold",
        "Event_Tunnel_PressureStarts",
        "Event_TunnelExit_FinalHouseBecomesReachable",
        "Event_FosterHouse_FinalApproach",
    ]:
        fire(manager, event_name)
        assert_state(manager, "START", f"skip resistance after {event_name}", failures)
    assert_bool(manager.is_final_house_unlocked(), False, "skip resistance final house unlock", failures)


def verify_first_house_lock(manager, named_actors, failures):
    manager.debug_reset_progression()
    for event_name in [
        "Event_FirstHouse_FrontApproach",
        "Event_FirstHouse_Entry",
        "Event_FirstHouse_HallwayStretch",
        "Event_FirstHouse_DoorAppearsInWall",
    ]:
        fire(manager, event_name)
        assert_state(manager, "START", f"first house cannot finish from marker {event_name}", failures)

    pickup(manager, "Pickup_BlankFamilyPhoto")
    assert_state(manager, "HOUSE_DONE", "blank photo completes first house", failures)
    assert_gate(named_actors, "RouteGate_ToPark_BlockedUntilHouse", False, "after photo", failures)
    assert_gate(named_actors, "FirstHouse_FalseWall_BecomesDoor", False, "after photo", failures)
    assert_gate(named_actors, "FirstHouse_NewDoor_AppearsWhereWallWas", True, "after photo", failures)


def verify_happy_path(manager, named_actors, failures):
    manager.debug_reset_progression()

    fire(manager, "Event_FirstHouse_FrontApproach")
    fire(manager, "Event_FirstHouse_Entry")
    pickup(manager, "Pickup_BlankFamilyPhoto")
    assert_state(manager, "HOUSE_DONE", "happy path house", failures)

    fire(manager, "Event_Park_LightsFlicker")
    assert_state(manager, "PARK_DONE", "happy path park", failures)
    assert_gate(named_actors, "RouteGate_ToCulDeSac_BlockedUntilPark", False, "after park", failures)

    fire(manager, "Event_CulDeSac_LightningPenanceAngle")
    assert_state(manager, "CUL_DE_SAC_DONE", "happy path cul-de-sac", failures)
    assert_gate(named_actors, "RouteGate_ToChurch_BlockedUntilCulDeSac", False, "after cul-de-sac", failures)
    assert_gate(named_actors, "Church_RustedDoorBlocker_LockedUntilCulDeSac", False, "after cul-de-sac", failures)

    fire(manager, "Event_Church_Threshold")
    assert_state(manager, "CHURCH_DONE", "happy path church", failures)
    fire(manager, "Event_Church_BasementEntrance")
    assert_state(manager, "CHURCH_DONE", "basement entrance waits for notice", failures)
    assert_gate(named_actors, "RouteGate_ToBasement_BlockedUntilChurch", True, "before church notice", failures)

    pickup(manager, "Pickup_InternalHandlingNotice")
    assert_bool(manager.is_church_notice_inspected(), True, "church notice inspected", failures)
    assert_gate(named_actors, "RouteGate_ToBasement_BlockedUntilChurch", False, "after church notice", failures)

    fire(manager, "Event_Tunnel_PressureStarts")
    assert_state(manager, "BASEMENT_DONE", "happy path tunnel pressure", failures)
    assert_bool(manager.is_final_house_unlocked(), False, "before tunnel exit final house unlock", failures)

    fire(manager, "Event_TunnelExit_FinalHouseBecomesReachable")
    assert_state(manager, "BASEMENT_DONE", "tunnel exit keeps basement state", failures)
    assert_bool(manager.is_final_house_unlocked(), True, "after tunnel exit final house unlock", failures)
    assert_gate(named_actors, "FinalHouse_RustedGate_BlocksEarlyRoute", False, "after tunnel exit", failures)
    assert_gate(named_actors, "FinalHouse_RoadExtension_AppearsLater", True, "after tunnel exit", failures)

    fire(manager, "Event_FosterHouse_FinalApproach")
    assert_state(manager, "DEMO_DONE", "happy path final house", failures)

    for event_name in [
        "Event_FirstHouse_FrontApproach",
        "Event_Park_LightsFlicker",
        "Event_CulDeSac_LightningPenanceAngle",
        "Event_Church_Threshold",
    ]:
        fire(manager, event_name)
        assert_state(manager, "DEMO_DONE", f"post-demo backtrack after {event_name}", failures)


def main():
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(LEVEL_PATH)
    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    managers = [actor for actor in actors if class_name(actor) == "PenanceProgressionManager"]
    triggers = [actor for actor in actors if class_name(actor) == "PenanceProgressionTrigger"]
    trigger_names = sorted(str(actor.get_editor_property("trigger_name")) for actor in triggers)
    named_actors = actors_by_imported_name(actors)

    failures = []
    if len(managers) != 1:
        failures.append(f"Expected exactly one PenanceProgressionManager, found {len(managers)}")
    if len(triggers) != 17:
        failures.append(f"Expected 17 PenanceProgressionTrigger actors, found {len(triggers)}")

    missing_triggers = [name for name in REQUIRED_TRIGGER_NAMES if name not in trigger_names]
    if missing_triggers:
        failures.append("Missing progression triggers: " + ", ".join(missing_triggers))

    missing_imported = [name for name in REQUIRED_IMPORTED_NAMES if name not in named_actors]
    if missing_imported:
        failures.append("Missing progression-controlled imported actors: " + ", ".join(missing_imported))

    if managers:
        manager = managers[0]
        verify_initial_world_state(manager, named_actors, failures)
        verify_skip_resistance(manager, failures)
        verify_first_house_lock(manager, named_actors, failures)
        verify_happy_path(manager, named_actors, failures)

    report_lines = [
        "PENANCE_PROGRESSION_VERIFY",
        f"Progression managers: {len(managers)}",
        f"Progression triggers: {len(triggers)}",
        f"Required trigger checks: {len(REQUIRED_TRIGGER_NAMES)}",
        f"Missing trigger checks: {len(missing_triggers)}",
        f"Required imported actor checks: {len(REQUIRED_IMPORTED_NAMES)}",
        f"Missing imported actor checks: {len(missing_imported)}",
        f"Failures: {len(failures)}",
    ]
    if failures:
        report_lines.append("FAILURES:")
        report_lines.extend(failures)

    report = "\n".join(report_lines) + "\n"
    report_path = PROJECT_ROOT / "Saved" / "PenanceProgressionVerify.txt"
    report_path.write_text(report)
    print(report)

    if failures:
        raise RuntimeError("Penance progression verification failed")


if __name__ == "__main__":
    main()
