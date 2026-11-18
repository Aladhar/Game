#include "PenancePlayerCharacter.h"

#include "ABP_Player.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimInstance.h"
#include "Camera/CameraComponent.h"
#include "Camera/CameraTypes.h"
#include "GameFramework/SpringArmComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputActionValue.h"
#include "Engine/LocalPlayer.h"
#include "TimerManager.h"
#include "Components/CapsuleComponent.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "Engine/CollisionProfile.h"
#include "Components/SceneComponent.h"
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
#include "PenanceStreamingDoor.h"
#include "PenancePickupItem.h"
#include "UObject/ConstructorHelpers.h"
#include "EngineUtils.h"

DEFINE_LOG_CATEGORY_STATIC(LogPenancePlayerBody, Log, All);

APenancePlayerCharacter::APenancePlayerCharacter()
{
    PrimaryActorTick.bCanEverTick = true;

    GetCapsuleComponent()->InitCapsuleSize(CapsuleRadius, StandingCapsuleHeight * 0.5f);

    USkeletalMeshComponent* PlayerMeshComponent = GetMesh();
    static ConstructorHelpers::FObjectFinder<USkeletalMesh> PlayerMeshAsset(TEXT("/Game/Player/MeshyPlayer/Untitled.Untitled"));
    if (PlayerMeshAsset.Succeeded())
    {
        PlayerMeshComponent->SetSkeletalMesh(PlayerMeshAsset.Object);
        PlayerMeshComponent->SetPhysicsAsset(LoadObject<UPhysicsAsset>(nullptr, TEXT("/Game/Player/MeshyPlayer/Untitled_PhysicsAsset.Untitled_PhysicsAsset")));
    }
    PlayerMeshComponent->SetupAttachment(GetCapsuleComponent());
    PlayerMeshComponent->SetRelativeLocation(FVector(0.0f, 0.0f, -StandingCapsuleHeight * 0.5f));
    PlayerMeshComponent->SetRelativeRotation(FRotator(0.0f, PlayerMeshVisualYawOffsetDegrees, 0.0f));
    PlayerMeshComponent->SetRelativeScale3D(FVector(1.0f));
    PlayerMeshComponent->SetOwnerNoSee(false);
    PlayerMeshComponent->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);
    PlayerMeshComponent->bCastHiddenShadow = true;

    FirstPersonBodyMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("Mesh_FP_Body"));
    FirstPersonBodyMesh->SetupAttachment(GetCapsuleComponent());
    FirstPersonBodyMesh->SetRelativeLocation(FVector(0.0f, 0.0f, -StandingCapsuleHeight * 0.5f));
    FirstPersonBodyMesh->SetRelativeRotation(FRotator(0.0f, PlayerMeshVisualYawOffsetDegrees, 0.0f));
    FirstPersonBodyMesh->SetRelativeScale3D(FVector(1.0f));
    FirstPersonBodyMesh->SetVisibility(false, true);
    FirstPersonBodyMesh->SetHiddenInGame(true, true);
    FirstPersonBodyMesh->SetCollisionProfileName(UCollisionProfile::NoCollision_ProfileName);

    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(GetCapsuleComponent());
    CameraBoom->SetRelativeLocation(FVector(0.0f, 0.0f, 72.0f));
    CameraBoom->TargetArmLength = 320.0f;
    CameraBoom->bUsePawnControlRotation = true;
    CameraBoom->bEnableCameraLag = true;
    CameraBoom->CameraLagSpeed = 12.0f;
    CameraBoom->bDoCollisionTest = true;

    FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
    FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    FollowCamera->bUsePawnControlRotation = false;
    FollowCamera->FieldOfView = 85.0f;

    FirstPersonCameraRoot = CreateDefaultSubobject<USceneComponent>(TEXT("FirstPersonCameraRoot"));
    FirstPersonCameraRoot->SetupAttachment(GetCapsuleComponent());
    FirstPersonCameraRoot->SetRelativeLocation(FVector(0.0f, 0.0f, GetCameraRelativeHeightForCurrentCapsule(StandingCameraHeight)));

    FirstPersonCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FirstPersonCamera"));
    FirstPersonCamera->SetupAttachment(FirstPersonCameraRoot);
    FirstPersonCamera->SetRelativeLocation(FVector::ZeroVector);
    FirstPersonCamera->SetRelativeRotation(FRotator::ZeroRotator);
    FirstPersonCamera->bUsePawnControlRotation = true;
    FirstPersonCamera->FieldOfView = 78.0f;
    FirstPersonCamera->bAutoActivate = false;

    static ConstructorHelpers::FObjectFinder<UInputMappingContext> MappingAsset(TEXT("/Game/Player/Input/IMC_Player.IMC_Player"));
    if (MappingAsset.Succeeded()) PlayerMappingContext = MappingAsset.Object;
    static ConstructorHelpers::FObjectFinder<UInputAction> MoveInputAsset(TEXT("/Game/Player/Input/IA_Move.IA_Move"));
    if (MoveInputAsset.Succeeded()) MoveAction = MoveInputAsset.Object;
    static ConstructorHelpers::FObjectFinder<UInputAction> LookInputAsset(TEXT("/Game/Player/Input/IA_Look.IA_Look"));
    if (LookInputAsset.Succeeded()) LookAction = LookInputAsset.Object;
    static ConstructorHelpers::FObjectFinder<UInputAction> SprintInputAsset(TEXT("/Game/Player/Input/IA_Sprint.IA_Sprint"));
    if (SprintInputAsset.Succeeded()) SprintAction = SprintInputAsset.Object;
    static ConstructorHelpers::FObjectFinder<UInputAction> CrouchInputAsset(TEXT("/Game/Player/Input/IA_Crouch.IA_Crouch"));
    if (CrouchInputAsset.Succeeded()) CrouchAction = CrouchInputAsset.Object;
    static ConstructorHelpers::FObjectFinder<UInputAction> InteractInputAsset(TEXT("/Game/Player/Input/IA_Interact.IA_Interact"));
    if (InteractInputAsset.Succeeded()) InteractAction = InteractInputAsset.Object;
    static ConstructorHelpers::FObjectFinder<UInputAction> JumpInputAsset(TEXT("/Game/Player/Input/IA_Jump.IA_Jump"));
    if (JumpInputAsset.Succeeded()) JumpAction = JumpInputAsset.Object;
    static ConstructorHelpers::FObjectFinder<UInputAction> InventoryInputAsset(TEXT("/Game/Player/Input/IA_Inventory.IA_Inventory"));
    if (InventoryInputAsset.Succeeded()) InventoryAction = InventoryInputAsset.Object;
    static ConstructorHelpers::FObjectFinder<UInputAction> TestShotInputAsset(TEXT("/Game/Player/Input/IA_TestShot.IA_TestShot"));
    if (TestShotInputAsset.Succeeded()) TestShotAction = TestShotInputAsset.Object;
    static ConstructorHelpers::FObjectFinder<UAnimMontage> ShotMontageAsset(TEXT("/Game/Player/Animations/AM_CharacterShot.AM_CharacterShot"));
    if (ShotMontageAsset.Succeeded()) ShotReactionMontage = ShotMontageAsset.Object;
    static ConstructorHelpers::FObjectFinder<UAnimMontage> ScaredMontageAsset(TEXT("/Game/Player/Animations/AM_ScaredIdle.AM_ScaredIdle"));
    if (ScaredMontageAsset.Succeeded()) ScaredMontage = ScaredMontageAsset.Object;

    bUseControllerRotationYaw = true;
    bUseControllerRotationPitch = false;
    bUseControllerRotationRoll = false;

    UCharacterMovementComponent* Movement = GetCharacterMovement();
    Movement->bOrientRotationToMovement = false;
    Movement->RotationRate = FRotator(0.0f, 360.0f, 0.0f);
    Movement->DefaultLandMovementMode = MOVE_Walking;
    Movement->MaxWalkSpeed = WalkSpeed;
    Movement->MaxWalkSpeedCrouched = CrouchSpeed;
    Movement->MaxAcceleration = 1000.0f;
    Movement->BrakingDecelerationWalking = 1000.0f;
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
    if (PlayerMappingContext)
    {
        if (APlayerController* PlayerController = Cast<APlayerController>(Controller))
        {
            if (ULocalPlayer* LocalPlayer = PlayerController->GetLocalPlayer())
            {
                if (UEnhancedInputLocalPlayerSubsystem* InputSubsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
                {
                    InputSubsystem->AddMappingContext(PlayerMappingContext, 0);
                }
            }
        }
    }
    GetCapsuleComponent()->SetCapsuleSize(CapsuleRadius, StandingCapsuleHeight * 0.5f, true);
    GetCharacterMovement()->SetCrouchedHalfHeight(CrouchingCapsuleHeight * 0.5f);
    GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
    GetCharacterMovement()->MaxWalkSpeedCrouched = CrouchSpeed;
    ForceGroundedMovementMode();
    ResetFirstPersonBodyPose();
    HideOwnerCameraClippingBones();
    if (FirstPersonCamera) FirstPersonCamera->Deactivate();
    if (GetMesh())
    {
        GetMesh()->SetOwnerNoSee(false);
        GetMesh()->SetHiddenInGame(false);
    }
    GetWorldTimerManager().SetTimer(InactivityTimerHandle, this, &APenancePlayerCharacter::HandleInactivityTimeout, 30.0f, false);

    UE_LOG(
        LogPenancePlayerBody,
        Log,
        TEXT("Player body initialized. Mesh=%s FPBody=%s AnimClass=%s OwnerOnly=%s OwnerNoSeeExternal=%s ForwardAnim=%s BackwardAnim=%s Walk=%.1f Sprint=%.1f Crouch=%.1f CameraRootRelative=%s CameraRelative=%s MeshVisualYawOffset=%.1f BodyYawFollow=%.1f"),
        GetMesh() && GetMesh()->GetSkeletalMeshAsset() ? *GetMesh()->GetSkeletalMeshAsset()->GetPathName() : TEXT("None"),
        FirstPersonBodyMesh && FirstPersonBodyMesh->GetSkinnedAsset() ? *FirstPersonBodyMesh->GetSkinnedAsset()->GetPathName() : TEXT("None"),
        GetMesh() && GetMesh()->GetAnimInstance() ? *GetMesh()->GetAnimInstance()->GetClass()->GetName() : TEXT("None"),
        FirstPersonBodyMesh && FirstPersonBodyMesh->bOnlyOwnerSee ? TEXT("true") : TEXT("false"),
        GetMesh() && GetMesh()->bOwnerNoSee ? TEXT("true") : TEXT("false"),
        FirstPersonForwardWalkAnimation ? *FirstPersonForwardWalkAnimation->GetPathName() : TEXT("None"),
        FirstPersonBackwardWalkAnimation ? *FirstPersonBackwardWalkAnimation->GetPathName() : TEXT("None"),
        WalkSpeed,
        SprintSpeed,
        CrouchSpeed,
        FirstPersonCameraRoot ? *FirstPersonCameraRoot->GetRelativeLocation().ToString() : TEXT("None"),
        FirstPersonCamera ? *FirstPersonCamera->GetRelativeLocation().ToString() : TEXT("None"),
        PlayerMeshVisualYawOffsetDegrees,
        BodyYawFollowSpeed);

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
    UpdateCameraDrivenBodyYaw(DeltaSeconds);
    UpdateFirstPersonBody(DeltaSeconds);
    UpdatePlayerBodySelfTest(DeltaSeconds);
    BroadcastStaminaIfNeeded();
}

void APenancePlayerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);

    if (UEnhancedInputComponent* EnhancedInput = Cast<UEnhancedInputComponent>(PlayerInputComponent))
    {
        if (MoveAction)
        {
            EnhancedInput->BindAction(MoveAction, ETriggerEvent::Triggered, this, &APenancePlayerCharacter::MoveEnhanced);
            EnhancedInput->BindAction(MoveAction, ETriggerEvent::Completed, this, &APenancePlayerCharacter::StopMoveEnhanced);
            EnhancedInput->BindAction(MoveAction, ETriggerEvent::Canceled, this, &APenancePlayerCharacter::StopMoveEnhanced);
        }
        if (LookAction) EnhancedInput->BindAction(LookAction, ETriggerEvent::Triggered, this, &APenancePlayerCharacter::LookEnhanced);
        if (SprintAction)
        {
            EnhancedInput->BindAction(SprintAction, ETriggerEvent::Started, this, &APenancePlayerCharacter::StartSprintEnhanced);
            EnhancedInput->BindAction(SprintAction, ETriggerEvent::Completed, this, &APenancePlayerCharacter::StopSprintEnhanced);
            EnhancedInput->BindAction(SprintAction, ETriggerEvent::Canceled, this, &APenancePlayerCharacter::StopSprintEnhanced);
        }
        if (CrouchAction)
        {
            EnhancedInput->BindAction(CrouchAction, ETriggerEvent::Started, this, &APenancePlayerCharacter::StartCrouchEnhanced);
            EnhancedInput->BindAction(CrouchAction, ETriggerEvent::Completed, this, &APenancePlayerCharacter::StopCrouchEnhanced);
            EnhancedInput->BindAction(CrouchAction, ETriggerEvent::Canceled, this, &APenancePlayerCharacter::StopCrouchEnhanced);
        }
        if (InteractAction) EnhancedInput->BindAction(InteractAction, ETriggerEvent::Started, this, &APenancePlayerCharacter::Interact);
        if (JumpAction) EnhancedInput->BindAction(JumpAction, ETriggerEvent::Started, this, &APenancePlayerCharacter::Jump);
        if (InventoryAction) EnhancedInput->BindAction(InventoryAction, ETriggerEvent::Started, this, &APenancePlayerCharacter::ToggleInventory);
        if (TestShotAction) EnhancedInput->BindAction(TestShotAction, ETriggerEvent::Started, this, &APenancePlayerCharacter::StartShotReactionEnhanced);
    }
}

