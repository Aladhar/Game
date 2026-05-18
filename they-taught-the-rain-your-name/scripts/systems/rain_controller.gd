extends Node3D

@export var follow_player: bool = true
@export var rain_enabled: bool = true
@export var rain_amount: int = 900
@export var near_camera_rain_amount: int = 120
@export var splash_amount: int = 90
@export var rain_area: Vector3 = Vector3(34.0, 6.0, 34.0)

var rain_particles: GPUParticles3D
var near_camera_rain_particles: GPUParticles3D
var splash_particles: GPUParticles3D
var rain_streak_material: StandardMaterial3D
var rain_splash_material: StandardMaterial3D

func _ready() -> void:
    _create_rain_materials()
    _create_local_rain()
    _create_near_camera_rain()
    _create_local_splashes()

func _process(_delta: float) -> void:
    var player := get_tree().get_first_node_in_group("player") as Node3D
    var camera := get_tree().get_first_node_in_group("player_camera") as Camera3D
    if follow_player:
        if player != null:
            global_position = player.global_position + Vector3(0.0, 4.5, 0.0)

    if rain_particles != null:
        rain_particles.emitting = rain_enabled and not GameState.game_over
    if near_camera_rain_particles != null:
        near_camera_rain_particles.emitting = rain_enabled and not GameState.game_over
        if camera != null:
            near_camera_rain_particles.global_position = camera.global_position + Vector3(0.0, 0.45, -0.35)
    if splash_particles != null:
        splash_particles.emitting = rain_enabled and not GameState.game_over
        if player != null:
            splash_particles.global_position = player.global_position + Vector3(0.0, 0.08, 0.0)

func _create_rain_materials() -> void:
    rain_streak_material = StandardMaterial3D.new()
    rain_streak_material.albedo_color = Color(0.50, 0.62, 0.70, 0.34)
    rain_streak_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    rain_streak_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED

    rain_splash_material = StandardMaterial3D.new()
    rain_splash_material.albedo_color = Color(0.46, 0.56, 0.62, 0.26)
    rain_splash_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    rain_splash_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED

func _create_local_rain() -> void:
    rain_particles = GPUParticles3D.new()
    rain_particles.name = "LocalRainParticles"
    rain_particles.amount = rain_amount
    rain_particles.lifetime = 0.75
    rain_particles.preprocess = 0.65
    rain_particles.visibility_aabb = AABB(Vector3(-45, -20, -45), Vector3(90, 45, 90))

    var particle_material := ParticleProcessMaterial.new()
    particle_material.direction = Vector3(0.12, -1.0, 0.04)
    particle_material.spread = 8.0
    particle_material.gravity = Vector3(0.0, -42.0, 0.0)
    particle_material.initial_velocity_min = 18.0
    particle_material.initial_velocity_max = 28.0
    particle_material.scale_min = 0.018
    particle_material.scale_max = 0.045
    particle_material.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
    particle_material.emission_box_extents = rain_area

    rain_particles.process_material = particle_material

    var mesh := BoxMesh.new()
    mesh.size = Vector3(0.018, 0.9, 0.018)
    mesh.material = rain_streak_material
    rain_particles.draw_pass_1 = mesh

    add_child(rain_particles)

func _create_near_camera_rain() -> void:
    near_camera_rain_particles = GPUParticles3D.new()
    near_camera_rain_particles.name = "NearCameraRainStreaks"
    near_camera_rain_particles.amount = near_camera_rain_amount
    near_camera_rain_particles.lifetime = 0.45
    near_camera_rain_particles.preprocess = 0.45
    near_camera_rain_particles.visibility_aabb = AABB(Vector3(-3, -4, -3), Vector3(6, 8, 6))

    var particle_material := ParticleProcessMaterial.new()
    particle_material.direction = Vector3(0.08, -1.0, 0.02)
    particle_material.spread = 5.0
    particle_material.gravity = Vector3(0.0, -54.0, 0.0)
    particle_material.initial_velocity_min = 22.0
    particle_material.initial_velocity_max = 34.0
    particle_material.scale_min = 0.012
    particle_material.scale_max = 0.026
    particle_material.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
    particle_material.emission_box_extents = Vector3(1.6, 1.2, 1.6)
    near_camera_rain_particles.process_material = particle_material

    var mesh := BoxMesh.new()
    mesh.size = Vector3(0.012, 0.55, 0.012)
    mesh.material = rain_streak_material
    near_camera_rain_particles.draw_pass_1 = mesh
    add_child(near_camera_rain_particles)

func _create_local_splashes() -> void:
    splash_particles = GPUParticles3D.new()
    splash_particles.name = "LocalRainSplashHints"
    splash_particles.amount = splash_amount
    splash_particles.lifetime = 0.35
    splash_particles.preprocess = 0.35
    splash_particles.visibility_aabb = AABB(Vector3(-8, -1, -8), Vector3(16, 4, 16))

    var particle_material := ParticleProcessMaterial.new()
    particle_material.direction = Vector3(0.0, 1.0, 0.0)
    particle_material.spread = 55.0
    particle_material.gravity = Vector3(0.0, -9.8, 0.0)
    particle_material.initial_velocity_min = 0.8
    particle_material.initial_velocity_max = 2.6
    particle_material.scale_min = 0.018
    particle_material.scale_max = 0.04
    particle_material.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
    particle_material.emission_box_extents = Vector3(6.0, 0.08, 6.0)
    splash_particles.process_material = particle_material

    var mesh := BoxMesh.new()
    mesh.size = Vector3(0.05, 0.018, 0.05)
    mesh.material = rain_splash_material
    splash_particles.draw_pass_1 = mesh
    add_child(splash_particles)
