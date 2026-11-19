"""Fresh Unreal reload and PIE verification for the straight-shrine mesh.
No animation sequences or existing gameplay assets are saved.
"""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=Path(__file__).with_name('validate_unreal_playback.py')
code=source.read_text().replace("UnrealPlaybackValidation.json","StraightShrineUnrealPlayback.json").replace("UnrealPlaybackFailure.txt","StraightShrineUnrealPlaybackFailure.txt").replace("EXPERIMENT_PIE_ALL_SEVEN_ADVANCED","STRAIGHT_SHRINE_PIE_ALL_SEVEN_ADVANCED")
exec(compile(code,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
