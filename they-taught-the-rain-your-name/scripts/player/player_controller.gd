extends CharacterBody3D

@export_category("Movement")
@export var walk_speed: float = 4.2
@export var sprint_speed: float = 6.4
@export var acceleration: float = 18.0
@export var friction: float = 22.0

@export_category("Mouse Look")
@export var mouse_sensitivity: float = 0.0024
@export var invert_y: bool = false
@export var capture_mouse_on_start: bool = true

@onready var camera_pivot: Node3D = $CameraPivot
@onready var camera: Camera3D = $CameraPivot/Camera3D

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var pitch: float = 0.0
var sprint_event_timer: float = 0.0
var silence_timer: float = 0.0

func _ready() -> void:
    add_to_group("player")
    camera.add_to_group("player_camera")
    _ensure_default_input()

    if capture_mouse_on_start:
        Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.pressed:
        if Input.get_mouse_mode() != Input.MOUSE_MODE_CAPTURED:
            Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
            get_viewport().set_input_as_handled()
            return

    if event.is_action_pressed("ui_cancel"):
        if Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
            Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)
        else:
            Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
        get_viewport().set_input_as_handled()
        return

    if event is InputEventMouseMotion and Input.get_mouse_mode() == Input.MOUSE_MODE_CAPTURED:
        rotate_y(-event.relative.x * mouse_sensitivity)

        var y_sign := 1.0 if invert_y else -1.0
        pitch = clamp(
            pitch + event.relative.y * mouse_sensitivity * y_sign,
            deg_to_rad(-82.0),
            deg_to_rad(82.0)
        )
        camera_pivot.rotation.x = pitch
        get_viewport().set_input_as_handled()

    if event.is_action_pressed("interact"):
        SceneBus.sound_event_recorded.emit({
            "type": "knock",
            "position": global_position,
            "intensity": 0.7,
            "source": "player",
            "note": "Manual test knock / interact input"
        })

func _physics_process(delta: float) -> void:
    _apply_gravity(delta)
    _apply_movement(delta)
    _track_sound_behavior(delta)
    move_and_slide()

func _apply_gravity(delta: float) -> void:
    if not is_on_floor():
        velocity.y -= gravity * delta
    else:
        velocity.y = 0.0

func _apply_movement(delta: float) -> void:
    var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    var world_dir := (global_transform.basis * Vector3(input_dir.x, 0.0, input_dir.y)).normalized()

    var target_speed := sprint_speed if Input.is_action_pressed("sprint") else walk_speed
    var target_velocity := world_dir * target_speed

    if world_dir.length() > 0.0:
        velocity.x = move_toward(velocity.x, target_velocity.x, acceleration * delta)
        velocity.z = move_toward(velocity.z, target_velocity.z, acceleration * delta)
    else:
        velocity.x = move_toward(velocity.x, 0.0, friction * delta)
        velocity.z = move_toward(velocity.z, 0.0, friction * delta)

func _track_sound_behavior(delta: float) -> void:
    var horizontal_speed := Vector2(velocity.x, velocity.z).length()

    if horizontal_speed > 0.25:
        silence_timer = 0.0
    else:
        silence_timer += delta

    if Input.is_action_pressed("sprint") and horizontal_speed > walk_speed:
        sprint_event_timer -= delta
        if sprint_event_timer <= 0.0:
            sprint_event_timer = 0.65
            SceneBus.sound_event_recorded.emit({
                "type": "sprint_step",
                "position": global_position,
                "intensity": 1.0,
                "source": "player",
                "note": "Player sprint rhythm"
            })
    else:
        sprint_event_timer = min(sprint_event_timer, 0.15)

    if silence_timer >= 5.0:
        silence_timer = 0.0
        SceneBus.sound_event_recorded.emit({
            "type": "silence_window",
            "position": global_position,
            "intensity": 0.45,
            "source": "player",
            "note": "Player stayed unnaturally quiet"
        })

func _ensure_default_input() -> void:
    _bind_key("move_forward", KEY_W)
    _bind_key("move_back", KEY_S)
    _bind_key("move_left", KEY_A)
    _bind_key("move_right", KEY_D)
    _bind_key("sprint", KEY_SHIFT)
    _bind_key("interact", KEY_E)

func _bind_key(action: String, keycode: Key) -> void:
    if not InputMap.has_action(action):
        InputMap.add_action(action)

    for existing_event in InputMap.action_get_events(action):
        if existing_event is InputEventKey and existing_event.physical_keycode == keycode:
            return

    var ev := InputEventKey.new()
    ev.physical_keycode = keycode
    InputMap.action_add_event(action, ev)
