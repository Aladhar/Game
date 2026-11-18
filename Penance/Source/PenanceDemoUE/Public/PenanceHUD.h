#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "PenanceHUD.generated.h"

UCLASS()
class PENANCEDEMOUE_API APenanceHUD : public AHUD
{
    GENERATED_BODY()

public:
    virtual void DrawHUD() override;
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    UPROPERTY(Transient,BlueprintReadOnly,Category="Objectives") TObjectPtr<class UPenanceObjectiveTrackerWidget> ObjectiveTracker;
    UFUNCTION(BlueprintCallable,Category="Objectives") void ToggleObjectives();

private:
    UPROPERTY(Transient) TObjectPtr<class UEnhancedInputComponent> ObjectiveInput;
    UPROPERTY(Transient) TObjectPtr<class UInputMappingContext> ObjectiveContext;
    void DrawStaminaBar(class APenancePlayerCharacter* Player);
    void DrawInventory(class APenancePlayerCharacter* Player);
    void DrawInteractionHint(class APenancePlayerCharacter* Player);
};
