"""Rig the textured Penance source without editing the original Blender file.

Run Blender in background with the source .blend open and pass an output root
after --. This retains the source geometry, UVs and packed material. In the rig
review action use the named timeline markers for six poses and a neutral return.
"""
from collections import defaultdict
from heapq import heappop, heappush
from math import radians
from pathlib import Path
import json
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

root = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
folder = root / 'Built'
blend_path = folder / 'BlenderWork/Penance_Rigged.blend'
fbx_path = folder / 'FBX/SK_Penance.fbx'
texture_path = folder / 'FBX/SK_Penance_BaseColor.png'
review = Path(sys.argv[sys.argv.index('--') + 2]).resolve()
for path in (blend_path.parent,fbx_path.parent,review):
    path.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve() == blend_path:
    raise RuntimeError('Open the original source, not the output file')
scene = bpy.context.scene
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

mesh = next(o for o in scene.objects if o.type == 'MESH')
original_rig = next(o for o in scene.objects if o.type == 'ARMATURE')
if not mesh.data.uv_layers or not mesh.data.materials:
    raise RuntimeError('Expected the textured Penance source')
mesh.hide_set(False)
mesh.hide_viewport = False
mesh.hide_render = False
coords = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
minimum = [min(v[i] for v in coords) for i in range(3)]
maximum = [max(v[i] for v in coords) for i in range(3)]
joint = {b.name: original_rig.matrix_world @ b.head_local for b in original_rig.data.bones}
offset = Vector((joint['root'].x,joint['root'].y,minimum[2]))
vertex_count, face_count = len(mesh.data.vertices), len(mesh.data.polygons)
existing_slots = [m.name for m in mesh.data.materials]
existing_uvs = [uv.name for uv in mesh.data.uv_layers]

# Bake only scene placement and the ground offset into the copy. Neither shape,
# density, triangulation, UV coordinates nor material assignments are altered.
world = mesh.matrix_world.copy()
mesh.parent = None
mesh.matrix_world = Matrix.Identity(4)
mesh.data.transform(Matrix.Translation(-offset) @ world)
for mod in list(mesh.modifiers):
    if mod.type == 'ARMATURE':
        mesh.modifiers.remove(mod)
mesh.vertex_groups.clear()
bpy.data.objects.remove(original_rig,do_unlink=True)
mesh.name = 'SK_Penance'
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

armature = bpy.data.armatures.new('Penance_Deform_Skeleton')
rig = bpy.data.objects.new('Armature',armature)
scene.collection.objects.link(rig)
rig.show_in_front = True
armature.display_type = 'OCTAHEDRAL'
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
bones = {}
for name in ('Humanoid','Secondary'):
    armature.collections.new(name)


def make(name,head,tail,parent=None,secondary=False):
    bone = armature.edit_bones.new(name)
    bone.head, bone.tail = Vector(head)-offset, Vector(tail)-offset
    if parent:
        bone.parent = armature.edit_bones[parent]
        bone.use_connect = (bone.parent.tail-bone.head).length < .00001 and parent!='root'
    bone.use_deform = name!='root'
    bone.align_roll(Vector((0,-1,0)))
    armature.collections['Secondary' if secondary else 'Humanoid'].assign(bone)
    bones[name] = (Vector(head),Vector(tail))
    return bone


