extends Node3D

@onready var world_environment: WorldEnvironment = $WorldEnvironment

func _ready() -> void:
    _configure_environment()
    Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)

func _configure_environment() -> void:
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.004, 0.007, 0.011)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.035, 0.05, 0.065)
    env.ambient_light_energy = 0.38

    env.fog_enabled = true
    env.fog_density = 0.055
    env.fog_light_color = Color(0.18, 0.24, 0.30)
    env.fog_light_energy = 0.25

    env.glow_enabled = true
    env.glow_intensity = 0.16
    env.glow_strength = 0.55

    world_environment.environment = env
