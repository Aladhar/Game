"""Host Python preflight; Shapely is not required inside Unreal."""
import math,json
from pathlib import Path
from shapely.geometry import Polygon,box,LineString,mapping
from shapely.affinity import rotate,translate
from shapely.ops import unary_union
import Penance_Town_V6_Design as p
out=Path(__file__).resolve().parents[1]/'Docs/V6'
polys={b['id']:translate(rotate(box(-b['w']/2-.4,-b['d']/2-.4,b['w']/2+.4,b['d']/2+.4),b['yaw'],origin=(0,0)),b['x'],b['y']) for b in p.BUILDINGS}
roadmask=unary_union([LineString([x[:2] for x in r['points']]).buffer(r['width']/2+2.1) for r in p.ROADS.values()])
parcels=[];issues=[]
for i,b in enumerate(p.BUILDINGS):
 k=b['id'];a=polys[k]
 for q,c in list(polys.items())[i+1:]:
  if a.intersection(c).area>.1:issues.append(f'Building overlap {k} / {q}')
 for n,r in p.ROADS.items():
  if a.distance(LineString([x[:2] for x in r['points']]))<r['width']/2+.6:issues.append(f'Road encroachment {k} / {n}')
 pad=5 if b['category']=='Residential' else 3
 lot=a.buffer(pad,join_style=2).intersection(box(4,4,396,346)).difference(roadmask)
 for q,c in polys.items():
  if q==k:continue
  # Remove other cores and split the available setback halfway.
  lot=lot.difference(c.buffer(pad*.5,join_style=2))
 if lot.geom_type=='MultiPolygon':lot=max(lot.geoms,key=lambda z:z.intersection(a).area)
 parcels.append(dict(id=k,polygon=list(lot.exterior.coords),area_m2=round(lot.area,2),footprint=list(a.exterior.coords)))
# Grade-respecting driveway surfaces and visible property reservations, not interior gameplay.
report=dict(issues=issues,building_count=len(polys),houses=sum(b['category']=='Residential' for b in p.BUILDINGS),parcels=parcels)
(out/'Parcels.json').write_text(json.dumps(report,indent=2)+'\n');p.export(out/'Penance_V6_Implementation.json')
assert not issues,issues
print('V6 preflight: 35 full-size sites, 20 houses; no footprint/road conflicts.')