void APenancePlayerCharacter::MoveEnhanced(const FInputActionValue& Value)
{
    MoveInput = Value.Get<FVector2D>();
    if (MoveInput.SizeSquared() > 0.0025f)
    {
        RegisterMeaningfulActivity();
        if (Controller)
        {
            const FRotator YawRotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
            AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X), MoveInput.Y);
            AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y), MoveInput.X);
        }
    }
}

void APenancePlayerCharacter::StopMoveEnhanced()
{
    MoveInput = FVector2D::ZeroVector;
    RegisterMeaningfulActivity();
}

void APenancePlayerCharacter::LookEnhanced(const FInputActionValue& Value)
{
    const FVector2D Look = Value.Get<FVector2D>();
    if (Controller && !Controller->IsLookInputIgnored() && !Look.IsNearlyZero(0.01f))
    {
        RegisterMeaningfulActivity();
        AddControllerYawInput(Look.X * MouseLookSensitivity);
        AddControllerPitchInput(Look.Y * MouseLookSensitivity);
    }
}

void APenancePlayerCharacter::StartSprintEnhanced()
{
    bWantsSprint = true;
    RegisterMeaningfulActivity();
}

void APenancePlayerCharacter::StopSprintEnhanced()
{
    bWantsSprint = false;
}

void APenancePlayerCharacter::StartShotReactionEnhanced()
{
    PlayShotReaction();
}

