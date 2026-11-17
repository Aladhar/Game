"""Create the independent V4 review map in Unreal 5.7.4.

Run with -EnablePlugins=GeometryScripting -run=pythonscript -script=<this file>.
Generated geometry is saved as regular Static Mesh assets. Geometry Scripting is
needed to build, not to open or play the map. Existing maps are never overwritten.
"""
from pathlib import Path
import math
import sys

import unreal as ue

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Penance_Town_V4_Design as plan

assets = ue.get_editor_subsystem(ue.EditorAssetSubsystem)
level = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actor_api = ue.get_editor_subsystem(ue.EditorActorSubsystem)
tools = ue.AssetToolsHelpers.get_asset_tools()
cube = ue.load_asset('/Engine/BasicShapes/Cube')
cone = ue.load_asset('/Engine/BasicShapes/Cone')
palette = {
    'Terrain': '486052', 'Residential': 'B99878', 'Commerce': 'CAA463',
    'Civic': '7BABAA', 'Cemetery':'97A58A', 'Green':'8AA479', 'Estate':'B79BC4',
    'Utility':'8DA4B7', 'Boundary':'C0C7A8', 'Reserve':'8F9F9C',
    'main':'3A414A', 'residential':'505960', 'service':'576F6D', 'path':'B5B8B0',
    'Creek':'327A92', 'Bridge':'9A9A8C', 'Stone':'707873', 'Woods':'354E3C',
    'Proxy':'CBC1DB', 'FosterScreen':'405B47',
}
materials = {}


def save(asset):
    if not assets.save_loaded_asset(asset, False):
        raise RuntimeError('Could not save ' + asset.get_path_name())


def material(key):
    if key in materials:
        return materials[key]
    folder = plan.GENERATED + '/Materials'
    name = 'M_V4_' + key
    path = folder + '/' + name
    if assets.does_asset_exist(path):
        result = assets.load_asset(path)
    else:
        result = tools.create_asset(name, folder, ue.Material, ue.MaterialFactoryNew())
        if not result:
            raise RuntimeError('Could not create ' + path)
        edit = ue.MaterialEditingLibrary
        color = edit.create_material_expression(result, ue.MaterialExpressionConstant3Vector, -340, -40)
        components = [int(palette[key][i:i+2],16)/255 for i in (0,2,4)]
        rgb = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in components]
        color.set_editor_property('constant', ue.LinearColor(*rgb,1))
        edit.connect_material_property(color,'',ue.MaterialProperty.MP_BASE_COLOR)
        rough = edit.create_material_expression(result,ue.MaterialExpressionConstant,-340,125)
        rough.set_editor_property('r',.94)
        edit.connect_material_property(rough,'',ue.MaterialProperty.MP_ROUGHNESS)
        result.set_editor_property('two_sided',True)
        edit.recompile_material(result)
        save(result)
    materials[key]=result
    return result


def spawn(cls,name,folder,xyz,rotation=None):
    actor = actor_api.spawn_actor_from_class(cls,ue.Vector(*xyz),rotation or ue.Rotator())
    if not actor:
        raise RuntimeError('Could not spawn ' + name)
    actor.set_actor_label('V4_' + name)
    actor.set_folder_path(ue.Name(plan.FOLDERS[folder]))
    return actor


def set_mesh(actor,mesh,color,collision):
    c=actor.get_editor_property('static_mesh_component')
    c.set_static_mesh(mesh)
    c.set_material(0,material(color))
    c.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
    actor.set_actor_enable_collision(collision)
    return actor


def box(name,folder,rect,top,depth,color,collision=False,mesh=None):
    cx,cy=plan.rect_center(rect)
    a=spawn(ue.StaticMeshActor,name,folder,plan.uu(cx,cy,top-depth*.5))
    a.set_actor_scale3d(ue.Vector(rect[2],rect[3],depth))  # Engine primitives are 100 UU per axis.
    return set_mesh(a,mesh or cube,color,collision)