p=joint
pelvis = Vector((.157,.048,.326))
spine_01 = Vector((.165,.052,.410))
spine_02 = Vector((.169,.021,.490))
spine_03 = Vector((.164,-.018,.552))
make('root',offset,offset+Vector((0,0,.09)))
make('pelvis',pelvis,spine_01,'root')
make('spine_01',spine_01,spine_02,'pelvis')
make('spine_02',spine_02,spine_03,'spine_01')
make('spine_03',spine_03,p['neck_01'],'spine_02')
make('neck_01',p['neck_01'],p['head'],'spine_03')
make('head',p['head'],(.153,-.207,.55),'neck_01')
for side,old in (('l','r'),('r','l')):
    # The source faces -Y. Positive Blender X is anatomical left.
    shoulder=p['upperarm_'+old]
    elbow=p['lowerarm_'+old]
    wrist=p['hand_'+old]
    hand=Vector((.345 if side=='l' else -.018,-.116,.302 if side=='l' else .295))
    make('clavicle_'+side,p['clavicle_'+old],shoulder,'spine_03')
    make('upperarm_'+side,shoulder,elbow,'clavicle_'+side)
    make('lowerarm_'+side,elbow,wrist,'upperarm_'+side)
    make('hand_'+side,wrist,hand,'lowerarm_'+side)

    hip, knee, ankle=[p[k+'_'+old] for k in ('thigh','calf','foot')]
    toes=Vector((.268 if side=='l' else .053,-.066 if side=='l' else -.085,-.062))
    foot_tip=toes+Vector((0,-.038,-.005))
    make('thigh_'+side,hip,knee,'pelvis')
    make('calf_'+side,knee,ankle,'thigh_'+side)
    make('foot_'+side,ankle,toes,'calf_'+side)
    make('ball_'+side,toes,foot_tip,'foot_'+side)

make('shrine_mount',(.157,.084,.511),(.157,.095,.692),'spine_03',True)
make('bell_r',(.002,-.122,.276),(.002,-.162,.096),'hand_r',True)
make('veil_01',(.154,-.186,.532),(.151,-.236,.33),'head',True)
make('veil_02',(.151,-.236,.33),(.151,-.232,.10),'veil_01',True)
bpy.ops.object.mode_set(mode='OBJECT')
mesh.parent=rig
mod=mesh.modifiers.new('Penance deformation','ARMATURE')
mod.object=rig
# Unreal uses linear skinning by default. Preview the same deformation in Blender.
mod.use_deform_preserve_volume=False
groups={name:mesh.vertex_groups.new(name=name) for name in bones if name!='root'}


def smooth(a,b,t):
    u=max(0.0,min(1.0,(t-a)/(b-a)))
    return u*u*(3.-2.*u)


def blend(a,b,t):
    if t <= .00001:
        return a
    if t >= .99999:
        return b
    result={k:v*(1-t) for k,v in a.items()}
    for k,v in b.items():
        result[k]=result.get(k,0)+v*t
    return result


def one(name):
    return {name:1.0}


def leg(x,y,z,side):
    knee=bones['calf_'+side][0].z
    ankle=bones['foot_'+side][0].z
    front=bones['ball_'+side][0].y
    foot=blend(one('foot_'+side),one('ball_'+side),
               (1-smooth(front-.033,front+.014,y))*(1-smooth(-.043,-.013,z)))
    w=blend(foot,one('calf_'+side),smooth(ankle-.020,ankle+.039,z))
    return blend(w,one('thigh_'+side),smooth(knee-.048,knee+.048,z))


def arm(z, side):
    wrist=bones['hand_'+side][0].z
    elbow=bones['lowerarm_'+side][0].z
    shoulder=bones['upperarm_'+side][0].z
    w=blend(one('hand_'+side),one('lowerarm_'+side),smooth(wrist-.022,wrist+.025,z))
    w=blend(w,one('upperarm_'+side),smooth(elbow-.026,elbow+.027,z))
    return blend(w,one('clavicle_'+side),smooth(shoulder-.014,shoulder+.033,z))


# The original wraps narrow shrine ornaments very close to the arms and
# calves. Isolate the actual limb surfaces below the shoulder and hip seams.
# Coincident UV splits share nodes here, while the exported mesh stays intact.
lookup={}
positions=[]
indices=[]
for co in coords:
    key=tuple(round(v*50000) for v in co)
    q=lookup.get(key)
    if q is None:
        q=len(positions)
        lookup[key]=q
        positions.append(co)
    indices.append(q)
adj=[set() for _ in positions]
for edge in mesh.data.edges:
    a,b=(indices[i] for i in edge.vertices)
    if a!=b:
        adj[a].add(b)
        adj[b].add(a)


def surface(seed, contains):
    seed=Vector(seed)
    allowed={i for i,point in enumerate(positions) if contains(*point)}
    first=min(allowed,key=lambda i:(positions[i]-seed).length_squared)
    seen={first}
    pending=[first]
    while pending:
        for neighbor in adj[pending.pop()] & allowed - seen:
            seen.add(neighbor)
            pending.append(neighbor)
    return seen