void APenancePlayerCharacter::StartCrouchEnhanced()
{
    bWantsCrouch = true;
    RegisterMeaningfulActivity();
}

void APenancePlayerCharacter::StopCrouchEnhanced()
{
    bWantsCrouch = false;
    RegisterMeaningfulActivity();
}

void APenancePlayerCharacter::RegisterMeaningfulActivity()
{
    if (!GetWorld()) return;
    GetWorldTimerManager().ClearTimer(InactivityTimerHandle);
    GetWorldTimerManager().SetTimer(InactivityTimerHandle, this, &APenancePlayerCharacter::HandleInactivityTimeout, 30.0f, false);
    if (ScaredMontage && GetMesh() && GetMesh()->GetAnimInstance() && GetMesh()->GetAnimInstance()->Montage_IsPlaying(ScaredMontage))
    {
        GetMesh()->GetAnimInstance()->Montage_Stop(0.25f, ScaredMontage);
    }
}

void APenancePlayerCharacter::HandleInactivityTimeout()
{
    // Held movement and mouse input already rearm the timer in their handlers.
    if (GetVelocity().SizeSquared2D() > 100.0f)
    {
        RegisterMeaningfulActivity();
        return;
    }
    if (ScaredMontage && GetMesh() && GetMesh()->GetAnimInstance() && !GetMesh()->GetAnimInstance()->Montage_IsPlaying(ScaredMontage))
    {
        const float MontageLength = GetMesh()->GetAnimInstance()->Montage_Play(ScaredMontage, 1.0f);
        UE_LOG(LogPenancePlayerBody, Verbose, TEXT("Inactivity triggered scared montage (play length %.2f seconds)."), MontageLength);
    }
}

void APenancePlayerCharacter::PlayShotReaction()
{
    if (ShotReactionMontage && GetMesh() && GetMesh()->GetAnimInstance()
        && !GetMesh()->GetAnimInstance()->Montage_IsPlaying(ShotReactionMontage))
    {
        GetMesh()->GetAnimInstance()->Montage_Play(ShotReactionMontage, 1.0f);
    }
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
        if (APenanceStreamingDoor* Portal = Cast<APenanceStreamingDoor>(Hit.GetActor()))
        {
            Portal->Interact(this);
            OnPlayerNoise.Broadcast(TEXT("door"), Portal->GetActorLocation(), 0.6f);
            return;
        }

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
    if (CameraBoom)
    {
        FVector Pivot = CameraBoom->GetRelativeLocation();
        Pivot.Z = FMath::FInterpTo(Pivot.Z, bIsCrouching ? 48.0f : 72.0f, DeltaSeconds, CrouchTransitionSpeed);
        CameraBoom->SetRelativeLocation(Pivot);
    }

    if (FirstPersonCameraRoot)
    {
        const FVector CameraRootLocation = FirstPersonCameraRoot->GetRelativeLocation();
        const float NewRelativeZ = FMath::FInterpTo(CameraRootLocation.Z, TargetRelativeZ, DeltaSeconds, CrouchTransitionSpeed);
        FirstPersonCameraRoot->SetRelativeLocation(FVector(CameraRootLocation.X, CameraRootLocation.Y, NewRelativeZ));
    }

    if (bIsCrouching != bWasCrouching)
    {
        bWasCrouching = bIsCrouching;
        OnCrouchChanged.Broadcast(bIsCrouching);
    }
}

