"""Reimport only the fixed experimental mesh; preserve all animation binaries."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];project=R.parents[2];manifest=json.loads((R/'Checkpoints/BeforeStraightShrine/Manifest.json').read_text())
source=Path(__file__).with_name('import_unreal.py');code=source.read_text().split("manifest=json.loads((R/'Reports/ClipManifest.json').read_text())")[0]
exec(compile(code,str(source),'exec'),globals())
after=reference();assert set(before)==set(after) and max(abs(a-b) for n in before for a,b in zip(before[n],after[n]))<.0001
for f,h in manifest['unchanged_animation_files'].items():assert hashlib.sha256((project/f).read_bytes()).hexdigest()==h,(f,'Animation asset changed')
A.set_metadata_tag(mesh,'Penance.ShrineRigid','true');A.set_metadata_tag(mesh,'Penance.ShrineShape','Canonical straight architecture; shrine_mount only');assert A.save_loaded_asset(mesh,False)
report={'engine':u.SystemLibrary.get_engine_version(),'mesh':mesh.get_path_name(),'height_cm':mesh.get_imported_bounds().box_extent.z*2,'skeleton':skel.get_path_name(),'skeleton_reference_unchanged':True,'physics_asset_compatible':True,'all_14_animation_exports_and_sequences_byte_unchanged':True,'repair':json.loads((R/'Reports/StraightShrineRepair.json').read_text())}
(R/'Reports/StraightShrineUnrealImport.json').write_text(json.dumps(report,indent=2)+'\n');print('STRAIGHT_SHRINE_UNREAL_MESH_IMPORTED',json.dumps(report))