def static_surface(name,folder,vertices,faces,color,collision):
    origin=plan.uu(vertices[0][0],vertices[0][1],0)
    path=plan.GENERATED+'/Meshes/SM_V4_'+name
    mesh=assets.load_asset(path) if assets.does_asset_exist(path) else None
    if mesh is None:
        dm=ue.DynamicMesh()
        buffers=ue.GeometryScriptSimpleMeshBuffers()
        world=[plan.uu(*p) for p in vertices]
        buffers.set_editor_property('vertices',[ue.Vector(x-origin[0],y-origin[1],z) for x,y,z in world])
        buffers.set_editor_property('triangles',[ue.IntVector(*f) for f in faces])
        buffers.set_editor_property('uv0',[ue.Vector2D(p[0]*.1,p[1]*.1) for p in vertices])
        ue.GeometryScript_MeshEdits.append_buffers_to_mesh(dm,buffers)
        opts=ue.GeometryScriptCreateNewStaticMeshAssetOptions()
        opts.set_editor_property('enable_recompute_normals',True)
        opts.set_editor_property('enable_recompute_tangents',True)
        opts.set_editor_property('enable_collision',collision)
        if collision:
            opts.set_editor_property('collision_mode',ue.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        mesh,outcome=ue.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm,path,opts)
        if not mesh or outcome != ue.GeometryScriptOutcomePins.SUCCESS:
            raise RuntimeError(f'Geometry Script could not create {path}: {outcome}')
        save(mesh)
    a=spawn(ue.StaticMeshActor,name,folder,origin)
    return set_mesh(a,mesh,color,collision)


def add_grid(vertices,faces,rows):
    """Append a row-major rectangular patch. Indices follow Unreal top-face winding."""
    base=len(vertices)
    columns=len(rows[0])
    for row in rows:
        vertices.extend(row)
    for j in range(len(rows)-1):
        for i in range(columns-1):
            a=base+j*columns+i
            b=a+1
            c=a+columns
            d=c+1
            faces.extend(((a,b,d),(a,d,c)))


