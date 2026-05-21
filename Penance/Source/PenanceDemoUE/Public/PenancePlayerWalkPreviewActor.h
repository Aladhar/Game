#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PenancePlayerWalkPreviewActor.generated.h"

class UAnimSequence;
class USkeletalMeshComponent;

UCLASS()
class PENANCEDEMOUE_API APenancePlayerWalkPreviewActor : public AActor
{
    GENERATED_BODY()

public:
    APenancePlayerWalkPreviewActor();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Animation Preview")
    TObjectPtr<USkeletalMeshComponent> PreviewMesh;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Penance|Animation Preview")
    TObjectPtr<UAnimSequence> WalkAnimation;

private:
    void SetPreviewWalking(bool bShouldWalk, float HorizontalSpeed, float DirectionSign);
    void UpdatePlayerMirroredPreview(float DeltaSeconds);
    void UpdateSelfTestPreview(float DeltaSeconds);
    void StartSelfTest();
    void FinishSelfTest();
    void AppendSelfTestCheck(const FString& Label, bool bPassed);
    float GetPreviewIdlePoseTime() const;

    bool bSelfTestActive = false;
    bool bCapturedInitialAnimationTime = false;
    bool bPreviewWalking = false;
    bool bIdlePhaseAnimationPlayed = false;
    bool bTurnOnlyPhaseAnimationPlayed = false;
    bool bMovePhaseAnimationPlayed = false;
    bool bReversePhaseAnimationPlayed = false;
    bool bStopPhaseAnimationPlayed = false;
    float SelfTestElapsed = 0.0f;
    float InitialAnimationTime = 0.0f;
    float MaxAnimationTimeDelta = 0.0f;
    float PreviewWalkBlendAlpha = 0.0f;
    float PreviewLastSignedPlayRate = 1.0f;
    FVector InitialActorLocation = FVector::ZeroVector;
    FVector MovePhaseStartLocation = FVector::ZeroVector;
    FVector ReversePhaseStartLocation = FVector::ZeroVector;
    FVector FinalActorLocation = FVector::ZeroVector;
    TArray<FString> SelfTestLines;
    TArray<FString> SelfTestErrors;
};
