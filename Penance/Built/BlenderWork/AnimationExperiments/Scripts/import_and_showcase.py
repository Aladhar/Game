"""Run in a separate UE editor; never load or save V5/V6 maps."""
from pathlib import Path
folder=Path(__file__).resolve().parent
for name in ['import_unreal.py','build_showcase.py']:
 path=folder/name
 exec(compile(path.read_text(),str(path),'exec'),{'__file__':str(path),'__name__':'__main__'})