def feather(region, width):
    """Ease a surface mask across welded attachments by distance along the mesh."""
    def boundary_distances(inside):
        border={i for i in inside if adj[i]-inside}
        dist=dict.fromkeys(border,0.0)
        pending=[(0.0,i) for i in border]
        while pending:
            depth,i=heappop(pending)
            if depth>dist[i]:
                continue
            for neighbor in adj[i] & inside:
                candidate=depth+(positions[neighbor]-positions[i]).length
                if candidate<dist.get(neighbor,width):
                    dist[neighbor]=candidate
                    heappush(pending,(candidate,neighbor))
        return dist

    outside=set(range(len(positions)))-region
    dist_in,dist_out=boundary_distances(region),boundary_distances(outside)
    return {
        **{i:smooth(-width,width,dist_in.get(i,width)) for i in region},
        **{i:smooth(-width,width,-d) for i,d in dist_out.items()},
    }


arm_surfaces={}
leg_surfaces={}
for side,direction in (('l',1),('r',-1)):
    elbow=bones['lowerarm_'+side][0]
    arm_surfaces[side]=surface(
        elbow+Vector((0,-.026,-.006)),
        lambda x,y,z: direction*(x-.154)>.055 and y<-.026 and z<.501)
    ankle=bones['foot_'+side][0]
    leg_surfaces[side]=surface(
        ankle+Vector((0,-.036,-.025)),
        lambda x,y,z: direction*(x-.154)>.018 and y<.090 and z<.287)
    for label,region in (('arm',arm_surfaces[side]),('leg',leg_surfaces[side])):
        print('PENANCE_LIMB_SURFACE',label,side,len(region),
              [(round(min(positions[i][axis] for i in region),4),
                round(max(positions[i][axis] for i in region),4)) for axis in range(3)])
        assert len(region)>100, (label,side)
    arm_surfaces[side]=feather(arm_surfaces[side],.038)
    leg_surfaces[side]=feather(leg_surfaces[side],.045)


def weights(index,p):
    x,y,z=p
    side='l' if x>=.154 else 'r'
    lateral=abs(x-.154)
    w=blend(leg(x,y,z,'r'),leg(x,y,z,'l'),smooth(.115,.192,x))
    w=blend(w,one('pelvis'),smooth(.275,.369,z))
    for lower,higher,a,b in (
        ('pelvis','spine_01',.356,.435),('spine_01','spine_02',.427,.503),
        ('spine_02','spine_03',.49,.561),('spine_03','neck_01',.551,.605),
    ):
        w=blend(w,one(higher),smooth(a,b,z))
    head_mask=(1-smooth(-.116,-.065,y))*smooth(.475,.556,z)*(1-smooth(.064,.099,lateral))
    w=blend(w,one('head'),head_mask)

    # Let the surface masks control the lower limbs and blend into the
    # continuous shoulder and hip skin at their attachments.
    leg_mask=max(mask.get(index,0.) for mask in leg_surfaces.values())
    hip=(1-smooth(.035,.093,y))*(1-smooth(.096,.160,lateral))
    leg_mask=leg_mask+(hip-leg_mask)*smooth(.235,.292,z)
    # Below the hanging ornaments, the complete heel and sole follow the foot.
    leg_mask=max(leg_mask,1-smooth(-.021,.012,z))
    legs_to_body=max(leg_mask,smooth(.339,.447,z))
    w=blend(one('shrine_mount'),w,legs_to_body)

    threshold=.111-.068*smooth(.415,.565,z)
    shoulder_mask=(smooth(threshold-.025,threshold+.022,lateral)
        *smooth(-.196,-.147,y)*(1-smooth(-.072,-.015,y))*(1-smooth(.56,.620,z)))
    arm_mask=arm_surfaces[side].get(index,0.)
    arm_mask=arm_mask+(shoulder_mask-arm_mask)*smooth(.467,.499,z)
    arm_mask*=1-smooth(-.036,.012,y)*(1-smooth(.477,.548,z))

    # Central front veil follows the hood at its attachment and can flex in
    # two sections. The upper bells and framework retain a rigid chest mount.
    veil=(1-smooth(.058,.087,lateral))*(1-smooth(-.135,-.108,y))*smooth(.01,.046,z)*(1-smooth(.485,.558,z))
    veil_attachment=(1-smooth(.060,.108,lateral))*(1-smooth(-.137,-.102,y))*smooth(.36,.47,z)*(1-smooth(.542,.624,z))
    w=blend(w,one('head'),veil_attachment)
    veil_chain=blend(one('veil_02'),one('veil_01'),smooth(.268,.396,z))
    w=blend(w,veil_chain,veil)
    shrine_high=smooth(.623,.662,z)
    shrine_back=smooth(.079,.117,y)*smooth(.23,.37,z)
    shrine_sides=smooth(.114,.165,lateral)*smooth(-.068,-.019,y)*smooth(.237,.34,z)
    shrine_upper=smooth(-.040,.019,y)*smooth(.373,.562,z)
    shrine=max(shrine_high,shrine_back,shrine_sides,shrine_upper)
    w=blend(w,one('shrine_mount'),shrine)
    w=blend(w,arm(z,side),arm_mask)

    # Pendant handle stays attached near the grip. The entire metal bell,
    # including its clapper, takes the same rigid transform below the handle.
    bell=arm_mask*(1-smooth(.263,.296,z)) if side=='r' else 0
    return blend(w,one('bell_r'),bell)


