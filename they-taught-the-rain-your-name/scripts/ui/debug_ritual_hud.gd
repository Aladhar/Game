extends CanvasLayer

@onready var title_label: Label = $Root/TitleLabel
@onready var warning_label: Label = $Root/WarningLabel
@onready var act_label: Label = $Root/ActLabel
@onready var memory_label: Label = $Root/MemoryLabel
@onready var event_label: Label = $Root/EventLabel
@onready var rule_label: Label = $Root/RuleLabel

var recent_events: Array[String] = []
var warning_timer: float = 0.0

func _ready() -> void:
    GameState.act_changed.connect(_on_act_changed)
    GameState.memory_intensity_changed.connect(_on_memory_changed)
    GameState.warning_changed.connect(_on_warning_changed)
    SceneBus.sound_event_recorded.connect(_on_sound_event_recorded)
    SceneBus.rain_imitation_played.connect(_on_rain_imitation_played)
    SceneBus.ritual_rule_changed.connect(_on_rule_changed)

    title_label.text = "THEY TAUGHT THE RAIN YOUR NAME"
    _on_act_changed(GameState.current_act)
    _on_memory_changed(GameState.memory_intensity)

func _process(delta: float) -> void:
    if warning_timer > 0.0:
        warning_timer -= delta
        if warning_timer <= 0.0:
            warning_label.text = ""

func _on_act_changed(act: int) -> void:
    act_label.text = "Act: %d" % act

func _on_memory_changed(value: float) -> void:
    memory_label.text = "Rain Memory: %.1f / 100" % value

func _on_warning_changed(text: String) -> void:
    warning_label.text = text
    warning_timer = 4.0

func _on_rule_changed(text: String) -> void:
    rule_label.text = "Rule: " + text

func _on_sound_event_recorded(event_data: Dictionary) -> void:
    var line := "heard: %s" % event_data.get("type", "unknown")
    _push_event(line)

func _on_rain_imitation_played(event_data: Dictionary) -> void:
    var line := "rain repeated: %s" % event_data.get("type", "unknown")
    _push_event(line)

func _push_event(line: String) -> void:
    recent_events.push_front(line)
    while recent_events.size() > 6:
        recent_events.pop_back()
    event_label.text = "\n".join(recent_events)
