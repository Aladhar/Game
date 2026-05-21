#include "PenancePlayerCharacter.h"

#include "Animation/AnimSequence.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "HAL/PlatformMisc.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Camera/PlayerCameraManager.h"
#include "PenanceHingedDoor.h"
#include "PenancePickupItem.h"
#include "UObject/ConstructorHelpers.h"
#include "EngineUtils.h"

DEFINE_LOG_CATEGORY_STATIC(LogPenancePlayerBody, Log, All);

APenancePlayerCharacter::APenancePlayerCharacter()
{
    PrimaryActorTick.bCanEverTick = true;

    GetCapsuleComponent()->InitCapsuleSize(CapsuleRadius, StandingCapsuleHeight * 0.5f);

    USkeletalMeshComponent* PlayerMeshComponent = GetMesh();
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> PlayerMeshAsset(TEXT("/Game/Player/BlenderSource/SK_Player_FromBlend.SK_Player_FromBlend"));
    if (!PlayerMeshAsset.Succeeded())
    {
        static ConstructorHelpers::FObjectFinder<USkeletalMesh> FallbackPlayerMeshAsset(TEXT("/Game/Player/Skeletal/SK_Player.SK_Player"));
        if (FallbackPlayerMeshAsset.Succeeded())
        {
            PlayerMeshAsset.Object = FallbackPlayerMeshAsset.Object;
        }
    }
    if (PlayerMeshAsset.Succeeded())
    {
        PlayerMeshComponent->SetSkeletalMesh(PlayerMeshAsset.Object);
    }
    PlayerMeshComponent->SetupAttachment(GetCapsuleComponent());
    PlayerMeshComponent->SetRelativeLocation(FVector(0.0f, 0.0f, -StandingCapsuleHeight * 0.5f));
    PlayerMeshComponent->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
    PlayerMeshComponent->SetRelativeScale3D(FVector(1.65f));
    PlayerMeshComponent->SetOwnerNoSee(true);
    PlayerMeshComponent->bCastHiddenShadow = true;

    FirstPersonBodyMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh_FP_Body"));
    FirstPersonBodyMesh->SetupAttachment(GetCapsuleComponent());
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> FirstPersonBodyMeshAsset(TEXT("/Game/Player/FirstPerson/SK_Player_FirstPersonBody.SK_Player_FirstPersonBody"));
    if (FirstPersonBodyMeshAsset.Succeeded())
    {
        FirstPersonBodyMesh->SetSkeletalMesh(FirstPersonBodyMeshAsset.Object);
    }
    else if (PlayerMeshAsset.Succeeded())
    {
        FirstPersonBodyMesh->SetSkeletalMesh(PlayerMeshAsset.Object);
    }
    static ConstructorHelpers::FObjectFinder<UAnimSequence> FirstPersonVerifyWalkAnimAsset(TEXT("/Game/Player/FirstPerson/AN_Player_Walk_Verify.AN_Player_Walk_Verify"));
    if (FirstPersonVerifyWalkAnimAsset.Succeeded())
    {
        FirstPersonWalkAnimation = FirstPersonVerifyWalkAnimAsset.Object;
    }
    else
    {
        static ConstructorHelpers::FObjectFinder<UAnimSequence> FirstPersonImportedWalkAnimAsset(TEXT("/Game/Player/FirstPerson/SK_Player_FirstPersonBody_Anim.SK_Player_FirstPersonBody_Anim"));
        if (FirstPersonImportedWalkAnimAsset.Succeeded())
        {
            FirstPersonWalkAnimation = FirstPersonImportedWalkAnimAsset.Object;
        }
    }
    FirstPersonBodyMesh->SetRelativeLocation(FVector(0.0f, 0.0f, -StandingCapsuleHeight * 0.5f));
    FirstPersonBodyMesh->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
    FirstPersonBodyMesh->SetRelativeScale3D(FVector(1.65f));
    FirstPersonBodyMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
    if (FirstPersonWalkAnimation)
    {
        FirstPersonBodyMesh->SetAnimation(FirstPersonWalkAnimation);
        FirstPersonBodyMesh->SetPosition(0.0f, false);
        FirstPersonBodyMesh->Stop();
    }
    FirstPersonBodyMesh->SetOnlyOwnerSee(true);
    FirstPersonBodyMesh->SetOwnerNoSee(false);
    FirstPersonBodyMesh->SetCastShadow(false);
    FirstPersonBodyMesh->bCastHiddenShadow = false;

    FirstPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FirstPersonCamera"));
    FirstPersonCamera->SetupAttachment(GetCapsuleComponent());
    FirstPersonCamera->SetRelativeLocation(FVector(0.0f, 0.0f, GetCameraRelativeHeightForCurrentCapsule(StandingCameraHeight)));
    FirstPersonCamera->bUsePawnControlRotation = true;
    FirstPersonCamera->FieldOfView = 78.0f;

    bUseControllerRotationYaw = true;
    bUseControllerRotationPitch = false;
    bUseControllerRotationRoll = false;

    UCharacterMovementComponent* Movement = GetCharacterMovement();
    Movement->bOrientRotationToMovement = false;
    Movement->DefaultLandMovementMode = MOVE_Walking;
    Movement->MaxWalkSpeed = WalkSpeed;
    Movement->MaxWalkSpeedCrouched = CrouchSpeed;
    Movement->MaxAcceleration = 1800.0f;
    Movement->BrakingDecelerationWalking = 2200.0f;
    Movement->GroundFriction = 8.0f;
    Movement->GravityScale = 1.0f;
    Movement->JumpZVelocity = JumpVelocity;
    Movement->AirControl = 0.22f;
    Movement->NavAgentProps.bCanCrouch = true;
    Movement->SetCrouchedHalfHeight(CrouchingCapsuleHeight * 0.5f);

    JumpMaxCount = 1;
    BaseEyeHeight = GetCameraRelativeHeightForCurrentCapsule(StandingCameraHeight);
    CrouchedEyeHeight = GetCameraRelativeHeightForCurrentCapsule(CrouchingCameraHeight);
}

