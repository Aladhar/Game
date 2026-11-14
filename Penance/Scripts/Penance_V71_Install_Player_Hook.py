"""Run with system Python in the local project root OR pass project path as argv[1].

Updates only the existing E-interaction code, with a backup, and refuses if it differs.
Does not modify any .uasset or .umap file.
"""
import sys
from pathlib import Path

project = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path.cwd()
if not (project / "PenanceDemoUE.uproject").exists():
    raise SystemExit("Pass the Penance project directory containing PenanceDemoUE.uproject")
cpp = project / "Source" / "PenanceDemoUE" / "Private" / "PenancePlayerCharacter.cpp"
s = cpp.read_text(encoding="utf-8-sig")
if '#include "PenanceStreamingDoor.h"' in s:
    print("Already installed; no changes")
    raise SystemExit(0)
needle = '#include "PenanceHingedDoor.h"'
assert s.count(needle)==1, "Unexpected include section, refusing patch"
needle2 = '        if (APenanceHingedDoor* Door = Cast<APenanceHingedDoor>(Hit.GetActor()))'
assert s.count(needle2)==1, "Unexpected interaction function, refusing patch"
s2 = s.replace(needle, needle+'\n#include "PenanceStreamingDoor.h"')
s2 = s2.replace(needle2,
'''        if (APenanceStreamingDoor* Portal = Cast<APenanceStreamingDoor>(Hit.GetActor()))
        {
            Portal->Interact(this);
            OnPlayerNoise.Broadcast(TEXT("door"), Portal->GetActorLocation(), 0.6f);
            return;
        }

'''+needle2)
backup = cpp.with_suffix(".cpp.v71_before_patch")
if backup.exists(): raise SystemExit("Backup already exists; will not overwrite " + str(backup))
backup.write_text(s, encoding="utf-8")
cpp.write_text(s2, encoding="utf-8")
print("Hook installed. Backup: " + str(backup))
