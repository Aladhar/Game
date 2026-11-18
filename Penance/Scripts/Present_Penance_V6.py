"""Interactive plan and comparison from V6's shared saved-world coordinates."""
import json,sys,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import Penance_Town_V6_Design as p
root=Path(__file__).resolve().parents[1];out=root/'Docs/V6';data=p.export(out/'Penance_V6_Implementation.json')
# All 14 chapter paths resolve their named sites against the relocated V6 inventory.
regions={'Arrival':(30,20),'Orchard Loop':(34,136),'PARK':(100,187),'GRAVEYARD':(354,188),'BRIDGE':(250,207.5),'BASEMENT':(145,297),'FOSTER interior':(324,291),'Return town':(214,164)}
regions.update({b['id']:(b['x'],b['y']) for b in p.BUILDINGS})
for c in data['chapters']:c['v6_path_coordinates_m']=[regions[k] for k in c['path'] if k in regions]
(out/'Penance_V6_Implementation.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
style='''*{box-sizing:border-box}body{margin:0;background:#101a1c;color:#e4e7df;font:15px system-ui}header{padding:24px 30px;border-bottom:1px solid #365047}h1{margin:5px 0;font-size:28px}small{color:#b1bcb0}main{display:grid;grid-template-columns:minmax(600px,1fr) 330px;gap:16px;padding:20px}canvas{width:100%;height:78vh;background:#1f302a;border:1px solid #52685d;border-radius:8px;touch-action:none}aside{background:#1b2929;padding:22px;border-radius:8px}button{background:#374d49;color:#fff;border:1px solid #728579;border-radius:4px;padding:9px;cursor:pointer}p{line-height:1.6}b{color:#e5c98e}#selected{margin-top:30px}a{color:#e5c98e}li{margin-bottom:12px}@media(max-width:950px){main{grid-template-columns:1fr}canvas{height:65vh}}'''
script=r'''
const D=DATA,canvas=document.querySelector('canvas'),ctx=canvas.getContext('2d');let s=1,ox=0,oy=0,drag=null,moved=false,chosen=null;
function resize(){canvas.width=canvas.clientWidth*devicePixelRatio;canvas.height=canvas.clientHeight*devicePixelRatio;fit()}
function fit(){s=Math.min(canvas.width/440,canvas.height/390);ox=(canvas.width-400*s)/2;oy=(canvas.height-350*s)/2;draw()}
function xy(x,y){return [ox+x*s,oy+(350-y)*s]}
function path(points,color,width,close=false){ctx.beginPath();points.forEach((p,i)=>{let q=xy(p[0],p[1]);i?ctx.lineTo(...q):ctx.moveTo(...q)});if(close)ctx.closePath();ctx.strokeStyle=color;ctx.lineWidth=width*s;ctx.lineCap='round';ctx.lineJoin='round';ctx.stroke()}
function draw(){ctx.clearRect(0,0,canvas.width,canvas.height);let q=xy(0,350);ctx.fillStyle='#344d3c';ctx.fillRect(q[0],q[1],400*s,350*s);ctx.strokeStyle='#779077';ctx.lineWidth=1;ctx.strokeRect(q[0],q[1],400*s,350*s);
ctx.globalAlpha=.12;for(let x=0;x<=400;x+=20)path([[x,0],[x,350]],'#d6e0ba',.25);for(let y=0;y<=350;y+=20)path([[0,y],[400,y]],'#d6e0ba',.25);ctx.globalAlpha=1;
path(D.creek,'#547d88',8);for(let [n,r]of Object.entries(D.roads)){path(r.points,r.kind==='main'?'#b9ab84':r.kind==='service'?'#718c7c':'#b3b8ae',r.width);if(document.querySelector('#labels').checked){let p=r.points[Math.floor(r.points.length*.5)],q=xy(p[0],p[1]);ctx.fillStyle='#f3eedc';ctx.font=`${Math.max(9,2.2*s)}px system-ui`;ctx.fillText(n,q[0]+4,q[1]-6)}}
for(let [n,pts]of Object.entries(D.paths))path(pts,'#91ad82',1.4);
for(let lot of D.parcels){path(lot.polygon,'#c9bc9566',.35,true)}
for(let b of D.buildings){let c=xy(b.x,b.y);ctx.save();ctx.translate(...c);ctx.rotate(-b.yaw*Math.PI/180);ctx.fillStyle=b.id===chosen?'#edba64':b.category==='Residential'?'#c4b18b':b.category==='Estate'?'#aaa4b2':'#93a6a0';ctx.fillRect(-b.w*s/2,-b.d*s/2,b.w*s,b.d*s);ctx.strokeStyle='#e8debf';ctx.lineWidth=.4*s;ctx.strokeRect(-b.w*s/2,-b.d*s/2,b.w*s,b.d*s);ctx.restore();ctx.fillStyle='#142321';ctx.font=`bold ${Math.max(8,1.9*s)}px system-ui`;ctx.textAlign='center';ctx.fillText(b.id,...c)}
if(document.querySelector('#route').checked)path(D.opening_route,'#e5b872',1.1);
ctx.textAlign='left';ctx.fillStyle='#ebdfbf';ctx.font=`bold ${13*devicePixelRatio}px system-ui`;ctx.fillText('N ↑   /   +Y',12*devicePixelRatio,22*devicePixelRatio)}
canvas.onwheel=e=>{e.preventDefault();let x=e.offsetX*devicePixelRatio,y=e.offsetY*devicePixelRatio,k=Math.exp(-e.deltaY*.001);ox=x+(ox-x)*k;oy=y+(oy-y)*k;s*=k;draw()};canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY,ox,oy];moved=false;canvas.setPointerCapture(e.pointerId)};canvas.onpointermove=e=>{if(drag){let dx=(e.clientX-drag[0])*devicePixelRatio,dy=(e.clientY-drag[1])*devicePixelRatio;ox=drag[2]+dx;oy=drag[3]+dy;moved|=Math.abs(dx)+Math.abs(dy)>5;draw()}};
canvas.onpointerup=e=>{drag=null;if(moved)return;let x=(e.offsetX*devicePixelRatio-ox)/s,y=350-(e.offsetY*devicePixelRatio-oy)/s;let b=D.buildings.find(b=>{let a=b.yaw*Math.PI/180,dx=x-b.x,dy=y-b.y;return Math.abs(dx*Math.cos(a)+dy*Math.sin(a))<b.w/2&&Math.abs(-dx*Math.sin(a)+dy*Math.cos(a))<b.d/2});if(b){chosen=b.id;document.querySelector('#selected').innerHTML=`<h2>${b.id} · ${b.name}</h2><p><b>${b.w} × ${b.d} m</b> footprint<br>${b.h+b.roof} m roof height above floor<br>Floor ${b.z} m<br>Center (${b.x}, ${b.y}) m<br>Yaw ${b.yaw}°<br>${b.id.match(/^H(1[5-9]|20)$/)?'New V6 house':'Original dimensions preserved'}</p>`;draw()}};
document.querySelector('#fit').onclick=fit;document.querySelectorAll('input').forEach(x=>x.onchange=draw);window.onresize=resize;resize();
'''
data['parcels']=json.loads((out/'Parcels.json').read_text())['parcels'];data['opening_route']=[(30,20),(40,37),(59,60),(70,83),(78,101),(92,106),(100,96),(78,88),(54,91),(34,109),(34,136),(53,154),(78,157),(100,187),(124,202),(190,185),(250,189),(250,239),(181,251),(145,269),(153,294),(137,323),(203,317),(291,275),(325,276)]
html='<!doctype html><html><meta charset="utf-8"><title>Penance V6 — Saved World Plan</title><style>'+style+'</style><header><small>PENANCE / V6 / ACTUAL IMPLEMENTATION COORDINATES</small><h1>A town compressed, not miniaturized.</h1><small>400 × 350 m · 35 main building sites · 20 houses · 10 named roads</small></header><main><div><canvas></canvas><p>Drag to pan · Wheel to zoom · Click a building for dimensions. North is +Y.</p></div><aside><button id="fit">Fit map</button><p><label><input id="labels" type="checkbox" checked> Road names</label><br><label><input id="route" type="checkbox" checked> Condensed opening route</label></p><p><b>33.7% less land area.</b><br>V5: 480 × 440 m<br>V6: 400 × 350 m<br>All 29 original building dimensions retained.</p><div id="selected"><h2>Explore the town</h2><p>Choose a house, shop or landmark.</p></div><hr><p>Existing House01 streaming and church basement preserved. Later interiors and story chapters remain reserved.</p><p>Plan and saved-world validation are separate deliverables. Read <a href="README.md">README</a> and validation reports for test results.</p></aside></main><script>'+script.replace('DATA',json.dumps(data,separators=(',',':')))+' </script></html>'
(out/'Penance_Town_V6_Interactive.html').write_text(html)
# Lightweight labeled overview; actual Unreal overhead is supplied separately.
im=Image.new('RGB',(1600,1540),'#101a1c');d=ImageDraw.Draw(im);scale=3.5;ox,oy=100,180
font='/System/Library/Fonts/Supplemental/Arial.ttf';f=ImageFont.truetype(font,18);small=ImageFont.truetype(font,14);h=ImageFont.truetype(font,36)
d.text((100,40),'PENANCE V6 / 400 × 350 m',font=h,fill='#eee1bc');d.text((100,100),'35 sites · 20 houses · all original buildings at full size · north ↑',font=f,fill='#aab8ab')
def xy(q):return(ox+q[0]*scale,oy+(350-q[1])*scale)
d.rectangle([xy((0,350)),xy((400,0))],fill='#344d3c',outline='#a9b594',width=2)
d.line([xy(q) for q in data['creek']],fill='#547d88',width=28)
for n,r in p.ROADS.items():d.line([xy(q) for q in r['points']],fill='#c1b28d' if r['kind']=='main' else '#a8b5ac',width=int(r['width']*scale),joint='curve')
for a in data['parcels']:d.line([xy(q) for q in a['polygon']],fill='#78856b',width=1)
for b in p.BUILDINGS:
 c,s=math.cos(math.radians(b['yaw'])),math.sin(math.radians(b['yaw']));pts=[(b['x']+c*x-s*y,b['y']+s*x+c*y) for x,y in[(-b['w']/2,-b['d']/2),(b['w']/2,-b['d']/2),(b['w']/2,b['d']/2),(-b['w']/2,b['d']/2)]];d.polygon([xy(q) for q in pts],fill='#c4b18b' if b['category']=='Residential' else '#9eacaa',outline='#e8dfbd');q=xy((b['x'],b['y']));d.text(q,b['id'],font=small,fill='#152426',anchor='mm')
d.text((100,1475),'Schematic from shared coordinates. See Views/Overhead.png for the rendered Unreal level.',font=f,fill='#aab8ab');im.save(out/'Penance_V6_Masterplan.png')
print('V6 presentation saved')
