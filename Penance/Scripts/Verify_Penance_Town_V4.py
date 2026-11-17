"""Read the saved V4 map through Unreal 5.7.4 and check its geometry.

Run with -ExecutePythonScript=<this file> in Unreal Editor. The verifier uses
PIE physics for traces and does not save or edit level assets.
Set PENANCE_V4_REPORT to override the default JSON report under Saved.
"""
from collections import Counter
from itertools import combinations
from pathlib import Path
import hashlib
import json
import math
import os
import sys

import unreal as ue

sys.path.insert(0,str(Path(__file__).resolve().parent))
import Penance_Town_V4_Design as plan

issues=[]
warnings=[]
report={}
vec=lambda xyz:ue.Vector(*xyz)


def require(condition,message):
    if not condition:
        issues.append(message)


def overlaps(a,b):
    x,y,w,d=a
    X,Y,W,D=b
    return min(x+w,X+W)-max(x,X)>.01 and min(y+d,Y+D)-max(y,Y)>.01


def inside(a,b):
    x,y,w,d=a
    X,Y,W,D=b
    return X<=x and Y<=y and x+w<=X+W and y+d<=Y+D


def trace(world,start,end,ignore=()):
    return ue.SystemLibrary.line_trace_single(world,vec(start),vec(end),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,
        True,list(ignore),ue.DrawDebugTrace.NONE,False)


def floor(world,x,y,ignore=()):
    h=trace(world,plan.uu(x,y,70),plan.uu(x,y,-20),ignore)
    return h.to_tuple()[5].z/100 if h else None


def position_matches(actor,rect,tolerance=3):
    wx,wy,_=plan.uu(*plan.rect_center(rect))
    a=actor.get_actor_location()
    return abs(a.x-wx)<=tolerance and abs(a.y-wy)<=tolerance


def sample(points,step=2):
    yield points[0]
    for a,b in zip(points,points[1:]):
        n=max(1,math.ceil(math.dist(a,b)/step))
        for i in range(1,n+1):
            yield (plan.mix(a[0],b[0],i/n),plan.mix(a[1],b[1],i/n))


