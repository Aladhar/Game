extends CanvasLayer

@onready var reason_label: Label = $Root/Reason

func _ready() -> void:
	GameState.game_lost.connect(_on_game_lost)
	visible = false

func _input(event: InputEvent) -> void:
	if not visible:
		return

	if event.is_action_pressed("restart"):
		get_tree().reload_current_scene()
		return

	if event is InputEventMouseButton and event.pressed:
		get_tree().reload_current_scene()

func _on_game_lost(reason: String) -> void:
	visible = true
	reason_label.text = "Cause: " + reason
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)