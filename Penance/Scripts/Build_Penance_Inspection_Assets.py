"""Supported Unreal APIs: actual static mesh, data asset, UMG Blueprint and materials.
Run after native build with GeometryScripting enabled. Adds only the demo board/post to V6.
"""
from pathlib import Path
import unreal as u,math,json
root=Path(__file__).resolve().parents[1];src=root/'SourceArt/Inspection';out=root/'Docs/Inspection'
A=u.get_editor_subsystem(u.EditorAssetSubsystem);T=u.AssetToolsHelpers.get_asset_tools();E=u.MaterialEditingLibrary
PROP='/Game/Props/Inspection';UI='/Game/UI/Inspection'
def save(x):assert A.save_loaded_asset(x,False),x.get_path_name()
def tex(filename,name):
 path=PROP+'/'+name
 if A.does_asset_exist(path):return A.load_asset(path)
 task=u.AssetImportTask();task.filename=str(src/filename);task.destination_path=PROP;task.destination_name=name;task.automated=True;task.save=True;T.import_asset_tasks([task]);assert task.imported_object_paths,filename
 return A.load_asset(path)
front=tex('GasBoard_Front.png','T_GasPriceBoard_Front');back=tex('GasBoard_Back.png','T_GasPriceBoard_Back');thumb=tex('GasBoard_Thumbnail.png','T_GasPriceBoard_Thumbnail');grain=tex('UI_Grain.png','T_InspectionGrain')
def expr(m,cls,**kw):
 x=E.create_material_expression(m,cls)
 for k,v in kw.items():x.set_editor_property(k,v)
 return x
def material(path):
 if A.does_asset_exist(path):return A.load_asset(path),False
 folder,name=path.rsplit('/',1);return T.create_asset(name,folder,u.Material,u.MaterialFactoryNew()),True
def surf(name,texture=None,color=(.28,.26,.21),metal=.1,rough=.7):
 m,new=material(PROP+'/'+name)
 if new:
  col=expr(m,u.MaterialExpressionTextureSample,texture=texture) if texture else expr(m,u.MaterialExpressionConstant3Vector,constant=u.LinearColor(*color,1))
  E.connect_material_property(col,'RGB' if texture else '',u.MaterialProperty.MP_BASE_COLOR)
  for prop,v in [(u.MaterialProperty.MP_METALLIC,metal),(u.MaterialProperty.MP_ROUGHNESS,rough)]:E.connect_material_property(expr(m,u.MaterialExpressionConstant,r=v),'',prop)
  m.two_sided=True;E.recompile_material(m);save(m)
 return m
