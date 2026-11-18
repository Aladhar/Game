#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "PenanceInspectionEditorLibrary.generated.h"
UCLASS()
class PENANCEDEMOUE_API UPenanceInspectionEditorLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable) static bool BuildWidget(class UBlueprint* Blueprint);
 UFUNCTION(BlueprintCallable) static class UFont* ImportInspectionFont(const FString& Filename,const FString& AssetPath);
 // Engine-input automation for PIE; no OS keyboard synthesis.
 UFUNCTION(BlueprintCallable) static bool SendGameKey(class APlayerController* Player,FKey Key,bool Pressed);
 UFUNCTION(BlueprintCallable) static bool SendInspectKey(class APlayerController* Player,FKey Key);
 UFUNCTION(BlueprintCallable) static bool SendInspectMouse(class APlayerController* Player,FVector2D Delta);
 UFUNCTION(BlueprintCallable) static bool SendInspectWheel(class APlayerController* Player,float Delta);
 UFUNCTION(BlueprintCallable) static bool RenderInspection(class APlayerController* Player,FIntPoint Resolution,const FString& Filename);
};
