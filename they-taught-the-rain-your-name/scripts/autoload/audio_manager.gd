extends Node

var rain_bed_player: AudioStreamPlayer
var wind_bed_player: AudioStreamPlayer
var rng := RandomNumberGenerator.new()

func _ready() -> void:
    rng.seed = 77813
    SceneBus.sound_event_recorded.connect(_on_sound_event_recorded)
    SceneBus.rain_imitation_requested.connect(play_rain_imitation)

func start_demo_storm_bed() -> void:
    if rain_bed_player == null:
        rain_bed_player = _make_2d_player("DemoRainBed", -15.0)
        rain_bed_player.stream = _make_noise_stream(2.0, 0.42, 0.92, true)
        add_child(rain_bed_player)
    if wind_bed_player == null:
        wind_bed_player = _make_2d_player("DemoWindBed", -24.0)
        wind_bed_player.stream = _make_hum_stream(3.0, 55.0, 0.35, true)
        add_child(wind_bed_player)

    if not rain_bed_player.playing:
        rain_bed_player.play()
    if not wind_bed_player.playing:
        wind_bed_player.play()

func play_ui_warning(_name: String) -> void:
    _play_2d_one_shot("UIWarning", _make_tone_stream(0.22, 290.0, 0.18), -18.0)

func play_ritual_stinger(name: String) -> void:
    var stream := _make_stinger_stream(0.95, 70.0, 0.75)
    var volume := -12.0
    if name.contains("tunnel") or name.contains("complete"):
        volume = -8.0
    _play_2d_one_shot("RitualStinger_" + name, stream, volume)

func play_thunder(strong: bool = false) -> void:
    var volume := -7.0 if strong else -12.0
    var stream := _make_thunder_stream(4.5 if strong else 2.8, 0.92 if strong else 0.62)
    _play_2d_one_shot("Thunder", stream, volume)

func play_rain_imitation(_event_data: Dictionary) -> void:
    var event_type := str(_event_data.get("type", "unknown"))
    var position := _get_event_position(_event_data)
    match event_type:
        "knock":
            _play_3d_one_shot("RainCopiesKnock", position + Vector3(1.5, 0.7, -1.5), _make_knock_stream(), -11.0)
        "sprint_step":
            _play_3d_one_shot("RainCopiesStep", position + Vector3(-1.0, 0.2, 1.0), _make_tone_stream(0.12, 95.0, 0.22), -20.0)
        _:
            _play_3d_one_shot("RainCopiesSound", position, _make_noise_stream(0.25, 0.35, 0.45, false), -20.0)

func _on_sound_event_recorded(event_data: Dictionary) -> void:
    var event_type := str(event_data.get("type", "unknown"))
    var position := _get_event_position(event_data)
    match event_type:
        "knock":
            _play_3d_one_shot("PlayerKnock", position, _make_knock_stream(), -13.0)
        "sprint_step":
            _play_3d_one_shot("SprintStep", position, _make_tone_stream(0.10, 82.0, 0.18), -24.0)
        "silence_window":
            _play_2d_one_shot("SilencePressure", _make_hum_stream(1.0, 48.0, 0.25, false), -24.0)

func _get_event_position(event_data: Dictionary) -> Vector3:
    var raw_position: Variant = event_data.get("position", Vector3.ZERO)
    if raw_position is Vector3:
        return raw_position
    return Vector3.ZERO

func _make_2d_player(player_name: String, volume_db: float) -> AudioStreamPlayer:
    var player := AudioStreamPlayer.new()
    player.name = player_name
    player.volume_db = volume_db
    player.bus = "Master"
    return player

func _play_2d_one_shot(player_name: String, stream: AudioStream, volume_db: float) -> void:
    var player := _make_2d_player(player_name, volume_db)
    player.stream = stream
    add_child(player)
    player.finished.connect(player.queue_free)
    player.play()

func _play_3d_one_shot(player_name: String, pos: Vector3, stream: AudioStream, volume_db: float) -> void:
    var player := AudioStreamPlayer3D.new()
    player.name = player_name
    player.volume_db = volume_db
    player.unit_size = 8.0
    player.max_distance = 28.0
    player.stream = stream
    get_tree().root.add_child(player)
    player.global_position = pos
    player.finished.connect(player.queue_free)
    player.play()