mats=[surf('M_GasBoard_Front',front),surf('M_GasBoard_Back',back,metal=.65,rough=.6),surf('M_GasBoard_Edge',color=(.24,.22,.17),metal=.8,rough=.38),surf('M_GasBoard_Screws',color=(.32,.31,.26),metal=.85,rough=.3)]
meshpath=PROP+'/SM_GasPriceBoard'
if A.does_asset_exist(meshpath):mesh=A.load_asset(meshpath)
else:
 verts=[];uv=[];faces=[];ids=[]
 def tri(points,coords,mat):
  base=len(verts);verts.extend(points);uv.extend(coords);faces.append((base,base+2,base+1));ids.append(mat)
 def quad(points,coords,mat):
  tri([points[i] for i in(0,1,2)],[coords[i] for i in(0,1,2)],mat);tri([points[i] for i in(0,2,3)],[coords[i] for i in(0,2,3)],mat)
 profile=[(-40.4,-30),(40.4,-30),(41,-29.4),(41,29.4),(40.4,30),(-40.4,30),(-41,29.4),(-41,-29.4)]
 for X,mat in [(-.65,0),(.65,1)]:
  for i,(Y,Z) in enumerate(profile):
   y,z=profile[(i+1)%8];points=[(X,0,0),(X,Y,Z),(X,y,z)];coords=[(.5,.5),((Y+41)/82 if mat==0 else(41-Y)/82,(30-Z)/60),((y+41)/82 if mat==0 else(41-y)/82,(30-z)/60)]
   if mat==0:points.reverse();coords.reverse()
   tri(points,coords,mat)
 for i,(y,z) in enumerate(profile):
  Y,Z=profile[(i+1)%8];quad([(-.65,y,z),(.65,y,z),(.65,Y,Z),(-.65,Y,Z)],[(0,0),(1,0),(1,1),(0,1)],2)
 def box(cx,cy,cz,dx,dy,dz,mat):
  v=[(cx+s*dx/2,cy+t*dy/2,cz+r*dz/2) for s,t,r in[(-1,-1,-1),(-1,1,-1),(-1,1,1),(-1,-1,1),(1,-1,-1),(1,1,-1),(1,1,1),(1,-1,1)]]
  for q in[(0,3,2,1),(4,5,6,7),(0,4,7,3),(1,2,6,5),(0,1,5,4),(3,7,6,2)]:quad([v[j] for j in q],[(0,0),(1,0),(1,1),(0,1)],mat)
 # Folded edge lips and rear stiffeners are real geometry.
 for y in(-40.8,40.8):box(0,y,0,1.7,.45,59,2)
 for z in(-29.8,29.8):box(0,0,z,1.7,81,.45,2)
 for y in(-26,26):box(1.05,y,0,.8,2.8,54,2)
 for X in(-.83,.83):
  for Y in(-38.4,38.4):
   for Z in(-27.4,27.4):
    for i in range(12):
     a=i*math.tau/12;b=(i+1)*math.tau/12
     tri([(X*1.18,Y,Z),(X,Y+.42*math.cos(a),Z+.42*math.sin(a)),(X,Y+.42*math.cos(b),Z+.42*math.sin(b))],[(.5,.5),(0,0),(1,1)],3)
 dm=u.DynamicMesh();buf=u.GeometryScriptSimpleMeshBuffers();buf.vertices=[u.Vector(*x) for x in verts];buf.triangles=[u.IntVector(*x) for x in faces];buf.uv0=[u.Vector2D(*x) for x in uv];u.GeometryScript_MeshEdits.append_buffers_to_mesh(dm,buf)
 u.GeometryScript_Materials.enable_material_ids(dm)
 for i,mat in enumerate(ids):u.GeometryScript_Materials.set_triangle_material_id(dm,i,mat)
 opts=u.GeometryScriptCreateNewStaticMeshAssetOptions();opts.enable_recompute_normals=True;opts.enable_recompute_tangents=True;opts.enable_collision=True;opts.collision_mode=u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
 mesh,result=u.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm,meshpath,opts);assert mesh
 for i,m in enumerate(mats):mesh.set_material(i,m)
 mesh.get_editor_property('body_setup').set_editor_property('double_sided_geometry',True);save(mesh)
 (out/'Board_Geometry.json').write_text(json.dumps(dict(vertices=verts,triangles=faces,uv0=uv,material_ids=ids,units='centimeters'),indent=2)+'\n')