void APenancePlayerCharacter::BeginPlay()
{
    Super::BeginPlay();

    Stamina = MaxStamina;
    GetCapsuleComponent()->SetCapsuleSize(CapsuleRadius, StandingCapsuleHeight * 0.5f, true);
    GetCharacterMovement()->SetCrouchedHalfHeight(CrouchingCapsuleHeight * 0.5f);
    GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
    GetCharacterMovement()->MaxWalkSpeedCrouched = CrouchSpeed;
    ForceGroundedMovementMode();
    ResetFirstPersonBodyPose();
    HideOwnerCameraClippingBones();

    UE_LOG(
        LogPenancePlayerBody,
        Log,
        TEXT("Player body initialized. Mesh=%s FPBody=%s OwnerOnly=%s OwnerNoSeeExternal=%s Walk=%.1f Sprint=%.1f Crouch=%.1f CameraRelative=%s"),
        GetMesh() && GetMesh()->GetSkeletalMeshAsset() ? *GetMesh()->GetSkeletalMeshAsset()->GetPathName() : TEXT("None"),
        FirstPersonBodyMesh && FirstPersonBodyMesh->GetSkinnedAsset() ? *FirstPersonBodyMesh->GetSkinnedAsset()->GetPathName() : TEXT("None"),
        FirstPersonBodyMesh && FirstPersonBodyMesh->bOnlyOwnerSee ? TEXT("true") : TEXT("false"),
        GetMesh() && GetMesh()->bOwnerNoSee ? TEXT("true") : TEXT("false"),
        WalkSpeed,
        SprintSpeed,
        CrouchSpeed,
        *FirstPersonCamera->GetRelativeLocation().ToString());

    if (APlayerController* PlayerController = Cast<APlayerController>(Controller))
    {
        PlayerController->SetInputMode(FInputModeGameOnly());
        PlayerController->SetShowMouseCursor(false);

        if (PlayerController->PlayerCameraManager)
        {
            PlayerController->PlayerCameraManager->ViewPitchMin = -82.0f;
            PlayerController->PlayerCameraManager->ViewPitchMax = 82.0f;
        }
    }

    OnStaminaChanged.Broadcast(Stamina, MaxStamina);

    if (FParse::Param(FCommandLine::Get(), TEXT("PenancePlayerBodySelfTest")))
    {
        StartPlayerBodySelfTest();
    }
}

void APenancePlayerCharacter::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    ForceGroundedMovementMode();
    UpdateMovementRules(DeltaSeconds);
    UpdateCrouchRules(DeltaSeconds);
    UpdateNoiseRules(DeltaSeconds);
    UpdateInteractionFocus();
    UpdateFirstPersonBody(DeltaSeconds);
    UpdatePlayerBodySelfTest(DeltaSeconds);
    BroadcastStaminaIfNeeded();
}

void APenancePlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);

    PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &APenancePlayerCharacter::MoveForward);
    PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &APenancePlayerCharacter::MoveRight);
    PlayerInputComponent->BindAxis(TEXT("Turn"), this, &APenancePlayerCharacter::Turn);
    PlayerInputComponent->BindAxis(TEXT("LookUp"), this, &APenancePlayerCharacter::LookUp);

    PlayerInputComponent->BindAction(TEXT("Sprint"), IE_Pressed, this, &APenancePlayerCharacter::StartSprint);
    PlayerInputComponent->BindAction(TEXT("Sprint"), IE_Released, this, &APenancePlayerCharacter::StopSprint);
    PlayerInputComponent->BindAction(TEXT("Crouch"), IE_Pressed, this, &APenancePlayerCharacter::StartCrouchInput);
    PlayerInputComponent->BindAction(TEXT("Crouch"), IE_Released, this, &APenancePlayerCharacter::StopCrouchInput);
    PlayerInputComponent->BindAction(TEXT("Interact"), IE_Pressed, this, &APenancePlayerCharacter::Interact);
    PlayerInputComponent->BindAction(TEXT("Jump"), IE_Pressed, this, &APenancePlayerCharacter::Jump);
    PlayerInputComponent->BindAction(TEXT("Inventory"), IE_Pressed, this, &APenancePlayerCharacter::ToggleInventory);
}

void APenancePlayerCharacter::Jump()
{
    Super::Jump();
    OnPlayerNoise.Broadcast(TEXT("jump"), GetActorLocation(), 0.85f);
}

