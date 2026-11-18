"""Create the independent V5 review map in Unreal 5.7.4.

Run with -EnablePlugins=GeometryScripting -run=pythonscript -script=<this file>.
Generated geometry is saved as regular Static Mesh assets. Geometry Scripting is
needed to build, not to open or play the map. Existing maps are never overwritten.
"""
from pathlib import Path
import math
import sys

import unreal as ue

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Penance_Town_V5_Design as plan

assets = ue.get_editor_subsystem(ue.EditorAssetSubsystem)
level = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actor_api = ue.get_editor_subsystem(ue.EditorActorSubsystem)
tools = ue.AssetToolsHelpers.get_asset_tools()
cube = ue.load_asset('/Engine/BasicShapes/Cube')
cone = ue.load_asset('/Engine/BasicShapes/Cone')
palette = {
 'Terrain':'586655','Residential':'A8A599','Commerce':'A98C71','Civic':'849A9A',
 'Estate':'A49DB1','Utility':'909494','Stone':'777E77','Woods':'354B39','Trunk':'605340',
 'Roof':'59616B','Glass':'47616A','Lit':'E6BE72','Path':'B9B2A0','Creek':'3C7180',
 'Bridge':'9C9C90','main':'424950','residential':'515860','service':'69716B','path':'ABA998',
 'Metal':'686D73','White':'D7D6C8','Dark':'303D40','Leaf':'6D775C'}
materials = {}


def save(asset):
    if not assets.save_loaded_asset(asset, False):
        raise RuntimeError('Could not save ' + asset.get_path_name())


def material(key):
    if key in materials:
        return materials[key]
    folder = plan.GENERATED + '/Materials'
    name = 'M_V5_' + key
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
    actor.set_actor_label('V5_' + name)
    actor.set_folder_path(ue.Name(plan.FOLDERS[folder]))
    light=actor.get_component_by_class(ue.LightComponentBase)
    if light:
        light.set_mobility(ue.ComponentMobility.MOVABLE)
        if isinstance(light,ue.DirectionalLightComponent):
            main=name=='Afternoon_Light'
            light.set_forward_shading_priority(2 if main else 0)
            light.set_atmosphere_sun_light(main)
            if main:light.set_atmosphere_sun_light_index(0)
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
    path=plan.GENERATED+'/Meshes/SM_V5_'+name
    mesh=assets.load_asset(path) if assets.does_asset_exist(path) else None
    if mesh is None:
        dm=ue.DynamicMesh()
        buffers=ue.GeometryScriptSimpleMeshBuffers()
        world=[plan.uu(*p) for p in vertices]
        buffers.set_editor_property('vertices',[ue.Vector(x-origin[0],y-origin[1],z) for x,y,z in world])
        buffers.set_editor_property('triangles',[ue.IntVector(f[0],f[2],f[1]) for f in faces])
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
        body=mesh.get_editor_property('body_setup')
        if body:body.set_editor_property('double_sided_geometry',True)
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
    actor=spawn(ue.TextRenderActor,'Label_'+label,11,plan.uu(x,y,z),ue.Rotator(pitch=90,yaw=90,roll=0))
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
    a=spawn(ue.CameraActor,'Review_'+name,10,(eye.x,eye.y,eye.z),rot)
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


def obox(name,folder,center,size,color,collision=True,yaw=0):
 a=spawn(ue.StaticMeshActor,name,folder,plan.uu(*center),ue.Rotator(yaw=yaw))
 a.set_actor_scale3d(ue.Vector(*size));return set_mesh(a,cube,color,collision)
def local(b,x,y,z):
 c,s=math.cos(math.radians(b['yaw'])),math.sin(math.radians(b['yaw']))
 return(b['x']+c*x-s*y,b['y']+s*x+c*y,b['z']+z)
def part(b,key,offset,size,color,collision=True):
 return obox(b['id']+'_'+key,3 if b['category']=='Residential' else 6 if b['category']=='Estate' else 5 if b['category']=='Civic' else 4,local(b,*offset),size,color,collision,b['yaw'])
def roof(b):
 w,d,h,r=b['w']+.8,b['d']+.8,b['h'],b['roof']
 points=[(-w/2,-d/2,h),(w/2,-d/2,h),(0,-d/2,h+r),(-w/2,d/2,h),(w/2,d/2,h),(0,d/2,h+r)]
 faces=[(0,2,1),(3,4,5),(0,3,5),(0,5,2),(2,5,4),(2,4,1),(0,1,4),(0,4,3)]
 return static_surface(b['id']+'_GableRoof',3 if b['category']=='Residential' else 6 if b['category']=='Estate' else 4,[local(b,*p) for p in points],faces,'Roof',True)