weights_by_position=[weights(i,point) for i,point in enumerate(positions)]
smoothed=[]
for a,source in enumerate(weights_by_position):
    w=source
    if adj[a] and max(source.get('shrine_mount',0),source.get('bell_r',0))<.997:
        neighbors=defaultdict(float)
        for b in adj[a]:
            for name,weight in weights_by_position[b].items():
                neighbors[name]+=weight/len(adj[a])
        w=blend(source,neighbors,.17)
    top=sorted(((name,v) for name,v in w.items() if v>.0005),key=lambda q:-q[1])[:4]
    total=sum(v for _,v in top)
    smoothed.append([(name,v/total) for name,v in top])

# Rounded buckets batch Blender API assignment and keep exact weights at seams.
buckets=defaultdict(list)
for i,q in enumerate(indices):
    row=smoothed[q]
    steps=[round(v*10000) for _,v in row]
    steps[0]+=10000-sum(steps)
    for (name,_),v in zip(row,steps):
        if v:
            buckets[name,v].append(i)
for (name,value),verts in buckets.items():
    groups[name].add(verts,value/10000.,'REPLACE')

base=mesh.data.materials[0]
image=next(link.from_node.image for link in base.node_tree.links
           if link.from_node.type=='TEX_IMAGE' and link.to_socket.name=='Base Color')
texture_path.write_bytes(image.packed_file.data)
for node in base.node_tree.nodes:
    if (node.type=='TEX_IMAGE' and node.image and node.image.packed_file
            and node.image.packed_file.data==image.packed_file.data):
        node.image=image
image.unpack(method='REMOVE')
image.filepath=str(texture_path)
image.pack()
principled=next(node for node in base.node_tree.nodes if node.type=='BSDF_PRINCIPLED')
print('PENANCE_SOURCE_SURFACE', [(key,principled.inputs[key].default_value)
                                for key in ('Metallic','Roughness','Specular IOR Level')])

# Express the same physical size in centimeters before export. A one-unit
# scene with meter-authored coordinates would otherwise import a scaled root.
cm_per_meter=100.
centimeters=Matrix.Scale(cm_per_meter,4)
mesh.data.transform(centimeters)
armature.transform(centimeters)
scene.unit_settings.scale_length=1/cm_per_meter

# World axes are converted to the source rest bone axes so posing is independent
# of the rest roll and remains symmetrical for the limbs.
def turn(name,axis,degrees):
    pb=rig.pose.bones[name]
    local_axis=armature.bones[name].matrix_local.to_quaternion().inverted() @ Vector(axis)
    pb.rotation_quaternion=Quaternion(local_axis,radians(degrees)) @ pb.rotation_quaternion


def reset():
    for pb in rig.pose.bones:
        pb.rotation_mode='QUATERNION'
        pb.rotation_quaternion=Quaternion((1,0,0,0))
        pb.location=(0,0,0)
        pb.scale=(1,1,1)


