#include "PenancePlayerCharacter.h"

#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerInput.h"
#include "Camera/PlayerCameraManager.h"

APenancePlayerCharacter::APenancePlayerCharacter()
{
    PrimaryActorTick.bCanEverTick = true;

    GetCapsuleComponent()->InitCapsuleSize(CapsuleRadius, StandingCapsuleHeight * 0.5f);

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
    Movement->JumpZVelocity = 0.0f;
    Movement->AirControl = 0.0f;
    Movement->NavAgentProps.bCanCrouch = true;
    Movement->SetCrouchedHalfHeight(CrouchingCapsuleHeight * 0.5f);

    JumpMaxCount = 0;
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
}

void APenancePlayerCharacter::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    ForceGroundedMovementMode();
    UpdateMovementRules(DeltaSeconds);
    UpdateCrouchRules(DeltaSeconds);
    UpdateNoiseRules(DeltaSeconds);
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
}

void APenancePlayerCharacter::Jump()
{
}

bool APenancePlayerCharacter::CanJumpInternal_Implementation() const
{
    return false;
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
    OnPlayerNoise.Broadcast(TEXT("knock"), GetActorLocation(), 0.7f);
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