func _make_noise_stream(duration: float, amplitude: float, brightness: float, loop: bool) -> AudioStreamWAV:
    var sample_rate := 22050
    var sample_count := int(duration * sample_rate)
    var data := PackedByteArray()
    data.resize(sample_count * 2)
    var previous := 0.0
    for i in range(sample_count):
        var raw := rng.randf_range(-1.0, 1.0)
        previous = lerpf(previous, raw, brightness)
        var envelope := 1.0
        if not loop:
            envelope = 1.0 - (float(i) / float(sample_count))
        data.encode_s16(i * 2, int(clamp(previous * amplitude * envelope, -1.0, 1.0) * 32767.0))
    return _make_wav(data, sample_rate, loop)

func _make_hum_stream(duration: float, frequency: float, amplitude: float, loop: bool) -> AudioStreamWAV:
    var sample_rate := 22050
    var sample_count := int(duration * sample_rate)
    var data := PackedByteArray()
    data.resize(sample_count * 2)
    for i in range(sample_count):
        var t := float(i) / float(sample_rate)
        var sample := sin(TAU * frequency * t) * amplitude
        sample += sin(TAU * (frequency * 0.5) * t) * amplitude * 0.45
        if not loop:
            sample *= 1.0 - (float(i) / float(sample_count))
        data.encode_s16(i * 2, int(clamp(sample, -1.0, 1.0) * 32767.0))
    return _make_wav(data, sample_rate, loop)

func _make_tone_stream(duration: float, frequency: float, amplitude: float) -> AudioStreamWAV:
    var sample_rate := 22050
    var sample_count := int(duration * sample_rate)
    var data := PackedByteArray()
    data.resize(sample_count * 2)
    for i in range(sample_count):
        var t := float(i) / float(sample_rate)
        var envelope := 1.0 - (float(i) / float(sample_count))
        var sample := sin(TAU * frequency * t) * amplitude * envelope
        data.encode_s16(i * 2, int(clamp(sample, -1.0, 1.0) * 32767.0))
    return _make_wav(data, sample_rate, false)

func _make_knock_stream() -> AudioStreamWAV:
    var sample_rate := 22050
    var sample_count := int(0.18 * sample_rate)
    var data := PackedByteArray()
    data.resize(sample_count * 2)
    for i in range(sample_count):
        var t := float(i) / float(sample_rate)
        var envelope := exp(-24.0 * t)
        var sample := rng.randf_range(-1.0, 1.0) * 0.65 * envelope
        sample += sin(TAU * 130.0 * t) * 0.28 * envelope
        data.encode_s16(i * 2, int(clamp(sample, -1.0, 1.0) * 32767.0))
    return _make_wav(data, sample_rate, false)

func _make_stinger_stream(duration: float, frequency: float, amplitude: float) -> AudioStreamWAV:
    var sample_rate := 22050
    var sample_count := int(duration * sample_rate)
    var data := PackedByteArray()
    data.resize(sample_count * 2)
    for i in range(sample_count):
        var t := float(i) / float(sample_rate)
        var envelope := exp(-3.8 * t)
        var sample := sin(TAU * frequency * t) * amplitude * envelope
        sample += sin(TAU * (frequency * 1.5) * t) * amplitude * 0.25 * envelope
        data.encode_s16(i * 2, int(clamp(sample, -1.0, 1.0) * 32767.0))
    return _make_wav(data, sample_rate, false)

func _make_thunder_stream(duration: float, amplitude: float) -> AudioStreamWAV:
    var sample_rate := 22050
    var sample_count := int(duration * sample_rate)
    var data := PackedByteArray()
    data.resize(sample_count * 2)
    var rumble := 0.0
    for i in range(sample_count):
        var t := float(i) / float(sample_rate)
        var envelope := exp(-1.35 * t)
        var crack := rng.randf_range(-1.0, 1.0) * exp(-18.0 * t)
        rumble = lerpf(rumble, rng.randf_range(-1.0, 1.0), 0.04)
        var sample := (rumble * 0.7 + crack * 0.5 + sin(TAU * 38.0 * t) * 0.35) * amplitude * envelope
        data.encode_s16(i * 2, int(clamp(sample, -1.0, 1.0) * 32767.0))
    return _make_wav(data, sample_rate, false)

func _make_wav(data: PackedByteArray, sample_rate: int, loop: bool) -> AudioStreamWAV:
    var wav := AudioStreamWAV.new()
    wav.format = AudioStreamWAV.FORMAT_16_BITS
    wav.mix_rate = sample_rate
    wav.stereo = false
    wav.data = data
    if loop:
        wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
        wav.loop_begin = 0
        wav.loop_end = data.size() / 2
    return wav