X,Y,Z=(1,0,0),(0,1,0),(0,0,1)
poses=[
    ('Neutral',1,[]),
    ('Arms_Raised',20,[('clavicle_l',Y,-10),('clavicle_r',Y,10),('upperarm_l',Y,-51),('upperarm_r',Y,51),
                      ('lowerarm_l',X,-11),('lowerarm_r',X,-13),('bell_r',Y,-26)]),
    ('Knees_Bent',40,[('thigh_l',X,-27),('thigh_r',X,-27),('calf_l',X,46),('calf_r',X,46),
                     ('foot_l',X,-19),('foot_r',X,-19),('spine_01',X,6),('veil_01',X,-9)]),
    ('Walking_Stance',60,[('thigh_l',X,-23),('thigh_r',X,17),('calf_l',X,13),('calf_r',X,24),
                         ('foot_l',X,4),('foot_r',X,-20),('ball_r',X,14),('spine_02',Z,6),
                         ('upperarm_l',X,15),('upperarm_r',X,-18),('lowerarm_r',X,-9),('veil_02',Y,5)]),
    ('Chase_Lean',80,[('spine_01',X,8),('spine_02',X,7),('spine_03',X,6),
                     ('neck_01',X,-8),('head',X,-4),('thigh_l',X,-25),('thigh_r',X,21),
                     ('calf_l',X,16),('calf_r',X,36),('foot_r',X,-20),('upperarm_l',X,15),
                     ('upperarm_r',X,-24),('lowerarm_r',X,-24),('veil_01',X,-7),('veil_02',X,6)]),
    ('Reach_Attack',100,[('spine_01',X,9),('spine_02',Z,-7),('upperarm_l',X,-61),
                        ('upperarm_l',Y,-9),('lowerarm_l',X,-19),('hand_l',X,14),
                        ('upperarm_r',X,-27),('lowerarm_r',X,-19),('bell_r',X,24),
                        ('thigh_l',X,-13),('calf_l',X,14),('veil_02',X,7)]),
    ('Neutral_Return',120,[]),
]
for marker in list(scene.timeline_markers):
    scene.timeline_markers.remove(marker)
scene.frame_start,scene.frame_end=1,120
for label,frame,rotations in poses:
    scene.frame_set(frame)
    reset()
    for bone,axis,degrees in rotations:
        turn(bone,axis,degrees)
    if label=='Knees_Bent':
        pb=rig.pose.bones['pelvis']
        pb.location=armature.bones['pelvis'].matrix_local.to_quaternion().inverted() @ Vector((0,2.2,-3.7))
    scene.timeline_markers.new(label,frame=frame)
    for pb in rig.pose.bones:
        pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name)
        if pb.name=='pelvis':
            pb.keyframe_insert('location',frame=frame,group=pb.name)
action=rig.animation_data.action
action.name='Penance_Rig_Review'
action.use_fake_user=True
scene.frame_set(1)
bpy.context.view_layer.update()
rig['rig_notes']='Timeline markers select the six test poses. The root is grounded and unweighted. Bell and shrine are rigid attachments. Rest length is preserved.'
rig['source_height_cm']=round(100*(maximum[2]-minimum[2]),4)

# Export only the skinned object and armature in centimeters, with identity
# object scales. No control objects or end bones.
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
mesh.select_set(True)
bpy.context.view_layer.objects.active=rig
# The packed source image is also wired to alpha. Its pixels are effectively
# opaque, so export one texture connection to avoid duplicate FBX texture nodes.
extra_image_links=[(link.from_socket,link.to_socket) for link in base.node_tree.links
                   if link.from_node.type=='TEX_IMAGE' and link.from_node.image==image
                   and link.to_socket.name!='Base Color']
for link in list(base.node_tree.links):
    if (link.from_socket,link.to_socket) in extra_image_links:
        base.node_tree.links.remove(link)
bpy.ops.export_scene.fbx(filepath=str(fbx_path),use_selection=True,object_types={'ARMATURE','MESH'},
    add_leaf_bones=False,use_armature_deform_only=False,axis_forward='-Y',axis_up='Z',
    apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,
    mesh_smooth_type='FACE',bake_anim=False,path_mode='RELATIVE',embed_textures=False)