def shell(b):
 w,d,h=b['w'],b['d'],b['h'];door=3.2 if b['id']=='CHURCH' else 1.35;dh=4.2 if b['id']=='CHURCH' else 2.3
 part(b,'WestWall',(-w/2,0,h/2),(.24,d,h),b['category'])
 part(b,'EastWall',(w/2,0,h/2),(.24,d,h),b['category'])
 part(b,'BackWall',(0,d/2,h/2),(w,.24,h),b['category'])
 for side in (-1,1):part(b,'Front_'+str(side),(side*(w+door)/4,-d/2,h/2),((w-door)/2,.24,h),b['category'])
 part(b,'Header',(0,-d/2,(h+dh)/2),(door,.24,h-dh),b['category'])
 if b['id']!='CHURCH':
  part(b,'Floor',(0,0,-.10),(w,d,.2),'Stone')
  if b['id']!='H01':part(b,'ClosedDoor',(0,-d/2-.02,dh/2),(door,.12,dh),'Dark')
 else:
  # A real opening over the east service stair, not a solid floor hiding it.
  for x,y,W,D in [(182,370,18,36),(195,375,4,26),(195,353.5,4,3)]:
   obox('Church_NaveFloor_'+str(x)+'_'+str(y),6,(x,y,9.9),(W,D,.2),'Stone')
 roof(b)
 # Glazed strips sit on the walls; original H01 interior remains streamed separately.
 for side in (-1,1):
  for j in range(2 if d<16 else 4):
   part(b,'Window_%s_%s'%(side,j),(side*(w/2+.13),-d*.30+j*d*.6/(1 if d<16 else 3),min(h-1,2.0)),(.03,1.3,1.3),'Lit' if b['id']=='H01' and side==-1 else 'Glass',False)
 if b['id'].startswith('H') and b['id'][1:].isdigit():
  part(b,'Porch',(0,-d/2-1,.06),(4.2,2,.12),'Stone')
  part(b,'PorchAwning',(0,-d/2-1,2.7),(4.5,2.5,.15),'Roof')
  for s in(-1,1):part(b,'PorchPost_'+str(s),(s*1.8,-d/2-1.7,1.35),(.15,.15,2.7),'White')
  # One garage or shed, varied to suit the lot.
  sx=-w/2-3.8;sy=d*.16
  part(b,'Outbuilding',(sx,sy,1.45),(4.2,5.2,2.9),'Residential')
  part(b,'OutbuildingRoof',(sx,sy,3),(4.6,5.6,.3),'Roof')
  # Rear fence in three stretches with an open side yard.
  part(b,'GardenFence',(0,d/2+5,.65),(w+9,.12,1.3),'Stone')
  part(b,'SideFence',(w/2+5,1,.65),(.12,d+7,1.3),'Stone')

def road_surface(name,pts,width,color,folder=1):
 v,f=[],[]
 # Keep explicit road/drive elevations; no nearest-road jumps at intersections.
 for a,b in zip(pts,pts[1:]):
  dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);nx,ny=-dy/L,dx/L
  n=max(1,math.ceil(L/2));rows=[]
  for i in range(n+1):
   t=i/n;x,y,z=(plan.mix(a[k],b[k],t) for k in range(3))
   rows.append([(x+nx*o,y+ny*o,z+.045) for o in (width/2,-width/2)])
  add_grid(v,f,rows)
 return static_surface(name,folder,v,f,color,True)
def sign(name,xyz,label,yaw=0,size=.4):
 a=spawn(ue.TextRenderActor,name,9,plan.uu(*xyz),ue.Rotator(yaw=yaw))
 c=a.get_component_by_class(ue.TextRenderComponent);c.set_text(label);c.set_world_size(size*100);c.set_horizontal_alignment(ue.HorizTextAligment.EHTA_CENTER);c.set_text_render_color(ue.Color(233,225,201,255));return a