void APenancePlayerCharacter::UpdateCameraDrivenBodyYaw(float DeltaSeconds)
{
    (void)DeltaSeconds;
    if (!Controller)
    {
        BodyYaw = GetActorRotation().Yaw;
        CameraYaw = BodyYaw;
        AimPitch = 0.0f;
        FirstPersonTurnYawDelta = 0.0f;
        return;
    }

    const FRotator ControlRotation = Controller->GetControlRotation();
    CameraYaw = ControlRotation.Yaw;
    AimPitch = FMath::FindDeltaAngleDegrees(0.0f, ControlRotation.Pitch);
    BodyYaw = GetActorRotation().Yaw;
    FirstPersonTurnYawDelta = FMath::FindDeltaAngleDegrees(BodyYaw, CameraYaw);
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

    const FVector Velocity2D(GetVelocity().X, GetVelocity().Y, 0.0f);
    const float HorizontalSpeed = Velocity2D.Size();
    FirstPersonForwardSpeed = FVector::DotProduct(Velocity2D, GetActorForwardVector());
    FirstPersonRightSpeed = FVector::DotProduct(Velocity2D, GetActorRightVector());
    const bool bHasMoveIntent = HasMovementInput() || (GetCharacterMovement() && GetCharacterMovement()->GetCurrentAcceleration().SizeSquared2D() > KINDA_SMALL_NUMBER);
    const bool bIsMovingForAnimation = HorizontalSpeed > 10.0f && bHasMoveIntent;
    EPenanceFirstPersonLocomotionState DesiredState = EPenanceFirstPersonLocomotionState::Idle;
    if (bIsMovingForAnimation)
    {
        DesiredState = FirstPersonForwardSpeed < -10.0f
            ? EPenanceFirstPersonLocomotionState::WalkBackward
            : EPenanceFirstPersonLocomotionState::WalkForward;
    }
    bFirstPersonBodyWalking = bIsMovingForAnimation;

    const float CapsuleHalfHeight = GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight();
    const float LocalRightAmount = HorizontalSpeed > 10.0f ? FirstPersonRightSpeed / FMath::Max(HorizontalSpeed, 1.0f) : 0.0f;
    const float TargetYawOffset = bIsMovingForAnimation ? FMath::Clamp(LocalRightAmount * FirstPersonMovementYawOffsetDegrees, -FirstPersonMovementYawOffsetDegrees, FirstPersonMovementYawOffsetDegrees) : 0.0f;
    FirstPersonBodyYawOffset = FMath::FInterpTo(FirstPersonBodyYawOffset, TargetYawOffset, DeltaSeconds, 8.0f);
    FirstPersonBodyMesh->SetRelativeLocation(FVector(0.0f, 0.0f, -CapsuleHalfHeight - 4.0f));
    FirstPersonBodyMesh->SetRelativeRotation(FRotator(0.0f, PlayerMeshVisualYawOffsetDegrees + FirstPersonBodyYawOffset, 0.0f));

    if (const UABP_Player* PlayerAnim = Cast<UABP_Player>(FirstPersonBodyMesh->GetAnimInstance()))
    {
        FirstPersonWalkCycleTime = PlayerAnim->ActiveAssetTime;
        FirstPersonLastPlayRate = PlayerAnim->WalkPlayRate;
        if (PlayerAnim->LocomotionState == EPenancePlayerAnimState::WalkBackward)
        {
            FirstPersonLocomotionState = EPenanceFirstPersonLocomotionState::WalkBackward;
        }
        else if (PlayerAnim->bIsMoving)
        {
            FirstPersonLocomotionState = EPenanceFirstPersonLocomotionState::WalkForward;
        }
        else
        {
            FirstPersonLocomotionState = EPenanceFirstPersonLocomotionState::Idle;
        }
    }

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
            TEXT("First-person body ABP walk starting. State=%d Speed=%.2f Forward=%.2f Right=%.2f MoveInput=%s Velocity=%s"),
            static_cast<int32>(DesiredState),
            HorizontalSpeed,
            FirstPersonForwardSpeed,
            FirstPersonRightSpeed,
            *MoveInput.ToString(),
            *GetVelocity().ToString());
    }
}

