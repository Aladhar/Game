extends Control

@onready var play_button: Button = $ContentRoot/MainLayout/ButtonStack/PlayButton
@onready var legacy_button: Button = $ContentRoot/MainLayout/ButtonStack/LegacyPrototypeButton
@onready var options_button: Button = $ContentRoot/MainLayout/ButtonStack/OptionsButton
@onready var quit_button: Button = $ContentRoot/MainLayout/ButtonStack/QuitButton

@onready var options_panel: PanelContainer = $OptionsPanel
@onready var back_button: Button = $OptionsPanel/OptionsMargin/OptionsVBox/BackButton
@onready var fullscreen_check: CheckBox = $OptionsPanel/OptionsMargin/OptionsVBox/FullscreenCheck
@onready var volume_slider: HSlider = $OptionsPanel/OptionsMargin/OptionsVBox/VolumeSlider
@onready var mouse_slider: HSlider = $OptionsPanel/OptionsMargin/OptionsVBox/MouseSensitivitySlider

const GAME_SCENE: String = "res://scenes/blockout/suburban_horror_blockout.tscn"
const LEGACY_SCENE: String = "res://scenes/main/rain_name_prototype.tscn"

func _ready() -> void:
	Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)

	play_button.pressed.connect(_on_play_pressed)
	legacy_button.pressed.connect(_on_legacy_pressed)
	options_button.pressed.connect(_on_options_pressed)
	quit_button.pressed.connect(_on_quit_pressed)
	back_button.pressed.connect(_on_back_pressed)
	fullscreen_check.toggled.connect(_on_fullscreen_toggled)
	volume_slider.value_changed.connect(_on_volume_changed)
	mouse_slider.value_changed.connect(_on_mouse_sensitivity_changed)

func _on_play_pressed() -> void:
	print("PLAY PRESSED")
	var err: Error = get_tree().change_scene_to_file(GAME_SCENE)
	if err != OK:
		push_error("Failed to load gameplay scene: " + GAME_SCENE + " error=" + str(err))

func _on_legacy_pressed() -> void:
	var err: Error = get_tree().change_scene_to_file(LEGACY_SCENE)
	if err != OK:
		push_error("Failed to load legacy prototype scene: " + LEGACY_SCENE + " error=" + str(err))

func _on_options_pressed() -> void:
	options_panel.visible = true

func _on_back_pressed() -> void:
	options_panel.visible = false

func _on_quit_pressed() -> void:
	get_tree().quit()

func _on_fullscreen_toggled(enabled: bool) -> void:
	if enabled:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)

func _on_volume_changed(value: float) -> void:
	var bus_index: int = AudioServer.get_bus_index("Master")
	if bus_index >= 0:
		AudioServer.set_bus_volume_db(bus_index, linear_to_db(max(value, 0.001)))

func _on_mouse_sensitivity_changed(value: float) -> void:
	ProjectSettings.set_setting("application/run/rain_mouse_sensitivity", value)
