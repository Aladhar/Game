using UnrealBuildTool;
using System.Collections.Generic;

public class PenanceDemoUEEditorTarget : TargetRules
{
    public PenanceDemoUEEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V6;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("PenanceDemoUE");
    }
}
