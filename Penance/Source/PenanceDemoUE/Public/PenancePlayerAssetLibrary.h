#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "PenancePlayerAssetLibrary.generated.h"

UCLASS()
class PENANCEDEMOUE_API UPenancePlayerAssetLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Penance|Editor")
    static bool BuildPlayerAnimationGraph();

    UFUNCTION(BlueprintCallable, Category = "Penance|Editor")
    static bool BuildPlayerInputMappings();
};
