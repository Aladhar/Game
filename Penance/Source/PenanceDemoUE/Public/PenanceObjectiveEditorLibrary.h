#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "PenanceObjectiveEditorLibrary.generated.h"
class UBlueprint;class APlayerController;
UCLASS()
class PENANCEDEMOUE_API UPenanceObjectiveEditorLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="Penance|Editor") static bool BuildTrackerBlueprint(UBlueprint* Blueprint);
 UFUNCTION(BlueprintCallable,Category="Penance|Editor") static bool ConfigurePlayerPlaySettings();
 UFUNCTION(BlueprintCallable,Category="Penance|Validation") static bool RenderTrackerLayout(APlayerController* Player,FIntPoint Resolution,const FString& Filename,FLinearColor Backdrop);
 UFUNCTION(BlueprintCallable,Category="Penance|Validation") static bool BeginValidationPlay(int32 Width,int32 Height);
 UFUNCTION(BlueprintCallable,Category="Penance|Validation") static void CaptureGameplay(const FString& Filename);
};