bool APenancePlayerCharacter::CanJumpInternal_Implementation() const
{
    return Super::CanJumpInternal_Implementation();
}

void APenancePlayerCharacter::MoveForward(float Value)
{
    MoveInput.Y = FMath::Clamp(Value, -1.0f, 1.0f);

    if (!Controller || FMath::IsNearlyZero(Value))
    {
        return;
    }

    const FRotator ControlRotation = Controller->GetControlRotation();
    const FRotator YawRotation(0.0f, ControlRotation.Yaw, 0.0f);
    AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X), Value);
}

void APenancePlayerCharacter::MoveRight(float Value)
{
    MoveInput.X = FMath::Clamp(Value, -1.0f, 1.0f);

    if (!Controller || FMath::IsNearlyZero(Value))
    {
        return;
    }

    const FRotator ControlRotation = Controller->GetControlRotation();
    const FRotator YawRotation(0.0f, ControlRotation.Yaw, 0.0f);
    AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y), Value);
}

void APenancePlayerCharacter::Turn(float Value)
{
    AddControllerYawInput(Value * MouseLookSensitivity);
}

void APenancePlayerCharacter::LookUp(float Value)
{
    AddControllerPitchInput(Value * MouseLookSensitivity);
}

void APenancePlayerCharacter::StartSprint()
{
    bWantsSprint = true;
}

void APenancePlayerCharacter::StopSprint()
{
    bWantsSprint = false;
}

void APenancePlayerCharacter::StartCrouchInput()
{
    bWantsCrouch = true;
}

void APenancePlayerCharacter::StopCrouchInput()
{
    bWantsCrouch = false;
}

void APenancePlayerCharacter::Interact()
{
    FHitResult Hit;
    if (GetInteractionTrace(Hit))
    {
        if (APenanceHingedDoor* Door = Cast<APenanceHingedDoor>(Hit.GetActor()))
        {
            Door->Interact(this);
            OnPlayerNoise.Broadcast(TEXT("door"), Door->GetActorLocation(), 0.8f);
            return;
        }

        if (APenancePickupItem* Pickup = Cast<APenancePickupItem>(Hit.GetActor()))
        {
            Pickup->Interact(this);
            OnPlayerNoise.Broadcast(TEXT("pickup"), Pickup->GetActorLocation(), 0.35f);
            return;
        }
    }

    OnPlayerNoise.Broadcast(TEXT("knock"), GetActorLocation(), 0.7f);
}

void APenancePlayerCharacter::AddInventoryEntry(const FText& ItemName, const FText& ItemDescription, bool bIsNote)
{
    const FString Name = ItemName.IsEmpty() ? FString(TEXT("Unknown")) : ItemName.ToString();
    const FString Description = ItemDescription.IsEmpty() ? FString() : FString(TEXT(" - ")) + ItemDescription.ToString();
    if (bIsNote)
    {
        CollectedNotes.Add(Name + Description);
    }
    else
    {
        InventoryItems.Add(Name + Description);
    }
}

void APenancePlayerCharacter::ToggleInventory()
{
    bInventoryOpen = !bInventoryOpen;
}

float APenancePlayerCharacter::GetStaminaRatio() const
{
    return MaxStamina > 0.0f ? FMath::Clamp(Stamina / MaxStamina, 0.0f, 1.0f) : 0.0f;
}

FString APenancePlayerCharacter::GetFirstPersonBodyMeshPath() const
{
    return FirstPersonBodyMesh && FirstPersonBodyMesh->GetSkinnedAsset()
        ? FirstPersonBodyMesh->GetSkinnedAsset()->GetPathName()
        : FString(TEXT("None"));
}

bool APenancePlayerCharacter::AreOwnerCameraClippingBonesHidden() const
{
    if (!FirstPersonBodyMesh)
    {
        return false;
    }

    const TArray<FName> HiddenBones = {
        TEXT("head"), TEXT("jaw"), TEXT("eye_l"), TEXT("eye_r")
    };

    for (const FName BoneName : HiddenBones)
    {
        if (FirstPersonBodyMesh->GetBoneIndex(BoneName) != INDEX_NONE && !FirstPersonBodyMesh->IsBoneHiddenByName(BoneName))
        {
            return false;
        }
    }

    return bOwnerCameraClippingBonesHidden;
}

void APenancePlayerCharacter::UpdateMovementRules(float DeltaSeconds)
{
    const bool bCanSprint = bWantsSprint && !bWantsCrouch && HasMovementInput() && Stamina > 0.5f;
    float TargetSpeed = WalkSpeed;

    if (bWantsCrouch)
    {
        TargetSpeed = CrouchSpeed;
    }
    else if (bCanSprint)
    {
        TargetSpeed = Stamina <= LowStaminaThreshold ? LowStaminaSprintSpeed : SprintSpeed;
        Stamina = FMath::Max(0.0f, Stamina - StaminaDrainPerSecond * DeltaSeconds);
        StaminaRegenTimer = StaminaRegenDelay;
    }
    else
    {
        StaminaRegenTimer = FMath::Max(0.0f, StaminaRegenTimer - DeltaSeconds);
        if (StaminaRegenTimer <= 0.0f)
        {
            Stamina = FMath::Min(MaxStamina, Stamina + StaminaRegenPerSecond * DeltaSeconds);
        }
    }

    GetCharacterMovement()->MaxWalkSpeed = TargetSpeed;
    GetCharacterMovement()->MaxWalkSpeedCrouched = CrouchSpeed;
}