def inspect(world):
    root=Path(ue.Paths.convert_relative_path_to_full(ue.Paths.project_dir()))
    file=root/'Content/Maps/Planning/Penance_Town_Masterplan_V4_Blockout.umap'
    require(file.is_file() and file.stat().st_size>10000,'Saved V4 map package missing or still empty')
    report['map_bytes']=file.stat().st_size
    actors=[a for a in ue.GameplayStatics.get_all_actors_of_class(world,ue.Actor)
            if str(a.get_actor_label()).startswith('V4_')]
    by_name={str(a.get_actor_label()):a for a in actors}
    report['actor_count']=len(actors)
    report['folders']=dict(sorted(Counter(str(a.get_folder_path()) for a in actors).items()))
    require(len(by_name)==len(actors),'Duplicate actor labels found')
    for folder in plan.FOLDERS:
        require(folder in report['folders'],'Missing World Outliner folder '+folder)
    require('V4_South_Entrance_PlayerStart' in by_name,'Missing south PlayerStart')
    require(sum(a.get_class().get_name()=='PlayerStart' for a in actors)==1,'Expected one PlayerStart')
    require(not any(a.get_class().get_name()=='PenanceStreamingDoor' for a in actors),'A gameplay streaming door was added')
    require(world.get_world_settings().get_editor_property('default_game_mode') is None,'Expected inherited project GameMode')

    tiles=[a for a in actors if str(a.get_actor_label()).startswith('V4_Terrain_')]
    mesh_bounds=[a.get_actor_bounds(True) for a in tiles]
    x0=min(p.x-e.x for p,e in mesh_bounds)
    x1=max(p.x+e.x for p,e in mesh_bounds)
    y0=min(p.y-e.y for p,e in mesh_bounds)
    y1=max(p.y+e.y for p,e in mesh_bounds)
    report['terrain_tiles']=len(tiles)
    report['site_uu']=[x1-x0,y1-y0]
    require(len(tiles)==16,'Missing terrain tiles')
    require(max(abs(x0),abs(y0),abs(x1-48000),abs(y1-60000))<3,'Site extent or origin mismatch')
    require(tuple(plan.uu(265,148,3))==(26500,45200,300),'Bridge source-coordinate conversion differs')
    require(tuple(plan.uu(*plan.rect_center((30,421,45,42))))==(5250,15800,0),'H01 source-coordinate conversion differs')

    houses=list(plan.RESERVES)
    report['residential_lots']=len(houses)
    report['parcel_count']=len(plan.PARCELS)
    report['building_pads']=len(plan.PADS)
    report['outbuilding_reserves']=sum(len(r) for r in plan.RESERVES.values())+1
    for key,p in plan.PARCELS.items():
        parcel=by_name.get('V4_'+key+'_Parcel')
        require(parcel is not None,'Missing parcel '+key)
        if parcel:
            bounds,extent=parcel.get_actor_bounds(False)
            x,y,_=plan.uu(*plan.rect_center(plan.parcel_rect(p)))
            require(abs(bounds.x-x)<25 and abs(bounds.y-y)<25,'Shifted parcel center '+key)
            require(abs(extent.x*2-p['w']*100)<30 and abs(extent.y*2-p['h']*100)<30,
                    'Wrong parcel width or depth '+key)
        require('V4_Label_'+plan.NAMES[key] in by_name,'Missing label '+key)
    for a,b in combinations(houses,2):
        require(not overlaps(plan.parcel_rect(plan.PARCELS[a]),plan.parcel_rect(plan.PARCELS[b])),
                f'Residential lots overlap: {a} and {b}')
    require(len(houses)==14,'Expected 14 residential lots')
    require(not overlaps(plan.parcel_rect(plan.PARCELS['CHURCH']),plan.parcel_rect(plan.PARCELS['FOSTER'])),
            'Church and Foster estates overlap')
    for key,reserves in plan.RESERVES.items():
        for i,(name,rect) in enumerate(reserves,1):
            actor=by_name.get(f'V4_{key}_{name}_Reserve_{i}')
            require(actor and position_matches(actor,rect),f'Missing or shifted reserve {key} {name}')
            require(inside(rect,plan.parcel_rect(plan.PARCELS[key])),f'{key} {name} is outside its lot')
            require(not overlaps(rect,plan.PADS[key][0]),f'{key} {name} overlaps its house pad')
        require('V4_'+key+'_Driveway' in by_name,'Missing driveway for '+key)

    pad_checks={}
    for key,(rect,_) in plan.PADS.items():
        actor=by_name.get('V4_'+key+'_Foundation')
        require(actor is not None,'Missing foundation '+key)
        if not actor:
            continue
        require(position_matches(actor,rect),'Wrong foundation center for '+key)
        center,extent=actor.get_actor_bounds(True)
        require(abs(extent.x*2-rect[2]*100)<3 and abs(extent.y*2-rect[3]*100)<3,'Wrong pad dimensions for '+key)
        top=(center.z+extent.z)/100
        x,y,w,d=rect
        probes=[(x+w*i/4,y+d*j/4) for i in (.15,2,3.85) for j in (.15,2,3.85)]
        ground=[floor(world,*p,(actor,)) for p in probes]
        require(all(g is not None for g in ground),'Missing ground under '+key)
        if all(g is not None for g in ground):
            clear=[top-g for g in ground]
            pad_checks[key]=[round(min(clear)*100,1),round(max(clear)*100,1)]
            require(min(clear)>=.035 and max(clear)<=.39,'Buried or floating pad '+key+': '+str(pad_checks[key]))
        for road,r in plan.ROADS.items():
            if r['kind']=='path':
                continue
            nearest=min(plan.project(*p,a,b)[0] for p in probes for a,b in zip(plan.route_points(road),plan.route_points(road)[1:]))
            require(nearest>=r['width']/2-.03,f'{key} pad overlaps {road}')
    report['pad_clearance_uu_min_max']=pad_checks

    road_checks={}
    # Measure the travel surface, not the tops of the screening proxies or
    # the intentional fence across the reserved pedestrian crossing.
    road_trace_ignore = [actor for label,actor in by_name.items()
                         if label.startswith(('V4_TEMP_', 'V4_Old_Footbridge_Blocked_'))]
    for key,r in plan.ROADS.items():
        name='V4_Road_'+plan.ROAD_NAMES[key]
        require(name in by_name,'Missing road actor '+key)
        points=plan.route_points(key)
        stations=list(sample(points))
        zlist=[floor(world,*p,road_trace_ignore) for p in stations]
        require(all(z is not None for z in zlist),f'{key} lacks continuous centerline collision')
        valid=[(100*abs(z1-z0)/math.dist(a,b),a) for a,b,z0,z1 in zip(stations,stations[1:],zlist,zlist[1:])
               if z0 is not None and z1 is not None and math.dist(a,b)>.05]
        m,p=max(valid,default=(0,(0,0)))
        road_checks[key]={'width_uu':r['width']*100,'length_m':round(plan.length(points),2),
                          'collision_samples':len(stations),'max_grade_pct':round(m,2),'steepest_xy_m':p}
        cap={'main':6.5,'residential':8,'service':11,'path':20}[r['kind']]
        if m>cap:
            warnings.append(f'{key} peaks at {m:.1f}% around {p}; target {cap:.1f}%')
    report['sampled_road_widths_uu']={}
    for key,x,y,dx,dy in (('R_MAIN',232,573,1,0),('R_DEADEND',345,500,0,1),('R_ESTATES',258,49,1,0)):
        width=plan.ROADS[key]['width']
        expected='V4_Road_'+plan.ROAD_NAMES[key]
        hits=[]
        for offset in (-width/2-.15,-width/2+.15,width/2-.15,width/2+.15):
            sx,sy=x+dx*offset,y+dy*offset
            hit=trace(world,plan.uu(sx,sy,70),plan.uu(sx,sy,-20),road_trace_ignore)
            actor=hit.to_tuple()[9] if hit else None
            hits.append(actor is not None and str(actor.get_actor_label())==expected)
        require(hits==[False,True,True,False],'Road cross-section width differs at '+key)
        if hits==[False,True,True,False]:
            report['sampled_road_widths_uu'][key]=width*100

    report['roads']=road_checks

    deck=by_name.get('V4_Creek_MainBridge')
    require(deck is not None,'Missing main bridge')
    crossings=[floor(world,265,y) for y in range(136,164)]
    creek=[floor(world,265,y,(deck,)) for y in (144,145,146,147,148,149,150,151,152)]
    report['bridge_deck_uu']=[round(z*100,1) if z is not None else None for z in crossings]
    report['bridge_creek_bed_min_uu']=round(min((z for z in creek if z is not None),default=0)*100,1)
    require(deck and abs(deck.get_actor_bounds(True)[1].x*2-700)<3,'Bridge must be 700 UU wide')
    require(all(z is not None and 2.93<=z<=3.20 for z in crossings),'Bridge deck/approach height or collision mismatch')
    require(all(z is not None and z<-.7 for z in creek),'Terrain pokes through the bridge deck or creek was filled')
    require(abs(report['bridge_creek_bed_min_uu']+400)<=25,'Creek bed misses design datum')
    for side in ('West','East'):
        factor=-1 if side=='West' else 1
        require(trace(world,plan.uu(265,148,3.55),plan.uu(265+factor*4.4,148,3.55)),
                'Missing bridge edge collision '+side)

    z_targets={key:round((floor(world,*plan.rect_center(plan.parcel_rect(plan.PARCELS[key]))) or 0)*100,1)
               for key in ('HALL','CEM')}
    for key in ('WATER','FOSTER','CHURCH'):
        x,y=plan.rect_center(plan.PADS[key][0])
        z_targets[key]=round((floor(world,x,y,(by_name['V4_'+key+'_Foundation'],)) or 0)*100,1)
    z_targets['BriarLane_End']=round((floor(world,453,500) or 0)*100,1)
    report['sampled_elevations_uu']=z_targets

    proxy_tops={'CHURCH':39,'FOSTER':20.25,'WATER':48.5}
    result={}
    for key,info in plan.SOURCE['sightlines'].items():
        x,y=info['target']
        for name,ox,oy,intent,_ in info['rays']:
            base=floor(world,ox,oy)
            if base is None:
                warnings.append('No ground at view marker '+name)
                continue
            hit=trace(world,plan.uu(ox,oy,base+1.65),plan.uu(x,y,proxy_tops[key]))
            observed='blocked' if hit else 'clear'
            result[key+'/'+name]={'design':intent,'proxy_top_trace':observed}
            if intent in ('blocked','clear') and intent!=observed:
                warnings.append(f'{key} from {name}: intended {intent}, top trace {observed}')
    report['sightlines']=result

    prior=plan.SOURCE['original_map_sha256']
    for path,digest in prior.items():
        require(hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,'Existing map changed: '+path)
    report['existing_maps_unchanged']=not any('Existing map changed' in i for i in issues)
    report['issues']=issues
    report['warnings']=warnings
    output=Path(os.environ.get('PENANCE_V4_REPORT',str(root/'Saved/Penance_V4_Verification.json')))
    output.write_text(json.dumps(report,indent=2)+'\n')
    print('PENANCE_V4_VERIFY_REPORT',str(output))
    if issues:
        raise RuntimeError('V4 verification: '+'; '.join(issues))
    print('PENANCE_V4_VERIFICATION_PASSED',len(actors),'actors',len(warnings),'observations')


def run_from_editor():
    level=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
    editor=ue.get_editor_subsystem(ue.UnrealEditorSubsystem)
    if level.is_in_play_in_editor():
        inspect(editor.get_game_world())
        return
    if not level.load_level(plan.MAP):
        raise RuntimeError('Could not load '+plan.MAP)
    ue.EditorPythonScripting.set_keep_python_script_alive(True)
    import time
    start=time.monotonic()

    def tick(_):
        world=editor.get_game_world()
        if not world and time.monotonic()-start < 45:
            return
        ue.unregister_slate_post_tick_callback(handle)
        try:
            if not world:
                raise RuntimeError('PIE physics was unavailable')
            inspect(world)
        finally:
            level.editor_request_end_play()
            ue.EditorPythonScripting.set_keep_python_script_alive(False)

    handle=ue.register_slate_post_tick_callback(tick)
    level.editor_request_begin_play()


if __name__ == '__main__':
    run_from_editor()
