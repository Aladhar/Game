using UnrealBuildTool;
using System.Collections.Generic;

public class PenanceDemoUETarget : TargetRules
{
    public PenanceDemoUETarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.Latest;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("PenanceDemoUE");
    }
}