void APenancePlayerCharacter::UpdateCrouchRules(float DeltaSeconds)
{
    if (bWantsCrouch)
    {
        Crouch(false);
    }
    else
    {
        UnCrouch(false);
    }

    const bool bIsCrouching = bIsCrouched;
    const float TargetEyeHeight = bIsCrouching ? CrouchingCameraHeight : StandingCameraHeight;
    const float TargetRelativeZ = GetCameraRelativeHeightForCurrentCapsule(TargetEyeHeight);
    const FVector CameraLocation = FirstPersonCamera->GetRelativeLocation();
    const float NewRelativeZ = FMath::FInterpTo(CameraLocation.Z, TargetRelativeZ, DeltaSeconds, CrouchTransitionSpeed);
    FirstPersonCamera->SetRelativeLocation(FVector(CameraLocation.X, CameraLocation.Y, NewRelativeZ));

    if (bIsCrouching != bWasCrouching)
    {
        bWasCrouching = bIsCrouching;
        OnCrouchChanged.Broadcast(bIsCrouching);
    }
}

void APenancePlayerCharacter::UpdateNoiseRules(float DeltaSeconds)
{
    const float HorizontalSpeed = FVector(GetVelocity().X, GetVelocity().Y, 0.0f).Size();

    if (HorizontalSpeed > 25.0f)
    {
        SilenceTimer = 0.0f;
    }
    else
    {
        SilenceTimer += DeltaSeconds;
    }

    if (bWantsSprint && !bWantsCrouch && HorizontalSpeed > WalkSpeed && Stamina > 0.5f)
    {
        SprintNoiseTimer -= DeltaSeconds;
        if (SprintNoiseTimer <= 0.0f)
        {
            SprintNoiseTimer = 0.65f;
            OnPlayerNoise.Broadcast(TEXT("sprint_step"), GetActorLocation(), 1.0f);
        }
    }
    else
    {
        SprintNoiseTimer = FMath::Min(SprintNoiseTimer, 0.15f);
    }

    if (SilenceTimer >= 5.0f)
    {
        SilenceTimer = 0.0f;
        OnPlayerNoise.Broadcast(TEXT("silence_window"), GetActorLocation(), 0.45f);
    }
}

void APenancePlayerCharacter::UpdateInteractionFocus()
{
    CurrentInteractionHint = FText::GetEmpty();

    FHitResult Hit;
    if (!GetInteractionTrace(Hit) || !Hit.GetActor())
    {
        return;
    }

    if (Cast<APenanceHingedDoor>(Hit.GetActor()))
    {
        CurrentInteractionHint = FText::FromString(TEXT("E - Open / close door"));
    }
    else if (APenancePickupItem* Pickup = Cast<APenancePickupItem>(Hit.GetActor()))
    {
        CurrentInteractionHint = FText::FromString(FString::Printf(TEXT("E - Pick up %s"), *Pickup->ItemName.ToString()));
    }
}

void APenancePlayerCharacter::UpdateFirstPersonBody(float DeltaSeconds)
{
    if (!FirstPersonBodyMesh)
    {
        return;
    }

    const float HorizontalSpeed = FVector(GetVelocity().X, GetVelocity().Y, 0.0f).Size();
    const bool bHasMoveIntent = HasMovementInput() || (GetCharacterMovement() && GetCharacterMovement()->GetCurrentAcceleration().SizeSquared2D() > KINDA_SMALL_NUMBER);
    const bool bIsMovingForAnimation = HorizontalSpeed > 10.0f && bHasMoveIntent;
    bFirstPersonBodyWalking = bIsMovingForAnimation;

    const float CapsuleHalfHeight = GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight();
    const float DirectionSign = GetFirstPersonMovementDirectionSign(HorizontalSpeed);
    const FVector Velocity2D(GetVelocity().X, GetVelocity().Y, 0.0f);
    const float LocalRightAmount = HorizontalSpeed > 10.0f ? FVector::DotProduct(Velocity2D.GetSafeNormal(), GetActorRightVector()) : 0.0f;
    const float TargetYawOffset = bIsMovingForAnimation ? FMath::Clamp(LocalRightAmount * FirstPersonMovementYawOffsetDegrees, -FirstPersonMovementYawOffsetDegrees, FirstPersonMovementYawOffsetDegrees) : 0.0f;
    FirstPersonBodyYawOffset = FMath::FInterpTo(FirstPersonBodyYawOffset, TargetYawOffset, DeltaSeconds, 8.0f);
    FirstPersonBodyMesh->SetRelativeLocation(FVector(0.0f, 0.0f, -CapsuleHalfHeight - 4.0f));
    FirstPersonBodyMesh->SetRelativeRotation(FRotator(0.0f, -90.0f + FirstPersonBodyYawOffset, 0.0f));

    ApplyFirstPersonBodyAnimation(DeltaSeconds, bIsMovingForAnimation, HorizontalSpeed, DirectionSign);

    if (!bIsMovingForAnimation && bFirstPersonBodyWalking != bFirstPersonBodyWasWalking)
    {
        bFirstPersonBodyWasWalking = bFirstPersonBodyWalking;
        UE_LOG(
            LogPenancePlayerBody,
            Verbose,
            TEXT("First-person body walk animation stopping. Speed=%.2f MoveInput=%s Velocity=%s BlendAlpha=%.2f"),
            HorizontalSpeed,
            *MoveInput.ToString(),
            *GetVelocity().ToString(),
            FirstPersonWalkBlendAlpha);
    }
    else if (bFirstPersonBodyWalking != bFirstPersonBodyWasWalking)
    {
        bFirstPersonBodyWasWalking = bFirstPersonBodyWalking;
        UE_LOG(
            LogPenancePlayerBody,
            Verbose,
            TEXT("First-person body walk animation starting. Animation=%s Speed=%.2f MoveInput=%s Velocity=%s DirectionSign=%.1f"),
            FirstPersonWalkAnimation ? *FirstPersonWalkAnimation->GetPathName() : TEXT("None"),
            HorizontalSpeed,
            *MoveInput.ToString(),
            *GetVelocity().ToString(),
            DirectionSign);
    }
}

