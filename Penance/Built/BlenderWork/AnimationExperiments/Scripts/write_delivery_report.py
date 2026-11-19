"""Compatibility entry point for the current straight-shrine delivery report."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('write_straight_shrine_report.py')),run_name='__main__')