void APenancePlayerCharacter::ResetFirstPersonBodyPose()
{
    if (!FirstPersonBodyMesh)
    {
        return;
    }

    FirstPersonWalkBlendAlpha = 0.0f;
    FirstPersonLastPlayRate = 1.0f;
    FirstPersonWalkCycleTime = 0.0f;
    FirstPersonLocomotionState = EPenanceFirstPersonLocomotionState::Idle;
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
    PlayerBodySelfTestMaxTurnYawDelta = 0.0f;
    PlayerBodySelfTestPitchCycleDelta = 0.0f;
    PlayerBodySelfTestMaxBodyPitch = 0.0f;
    PlayerBodySelfTestMoveStartCycle = 0.0f;
    PlayerBodySelfTestMoveMaxSpeed = 0.0f;
    PlayerBodySelfTestMoveCycleDelta = 0.0f;
    PlayerBodySelfTestBackwardMaxSpeed = 0.0f;
    PlayerBodySelfTestBackwardCycleDelta = 0.0f;
    PlayerBodySelfTestStopMinSpeed = TNumericLimits<float>::Max();
    bPlayerBodySelfTestSawWalking = false;
    bPlayerBodySelfTestSawBackwardWalking = false;
    bPlayerBodySelfTestTurnAnimationPlaying = false;
    bPlayerBodySelfTestPitchAnimationPlaying = false;
    bPlayerBodySelfTestSawAnimationPlaying = false;
    bPlayerBodySelfTestSawBackwardAnimationPlaying = false;
    PlayerBodySelfTestLines.Reset();
    PlayerBodySelfTestErrors.Reset();

    PlayerBodySelfTestLines.Add(TEXT("PLAYER_FIRST_PERSON_RUNTIME_SELF_TEST_REPORT"));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Map: %s"), GetWorld() ? *GetWorld()->GetName() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Pawn: %s"), *GetName()));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Location: %s"), *GetActorLocation().ToString()));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("External mesh: %s"), GetMesh() && GetMesh()->GetSkeletalMeshAsset() ? *GetMesh()->GetSkeletalMeshAsset()->GetPathName() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("First-person body mesh: %s"), *GetFirstPersonBodyMeshPath()));
    const UABP_Player* PlayerAnim = FirstPersonBodyMesh ? Cast<UABP_Player>(FirstPersonBodyMesh->GetAnimInstance()) : nullptr;
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("First-person anim instance: %s"), PlayerAnim ? *PlayerAnim->GetClass()->GetName() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Idle_FeetTogether: %s"), PlayerAnim && PlayerAnim->IdleFeetTogether ? *PlayerAnim->IdleFeetTogether->GetPathName() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Walk_Forward_Loop: %s"), PlayerAnim && PlayerAnim->WalkForwardLoop ? *PlayerAnim->WalkForwardLoop->GetPathName() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Walk_Backward_Loop: %s"), PlayerAnim && PlayerAnim->WalkBackwardLoop ? *PlayerAnim->WalkBackwardLoop->GetPathName() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Camera root relative location: %s"), FirstPersonCameraRoot ? *FirstPersonCameraRoot->GetRelativeLocation().ToString() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Camera relative location: %s"), FirstPersonCamera ? *FirstPersonCamera->GetRelativeLocation().ToString() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Body relative location: %s"), FirstPersonBodyMesh ? *FirstPersonBodyMesh->GetRelativeLocation().ToString() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Body relative rotation: %s"), FirstPersonBodyMesh ? *FirstPersonBodyMesh->GetRelativeRotation().ToString() : TEXT("None")));
    PlayerBodySelfTestLines.Add(FString::Printf(TEXT("Mesh visual yaw offset: %.3f"), PlayerMeshVisualYawOffsetDegrees));
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
    const UABP_Player* PlayerAnim = FirstPersonBodyMesh ? Cast<UABP_Player>(FirstPersonBodyMesh->GetAnimInstance()) : nullptr;
    const bool bABPActive = PlayerAnim && PlayerAnim->IsActivelyPlayingLocomotion();
    const bool bABPWalkingState = PlayerAnim && (
        PlayerAnim->LocomotionState == EPenancePlayerAnimState::StartWalkForward
        || PlayerAnim->LocomotionState == EPenancePlayerAnimState::WalkForward
        || PlayerAnim->LocomotionState == EPenancePlayerAnimState::WalkBackward
        || PlayerAnim->LocomotionState == EPenancePlayerAnimState::StopWalkForward);
    const bool bABPBackwardState = PlayerAnim && PlayerAnim->LocomotionState == EPenancePlayerAnimState::WalkBackward;

    if (PlayerBodySelfTestPhase == 0)
    {
        PlayerBodySelfTestInitialCycle = FirstPersonWalkCycleTime;
        if (PlayerBodySelfTestPhaseTime >= 0.35f)
        {
            PlayerBodySelfTestLines.Add(FString::Printf(
                TEXT("Initial: Speed=%.3f ForwardSpeed=%.3f RightSpeed=%.3f CameraYaw=%.3f BodyYaw=%.3f AimPitch=%.3f TurnYawDelta=%.3f State=%d Walking=%s AnimPlaying=%s Cycle=%.5f"),
                HorizontalSpeed,
                FirstPersonForwardSpeed,
                FirstPersonRightSpeed,
                CameraYaw,
                BodyYaw,
                AimPitch,
                FirstPersonTurnYawDelta,
                static_cast<int32>(FirstPersonLocomotionState),
                bFirstPersonBodyWalking ? TEXT("true") : TEXT("false"),
                bABPActive ? TEXT("true") : TEXT("false"),
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
        PlayerBodySelfTestMaxTurnYawDelta = FMath::Max(PlayerBodySelfTestMaxTurnYawDelta, FMath::Abs(FirstPersonTurnYawDelta));
        bPlayerBodySelfTestTurnAnimationPlaying = bPlayerBodySelfTestTurnAnimationPlaying || bABPWalkingState;
        if (PlayerBodySelfTestPhaseTime >= 1.2f)
        {
            PlayerBodySelfTestLines.Add(FString::Printf(
                TEXT("YawTurnOnly: Speed=%.3f ForwardSpeed=%.3f RightSpeed=%.3f CameraYaw=%.3f BodyYaw=%.3f MaxYawDelta=%.3f AimPitch=%.3f State=%d Walking=%s AnimPlayingSeen=%s CycleDelta=%.5f"),
                HorizontalSpeed,
                FirstPersonForwardSpeed,
                FirstPersonRightSpeed,
                CameraYaw,
                BodyYaw,
                PlayerBodySelfTestMaxTurnYawDelta,
                AimPitch,
                static_cast<int32>(FirstPersonLocomotionState),
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
        if (APlayerController* PlayerController = Cast<APlayerController>(Controller))
        {
            const float Pitch = FMath::Sin(PlayerBodySelfTestPhaseTime * UE_TWO_PI) * 65.0f;
            PlayerController->SetControlRotation(FRotator(Pitch, CameraYaw, 0.0f));
        }
        PlayerBodySelfTestPitchCycleDelta = FMath::Max(PlayerBodySelfTestPitchCycleDelta, FMath::Abs(FirstPersonWalkCycleTime - PlayerBodySelfTestInitialCycle));
        PlayerBodySelfTestMaxBodyPitch = FMath::Max(PlayerBodySelfTestMaxBodyPitch, FirstPersonBodyMesh ? FMath::Abs(FirstPersonBodyMesh->GetRelativeRotation().Pitch) : 999.0f);
        bPlayerBodySelfTestPitchAnimationPlaying = bPlayerBodySelfTestPitchAnimationPlaying || bABPWalkingState;
        if (PlayerBodySelfTestPhaseTime >= 1.0f)
        {
            PlayerBodySelfTestLines.Add(FString::Printf(
                TEXT("PitchOnly: Speed=%.3f ForwardSpeed=%.3f RightSpeed=%.3f CameraYaw=%.3f BodyYaw=%.3f AimPitch=%.3f MaxBodyPitch=%.3f State=%d Walking=%s AnimPlayingSeen=%s CycleDelta=%.5f"),
                HorizontalSpeed,
                FirstPersonForwardSpeed,
                FirstPersonRightSpeed,
                CameraYaw,
                BodyYaw,
                AimPitch,
                PlayerBodySelfTestMaxBodyPitch,
                static_cast<int32>(FirstPersonLocomotionState),
                bFirstPersonBodyWalking ? TEXT("true") : TEXT("false"),
                bPlayerBodySelfTestPitchAnimationPlaying ? TEXT("true") : TEXT("false"),
                PlayerBodySelfTestPitchCycleDelta));
            PlayerBodySelfTestMoveStartCycle = FirstPersonWalkCycleTime;
            PlayerBodySelfTestPhase = 3;
            PlayerBodySelfTestPhaseTime = 0.0f;
        }
        return;
    }

    if (PlayerBodySelfTestPhase == 3)
    {
        MoveForward(1.0f);
        PlayerBodySelfTestMoveMaxSpeed = FMath::Max(PlayerBodySelfTestMoveMaxSpeed, HorizontalSpeed);
        PlayerBodySelfTestMoveCycleDelta = FMath::Max(PlayerBodySelfTestMoveCycleDelta, FMath::Abs(FirstPersonWalkCycleTime - PlayerBodySelfTestMoveStartCycle));
        bPlayerBodySelfTestSawWalking = bPlayerBodySelfTestSawWalking || bFirstPersonBodyWalking;
        bPlayerBodySelfTestSawAnimationPlaying = bPlayerBodySelfTestSawAnimationPlaying || bABPActive;
        if (PlayerBodySelfTestPhaseTime >= 1.8f)
        {
            PlayerBodySelfTestLines.Add(FString::Printf(
                TEXT("ForwardMove: MaxSpeed=%.3f ForwardSpeed=%.3f State=%d WalkingSeen=%s AnimPlayingSeen=%s CycleDelta=%.5f"),
                PlayerBodySelfTestMoveMaxSpeed,
                FirstPersonForwardSpeed,
                static_cast<int32>(FirstPersonLocomotionState),
                bPlayerBodySelfTestSawWalking ? TEXT("true") : TEXT("false"),
                bPlayerBodySelfTestSawAnimationPlaying ? TEXT("true") : TEXT("false"),
                PlayerBodySelfTestMoveCycleDelta));
            PlayerBodySelfTestPhase = 4;
            PlayerBodySelfTestPhaseTime = 0.0f;
            PlayerBodySelfTestMoveStartCycle = FirstPersonWalkCycleTime;
        }
        return;
    }

    if (PlayerBodySelfTestPhase == 4)
    {
        MoveForward(-1.0f);
        PlayerBodySelfTestBackwardMaxSpeed = FMath::Max(PlayerBodySelfTestBackwardMaxSpeed, HorizontalSpeed);
        PlayerBodySelfTestBackwardCycleDelta = FMath::Max(PlayerBodySelfTestBackwardCycleDelta, FMath::Abs(FirstPersonWalkCycleTime - PlayerBodySelfTestMoveStartCycle));
        bPlayerBodySelfTestSawBackwardWalking = bPlayerBodySelfTestSawBackwardWalking || (bFirstPersonBodyWalking && bABPBackwardState);
        bPlayerBodySelfTestSawBackwardAnimationPlaying = bPlayerBodySelfTestSawBackwardAnimationPlaying || bABPActive;
        if (PlayerBodySelfTestPhaseTime >= 1.5f)
        {
            PlayerBodySelfTestLines.Add(FString::Printf(
                TEXT("BackwardMove: MaxSpeed=%.3f ForwardSpeed=%.3f State=%d WalkingSeen=%s AnimPlayingSeen=%s CycleDelta=%.5f"),
                PlayerBodySelfTestBackwardMaxSpeed,
                FirstPersonForwardSpeed,
                static_cast<int32>(FirstPersonLocomotionState),
                bPlayerBodySelfTestSawBackwardWalking ? TEXT("true") : TEXT("false"),
                bPlayerBodySelfTestSawBackwardAnimationPlaying ? TEXT("true") : TEXT("false"),
                PlayerBodySelfTestBackwardCycleDelta));
            PlayerBodySelfTestPhase = 5;
            PlayerBodySelfTestPhaseTime = 0.0f;
        }
        return;
    }

    if (PlayerBodySelfTestPhase == 5)
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
                TEXT("Stop: Speed=%.3f ForwardSpeed=%.3f MinSpeedAfterBrake=%.3f State=%d Walking=%s AnimPlaying=%s Cycle=%.5f"),
                HorizontalSpeed,
                FirstPersonForwardSpeed,
                PlayerBodySelfTestStopMinSpeed,
                static_cast<int32>(FirstPersonLocomotionState),
                bFirstPersonBodyWalking ? TEXT("true") : TEXT("false"),
                bABPActive ? TEXT("true") : TEXT("false"),
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
    const UABP_Player* PlayerAnim = FirstPersonBodyMesh ? Cast<UABP_Player>(FirstPersonBodyMesh->GetAnimInstance()) : nullptr;
    AppendPlayerBodySelfTestCheck(TEXT("player spawns correctly"), IsValid(this) && Controller != nullptr);
    AppendPlayerBodySelfTestCheck(TEXT("single player character in runtime world"), PlayerCharacterCount == 1);
    AppendPlayerBodySelfTestCheck(TEXT("camera root component exists"), FirstPersonCameraRoot != nullptr);
    AppendPlayerBodySelfTestCheck(TEXT("camera component exists"), FirstPersonCamera != nullptr);
    AppendPlayerBodySelfTestCheck(TEXT("first-person body component exists"), FirstPersonBodyMesh != nullptr);
    AppendPlayerBodySelfTestCheck(TEXT("camera is attached to camera root"), FirstPersonCamera && FirstPersonCameraRoot && FirstPersonCamera->GetAttachParent() == FirstPersonCameraRoot);
    AppendPlayerBodySelfTestCheck(TEXT("first-person body is attached to capsule root"), FirstPersonBodyMesh && FirstPersonBodyMesh->GetAttachParent() == GetCapsuleComponent());
    AppendPlayerBodySelfTestCheck(TEXT("first-person body uses fixed imported mesh"), GetFirstPersonBodyMeshPath().Contains(TEXT("/Game/Player/FirstPerson/SK_Player_FirstPersonBody")));
    AppendPlayerBodySelfTestCheck(TEXT("ABP_Player anim instance is assigned"), PlayerAnim != nullptr);
    AppendPlayerBodySelfTestCheck(TEXT("ABP_Player required locomotion assets are loaded"), PlayerAnim && PlayerAnim->AreRequiredAssetsLoaded());
    AppendPlayerBodySelfTestCheck(TEXT("external full body is hidden from owner"), GetMesh() && GetMesh()->bOwnerNoSee);
    AppendPlayerBodySelfTestCheck(TEXT("first-person body is owner-only"), FirstPersonBodyMesh && FirstPersonBodyMesh->bOnlyOwnerSee);
    AppendPlayerBodySelfTestCheck(TEXT("first-person body remains visible to owner"), FirstPersonBodyMesh && !FirstPersonBodyMesh->bOwnerNoSee);
    AppendPlayerBodySelfTestCheck(TEXT("owner camera clipping bones are hidden"), AreOwnerCameraClippingBonesHidden());
    AppendPlayerBodySelfTestCheck(TEXT("walk speed is 250 UU/s"), FMath::IsNearlyEqual(WalkSpeed, 250.0f));
    AppendPlayerBodySelfTestCheck(TEXT("sprint speed is 550 UU/s"), FMath::IsNearlyEqual(SprintSpeed, 550.0f));
    AppendPlayerBodySelfTestCheck(TEXT("crouch speed is 140 UU/s"), FMath::IsNearlyEqual(CrouchSpeed, 140.0f));
    AppendPlayerBodySelfTestCheck(TEXT("mesh visual yaw offset is applied to first-person body"), FirstPersonBodyMesh && FMath::IsNearlyEqual(FirstPersonBodyMesh->GetRelativeRotation().Yaw, PlayerMeshVisualYawOffsetDegrees + FirstPersonBodyYawOffset, 0.5f));
    AppendPlayerBodySelfTestCheck(TEXT("camera yaw drives body yaw"), PlayerBodySelfTestMaxTurnYawDelta <= 25.0f);
    AppendPlayerBodySelfTestCheck(TEXT("turning in place does not trigger walking"), PlayerBodySelfTestTurnCycleDelta <= 0.001f && !bPlayerBodySelfTestTurnAnimationPlaying);
    AppendPlayerBodySelfTestCheck(TEXT("camera pitch does not rotate legs or trigger walking"), PlayerBodySelfTestMaxBodyPitch <= 0.1f && PlayerBodySelfTestPitchCycleDelta <= 0.001f && !bPlayerBodySelfTestPitchAnimationPlaying);
    AppendPlayerBodySelfTestCheck(TEXT("forward movement starts walk cycle"), bPlayerBodySelfTestSawWalking && bPlayerBodySelfTestSawAnimationPlaying && PlayerBodySelfTestMoveCycleDelta > 0.01f && PlayerBodySelfTestMoveMaxSpeed > 25.0f);
    AppendPlayerBodySelfTestCheck(TEXT("backward movement uses backward state without negative play rate"), bPlayerBodySelfTestSawBackwardWalking && bPlayerBodySelfTestSawBackwardAnimationPlaying && PlayerBodySelfTestBackwardCycleDelta > 0.01f && PlayerBodySelfTestBackwardMaxSpeed > 25.0f && FirstPersonLastPlayRate >= 0.0f);
    AppendPlayerBodySelfTestCheck(TEXT("stopping stops walking"), PlayerBodySelfTestStopMinSpeed < 15.0f && !bFirstPersonBodyWalking && PlayerAnim && !PlayerAnim->IsActivelyPlayingLocomotion());

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
    const FVector Start = GetPawnViewLocation();
    const FVector End = Start + GetViewRotation().Vector() * InteractionDistance;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(PenanceInteractTrace), false, this);
    return GetWorld() && GetWorld()->LineTraceSingleByChannel(OutHit, Start, End, ECC_Visibility, Params);
}