void APenancePlayerCharacter::ApplyFirstPersonBodyAnimation(float DeltaSeconds, bool bShouldWalk, float HorizontalSpeed, float DirectionSign)
{
    if (!FirstPersonBodyMesh)
    {
        return;
    }

    if (FirstPersonWalkAnimation)
    {
        FirstPersonBodyMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);

        if (bShouldWalk)
        {
            if (!FirstPersonBodyMesh->IsPlaying())
            {
                FirstPersonBodyMesh->SetAnimation(FirstPersonWalkAnimation);
                FirstPersonBodyMesh->SetPosition(GetFirstPersonIdlePoseTime(), false);
                FirstPersonBodyMesh->Play(true);
            }

            FirstPersonWalkBlendAlpha = FMath::Min(1.0f, FirstPersonWalkBlendAlpha + DeltaSeconds / FMath::Max(FirstPersonWalkBlendInTime, KINDA_SMALL_NUMBER));
            const float BlendedRateScale = FMath::InterpEaseInOut(0.0f, 1.0f, FirstPersonWalkBlendAlpha, 2.0f);
            const float SignedDirection = DirectionSign < 0.0f ? -1.0f : 1.0f;
            FirstPersonLastSignedPlayRate = FMath::Clamp(HorizontalSpeed / WalkSpeed, 0.75f, 1.25f) * SignedDirection;
            FirstPersonBodyMesh->SetPlayRate(FirstPersonLastSignedPlayRate * BlendedRateScale);
        }
        else if (FirstPersonWalkBlendAlpha > 0.0f && FirstPersonBodyMesh->IsPlaying())
        {
            FirstPersonWalkBlendAlpha = FMath::Max(0.0f, FirstPersonWalkBlendAlpha - DeltaSeconds / FMath::Max(FirstPersonWalkBlendOutTime, KINDA_SMALL_NUMBER));
            const float BlendedRateScale = FMath::InterpEaseInOut(0.0f, 1.0f, FirstPersonWalkBlendAlpha, 2.0f);
            FirstPersonBodyMesh->SetPlayRate(FirstPersonLastSignedPlayRate * BlendedRateScale);

            if (FirstPersonWalkBlendAlpha <= KINDA_SMALL_NUMBER)
            {
                ResetFirstPersonBodyPose();
            }
        }
        else
        {
            ResetFirstPersonBodyPose();
        }
    }

    FirstPersonWalkCycleTime = FirstPersonBodyMesh->GetPosition();
}

float APenancePlayerCharacter::GetFirstPersonIdlePoseTime() const
{
    if (!FirstPersonWalkAnimation)
    {
        return 0.0f;
    }

    const float Length = FirstPersonWalkAnimation->GetPlayLength();
    switch (FirstPersonIdlePoseMode)
    {
    case EPenanceFirstPersonIdlePoseMode::LeftFootForward:
        return 0.0f;
    case EPenanceFirstPersonIdlePoseMode::RightFootForward:
        return Length * 0.5f;
    case EPenanceFirstPersonIdlePoseMode::FeetTogether:
    default:
        return Length * 0.25f;
    }
}

float APenancePlayerCharacter::GetFirstPersonMovementDirectionSign(float HorizontalSpeed) const
{
    if (HorizontalSpeed <= 10.0f)
    {
        return 1.0f;
    }

    const FVector Velocity2D(GetVelocity().X, GetVelocity().Y, 0.0f);
    const FVector VelocityDirection = Velocity2D.GetSafeNormal();
    const float ForwardAmount = FVector::DotProduct(VelocityDirection, GetActorForwardVector());
    const float RightAmount = FVector::DotProduct(VelocityDirection, GetActorRightVector());
    return ForwardAmount < -0.35f && FMath::Abs(ForwardAmount) >= FMath::Abs(RightAmount) ? -1.0f : 1.0f;
}

