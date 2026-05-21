#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "PenancePlayerCharacter.generated.h"

class UCameraComponent;
class UAnimSequence;
class USkeletalMeshComponent;
class USceneComponent;
class APenanceHingedDoor;
class APenancePickupItem;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FPenanceStaminaChangedSignature, float, CurrentStamina, float, MaxStamina);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FPenanceCrouchChangedSignature, bool, bIsCrouching);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FPenancePlayerNoiseSignature, FName, NoiseType, FVector, WorldLocation, float, Intensity);

UENUM(BlueprintType)
enum class EPenanceFirstPersonIdlePoseMode : uint8
{
    FeetTogether UMETA(DisplayName = "Feet Together"),
    LeftFootForward UMETA(DisplayName = "Left Foot Forward"),
    RightFootForward UMETA(DisplayName = "Right Foot Forward")
};

UENUM(BlueprintType)
enum class EPenanceFirstPersonLocomotionState : uint8
{
    Idle UMETA(DisplayName = "Idle"),
    WalkForward UMETA(DisplayName = "Walk Forward"),
    WalkBackward UMETA(DisplayName = "Walk Backward")
};

UCLASS()
class PENANCEDEMOUE_API APenancePlayerCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    APenancePlayerCharacter();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    virtual void Jump() override;

    UPROPERTY(BlueprintAssignable, Category = "Penance|Player")
    FPenanceStaminaChangedSignature OnStaminaChanged;

    UPROPERTY(BlueprintAssignable, Category = "Penance|Player")
    FPenanceCrouchChangedSignature OnCrouchChanged;

    UPROPERTY(BlueprintAssignable, Category = "Penance|Player")
    FPenancePlayerNoiseSignature OnPlayerNoise;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Player")
    TObjectPtr<UCameraComponent> FirstPersonCamera;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Player")
    TObjectPtr<USceneComponent> FirstPersonCameraRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Player")
    TObjectPtr<USkeletalMeshComponent> FirstPersonBodyMesh;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Player Animation")
    EPenanceFirstPersonIdlePoseMode FirstPersonIdlePoseMode = EPenanceFirstPersonIdlePoseMode::FeetTogether;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Player Animation", meta = (ClampMin = "0.01", ClampMax = "1.00"))
    float FirstPersonWalkBlendInTime = 0.18f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Player Animation", meta = (ClampMin = "0.01", ClampMax = "1.00"))
    float FirstPersonWalkBlendOutTime = 0.16f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Player Animation", meta = (ClampMin = "0.00", ClampMax = "30.00"))
    float FirstPersonMovementYawOffsetDegrees = 10.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Player Camera", meta = (ClampMin = "-180.00", ClampMax = "180.00"))
    float PlayerMeshVisualYawOffsetDegrees = -90.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Player Camera", meta = (ClampMin = "0.10", ClampMax = "60.00"))
    float BodyYawFollowSpeed = 18.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Movement")
    float WalkSpeed = 250.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Movement")
    float SprintSpeed = 550.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Movement")
    float LowStaminaSprintSpeed = 480.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Movement")
    float CrouchSpeed = 140.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Movement")
    float MouseLookSensitivity = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Movement")
    float JumpVelocity = 420.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Stamina")
    float MaxStamina = 100.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Stamina")
    float Stamina = 100.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Stamina")
    float StaminaDrainPerSecond = 20.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Stamina")
    float StaminaRegenPerSecond = 12.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Stamina")
    float StaminaRegenDelay = 1.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Stamina")
    float LowStaminaThreshold = 20.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Crouch")
    float StandingCameraHeight = 155.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Crouch")
    float CrouchingCameraHeight = 95.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Crouch")
    float StandingCapsuleHeight = 165.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Crouch")
    float CrouchingCapsuleHeight = 105.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Crouch")
    float CapsuleRadius = 35.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Crouch")
    float CrouchTransitionSpeed = 10.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Interaction")
    float InteractionDistance = 280.0f;

    UFUNCTION(BlueprintCallable, Category = "Penance|Inventory")
    void AddInventoryEntry(const FText& ItemName, const FText& ItemDescription, bool bIsNote);

    UFUNCTION(BlueprintCallable, Category = "Penance|Inventory")
    void ToggleInventory();

    UFUNCTION(BlueprintCallable, Category = "Penance|Inventory")
    bool IsInventoryOpen() const { return bInventoryOpen; }

    UFUNCTION(BlueprintCallable, Category = "Penance|Stamina")
    float GetStaminaRatio() const;

    UFUNCTION(BlueprintPure, Category = "Penance|Debug")
    bool IsFirstPersonBodyWalking() const { return bFirstPersonBodyWalking; }

    UFUNCTION(BlueprintPure, Category = "Penance|Debug")
    float GetFirstPersonWalkCycleTime() const { return FirstPersonWalkCycleTime; }

    UFUNCTION(BlueprintPure, Category = "Penance|Debug")
    float GetFirstPersonForwardSpeed() const { return FirstPersonForwardSpeed; }

    UFUNCTION(BlueprintPure, Category = "Penance|Debug")
    float GetFirstPersonRightSpeed() const { return FirstPersonRightSpeed; }

    UFUNCTION(BlueprintPure, Category = "Penance|Debug")
    EPenanceFirstPersonLocomotionState GetFirstPersonLocomotionState() const { return FirstPersonLocomotionState; }

    UFUNCTION(BlueprintPure, Category = "Penance|Debug")
    float GetCameraYaw() const { return CameraYaw; }

    UFUNCTION(BlueprintPure, Category = "Penance|Debug")
    float GetBodyYaw() const { return BodyYaw; }

    UFUNCTION(BlueprintPure, Category = "Penance|Debug")
    float GetTurnYawDelta() const { return FirstPersonTurnYawDelta; }

    UFUNCTION(BlueprintPure, Category = "Penance|Debug")
    float GetAimPitch() const { return AimPitch; }

    UFUNCTION(BlueprintPure, Category = "Penance|Debug")
    FString GetFirstPersonBodyMeshPath() const;

    UFUNCTION(BlueprintPure, Category = "Penance|Debug")
    bool AreOwnerCameraClippingBonesHidden() const;

    const TArray<FString>& GetInventoryItems() const { return InventoryItems; }
    const TArray<FString>& GetCollectedNotes() const { return CollectedNotes; }
    FText GetCurrentInteractionHint() const { return CurrentInteractionHint; }