# Translucent UI composite of live HDR + inverse opacity (not a static object image).
m,new=material(UI+'/M_InspectionComposite')
if new:
 m.material_domain=u.MaterialDomain.MD_UI;m.blend_mode=u.BlendMode.BLEND_TRANSLUCENT
 sample=expr(m,u.MaterialExpressionTextureSampleParameter2D,parameter_name='Preview',texture=u.load_asset('/Engine/EngineResources/WhiteSquareTexture'));sample.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
 one=expr(m,u.MaterialExpressionConstant,r=1);add=expr(m,u.MaterialExpressionAdd);div=expr(m,u.MaterialExpressionDivide)
 E.connect_material_expressions(sample,'RGB',add,'A');E.connect_material_expressions(one,'',add,'B');E.connect_material_expressions(sample,'RGB',div,'A');E.connect_material_expressions(add,'',div,'B');E.connect_material_property(div,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
 inv=expr(m,u.MaterialExpressionOneMinus);E.connect_material_expressions(sample,'A',inv,'Input');E.connect_material_property(inv,'',u.MaterialProperty.MP_OPACITY);E.recompile_material(m);save(m)
def ui_custom(name,code,color):
 m,new=material(UI+'/'+name)
 if new:
  m.material_domain=u.MaterialDomain.MD_UI;m.blend_mode=u.BlendMode.BLEND_TRANSLUCENT
  coord=expr(m,u.MaterialExpressionTextureCoordinate);c=expr(m,u.MaterialExpressionCustom,code=code,output_type=u.CustomMaterialOutputType.CMOT_FLOAT1);inp=u.CustomInput();inp.input_name='UV';c.inputs=[inp];E.connect_material_expressions(coord,'',c,'UV');E.connect_material_property(c,'',u.MaterialProperty.MP_OPACITY);col=expr(m,u.MaterialExpressionConstant3Vector,constant=u.LinearColor(*color,1));E.connect_material_property(col,'',u.MaterialProperty.MP_EMISSIVE_COLOR);E.recompile_material(m);save(m)
 return m
ui_custom('M_InspectionShade','float d=length((UV-.5)*float2(1,.85)); float n=frac(sin(dot(floor(UV*1400),float2(12.9898,78.233)))*43758.5453); return .77+smoothstep(.1,.65,d)*.2+(n-.5)*.018;',(.018,.012,.008))
ui_custom('M_InspectionGlow','return pow(max(0,1-abs(UV.x-.5)*2),2)*exp(-pow((UV.y-.5)*12,2))*.9;',(.95,.5,.2))
for filename,name in [('CormorantGaramond.ttf','F_InspectionSerif'),('Caveat.ttf','F_InspectionHand')]:
 font=u.PenanceInspectionEditorLibrary.import_inspection_font(str(src/'Fonts'/filename),UI+'/Fonts/'+name);assert font
 save(font);save(A.load_asset(UI+'/Fonts/'+name+'_Face'))
itempath=PROP+'/DA_LastStopGasPrices'
if A.does_asset_exist(itempath):item=A.load_asset(itempath)
else:
 f=u.DataAssetFactory();f.data_asset_class=u.PenanceInspectItem;item=T.create_asset('DA_LastStopGasPrices',PROP,u.PenanceInspectItem,f)
item.set_editor_properties(dict(title='Gas Prices — Last Stop',description='An enamel price board from Last Stop Gas.\nRegular, Plus, and Premium — per gallon.',thought='Whoa, look at these gas prices.',mesh=mesh,thumbnail=thumb));save(item)
wbpath=UI+'/WBP_ObjectInspection'
if A.does_asset_exist(wbpath):wb=A.load_asset(wbpath)
else:
 f=u.WidgetBlueprintFactory();f.parent_class=u.PenanceInspectionWidget;wb=T.create_asset('WBP_ObjectInspection',UI,u.WidgetBlueprint,f)
assert u.PenanceInspectionEditorLibrary.build_widget(wb);save(wb)
# Add only the target and its post; preserve every existing saved actor.
L=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem);assert L.load_level('/Game/Maps/V6/Penance_Town_V6');existing=actors.get_all_level_actors()
board=next((x for x in existing if x.get_actor_label()=='V6_Inspectable_GasPrices'),None)
if not board:
 board=actors.spawn_actor_from_class(u.PenanceInspectObject,u.Vector(6800,6100,640),u.Rotator(yaw=180));board.set_actor_label('V6_Inspectable_GasPrices');board.set_folder_path('V6/Inspection');board.object_mesh.set_static_mesh(mesh);board.items=[item]
 post=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(6800,6100,555));post.set_actor_label('V6_GasPrices_Post');post.set_folder_path('V6/Inspection');post.set_actor_scale3d(u.Vector(.08,.08,1.1));post.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cube'));post.static_mesh_component.set_material(0,mats[2])
w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();assert u.EditorLoadingAndSavingUtils.save_map(w,'/Game/Maps/V6/Penance_Town_V6')
u.SystemLibrary.execute_console_command(w,'MAP CHECK DONTDISPLAYDIALOG');print('PENANCE_INSPECTION_ASSETS_SAVED')