void APenancePlayerCharacter::ResetFirstPersonBodyPose()
{
    if (!FirstPersonBodyMesh)
    {
        return;
    }

    if (FirstPersonWalkAnimation)
    {
        FirstPersonBodyMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);
        FirstPersonBodyMesh->SetAnimation(FirstPersonWalkAnimation);
        FirstPersonBodyMesh->SetPosition(GetFirstPersonIdlePoseTime(), false);
        FirstPersonBodyMesh->Stop();
        FirstPersonWalkBlendAlpha = 0.0f;
        FirstPersonLastSignedPlayRate = 1.0f;
        FirstPersonWalkCycleTime = FirstPersonBodyMesh->GetPosition();
    }
}

void APenancePlayerCharacter::HideOwnerCameraClippingBones()
{
    if (!FirstPersonBodyMesh)
    {
        return;
    }

    const TArray<FName> HiddenBones = {
        TEXT("head"), TEXT("hair_front_l"), TEXT("hair_front_r"), TEXT("jaw"), TEXT("eye_l"), TEXT("eye_r")
    };

    for (const FName BoneName : HiddenBones)
    {
        FirstPersonBodyMesh->HideBoneByName(BoneName, EPhysBodyOp::PBO_None);
    }

    bOwnerCameraClippingBonesHidden = true;
}

void APenancePlayerCharacter::StartPlayerBodySelfTest()
{
    bPlayerBodySelfTestActive = true;
    PlayerBodySelfTestPhase = 0;
    PlayerBodySelfTestPhaseTime = 0.0f;
    PlayerBodySelfTestInitialCycle = FirstPersonWalkCycleTime;
    PlayerBodySelfTestTurnCycleDelta = 0.0f;
    PlayerBodySelfTestMoveStartCycle = 0.0f;
    PlayerBodySelfTestMoveMaxSpeed = 0.0f;
    PlayerBodySelfTestMoveCycleDelta = 0.0f;
    PlayerBodySelfTestStopMinSpeed = TNumericLimits<float>::Max();
    bPlayerBodySelfTestSawWalking = false;
    bPlayerBodySelfTestTurnAnimationPlaying = false;
    bPlayerBodySelfTestSawAnimationPlaying = false;
    PlayerBodySelfTestLines.Reset();
    PlayerBodySelfTestErrors.Reset();

    PlayerBodySelfTestLines.Add(TEXT("PLAYER_FIRST_PERSON_RUNTIME_SELF_TEST_REPORT"));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Map: %s"), GetWorld() ? *GetWorld()->GetName() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Pawn: %s"), *GetName()));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Location: %s"), *GetActorLocation().ToString()));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("External mesh: %s"), GetMesh() && GetMesh()->GetSkeletalMeshAsset() ? *GetMesh()->GetSkeletalMeshAsset()->GetPathName() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("First-person body mesh: %s"), *GetFirstPersonBodyMeshPath()));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("First-person walk animation: %s"), FirstPersonWalkAnimation ? *FirstPersonWalkAnimation->GetPathName() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Camera relative location: %s"), FirstPersonCamera ? *FirstPersonCamera->GetRelativeLocation().ToString() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Body relative location: %s"), FirstPersonBodyMesh ? *FirstPersonBodyMesh->GetRelativeLocation().ToString() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Speeds: Walk=%.1f Sprint=%.1f Crouch=%.1f"), WalkSpeed, SprintSpeed, CrouchSpeed));

    if (APlayerController* PlayerController = Cast<APlayerController>(Controller))
    {
        PlayerController->SetControlRotation(FRotator(-72.0f, 90.0f, 0.0f));
    }

    UE_LOG(LogPenancePlayerBody, Display, TEXT("Started Penance player body self-test."));
}

