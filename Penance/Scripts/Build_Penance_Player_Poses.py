"""Build editable temporary locomotion clips with Unreal's animation data controller."""
import math

import unreal as ue

ANIM = '/Game/Player/Animations'
SOURCE = '/Game/Player/MeshyPlayer'
PREFIX = SOURCE + '/Untitled_Anim_Armature_'
FPS = 30
assets = ue.get_editor_subsystem(ue.EditorAssetSubsystem)
tools = ue.AssetToolsHelpers.get_asset_tools()
mathlib = ue.MathLibrary
poses = ue.AnimPoseExtensions
options = ue.AnimPoseEvaluationOptions()

mesh = ue.load_asset(SOURCE + '/Untitled')
skeleton = mesh.get_editor_property('skeleton')
scared = ue.load_asset(PREFIX + 'Scared_Looking_around_if_afk_for_longer_than_30_seconds')
idle_pose = poses.get_anim_pose_at_time(scared, 0.0, options)
bones = poses.get_bone_names(idle_pose)


def read_pose(pose, space=ue.AnimPoseSpaces.LOCAL):
    return {str(b): poses.get_bone_pose(pose, b, space) for b in bones}


idle = read_pose(idle_pose)
standing = read_pose(idle_pose, ue.AnimPoseSpaces.WORLD)


def write_clip(name, frames):
    path = ANIM + '/' + name
    if assets.does_asset_exist(path):
        return assets.load_asset(path)
    factory = ue.AnimSequenceFactory()
    factory.set_editor_property('target_skeleton', skeleton)
    factory.set_editor_property('preview_skeletal_mesh', mesh)
    clip = tools.create_asset(name, ANIM, ue.AnimSequence, factory)
    if not clip:
        raise RuntimeError('Could not create ' + path)
    flat_frames = [frame[str(bone)] for frame in frames for bone in bones]
    if not ue.PenancePlayerAssetLibrary.write_player_pose_clip(clip, FPS, bones, flat_frames):
        raise RuntimeError('Could not key ' + path)
    if not assets.save_loaded_asset(clip):
        raise RuntimeError('Could not save ' + path)
    return clip


def transform(translation, rotation, scale):
    result = ue.Transform()
    result.translation = translation
    result.rotation = rotation
    result.scale3d = scale
    return result


def leg_pose(phase=None, strafe=False, airborne=False):
    """Solve two-bone legs for the temporary crouch, strafe and jump clips."""
    result = dict(idle)
    root_drop = ue.Vector(0, 0, -8) if strafe or airborne else ue.Vector(0, -8, -29)
    if phase is not None:
        root_drop.z += 1.2 * math.cos(phase * math.tau * 2)
    hips = standing['Hips']
    result['Hips'] = transform(hips.translation + root_drop, hips.rotation, hips.scale3d)

    for index, side in enumerate(('Left', 'Right')):
        thigh_name, shin_name, foot_name = (side + bone for bone in ('UpLeg', 'Leg', 'Foot'))
        thigh, shin, foot = (standing[b] for b in (thigh_name, shin_name, foot_name))
        upper = shin.translation - thigh.translation
        lower = foot.translation - shin.translation
        upper_length, lower_length = upper.length(), lower.length()
        hip = thigh.translation + root_drop
        ankle = ue.Vector(foot.translation.x, foot.translation.y, foot.translation.z)
        if airborne:
            ankle.y += 9 if index == 0 else -10
            ankle.z += 19 if index == 0 else 9
        if strafe:
            # The mesh faces +Y and its right side is -X. Feet travel +X
            # during stance as the capsule moves right.
            step = (phase + index * 0.5) % 1.0
            ankle.x += 7 if index == 0 else -7
            if step < 0.5:
                ankle.x += -15 + 60 * step
            else:
                swing = (step - 0.5) * 2
                ankle.x += 15 * math.cos(math.pi * swing)
                ankle.z += 9 * math.sin(math.pi * swing)
        elif phase is not None:
            step = (phase + index * 0.5) % 1.0
            if step < 0.5:
                ankle.y += 25 - 100 * step
            else:
                swing = (step - 0.5) * 2
                ankle.y += -25 * math.cos(math.pi * swing)
                ankle.z += 10 * math.sin(math.pi * swing)

        reach = ankle - hip
        direction = reach / reach.length()
        distance = min(reach.length(), upper_length + lower_length - 0.1)
        forward = ue.Vector(0, 1, 0)
        knee_direction = (forward - direction * forward.dot(direction)).normal()
        along = (upper_length ** 2 - lower_length ** 2 + distance ** 2) / (2 * distance)
        bend = math.sqrt(max(0, upper_length ** 2 - along ** 2))
        knee = hip + direction * along + knee_direction * bend
        ankle = hip + direction * distance

        thigh_rotation = mathlib.quat_find_between_vectors(upper, knee - hip) * thigh.rotation
        shin_rotation = mathlib.quat_find_between_vectors(lower, ankle - knee) * shin.rotation
        thigh_target = transform(hip, thigh_rotation, thigh.scale3d)
        shin_target = transform(knee, shin_rotation, shin.scale3d)
        foot_target = transform(ankle, foot.rotation, foot.scale3d)
        result[thigh_name] = mathlib.make_relative_transform(thigh_target, result['Hips'])
        result[shin_name] = mathlib.make_relative_transform(shin_target, thigh_target)
        result[foot_name] = mathlib.make_relative_transform(foot_target, shin_target)
    return result


write_clip('AN_PlayerIdle', [idle, idle])
crouch_idle = leg_pose()
write_clip('AN_PlayerCrouchIdle', [crouch_idle, crouch_idle])
write_clip('AN_PlayerCrouchWalk', [leg_pose(i / 24) for i in range(25)])
write_clip('AN_PlayerStrafe', [leg_pose(i / 24, strafe=True) for i in range(25)])
jump = leg_pose(airborne=True)
write_clip('AN_PlayerAirborne', [jump, jump])

path = ANIM + '/BS_PlayerCrouch'
if not assets.does_asset_exist(path):
    factory = ue.BlendSpaceFactory1D()
    factory.set_editor_property('target_skeleton', skeleton)
    blend = tools.create_asset('BS_PlayerCrouch', ANIM, ue.BlendSpace1D, factory)
    if not blend or not assets.save_loaded_asset(blend):
        raise RuntimeError('Could not save ' + path)
print('PENANCE_PLAYER_POSES_READY')
