#pragma once

#include "Animation/AnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "Animation/AnimNode_SequencePlayer.h"
#include "ABP_Player.generated.h"

class APawn;
class UAnimSequence;

UENUM(BlueprintType)
enum class EPenancePlayerAnimState : uint8
{
    Idle UMETA(DisplayName = "Idle"),
    StartWalkForward UMETA(DisplayName = "Start Walk Forward"),
    WalkForward UMETA(DisplayName = "Walk Forward"),
    WalkBackward UMETA(DisplayName = "Walk Backward"),
    StopWalkForward UMETA(DisplayName = "Stop Walk Forward"),
    TurnInPlaceLeft UMETA(DisplayName = "Turn In Place Left"),
    TurnInPlaceRight UMETA(DisplayName = "Turn In Place Right")
};

USTRUCT()
struct FABP_PlayerProxy : public FAnimInstanceProxy
{
    GENERATED_BODY()

    FABP_PlayerProxy() = default;
    explicit FABP_PlayerProxy(UAnimInstance* InAnimInstance);

    virtual void Initialize(UAnimInstance* InAnimInstance) override;
    virtual void PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds) override;
    virtual void UpdateAnimationNode(const FAnimationUpdateContext& InContext) override;
    virtual bool Evaluate(FPoseContext& Output) override;

private:
    FAnimNode_SequencePlayer_Standalone SequencePlayer;
    UAnimSequenceBase* ActiveSequence = nullptr;
    UAnimSequenceBase* LastSequence = nullptr;
    float ActivePlayRate = 1.0f;
    float ActiveStartPosition = 0.0f;
    bool bActiveLooping = true;
};

UCLASS(Blueprintable, BlueprintType, Transient)
class PENANCEDEMOUE_API UABP_Player : public UAnimInstance
{
    GENERATED_BODY()

public:
    UABP_Player();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    float Speed = 0.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    float ForwardSpeed = 0.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    float RightSpeed = 0.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    float Direction = 0.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    bool bIsMoving = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    bool bMovingForward = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    bool bMovingBackward = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    bool bIsTurningInPlace = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    float TurnYawDelta = 0.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    float WalkPlayRate = 1.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    EPenancePlayerAnimState LocomotionState = EPenancePlayerAnimState::Idle;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    float StateElapsedTime = 0.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ABP_Player|Locomotion")
    float ActiveAssetTime = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Assets")
    TObjectPtr<UAnimSequence> IdleFeetTogether;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Assets")
    TObjectPtr<UAnimSequence> IdleStaggered;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Assets")
    TObjectPtr<UAnimSequence> StartWalkForward;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Assets")
    TObjectPtr<UAnimSequence> WalkForwardLoop;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Assets")
    TObjectPtr<UAnimSequence> WalkBackwardLoop;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Assets")
    TObjectPtr<UAnimSequence> StopWalkForward;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Assets")
    TObjectPtr<UAnimSequence> TurnInPlaceLeft;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Assets")
    TObjectPtr<UAnimSequence> TurnInPlaceRight;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Settings", meta = (ClampMin = "0.00", ClampMax = "1.00"))
    float IdleFeetTogetherPoseTime = 0.3229f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Settings", meta = (ClampMin = "0.00", ClampMax = "120.00"))
    float MovingThreshold = 10.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Settings", meta = (ClampMin = "0.00", ClampMax = "120.00"))
    float StopThreshold = 5.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Settings", meta = (ClampMin = "1.00", ClampMax = "1200.00"))
    float WalkSpeedTarget = 250.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Settings", meta = (ClampMin = "1.00", ClampMax = "180.00"))
    float TurnInPlaceThreshold = 45.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Settings")
    bool bUseStartStopAnimations = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ABP_Player|Settings")
    bool bUseTurnInPlaceAnimations = false;

    virtual void NativeInitializeAnimation() override;
    virtual void NativeUpdateAnimation(float DeltaSeconds) override;

    UAnimSequenceBase* GetActiveSequence() const;
    float GetActivePlayRate() const;
    float GetActiveStartPosition() const;
    bool IsActiveSequenceLooping() const;
    bool IsActivelyPlayingLocomotion() const;
    bool AreRequiredAssetsLoaded() const;

protected:
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override;
    virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy) override;

private:
    void LoadDefaultAssets();
    void UpdateMotionVariables(APawn* OwningPawn);
    void UpdateStateMachine(float DeltaSeconds);
    void SetLocomotionState(EPenancePlayerAnimState NewState);
    UAnimSequence* ResolveAssetForState(EPenancePlayerAnimState State) const;
};