void APenancePlayerCharacter::UpdatePlayerBodySelfTest(float DeltaSeconds)
{
    if (!bPlayerBodySelfTestActive)
    {
        return;
    }

    PlayerBodySelfTestPhaseTime += DeltaSeconds;
    const float HorizontalSpeed = FVector(GetVelocity().X, GetVelocity().Y, 0.0f).Size();

    if (PlayerBodySelfTestPhase == 0)
    {
        PlayerBodySelfTestInitialCycle = FirstPersonWalkCycleTime;
        if (PlayerBodySelfTestPhaseTime >= 0.35f)
        {
            PlayerBodySelfTestLines.Add(FString::Printf(
                TEXT("Initial: Speed=%.3f Walking=%s AnimPlaying=%s Cycle=%.5f"),
                HorizontalSpeed,
                bFirstPersonBodyWalking ? TEXT("true") : TEXT("false"),
                FirstPersonBodyMesh && FirstPersonBodyMesh->IsPlaying() ? TEXT("true") : TEXT("false"),
                FirstPersonWalkCycleTime));
            PlayerBodySelfTestPhase = 1;
            PlayerBodySelfTestPhaseTime = 0.0f;
        }
        return;
    }

    if (PlayerBodySelfTestPhase == 1)
    {
        if (APlayerController* PlayerController = Cast<APlayerController>(Controller))
        {
            const float Yaw = 90.0f + PlayerBodySelfTestPhaseTime * 120.0f;
            PlayerController->SetControlRotation(FRotator(-72.0f, Yaw, 0.0f));
        }
        PlayerBodySelfTestTurnCycleDelta = FMath::Max(PlayerBodySelfTestTurnCycleDelta, FMath::Abs(FirstPersonWalkCycleTime - PlayerBodySelfTestInitialCycle));
        bPlayerBodySelfTestTurnAnimationPlaying = bPlayerBodySelfTestTurnAnimationPlaying || (FirstPersonBodyMesh && FirstPersonBodyMesh->IsPlaying());
        if (PlayerBodySelfTestPhaseTime >= 1.2f)
        {
            PlayerBodySelfTestLines.Add(FString::Printf(
                TEXT("TurnOnly: Speed=%.3f Walking=%s AnimPlayingSeen=%s CycleDelta=%.5f"),
                HorizontalSpeed,
                bFirstPersonBodyWalking ? TEXT("true") : TEXT("false"),
                bPlayerBodySelfTestTurnAnimationPlaying ? TEXT("true") : TEXT("false"),
                PlayerBodySelfTestTurnCycleDelta));
            PlayerBodySelfTestMoveStartCycle = FirstPersonWalkCycleTime;
            PlayerBodySelfTestPhase = 2;
            PlayerBodySelfTestPhaseTime = 0.0f;
        }
        return;
    }

    if (PlayerBodySelfTestPhase == 2)
    {
        MoveForward(1.0f);
        PlayerBodySelfTestMoveMaxSpeed = FMath::Max(PlayerBodySelfTestMoveMaxSpeed, HorizontalSpeed);
        PlayerBodySelfTestMoveCycleDelta = FMath::Max(PlayerBodySelfTestMoveCycleDelta, FMath::Abs(FirstPersonWalkCycleTime - PlayerBodySelfTestMoveStartCycle));
        bPlayerBodySelfTestSawWalking = bPlayerBodySelfTestSawWalking || bFirstPersonBodyWalking;
        bPlayerBodySelfTestSawAnimationPlaying = bPlayerBodySelfTestSawAnimationPlaying || (FirstPersonBodyMesh && FirstPersonBodyMesh->IsPlaying());
        if (PlayerBodySelfTestPhaseTime >= 1.8f)
        {
            PlayerBodySelfTestLines.Add(FString::Printf(
                TEXT("Move: MaxSpeed=%.3f WalkingSeen=%s AnimPlayingSeen=%s CycleDelta=%.5f"),
                PlayerBodySelfTestMoveMaxSpeed,
                bPlayerBodySelfTestSawWalking ? TEXT("true") : TEXT("false"),
                bPlayerBodySelfTestSawAnimationPlaying ? TEXT("true") : TEXT("false"),
                PlayerBodySelfTestMoveCycleDelta));
            PlayerBodySelfTestPhase = 3;
            PlayerBodySelfTestPhaseTime = 0.0f;
        }
        return;
    }

    if (PlayerBodySelfTestPhase == 3)
    {
        MoveForward(0.0f);
        MoveRight(0.0f);
        if (PlayerBodySelfTestPhaseTime > 0.35f)
        {
            PlayerBodySelfTestStopMinSpeed = FMath::Min(PlayerBodySelfTestStopMinSpeed, HorizontalSpeed);
        }
        if (PlayerBodySelfTestPhaseTime >= 2.0f)
        {
            PlayerBodySelfTestLines.Add(FString::Printf(
                TEXT("Stop: Speed=%.3f MinSpeedAfterBrake=%.3f Walking=%s AnimPlaying=%s Cycle=%.5f"),
                HorizontalSpeed,
                PlayerBodySelfTestStopMinSpeed,
                bFirstPersonBodyWalking ? TEXT("true") : TEXT("false"),
                FirstPersonBodyMesh && FirstPersonBodyMesh->IsPlaying() ? TEXT("true") : TEXT("false"),
                FirstPersonWalkCycleTime));
            FinishPlayerBodySelfTest();
        }
    }
}

void APenancePlayerCharacter::AppendPlayerBodySelfTestCheck(const FString& Label, bool bPassed)
{
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("%s - %s"), bPassed ? TEXT("PASS") : TEXT("FAIL"), *Label));
    if (!bPassed)
    {
        PlayerBodySelfTestErrors.Add(Label);
    }
}

