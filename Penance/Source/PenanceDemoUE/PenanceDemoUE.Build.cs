using UnrealBuildTool;

public class PenanceDemoUE : ModuleRules
{
    public PenanceDemoUE(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "EnhancedInput",
            "InputCore",
            "UMG",
            "Slate",
            "SlateCore",
            "RenderCore"
        });

        if (Target.bBuildEditor)
        {
            PrivateDependencyModuleNames.AddRange(new string[]
            {
                "UnrealEd",
                "Kismet",
                "BlueprintGraph",
                "AnimGraph",
                "AnimGraphRuntime",
                "GraphEditor",
                "UMGEditor"
            });
        }
    }
}
