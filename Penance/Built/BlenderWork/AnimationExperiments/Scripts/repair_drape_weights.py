"""Compatibility entry point: the shrine is rigid architecture, not drape.
The former height-blended ornament assignment is intentionally removed.
"""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('repair_shrine_rigidity.py')), run_name='__main__')