void APenancePlayerCharacter::FinishPlayerBodySelfTest()
{
    bPlayerBodySelfTestActive = false;

    int32 PlayerCharacterCount = 0;
    for (TActorIterator<APenancePlayerCharacter> It(GetWorld()); It; ++It)
    {
        ++PlayerCharacterCount;
    }

    PlayerBodySelfTestLines.Add(TEXT(""));
    PlayerBodySelfTestLines.Add(TEXT("Acceptance checks:"));
    AppendPlayerBodySelfTestCheck(TEXT("player spawns correctly"), IsValid(this) && Controller != nullptr);
    AppendPlayerBodySelfTestCheck(TEXT("single player character in runtime world"), PlayerCharacterCount == 1);
    AppendPlayerBodySelfTestCheck(TEXT("camera component exists"), FirstPersonCamera != nullptr);
    AppendPlayerBodySelfTestCheck(TEXT("first-person body component exists"), FirstPersonBodyMesh != nullptr);
    AppendPlayerBodySelfTestCheck(TEXT("first-person body uses fixed imported mesh"), GetFirstPersonBodyMeshPath().Contains(TEXT("/Game/Player/FirstPerson/SK_Player_FirstPersonBody")));
    AppendPlayerBodySelfTestCheck(TEXT("first-person walk-in-place animation is loaded"), FirstPersonWalkAnimation && FirstPersonWalkAnimation->GetPathName().Contains(TEXT("/Game/Player/FirstPerson/AN_Player_Walk_Verify")));
    AppendPlayerBodySelfTestCheck(TEXT("external full body is hidden from owner"), GetMesh() && GetMesh()->bOwnerNoSee);
    AppendPlayerBodySelfTestCheck(TEXT("first-person body is owner-only"), FirstPersonBodyMesh && FirstPersonBodyMesh->bOnlyOwnerSee);
    AppendPlayerBodySelfTestCheck(TEXT("first-person body remains visible to owner"), FirstPersonBodyMesh && !FirstPersonBodyMesh->bOwnerNoSee);
    AppendPlayerBodySelfTestCheck(TEXT("owner camera clipping bones are hidden"), AreOwnerCameraClippingBonesHidden());
    AppendPlayerBodySelfTestCheck(TEXT("walk speed is 250 UU/s"), FMath::IsNearlyEqual(WalkSpeed, 250.0f));
    AppendPlayerBodySelfTestCheck(TEXT("sprint speed is 550 UU/s"), FMath::IsNearlyEqual(SprintSpeed, 550.0f));
    AppendPlayerBodySelfTestCheck(TEXT("crouch speed is 140 UU/s"), FMath::IsNearlyEqual(CrouchSpeed, 140.0f));
    AppendPlayerBodySelfTestCheck(TEXT("turning in place does not trigger walking"), PlayerBodySelfTestTurnCycleDelta <= 0.001f && !bPlayerBodySelfTestTurnAnimationPlaying);
    AppendPlayerBodySelfTestCheck(TEXT("moving starts walk cycle"), bPlayerBodySelfTestSawWalking && bPlayerBodySelfTestSawAnimationPlaying && PlayerBodySelfTestMoveCycleDelta > 0.01f && PlayerBodySelfTestMoveMaxSpeed > 25.0f);
    AppendPlayerBodySelfTestCheck(TEXT("stopping stops walking"), PlayerBodySelfTestStopMinSpeed < 15.0f && !bFirstPersonBodyWalking && FirstPersonBodyMesh && !FirstPersonBodyMesh->IsPlaying());

    PlayerBodySelfTestLines.Add(TEXT(""));
    PlayerBodySelfTestLines.Add(TEXT("Errors:"));
    if (PlayerBodySelfTestErrors.IsEmpty())
    {
        PlayerBodySelfTestLines.Add(TEXT("- none"));
    }
    else
    {
        for (const FString& Error : PlayerBodySelfTestErrors)
        {
            PlayerBodySelfTestLines.Add(FString::Printf(TEXT("- %s"), *Error));
        }
    }

    const FString ReportPath = FPaths::ProjectSavedDir() / TEXT("PlayerFirstPersonRuntimeSelfTestReport.txt");
    FFileHelper::SaveStringArrayToFile(PlayerBodySelfTestLines, *ReportPath);
    UE_LOG(LogPenancePlayerBody, Display, TEXT("Finished Penance player body self-test. Report=%s Errors=%d"), *ReportPath, PlayerBodySelfTestErrors.Num());
    FPlatformMisc::RequestExit(false);
}

void APenancePlayerCharacter::BroadcastStaminaIfNeeded()
{
    const float Ratio = MaxStamina > 0.0f ? Stamina / MaxStamina : 0.0f;
    if (FMath::Abs(Ratio - LastBroadcastStaminaRatio) < 0.01f)
    {
        return;
    }

    LastBroadcastStaminaRatio = Ratio;
    OnStaminaChanged.Broadcast(Stamina, MaxStamina);
}

void APenancePlayerCharacter::ForceGroundedMovementMode()
{
    UCharacterMovementComponent* Movement = GetCharacterMovement();
    if (Movement->MovementMode == MOVE_Flying)
    {
        Movement->SetMovementMode(Movement->IsMovingOnGround() ? MOVE_Walking : MOVE_Falling);
    }
}

float APenancePlayerCharacter::GetCameraRelativeHeightForCurrentCapsule(float EyeHeight) const
{
    const float CapsuleHalfHeight = GetCapsuleComponent() ? GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight() : StandingCapsuleHeight * 0.5f;
    return EyeHeight - CapsuleHalfHeight;
}

bool APenancePlayerCharacter::HasMovementInput() const
{
    return MoveInput.SizeSquared() > KINDA_SMALL_NUMBER;
}

bool APenancePlayerCharacter::GetInteractionTrace(FHitResult& OutHit) const
{
    if (!FirstPersonCamera)
    {
        return false;
    }

    const FVector Start = FirstPersonCamera->GetComponentLocation();
    const FVector End = Start + FirstPersonCamera->GetForwardVector() * InteractionDistance;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(PenanceInteractTrace), false, this);
    return GetWorld() && GetWorld()->LineTraceSingleByChannel(OutHit, Start, End, ECC_Visibility, Params);
}
