"""Create the Penance player Enhanced Input and animation assets in Unreal Editor.
Run with the UE 5.7 PythonScript commandlet from the Penance project root.
Existing assets are reused and never overwritten.
"""
import unreal

TOOLS = unreal.AssetToolsHelpers.get_asset_tools()


def asset(path):
    return unreal.EditorAssetLibrary.load_asset(path)


def create_data_asset(name, cls, folder):
    path = folder + '/' + name
    existing = asset(path)
    if existing:
        return existing
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', cls)
    created = TOOLS.create_asset(name, folder, cls, factory)
    if not created:
        raise RuntimeError('Failed to create ' + path)
    return created


folder = '/Game/Player/Input'
unreal.EditorAssetLibrary.make_directory(folder)
move = create_data_asset('IA_Move', unreal.InputAction, folder)
look = create_data_asset('IA_Look', unreal.InputAction, folder)
sprint = create_data_asset('IA_Sprint', unreal.InputAction, folder)
test_shot = create_data_asset('IA_TestShot', unreal.InputAction, folder)
move.set_editor_property('value_type', unreal.InputActionValueType.AXIS2D)
look.set_editor_property('value_type', unreal.InputActionValueType.AXIS2D)
sprint.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
test_shot.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)

# Keep the existing crouch, interaction, jump, and inventory controls while
# moving player input fully onto Enhanced Input.
extra = {}
for name in ['Crouch', 'Interact', 'Jump', 'Inventory']:
    extra[name] = create_data_asset('IA_' + name, unreal.InputAction, folder)
    extra[name].set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)

context = create_data_asset('IMC_Player', unreal.InputMappingContext, folder)
context.unmap_all()
modifiers_by_key = {}


def map_key(action, key_name, modifiers=None):
    key = unreal.Key()
    key.set_editor_property('key_name', unreal.Name(key_name))
    mapping = context.map_key(action, key)
    modifiers_by_key[key_name] = modifiers or []
    return mapping


def swizzle_y():
    modifier = unreal.InputModifierSwizzleAxis()
    modifier.set_editor_property('order', unreal.InputAxisSwizzle.YXZ)
    return modifier


def negate():
    return unreal.InputModifierNegate()

map_key(move, 'W', [swizzle_y()])
map_key(move, 'S', [swizzle_y(), negate()])
map_key(move, 'A', [negate()])
map_key(move, 'D')
map_key(look, 'MouseX')
map_key(look, 'MouseY', [swizzle_y()])
map_key(sprint, 'LeftShift')
map_key(test_shot, 'T')
map_key(extra['Crouch'], 'LeftControl')
map_key(extra['Crouch'], 'C')
map_key(extra['Interact'], 'E')
map_key(extra['Jump'], 'SpaceBar')
map_key(extra['Inventory'], 'J')

# Python exposes the returned EnhancedActionKeyMapping as a copy. Write the
# edited array back through the UE 5.7 DefaultKeyMappings struct.
key_mapping_data = context.get_editor_property('default_key_mappings')
key_mappings = key_mapping_data.get_editor_property('mappings')
for mapping in key_mappings:
    key_name = mapping.get_editor_property('key').get_editor_property('key_name').__str__()
    mapping.set_editor_property('modifiers', modifiers_by_key.get(key_name, []))
key_mapping_data.set_editor_property('mappings', key_mappings)
context.set_editor_property('default_key_mappings', key_mapping_data)

if not unreal.PenancePlayerAssetLibrary.build_player_input_mappings():
    raise RuntimeError('Failed to persist input mapping modifiers through UE API')

for name, obj in [('IA_Move', move), ('IA_Look', look), ('IA_Sprint', sprint), ('IA_TestShot', test_shot),
                  ('IA_Crouch', extra['Crouch']), ('IA_Interact', extra['Interact']),
                  ('IA_Jump', extra['Jump']), ('IA_Inventory', extra['Inventory']),
                  ('IMC_Player', context)]:
    unreal.EditorAssetLibrary.save_loaded_asset(obj)
    print('PENANCE_PLAYER_ASSET_OK', obj.get_path_name())