def tree_meshes(terrain):
 import random
 rng=random.Random(52109);groups={}
 for i in range(1400):
  x,y=rng.uniform(5,475),rng.uniform(5,435)
  peripheral=x<40 or x>443 or y<18 or y>413
  north=y>plan.creek_y(x)+25
  if not peripheral and not north and rng.random()>.13:continue
  if abs(y-plan.creek_y(x))<12:continue
  if terrain.road_candidate(x,y)[0]<9:continue
  if any(abs(x-b['x'])<b['w']/2+12 and abs(y-b['y'])<b['d']/2+12 for b in plan.BUILDINGS):continue
  if 95<x<155 and 204<y<237:continue
  if 376<x<419 and 218<y<253:continue
  if any(min(plan.project(x,y,a,b)[0] for a,b in zip(p,p[1:]))<4 for p in plan.PATHS.values()):continue
  z=terrain.surface(x,y);h=rng.uniform(7,13);rad=rng.uniform(1.6,3.4);key=(int(x//120),int(y//110));groups.setdefault(key,[]).append((x,y,z,h,rad))
 for key,trees in groups.items():
  v,f=[],[];tv,tf=[],[]
  for x,y,z,h,r in trees:
   base=len(v)
   for j in range(7):a=j*math.tau/7;v.append((x+r*math.cos(a),y+r*math.sin(a),z+h*.28))
   v.append((x,y,z+h))
   for j in range(7):f.append((base+j,base+(j+1)%7,base+7))
   base=len(tv)
   for Z in(z,z+h*.5):
    for j in range(6):a=j*math.tau/6;tv.append((x+.18*math.cos(a),y+.18*math.sin(a),Z))
   for j in range(6):tf.extend([(base+j,base+(j+1)%6,base+6+(j+1)%6),(base+j,base+6+(j+1)%6,base+6+j)])
  static_surface('TreeCrowns_%s_%s'%key,7,v,f,'Woods',False)
  static_surface('TreeTrunks_%s_%s'%key,7,tv,tf,'Trunk',True)
 print('V5_FOREST_COUNT',sum(map(len,groups.values())))

def basement():
 # Terrain is omitted beneath this structure. Floors, walls, stair treads and
 # the rear roof slab close the excavation; both exits are physically walkable.
 floor=5.32
 obox('Church_TopLanding',6,(193,355.5,9.9),(3,1,.2),'Stone')
 obox('Church_Threshold',6,(185,351,9.9),(26,2,.2),'Stone')
 for x in(172.5,197.5):obox('Church_ExcavationEdge_'+str(x),6,(x,377,9.9),(1,54,.2),'Stone')
 obox('Church_RearThreshold',6,(185,403,9.9),(26,2,.2),'Terrain')
 obox('Basement_Floor',6,(185,377,floor-.12),(24,50,.24),'Stone')
 for x in(173,197):obox('Basement_Wall_'+str(x),6,(x,377,7.6),(.3,50,4.56),'Stone')
 obox('Basement_FrontWall',6,(185,352,7.6),(24,.3,4.56),'Stone')
 # Exit west at x177; leave the north wall opening.
 obox('Basement_NorthWall',6,(188,402,7.6),(18,.3,4.56),'Stone')
 obox('Basement_NorthWallWest',6,(174,402,7.6),(2,.3,4.56),'Stone')
 # Rear ceiling / ground. Leave an opening over the west escape stair.
 obox('Basement_RearCoverEast',6,(188,395,9.9),(18,14,.2),'Terrain')
 obox('Basement_RearCoverWest',6,(175,389,9.9),(4,2,.2),'Terrain')
 for i in range(26):
  top=10-(i+1)*.18;y=356+i*.3
  obox('Church_Descent_%02d'%i,6,(193,y,top-.12),(3,.3,.24),'Stone')
  # A solid wedge of steps from the basement slab, no unsupported treads.
  z=floor+(i+1)*.18;y=390+i*.3
  obox('Church_Escape_%02d'%i,6,(177,y,(z+floor)/2),(3,.3,z-floor),'Stone')
 obox('Descent_Landing',6,(193,364.2,floor-.10),(3,1.2,.2),'Stone')
 obox('Escape_Landing',6,(177,399.8,9.9),(3,4,.2),'Stone')
 for x,y in[(181,369),(188,384),(181,380)]:obox('Basement_Cover_%s_%s'%(x,y),6,(x,y,6.05),(2,1,1.46),'Utility')
 # Navigation remains a wide loop around the cover. These are not AI actors.
 sign('Basement_EscapeSign',(180,389,8.3),'SERVICE EXIT',-90,.4)
 for x,y in[(193,363),(185,378),(177,397)]:
  a=spawn(ue.PointLight,'Basement_Lamp_'+str(y),6,plan.uu(x,y,8.8));c=a.get_component_by_class(ue.PointLightComponent);c.set_intensity(1500);c.set_attenuation_radius(1200)

def main():
 if assets.does_asset_exist(plan.MAP):raise RuntimeError('Refusing to overwrite existing V5 map; use a reviewed repair script.')
 t=plan.Terrain();assert level.new_level(plan.MAP,is_partitioned_world=False)
 print('V5_BUILD_TERRAIN')
 for ix in range(4):
  for iy in range(4):
   v,f=[],[];xs=range(ix*120,ix*120+121,2);ys=range(iy*110,iy*110+111,2)
   add_grid(v,f,[[(x,y,t.surface(x,y)) for x in xs] for y in ys])
   # Church basement excavation; its perimeter aligns with the terrain grid.
   f=[tri for tri in f if not(172<=sum(v[j][0] for j in tri)/3<=198 and 350<=sum(v[j][1] for j in tri)/3<=404)]
   static_surface('Terrain_%s_%s'%(ix,iy),0,v,f,'Terrain',True)
 print('V5_BUILD_ROADS')
 for name,r in plan.ROADS.items():
  pts=r['points'];road_surface('Road_'+name.replace(' ','_'),pts,r['width'],r['kind'])
  if r['kind'] in('main','residential'):
   for side in(-1,1):
    v,f=[],[]
    for a,b in zip(pts,pts[1:]):
     if name=='Mill Road' and a[1]>=220:continue
     dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);nx,ny=-dy/L,dx/L;off=side*(r['width']/2+.85)
     q=[(p[0]+nx*off,p[1]+ny*off,p[2]+.035) for p in(a,b)]
     # actual sidewalk surface with only an 8 cm step from asphalt
     vv,ff=[],[]
     rows=[]
     for i in range(max(1,math.ceil(L/2))+1):
      tt=i/max(1,math.ceil(L/2));x,y,z=(plan.mix(q[0][k],q[1][k],tt) for k in range(3));rows.append([(x+nx*.75,y+ny*.75,z+.045),(x-nx*.75,y-ny*.75,z+.045)])
     add_grid(v,f,rows)
    if v:static_surface('Walk_'+name.replace(' ','_')+str(side),1,v,f,'Path',True)
 for name,points in plan.PATHS.items():surface_ribbon('Path_'+name.replace(' ','_'),1,points,2.6,'Path',t,.055,True)
 for k,points in plan.DRIVES.items():
  b=plan.BUILDING_BY_ID[k];start=t.road_candidate(*points[0])[1];length=sum(math.dist(a,q) for a,q in zip(points,points[1:]));run=0;pts=[]
  for i,p in enumerate(points):
   if i:run+=math.dist(points[i-1],p)
   pts.append((*p,plan.mix(start,b['z']-.08,run/max(.01,length))))
  road_surface('Drive_'+k,pts,3.2,'Path',3)
 print('V5_BUILD_CREEK')
 pts=[(x,plan.creek_y(x),0) for x in range(0,481,3)]
 road_surface('Creek_Water',pts,7,'Creek',2).set_actor_enable_collision(False)
 # Main road deck bridges the whole incised bank; no crossing water collision.
 obox('MainBridge_Deck',2,(305,263,3.95),(7,56,.5),'Bridge')
 for x in(301.45,308.55):
  obox('MainBridge_Rail_'+str(x),2,(x,263,4.8),(.18,56,1.2),'Metal')
 for y in(245,280):obox('MainBridge_Pier_'+str(y),2,(305,y,.5),(6,1.3,6.5),'Stone')
 # Old footbridge is a future alternative crossing, visibly fenced off.
 cy=plan.creek_y(160)
 obox('OldFootbridge',2,(160,cy,2),(2.6,34,.24),'Bridge')
 for y in(cy-17,cy+17):obox('OldFootbridge_Closed_'+str(y),2,(160,y,3),(3.2,.25,1.8),'Metal')
 print('V5_BUILD_TOWN')
 for b in plan.BUILDINGS:
  shell(b)
  # Level yards and foundations are actual terrain grading, not floating boxes.
  if b['id']!='CHURCH':
   part(b,'Foundation',(0,0,-.22),(b['w']+.5,b['d']+.5,.35),'Stone')
  if b['category'] in ('Civic','Commerce','Estate'):sign(b['id']+'_Sign',local(b,0,-b['d']/2-.15,min(b['h']-.4,3.3)),b['name'],b['yaw']-90,.5)
 # Church bell tower, steep spire, buttresses; Foster distinct estate wings.
 b=plan.BUILDING_BY_ID['CHURCH']
 part(b,'BellTower',(-8,-11,11),(6,7,22),'Estate')
 a=spawn(ue.StaticMeshActor,'Church_Spire',6,(17700,35900,3500));a.set_actor_scale3d(ue.Vector(7,8,9));set_mesh(a,cone,'Roof',True)
 for x in(-12.5,12.5):
  for y in(-10,0,10):part(b,'Buttress_%s_%s'%(x,y),(x,y,3),(1.2,2,6),'Stone')
 for i in range(7):
  for x in(-5,5):part(b,'Pew_%s_%s'%(x,i),(x,-10+i*3,.45),(5,1,.9),'Dark')
 b=plan.BUILDING_BY_ID['FOSTER']
 for side in(-1,1):part(b,'Wing_'+str(side),(side*19,1,4.2),(8,19,8.4),'Estate')
 part(b,'Portico',(0,-15,7.8),(16,6,.5),'White')
 for x in(-6,-2,2,6):part(b,'Column_'+str(x),(x,-16,3.8),(.55,.55,7.6),'White')
 b=plan.BUILDING_BY_ID['SCHOOL'];part(b,'SchoolBellTower',(-8,0,7),(3.4,3.4,4),'Civic')
 # Civic square, playground, a terraced separate old graveyard.
 obox('CivicSquare',5,(260,180,4.88),(30,7,.15),'Path')
 for x in(249,258,267):obox('Square_Bench_'+str(x),8,(x,177,5.3),(2,.55,.8),'Dark')
 for x in(112,132):
  obox('Play_Frame_'+str(x),5,(x,219,t.surface(x,219)+2.5),(.2,.2,5),'Metal')
 obox('Play_Crossbar',5,(122,219,t.surface(122,219)+4.8),(20,.2,.2),'Metal')
 for x in(118,126):obox('Play_Swing_'+str(x),5,(x,219,t.surface(x,219)+.5),(1,.5,.12),'Dark')
 for j in range(5):
  y=225+j*4
  for i in range(6):
   x=386+i*4;z=t.surface(x,y)
   obox('Grave_%s_%s'%(i,j),5,(x,y,z+.45),(.6,.22,.9),'Stone')
 for x,y,w,d in[(380,237,.35,32),(416,237,.35,32),(398,253,36,.35),(402,221,28,.35)]:obox('GraveyardWall_%s_%s'%(x,y),5,(x,y,t.surface(x,y)+.6),(w,d,1.2),'Stone')
 # Water tower atop the older high ground; modular legs + tank silhouette.
 z=t.surface(30,224)
 for x in(27,33):
  for y in(221,227):obox('Tower_Leg_%s_%s'%(x,y),5,(x,y,z+9),(.45,.45,18),'Metal')
 obox('WaterTower_Tank',5,(30,224,z+18),(10,10,5),'Utility')
 sign('TownWater',(30,218.9,z+18),'PENANCE',-90,.8)
 # Arrival washout is physical, readable and never crosses the forward route.
 obox('Arrival_RoadClosed',8,(47,10,7),(8,1,1.1),'Metal',True,30)
 for i in range(8):obox('WashoutRock_'+str(i),0,(42+i*2,6,t.surface(42+i*2,6)+.6),(2,2,1.2),'Stone')
 sign('Arrival_Welcome',(66,30,7),'PENANCE\nMill Road',-115,.65)
 # Interrupted everyday life, no destroyed town or apocalypse dressing.
 for i,(x,y,yaw) in enumerate([(80,50,-25),(155,177,10),(258,135,-25),(338,103,0),(401,146,85),(282,199,-20)]):
  z=t.surface(x,y);obox('ParkedCar_'+str(i),8,(x,y,z+.65),(1.8,4.2,1.3),'Utility',True,yaw);obox('CarRoof_'+str(i),8,(x,y,z+1.35),(1.6,2.2,.5),'Glass',True,yaw)
 # New memory car obstructs only the old front path, leaving the side route open.
 a=obox('Memory_Car_AfterHouse',9,(99,116,5.6),(1.8,4.2,1.3),'Utility');a.tags=[ue.Name('V5_AfterHouse')]
 a=obox('ParkShortcut_Barrier',9,(103,205,t.surface(103,205)+.7),(3.4,.2,1.4),'Metal');a.tags=[ue.Name('V5_ParkShortcutBarrier')]
 a=obox('Estate_Gate',9,(332,367,t.surface(332,367)+1),(6,.25,2),'Metal');a.tags=[ue.Name('V5_EstateBarrier')]
 tree_meshes(t);basement()
 # Reuse the unmodified House01 streaming implementation and interior package.
 b=plan.BUILDING_BY_ID['H01'];pos=local(b,0,-b['d']/2,b['z']*0+1.075)
 door=spawn(ue.PenanceStreamingDoor,'House01_StreamingEntrance',9,plan.uu(*pos))
 door.set_editor_properties({'exterior_entrance':True,'interior_level_name':'/Game/Maps/Interiors/House01_Interior','exterior_exit_world':ue.Vector(*plan.uu(109,108,5.8))})
 sign('House01_UseDoor',(100.5,118,7),'E - ENTER',180,.25)
 light=spawn(ue.PointLight,'House01_WarmPorch',9,plan.uu(100,118,7.1));lc=light.get_component_by_class(ue.PointLightComponent);lc.set_intensity(2000);lc.set_attenuation_radius(1800);lc.set_light_color(ue.LinearColor(1,.67,.33))
 director=spawn(ue.PenanceV5WorldDirector,'Opening_Director',9,(0,0,0))
 director.set_editor_properties({'checkpoints':[ue.Vector(*plan.uu(*p)) for p in plan.CHECKPOINTS],'objectives':plan.OBJECTIVES,
  'enemy_mesh':assets.load_asset('/Game/Enemies/Penance/SK_Penance'),'idle_animation':assets.load_asset('/Game/Enemies/Penance/Animations/AN_Penance_Idle'),
  'chase_animation':assets.load_asset('/Game/Enemies/Penance/Animations/AN_Penance_Chase'),
  'chase_path':[ue.Vector(*plan.uu(*p)) for p in[(193,367,5.32),(193,376,5.32),(193,386,5.32),(179,388,5.32)]]})
 spawn(ue.PlayerStart,'Arrival_PlayerStart',9,plan.uu(55,22,6.0),ue.Rotator(yaw=57))
 world=editor_world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
 world.get_world_settings().set_editor_property('force_no_precomputed_lighting',True)
 world.get_world_settings().set_editor_property('default_game_mode',ue.load_class(None,'/Script/PenanceDemoUE.PenanceDemoGameMode'))
 light=spawn(ue.DirectionalLight,'Afternoon_Light',0,(24000,22000,8000),ue.Rotator(pitch=-42,yaw=-48));light.get_component_by_class(ue.DirectionalLightComponent).set_intensity(4)
 sky=spawn(ue.SkyLight,'SkyFill',0,(24000,22000,12000));sky.get_component_by_class(ue.SkyLightComponent).set_intensity(1.1)
 spawn(ue.SkyAtmosphere,'Sky',0,(0,0,-200))
 # Review cameras use saved 1.65 m eye heights, and never act as player pawns.
 for name,xy,target in plan.VIEWS:camera(name,(*xy,t.surface(*xy)+1.65),target)
 camera('Overhead',(240,220,650),(240,220,0),530)
 camera('World',(515,-110,260),(240,240,5))
 for i,p in enumerate(plan.CHECKPOINTS):
  if i!=1:spawn(ue.TargetPoint,'Checkpoint_'+str(i),10,plan.uu(*p))
 ue.get_editor_subsystem(ue.UnrealEditorSubsystem).set_level_viewport_camera_info(ue.Vector(51500,-11000,26000),ue.MathLibrary.find_look_at_rotation(ue.Vector(51500,-11000,26000),ue.Vector(24000,24000,500)))
 assert ue.EditorLoadingAndSavingUtils.save_map(world,plan.MAP)
 plan.export(Path(__file__).resolve().parents[1]/'Docs/V5/Penance_V5_Implementation.json')
 print('PENANCE_V5_SAVED',plan.MAP,len(actor_api.get_all_level_actors()))
if __name__=='__main__':main()
