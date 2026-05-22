using UnrealBuildTool;
using System.Collections.Generic;

public class PenanceDemoUEEditorTarget : TargetRules
{
    public PenanceDemoUEEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("PenanceDemoUE");
    }
}
