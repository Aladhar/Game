extends Node
class_name DemoDirector

signal state_changed(new_state: String)

const START := "START"
const HOUSE_DONE := "HOUSE_DONE"
const PARK_DONE := "PARK_DONE"
const CUL_DE_SAC_DONE := "CUL_DE_SAC_DONE"
const CHURCH_DONE := "CHURCH_DONE"
const BASEMENT_DONE := "BASEMENT_DONE"
const DEMO_DONE := "DEMO_DONE"

var state: String = START
var first_house_approached: bool = false
var first_house_reveal_done: bool = false
var first_house_entered: bool = false
var first_house_photo_inspected: bool = false
var first_house_complete: bool = false

func reset() -> void:
    state = START
    first_house_approached = false
    first_house_reveal_done = false
    first_house_entered = false
    first_house_photo_inspected = false
    first_house_complete = false
    print("STATE: " + state)
    state_changed.emit(state)

func advance(new_state: String) -> void:
    state = new_state
    print("STATE: " + state)
    state_changed.emit(state)

func try_advance(expected_state: String, new_state: String, reached_label: String = "") -> bool:
    if state != expected_state:
        print("BLOCKED: " + reached_label + " expected=" + expected_state + " actual=" + state)
        return false

    if reached_label != "":
        print(reached_label)
    advance(new_state)
    return true

func mark_first_house_approached() -> bool:
    if first_house_approached:
        return false
    first_house_approached = true
    print("FIRST_HOUSE_FLAG: approached")
    return true

func mark_first_house_reveal_done() -> bool:
    if first_house_reveal_done:
        return false
    first_house_reveal_done = true
    print("FIRST_HOUSE_FLAG: reveal_done")
    return true

func mark_first_house_entered() -> bool:
    if first_house_entered:
        return false
    first_house_approached = true
    first_house_entered = true
    print("FIRST_HOUSE_FLAG: entered")
    return true

func mark_first_house_photo_inspected() -> bool:
    if first_house_photo_inspected:
        return false
    first_house_approached = true
    first_house_entered = true
    first_house_photo_inspected = true
    print("FIRST_HOUSE_FLAG: photo_inspected")
    return true

func complete_first_house() -> bool:
    if first_house_complete:
        return false
    first_house_complete = true
    first_house_photo_inspected = true
    print("FIRST_HOUSE_FLAG: complete")
    if state == START:
        advance(HOUSE_DONE)
    return true
