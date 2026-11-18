"""Full-town native capture; temporarily bypass foliage distance culling in PIE only."""
from pathlib import Path
import unreal as u,time
MAP='/Game/Maps/V6/Penance_Town_V6';out=Path(__file__).resolve().parents[1]/'Docs/V6/Views'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);assert L.load_level(MAP)
cam=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='V6_Review_Overhead');cam.set_actor_location(u.Vector(20000,17500,18000),False,False)
w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();assert u.EditorLoadingAndSavingUtils.save_map(w,MAP)
cap=A.spawn_actor_from_class(u.SceneCapture2D,u.Vector(20000,17500,18000),u.Rotator(pitch=-90,yaw=90));cap.set_actor_label('V6_Transient_Overhead')
u.EditorPythonScripting.set_keep_python_script_alive(True);start=time.monotonic();phase=0;busy=False;cc=None;rt=None;world=None
def tick(dt):
 global phase,start,busy,cc,rt,world
 if busy:return
 busy=True
 try:
  if time.monotonic()-start<3:return
  if phase==0:L.editor_request_begin_play();phase=1;start=time.monotonic()
  elif phase==1:
   world=u.EditorLevelLibrary.get_pie_worlds(False)[0]
   for a in u.GameplayStatics.get_all_actors_of_class(world,u.PenanceV6InstancedSet):a.instances.set_cull_distances(0,0)
   c=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.SceneCapture2D) if a.get_actor_label()=='V6_Transient_Overhead');cc=c.get_component_by_class(u.SceneCaptureComponent2D)
   rt=u.RenderingLibrary.create_render_target2d(world,1440,1260,u.TextureRenderTargetFormat.RTF_RGBA8);cc.set_editor_properties({'texture_target':rt,'projection_type':u.CameraProjectionMode.ORTHOGRAPHIC,'ortho_width':43000,'capture_source':u.SceneCaptureSource.SCS_FINAL_COLOR_LDR,'capture_every_frame':False})
   u.SystemLibrary.execute_console_command(world,'r.EyeAdaptationQuality 0');phase=2;start=time.monotonic()
  elif phase==2:cc.capture_scene();u.RenderingLibrary.export_render_target(world,rt,str(out),'Overhead.png');L.editor_request_end_play();phase=3;start=time.monotonic()
  elif phase==3:
   if L.is_in_play_in_editor():return
   print('V6_FULL_OVERHEAD_CAPTURED');u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False)
 finally:busy=False
handle=u.register_slate_post_tick_callback(tick)
