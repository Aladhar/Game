extends Node3D

@export var follow_player: bool = true
@export var rain_enabled: bool = true
@export var rain_amount: int = 900
@export var rain_area: Vector3 = Vector3(34.0, 6.0, 34.0)

var rain_particles: GPUParticles3D

func _ready() -> void:
    _create_local_rain()

func _process(_delta: float) -> void:
    if follow_player:
        var player := get_tree().get_first_node_in_group("player") as Node3D
        if player != null:
            global_position = player.global_position + Vector3(0.0, 4.5, 0.0)

    if rain_particles != null:
        rain_particles.emitting = rain_enabled and not GameState.game_over

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
    rain_particles.draw_pass_1 = mesh

    add_child(rain_particles)