def ribbon(points,width,z_func,lateral=0,step=1.5,across=1):
    """Mitered ribbon sampled along and across the centerline, in plan-space meters."""
    points = [p for i,p in enumerate(points) if not i or math.dist(points[i-1],p)>.04]
    rows=[]
    normals=[]
    for a,b in zip(points,points[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1]
        d=math.hypot(dx,dy)
        normals.append((-dy/d,dx/d))
    for i,(a,b) in enumerate(zip(points,points[1:])):
        cx,cy=normals[i]
        count=max(1,math.ceil(math.dist(a,b)/step))
        for j in range(count+(i==len(points)-2)):
            t=j/count
            px,py=plan.mix(a[0],b[0],t),plan.mix(a[1],b[1],t)
            nx,ny=cx,cy
            if j==0 and i:
                ax,ay=normals[i-1]
                denom=max(.45,1+ax*cx+ay*cy)
                nx,ny=(ax+cx)/denom,(ay+cy)/denom
            row=[]
            for col in range(across+1):
                offset=lateral+width*(col/across-.5)
                x=min(plan.WIDTH,max(0,px+nx*offset))
                y=min(plan.HEIGHT,max(0,py+ny*offset))
                row.append((x,y,z_func(x,y)))
            rows.append(row)
    return rows


def add_ribbon(vertices,faces,*args,**kwargs):
    # Rows travel the line, columns travel toward its left normal. Reverse the
    # columns for the same plan-space winding as the terrain patches.
    rows=ribbon(*args,**kwargs)
    add_grid(vertices,faces,[row[::-1] for row in rows])


def surface_ribbon(name,folder,points,width,color,terrain,lift=.07,collision=False):
    v,f=[],[]
    add_ribbon(v,f,points,width,lambda x,y:terrain.surface(x,y)+lift,across=max(1,math.ceil(width)))
    return static_surface(name,folder,v,f,color,collision)


def text(label,x,y,z,size=2.3):
    actor=spawn(ue.TextRenderActor,'Label_'+label,11,plan.uu(x,y,z),ue.Rotator(90,90,0))
    c=actor.get_component_by_class(ue.TextRenderComponent)
    c.set_text(label.replace('_',' '))
    c.set_world_size(size*100)
    c.set_horizontal_alignment(ue.HorizTextAligment.EHTA_CENTER)
    c.set_text_render_color(ue.Color(245,245,230,255))
    actor.set_actor_enable_collision(False)
    return actor


def rectangle_path(rect,close=True):
    x,y,w,d=rect
    p=[(x,y),(x+w,y),(x+w,y+d),(x,y+d)]
    return p+[p[0]] if close else p


def camera(name,location,target,ortho_width=None):
    eye=ue.Vector(*plan.uu(*location))
    to=ue.Vector(*plan.uu(*target))
    rot=ue.Rotator(pitch=-90,yaw=90,roll=0) if ortho_width else ue.MathLibrary.find_look_at_rotation(eye,to)
    a=spawn(ue.CameraActor,'Review_'+name,11,(eye.x,eye.y,eye.z),rot)
    c=a.get_component_by_class(ue.CameraComponent)
    c.set_editor_property('constrain_aspect_ratio',False)
    if ortho_width:
        c.set_editor_property('projection_mode',ue.CameraProjectionMode.ORTHOGRAPHIC)
        c.set_editor_property('ortho_width',ortho_width*100)
        c.set_editor_property('auto_calculate_ortho_planes',False)
        c.set_editor_property('update_ortho_planes',False)
        c.set_editor_property('ortho_near_clip_plane',0.)
        c.set_editor_property('ortho_far_clip_plane',180000.)
    return a


def main():
    if assets.does_asset_exist(plan.MAP):
        raise RuntimeError('Refusing to overwrite saved map ' + plan.MAP)
    terrain=plan.Terrain()
    if not level.new_level(plan.MAP, is_partitioned_world=False):
        raise RuntimeError('Could not create new non-partitioned level')
    print('V4_BUILD_TERRAIN')
    for ix in range(4):
        for iy in range(4):
            v,f=[],[]
            add_grid(v,f,[[(x,y,terrain.surface(x,y)) for x in range(ix*120,ix*120+121,2)]
                          for y in range(iy*150,iy*150+151,2)])
            static_surface(f'Terrain_{ix}_{iy}',0,v,f,'Terrain',True)
    surface_ribbon('PlanningBounds',0,rectangle_path((0,0,480,600)),.25,'Boundary',terrain,.13)
    print('V4_BUILD_ROADS')
    sidewalks_v,sidewalks_f=[],[]
    for key,r in plan.ROADS.items():
        points=plan.route_points(key)
        kind=r['kind']
        surface_ribbon('Road_'+plan.ROAD_NAMES[key],1,points,r['width'],kind,
                       terrain,{'main':.09,'residential':.07,'service':.055,'path':.035}[kind],kind!='path')
        if kind in ('main','residential') and key not in ('R_NORTH',):
            walk=points if key!='R_MAIN' else points[:5]
            for side in (-1,1):
                add_ribbon(sidewalks_v,sidewalks_f,walk,1.45,lambda x,y:terrain.surface(x,y)+.045,
                           lateral=side*(r['width']/2+.73),across=2)
    static_surface('Sidewalks_Public',1,sidewalks_v,sidewalks_f,'path',False)
    surface_ribbon('OldFootbridge_NorthApproach',2,[(97,135),(91,111)],2,'path',terrain,.10)
    for key,(width,points) in plan.EXTRA_PATHS.items():
        surface_ribbon('Path_'+key,1,points,width,'service' if width>=3 else 'path',terrain,.045)

    v,f=[],[]
    path=[(0,plan.creek_y(0)), *[p for p in plan.CREEK_SAMPLES if 0<p[0]<480], (480,plan.creek_y(480))]
    add_ribbon(v,f,path,10.9,lambda x,y:-2.92,step=2)
    static_surface('Creek_WaterReserve',2,v,f,'Creek',False)
    box('Creek_MainBridge',2,(261.5,135.88,7,27.24),3.09,.53,'Bridge',True)
    for x,side in ((261.5,'West'),(268.27,'East')):
        box('Bridge_Parapet_'+side,2,(x,136,.23,27),3.94,.85,'Stone',True)
    for y,side in ((136.1,'North'),(161.7,'South')):
        box('Bridge_Abutment_'+side,2,(261.45,y,7.1,1.2),2.59,1.9,'Stone',True)
    box('Old_Footbridge_Reserve',2,(95.8,135,2.4,27),1.6,.24,'Bridge')
    for y,side in ((135,'North'),(161.9,'South')):
        box('Old_Footbridge_Blocked_'+side,2,(95.25,y,3.5,.30),max(1.6,terrain.surface(97,y))+.75,.95,'Stone',True)

    print('V4_BUILD_PARCELS')
    category_folder={'Residential':3,'Commerce':7,'Civic':6,'Cemetery':6,'Green':6,'Estate':8,'Utility':9}
    for key,p in plan.PARCELS.items():
        rect=plan.parcel_rect(p)
        color=p['category']
        folder=category_folder[color]
        surface_ribbon(key+'_Parcel',folder,rectangle_path(rect),.22,color,terrain,.13)
        if key not in plan.PADS:
            x,y=plan.rect_center(rect)
            text(plan.NAMES[key],x,y,terrain.surface(x,y)+.25)
    for key,(rect,color) in plan.PADS.items():
        folder=4 if color=='Residential' else category_folder[color]
        z=plan.pad_grade(key,rect)
        box(key+'_Foundation',folder,rect,z+.16,.38,color,True)
        x,y=plan.rect_center(rect)
        text(plan.NAMES[key],x,y,z+.25,1.75 if color=='Commerce' else 2.15)
    for key,reserves in plan.RESERVES.items():
        z=plan.pad_grade(key,plan.PADS[key][0])
        for index,(kind,rect) in enumerate(reserves):
            box(key+'_'+kind+'_Reserve_'+str(index+1),5,rect,z+.10,.40,'Reserve',False)
        surface_ribbon(key+'_Driveway',3,plan.driveway(key),3.05,'path',terrain,.052)

    box('Civic_Square',6,(152,282,60,23),.11,.20,'Civic',True)
    text('Civic_Square',182,292,.2,2.4)
    for index,rect in enumerate(((304,225,84,.65),(304,225,.65,93),(387.35,225,.65,93),
                                  (304,317.35,44,.65),(352,317.35,36,.65)),1):
        box(f'Graveyard_Wall_{index:02d}',6,rect,3.64,.67,'Stone',True)
    for j in range(6):
        for x,w in ((313,31),(355,25)):
            box(f'Graveyard_Terrace_{j}_{x}',6,(x,236+j*9,w,1.3),3.06,.1,'Green')
    box('BriarLane_Fenced_End',3,(458.7,495.3,.26,9.4),terrain.surface(459,500)+1.45,1.5,'Stone',True)
    text('Briar_Lane',336,496,terrain.surface(336,496)+.2,2.5)
    text('Town_Arrival',232,583,terrain.surface(232,583)+.3,2.5)
    text('Main_Street',232,389,terrain.surface(232,389)+.2,2.1)

    # Outline reserve uses in the larger sites. None are finished buildings.
    for name,folder,rect,color in (
        ('School_Play_Yard',6,(106,188,33,24),'Green'),
        ('Gas_Pump_Island',7,(190,464,12,11),'Commerce'),
        ('Church_Front_Courtyard',8,(164.5,81,45,15),'Estate'),
        ('Foster_Rear_Garden',8,(364,34,18,22),'Green'),
        ('WaterTower_Service_Yard',9,(72,55,21,19),'Utility'),
        ('WaterTower_Woodland',9,(21,22,60,25),'Green'),
        ('Roadside_Sign_Reserve',9,(240,574,3,2),'Utility'),
        ('Foster_Storage_Reserve',8,(350,83,9,8),'Reserve'),
    ):
        surface_ribbon(name,folder,rectangle_path(rect),.23,color,terrain,.11)

    for name,rect,top,depth in (
        ('TEMP_Church_BellTower',(184.5,54.5,7,7),40,28),
        ('TEMP_Foster_House_Mass',(317,53,28,22),21,11),
        ('TEMP_WaterTower_Stanchion',(59.8,48.8,4.4,4.4),42,22),
        ('TEMP_WaterTower_Tank',(56,45,12,12),49,7),
    ):
        box(name,10,rect,top,depth,'Proxy')
    for i in range(14):
        x=281+i*5.45
        y=96+3.5*math.sin(i*.8)
        if i in (5,6):  # Leave the bridge approach view open.
            continue
        base=terrain.surface(x,y)
        height=15 if i in (7,8) else 9
        screen=box(f'TEMP_Foster_Screen_{i:02d}',10,(x-3.4,y-3.4,6.8,6.8),base+height,height,'FosterScreen',False,cone)
        component=screen.get_component_by_class(ue.StaticMeshComponent)
        screen.set_actor_enable_collision(True)
        # Built-in query profile blocks visibility traces and overlaps the pawn.
        component.set_collision_profile_name('UI')
    for i in range(22):
        x,y=(23+(i%8)*10,16+(i//8)*8) if i<16 else (462+(i%2)*6,472+(i-16)*10)
        base=terrain.surface(x,y)
        box(f'TEMP_Woodland_{i:02d}',10,(x-2.7,y-2.7,5.4,5.4),base+6.5,6.5,'Woods',False,cone)

    for name,x,y in (('Town_Square',230,323),('Park_Overlook',134,261),('Bridge_Approach',265,173),
                     ('Graveyard_Gate',300,330),('Briar_End',453,500),('Arrival',232,572)):
        a=spawn(ue.TargetPoint,'Sightline_'+name,11,plan.uu(x,y,terrain.surface(x,y)+1.65))
        a.set_actor_enable_collision(False)

    for name,eye,target,ortho in (
        ('TopDown',(240,300,720),(240,300,0),650),
        ('Terrain',(530,615,270),(235,300,0),None),
        ('Residential',(20,505,78),(95,395,0),None),
        ('TownCenter',(366,385,73),(247,287,0),None),
        ('Estate',(280,145,66),(259,62,12),None),
        ('MainBridge',(291,176,19),(262,145,3),None),
        ('WaterTower',(126,120,52),(61,54,20),None),
        ('BriarLane',(307,510,20),(449,500,5),None),
        ('ChurchSightline',(230,323,1.65),(188,58,36),None),
        ('FosterSightline',(265,173,terrain.surface(265,173)+1.65),(332,61,18),None),
        ('TowerSightline',(134,261,terrain.surface(134,261)+1.65),(62,51,46),None),
    ):
        camera(name,eye,target,ortho)
    start=(232,581)
    spawn(ue.PlayerStart,'South_Entrance_PlayerStart',12,
          plan.uu(*start,terrain.surface(*start)+1.00),ue.Rotator(pitch=0,yaw=90,roll=0))
    spawn(ue.DirectionalLight,'Daylight',0,plan.uu(240,300,40),ue.Rotator(-51,-36,0)
          ).get_component_by_class(ue.DirectionalLightComponent).set_intensity(3.0)
    sky=spawn(ue.SkyLight,'Sky_Fill',0,plan.uu(240,300,100))
    sky.get_component_by_class(ue.SkyLightComponent).set_intensity(1.25)
    spawn(ue.SkyAtmosphere,'Sky_Atmosphere',0,(0,0,-200))
    ue.get_editor_subsystem(ue.UnrealEditorSubsystem).set_level_viewport_camera_info(
        ue.Vector(*plan.uu(530,615,270)),ue.MathLibrary.find_look_at_rotation(
            ue.Vector(*plan.uu(530,615,270)),ue.Vector(*plan.uu(235,300))))
    if not ue.EditorLoadingAndSavingUtils.save_current_level():
        raise RuntimeError('Could not save ' + plan.MAP)
    print('PENANCE_V4_MAP_SAVED',plan.MAP,len(actor_api.get_all_level_actors()))


main()