protected:
    virtual bool CanJumpInternal_Implementation() const override;

private:
    void MoveForward(float Value);
    void MoveRight(float Value);
    void Turn(float Value);
    void LookUp(float Value);
    void StartSprint();
    void StopSprint();
    void StartCrouchInput();
    void StopCrouchInput();
    void Interact();

    void UpdateMovementRules(float DeltaSeconds);
    void UpdateCrouchRules(float DeltaSeconds);
    void UpdateNoiseRules(float DeltaSeconds);
    void UpdateInteractionFocus();
    void UpdateCameraDrivenBodyYaw(float DeltaSeconds);
    void UpdateFirstPersonBody(float DeltaSeconds);
    void ResetFirstPersonBodyPose();
    void HideOwnerCameraClippingBones();
    void UpdatePlayerBodySelfTest(float DeltaSeconds);
    void StartPlayerBodySelfTest();
    void FinishPlayerBodySelfTest();
    void AppendPlayerBodySelfTestCheck(const FString& Label, bool bPassed);
    void BroadcastStaminaIfNeeded();
    void ForceGroundedMovementMode();
    float GetCameraRelativeHeightForCurrentCapsule(float EyeHeight) const;
    bool HasMovementInput() const;
    bool GetInteractionTrace(FHitResult& OutHit) const;

    FVector2D MoveInput = FVector2D::ZeroVector;
    bool bWantsSprint = false;
    bool bWantsCrouch = false;
    bool bWasCrouching = false;
    bool bInventoryOpen = false;
    float StaminaRegenTimer = 0.0f;
    float LastBroadcastStaminaRatio = -1.0f;
    float SprintNoiseTimer = 0.0f;
    float SilenceTimer = 0.0f;
    float FirstPersonWalkCycleTime = 0.0f;
    float FirstPersonWalkBlendAlpha = 0.0f;
    float FirstPersonLastPlayRate = 1.0f;
    float FirstPersonBodyYawOffset = 0.0f;
    float FirstPersonForwardSpeed = 0.0f;
    float FirstPersonRightSpeed = 0.0f;
    float FirstPersonTurnYawDelta = 0.0f;
    float CameraYaw = 0.0f;
    float BodyYaw = 0.0f;
    float AimPitch = 0.0f;
    bool bFirstPersonBodyWalking = false;
    bool bFirstPersonBodyWasWalking = false;
    EPenanceFirstPersonLocomotionState FirstPersonLocomotionState = EPenanceFirstPersonLocomotionState::Idle;
    bool bPlayerBodySelfTestActive = false;
    bool bOwnerCameraClippingBonesHidden = false;
    int32 PlayerBodySelfTestPhase = 0;
    float PlayerBodySelfTestPhaseTime = 0.0f;
    float PlayerBodySelfTestInitialCycle = 0.0f;
    float PlayerBodySelfTestTurnCycleDelta = 0.0f;
    float PlayerBodySelfTestMaxTurnYawDelta = 0.0f;
    float PlayerBodySelfTestPitchCycleDelta = 0.0f;
    float PlayerBodySelfTestMaxBodyPitch = 0.0f;
    float PlayerBodySelfTestMoveStartCycle = 0.0f;
    float PlayerBodySelfTestMoveMaxSpeed = 0.0f;
    float PlayerBodySelfTestMoveCycleDelta = 0.0f;
    float PlayerBodySelfTestBackwardMaxSpeed = 0.0f;
    float PlayerBodySelfTestBackwardCycleDelta = 0.0f;
    float PlayerBodySelfTestStopMinSpeed = TNumericLimits<float>::Max();
    bool bPlayerBodySelfTestSawWalking = false;
    bool bPlayerBodySelfTestSawBackwardWalking = false;
    bool bPlayerBodySelfTestTurnAnimationPlaying = false;
    bool bPlayerBodySelfTestPitchAnimationPlaying = false;
    bool bPlayerBodySelfTestSawAnimationPlaying = false;
    bool bPlayerBodySelfTestSawBackwardAnimationPlaying = false;
    TArray<FString> PlayerBodySelfTestLines;
    TArray<FString> PlayerBodySelfTestErrors;
    TObjectPtr<UAnimSequence> FirstPersonForwardWalkAnimation;
    TObjectPtr<UAnimSequence> FirstPersonBackwardWalkAnimation;
    FText CurrentInteractionHint;
    TArray<FString> InventoryItems;
    TArray<FString> CollectedNotes;
};