for source_socket,target_socket in extra_image_links:
    base.node_tree.links.new(source_socket,target_socket)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active=rig
for area in bpy.context.screen.areas if bpy.context.screen else ():
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_location=Vector((0,0,51.))
        area.spaces.active.region_3d.view_distance=185.
        area.spaces.active.region_3d.view_rotation=Vector((1.35,-1.7,.44)).to_track_quat('Z','Y')
        area.spaces.active.shading.color_type='TEXTURE'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path),compress=True)

# Optional animation-only export for the temporary Unreal pose check.
if len(sys.argv)>sys.argv.index('--')+3:
    bpy.ops.export_scene.fbx(filepath=sys.argv[sys.argv.index('--')+3],use_selection=True,
        object_types={'ARMATURE'},add_leaf_bones=False,use_armature_deform_only=False,
        axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',
        bake_space_transform=False,bake_anim=True,bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,bake_anim_simplify_factor=0.,path_mode='RELATIVE')

def evaluated(frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [v.co.copy() for v in ev.data.vertices]

rest=evaluated(1)
edge_list=[(a,b,(rest[a]-rest[b]).length) for a,b in (tuple(e.vertices) for e in mesh.data.edges)]
pose_results={}
for label,frame,_ in poses:
    sample=evaluated(frame)
    distances=sorted((sample[i]-v).length for i,v in enumerate(rest))
    ratios=sorted((sample[a]-sample[b]).length/length for a,b,length in edge_list if length>.15)
    pose_results[label]={'max_vertex_movement_cm':distances[-1],
        'edge_stretch_p99':ratios[int(len(ratios)*.99)],'edges_over_1_5x':sum(r>1.5 for r in ratios)}
    longest=max(edge_list,key=lambda edge:(sample[edge[0]]-sample[edge[1]]).length-edge[2])
    print('PENANCE_POSE_EDGE',label,[(tuple(round(value,3) for value in coords[i]),smoothed[indices[i]])
                                   for i in longest[:2]])
assert pose_results['Neutral_Return']['max_vertex_movement_cm']<.0001
assert len(mesh.data.vertices)==vertex_count and len(mesh.data.polygons)==face_count
assert [uv.name for uv in mesh.data.uv_layers]==existing_uvs
assert [m.name for m in mesh.data.materials]==existing_slots
assert all(1<=len(v.groups)<=4 and abs(sum(g.weight for g in v.groups)-1.)<.0002 for v in mesh.data.vertices)
audit={'source_height_cm':rig['source_height_cm'],'vertices':vertex_count,'faces':face_count,
       'bones':list(bones),'material_slots':existing_slots,'uv_layers':existing_uvs,
       'fps':scene.render.fps/scene.render.fps_base,'poses':pose_results}
(review/'Blender_Rig_Checks.json').write_text(json.dumps(audit,indent=2)+'\n')
print('PENANCE_BLENDER_RIG_PASSED',json.dumps(audit))

# Render the evaluated original material and geometry without saving review
# cameras into the deliverable. The render scene shares keyed rig and mesh data.
preview=scene
preview.render.engine='BLENDER_WORKBENCH'
preview.display.shading.light='STUDIO'
preview.display.shading.color_type='TEXTURE'
preview.display.shading.show_cavity=True
preview.display.shading.cavity_type='BOTH'
preview.display.shading.background_type='WORLD'
preview.world=bpy.data.worlds.new('Rig Review Background')
preview.world.color=(.075,.075,.075)
preview.view_settings.view_transform='Standard'
camera=bpy.data.objects.new('Review Camera',bpy.data.cameras.new('Review Lens'))
preview.collection.objects.link(camera)
preview.camera=camera
camera.location=(96,-165,68)
camera.rotation_euler=(Vector((0,0,49))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type='ORTHO'
camera.data.ortho_scale=144
preview.render.resolution_x=720
preview.render.resolution_y=850
preview.render.resolution_percentage=100
for name,frame,_ in poses[:-1]:
    preview.frame_set(frame)
    bpy.context.view_layer.update()
    preview.render.filepath=str(review/(name+'.png'))
    bpy.ops.render.render(write_still=True,scene=preview.name)
