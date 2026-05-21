#include "ABP_Player.h"

#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "PenancePlayerCharacter.h"

FABP_PlayerProxy::FABP_PlayerProxy(UAnimInstance* InAnimInstance)
    : FAnimInstanceProxy(InAnimInstance)
{
}

void FABP_PlayerProxy::Initialize(UAnimInstance* InAnimInstance)
{
    FAnimInstanceProxy::Initialize(InAnimInstance);

    FAnimationInitializeContext InitContext(this);
    SequencePlayer.Initialize_AnyThread(InitContext);
}

void FABP_PlayerProxy::PreUpdate(UAnimInstance* InAnimInstance, float DeltaSeconds)
{
    FAnimInstanceProxy::PreUpdate(InAnimInstance, DeltaSeconds);

    const UABP_Player* PlayerAnim = Cast<UABP_Player>(InAnimInstance);
    ActiveSequence = PlayerAnim ? PlayerAnim->GetActiveSequence() : nullptr;
    ActivePlayRate = PlayerAnim ? PlayerAnim->GetActivePlayRate() : 1.0f;
    ActiveStartPosition = PlayerAnim ? PlayerAnim->GetActiveStartPosition() : 0.0f;
    bActiveLooping = PlayerAnim ? PlayerAnim->IsActiveSequenceLooping() : true;
}

void FABP_PlayerProxy::UpdateAnimationNode(const FAnimationUpdateContext& InContext)
{
    UpdateCounter.Increment();

    if (!ActiveSequence)
    {
        return;
    }

    const bool bChangedSequence = LastSequence != ActiveSequence;
    if (bChangedSequence)
    {
        SequencePlayer.SetSequence(ActiveSequence);
        SequencePlayer.SetStartPosition(ActiveStartPosition);
        LastSequence = ActiveSequence;
    }

    SequencePlayer.SetLoopAnimation(bActiveLooping);
    SequencePlayer.SetPlayRate(ActivePlayRate);
    SequencePlayer.Update_AnyThread(InContext);
}

bool FABP_PlayerProxy::Evaluate(FPoseContext& Output)
{
    if (!ActiveSequence)
    {
        Output.ResetToRefPose();
        return true;
    }

    SequencePlayer.Evaluate_AnyThread(Output);
    return true;
}

UABP_Player::UABP_Player()
{
}

void UABP_Player::NativeInitializeAnimation()
{
    Super::NativeInitializeAnimation();
    LoadDefaultAssets();
}

void UABP_Player::NativeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeUpdateAnimation(DeltaSeconds);

    APawn* OwningPawn = TryGetPawnOwner();
    UpdateMotionVariables(OwningPawn);
    UpdateStateMachine(DeltaSeconds);
}

FAnimInstanceProxy* UABP_Player::CreateAnimInstanceProxy()
{
    return new FABP_PlayerProxy(this);
}

void UABP_Player::DestroyAnimInstanceProxy(FAnimInstanceProxy* InProxy)
{
    delete InProxy;
}

void UABP_Player::LoadDefaultAssets()
{
    if (!IdleFeetTogether)
    {
        IdleFeetTogether = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/FirstPerson/AN_Player_Idle_FeetTogether.AN_Player_Idle_FeetTogether"), nullptr, LOAD_NoWarn);
    }
    if (!IdleStaggered)
    {
        IdleStaggered = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/FirstPerson/AN_Player_Idle_Staggered.AN_Player_Idle_Staggered"), nullptr, LOAD_NoWarn);
    }
    if (!StartWalkForward)
    {
        StartWalkForward = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/FirstPerson/AN_Player_StartWalk_Forward.AN_Player_StartWalk_Forward"), nullptr, LOAD_NoWarn);
    }
    if (!WalkForwardLoop)
    {
        WalkForwardLoop = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/FirstPerson/AN_Player_Walk_Forward_Loop.AN_Player_Walk_Forward_Loop"), nullptr, LOAD_NoWarn);
    }
    if (!WalkBackwardLoop)
    {
        WalkBackwardLoop = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/FirstPerson/AN_Player_Walk_Backward_Loop.AN_Player_Walk_Backward_Loop"), nullptr, LOAD_NoWarn);
    }
    if (!StopWalkForward)
    {
        StopWalkForward = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/FirstPerson/AN_Player_StopWalk_Forward.AN_Player_StopWalk_Forward"), nullptr, LOAD_NoWarn);
    }
    if (!TurnInPlaceLeft)
    {
        TurnInPlaceLeft = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/FirstPerson/AN_Player_TurnInPlace_Left.AN_Player_TurnInPlace_Left"), nullptr, LOAD_NoWarn);
    }
    if (!TurnInPlaceRight)
    {
        TurnInPlaceRight = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/FirstPerson/AN_Player_TurnInPlace_Right.AN_Player_TurnInPlace_Right"), nullptr, LOAD_NoWarn);
    }

    UAnimSequence* VerifyWalk = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/FirstPerson/AN_Player_Walk_Verify.AN_Player_Walk_Verify"), nullptr, LOAD_NoWarn);
    UAnimSequence* ImportedWalk = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/FirstPerson/SK_Player_FirstPersonBody_Anim.SK_Player_FirstPersonBody_Anim"), nullptr, LOAD_NoWarn);
    UAnimSequence* Fallback = VerifyWalk ? VerifyWalk : ImportedWalk;

    if (!IdleFeetTogether)
    {
        IdleFeetTogether = Fallback;
    }
    if (!StartWalkForward)
    {
        StartWalkForward = Fallback;
    }
    if (!WalkForwardLoop)
    {
        WalkForwardLoop = Fallback;
    }
    if (!WalkBackwardLoop)
    {
        WalkBackwardLoop = WalkForwardLoop;
    }
    if (!StopWalkForward)
    {
        StopWalkForward = IdleFeetTogether;
    }
    if (!TurnInPlaceLeft)
    {
        TurnInPlaceLeft = IdleFeetTogether;
    }
    if (!TurnInPlaceRight)
    {
        TurnInPlaceRight = IdleFeetTogether;
    }
}

void UABP_Player::UpdateMotionVariables(APawn* OwningPawn)
{
    if (!OwningPawn)
    {
        Speed = 0.0f;
        ForwardSpeed = 0.0f;
        RightSpeed = 0.0f;
        Direction = 0.0f;
        bIsMoving = false;
        bMovingForward = false;
        bMovingBackward = false;
        bIsTurningInPlace = false;
        TurnYawDelta = 0.0f;
        WalkPlayRate = 1.0f;
        return;
    }

    const FVector Velocity2D(OwningPawn->GetVelocity().X, OwningPawn->GetVelocity().Y, 0.0f);
    Speed = Velocity2D.Size();
    ForwardSpeed = FVector::DotProduct(Velocity2D, OwningPawn->GetActorForwardVector());
    RightSpeed = FVector::DotProduct(Velocity2D, OwningPawn->GetActorRightVector());
    Direction = Speed > KINDA_SMALL_NUMBER ? FMath::RadiansToDegrees(FMath::Atan2(RightSpeed, ForwardSpeed)) : 0.0f;

    bIsMoving = Speed > MovingThreshold;
    bMovingForward = ForwardSpeed > MovingThreshold;
    bMovingBackward = ForwardSpeed < -MovingThreshold;

    if (const APenancePlayerCharacter* PlayerCharacter = Cast<APenancePlayerCharacter>(OwningPawn))
    {
        TurnYawDelta = PlayerCharacter->GetTurnYawDelta();
    }
    else if (const AController* Controller = OwningPawn->GetController())
    {
        TurnYawDelta = FMath::FindDeltaAngleDegrees(OwningPawn->GetActorRotation().Yaw, Controller->GetControlRotation().Yaw);
    }
    else
    {
        TurnYawDelta = 0.0f;
    }

    bIsTurningInPlace = !bIsMoving && FMath::Abs(TurnYawDelta) > TurnInPlaceThreshold;

    if (bMovingBackward)
    {
        WalkPlayRate = FMath::Clamp(FMath::Abs(ForwardSpeed) / WalkSpeedTarget, 0.75f, 1.15f);
    }
    else
    {
        WalkPlayRate = FMath::Clamp(Speed / WalkSpeedTarget, 0.75f, 1.25f);
    }
}

void UABP_Player::UpdateStateMachine(float DeltaSeconds)
{
    StateElapsedTime += DeltaSeconds;
    ActiveAssetTime += DeltaSeconds * FMath::Max(GetActivePlayRate(), 0.0f);

    const bool bStopped = Speed <= StopThreshold;

    if (bMovingBackward)
    {
        SetLocomotionState(EPenancePlayerAnimState::WalkBackward);
        return;
    }

    if (bMovingForward)
    {
        if (LocomotionState != EPenancePlayerAnimState::StartWalkForward && LocomotionState != EPenancePlayerAnimState::WalkForward)
        {
            SetLocomotionState((bUseStartStopAnimations && StartWalkForward) ? EPenancePlayerAnimState::StartWalkForward : EPenancePlayerAnimState::WalkForward);
            return;
        }

        if (LocomotionState == EPenancePlayerAnimState::StartWalkForward)
        {
            const float StartLength = StartWalkForward ? StartWalkForward->GetPlayLength() : 0.0f;
            if (StartLength <= KINDA_SMALL_NUMBER || StateElapsedTime >= FMath::Max(0.0f, StartLength - 0.05f))
            {
                SetLocomotionState(EPenancePlayerAnimState::WalkForward);
            }
            return;
        }

        SetLocomotionState(EPenancePlayerAnimState::WalkForward);
        return;
    }

    if (bStopped)
    {
        if (bUseStartStopAnimations && LocomotionState == EPenancePlayerAnimState::WalkForward && StopWalkForward && StopWalkForward != IdleFeetTogether)
        {
            SetLocomotionState(EPenancePlayerAnimState::StopWalkForward);
            return;
        }

        if (LocomotionState == EPenancePlayerAnimState::StopWalkForward)
        {
            const float StopLength = StopWalkForward ? StopWalkForward->GetPlayLength() : 0.0f;
            if (StopLength <= KINDA_SMALL_NUMBER || StateElapsedTime >= FMath::Max(0.0f, StopLength - 0.05f))
            {
                SetLocomotionState(EPenancePlayerAnimState::Idle);
            }
            return;
        }

        if (bUseTurnInPlaceAnimations && bIsTurningInPlace && TurnYawDelta < -TurnInPlaceThreshold && TurnInPlaceLeft && TurnInPlaceLeft != IdleFeetTogether)
        {
            SetLocomotionState(EPenancePlayerAnimState::TurnInPlaceLeft);
            return;
        }

        if (bUseTurnInPlaceAnimations && bIsTurningInPlace && TurnYawDelta > TurnInPlaceThreshold && TurnInPlaceRight && TurnInPlaceRight != IdleFeetTogether)
        {
            SetLocomotionState(EPenancePlayerAnimState::TurnInPlaceRight);
            return;
        }

        SetLocomotionState(EPenancePlayerAnimState::Idle);
    }
}

void UABP_Player::SetLocomotionState(EPenancePlayerAnimState NewState)
{
    if (LocomotionState != NewState)
    {
        LocomotionState = NewState;
        StateElapsedTime = 0.0f;
        ActiveAssetTime = 0.0f;
    }
}

UAnimSequence* UABP_Player::ResolveAssetForState(EPenancePlayerAnimState State) const
{
    switch (State)
    {
    case EPenancePlayerAnimState::StartWalkForward:
        return StartWalkForward ? StartWalkForward.Get() : WalkForwardLoop.Get();
    case EPenancePlayerAnimState::WalkForward:
        return WalkForwardLoop ? WalkForwardLoop.Get() : StartWalkForward.Get();
    case EPenancePlayerAnimState::WalkBackward:
        return WalkBackwardLoop ? WalkBackwardLoop.Get() : WalkForwardLoop.Get();
    case EPenancePlayerAnimState::StopWalkForward:
        return StopWalkForward ? StopWalkForward.Get() : IdleFeetTogether.Get();
    case EPenancePlayerAnimState::TurnInPlaceLeft:
        return TurnInPlaceLeft ? TurnInPlaceLeft.Get() : IdleFeetTogether.Get();
    case EPenancePlayerAnimState::TurnInPlaceRight:
        return TurnInPlaceRight ? TurnInPlaceRight.Get() : IdleFeetTogether.Get();
    case EPenancePlayerAnimState::Idle:
    default:
        return IdleFeetTogether.Get();
    }
}

UAnimSequenceBase* UABP_Player::GetActiveSequence() const
{
    return ResolveAssetForState(LocomotionState);
}

float UABP_Player::GetActivePlayRate() const
{
    switch (LocomotionState)
    {
    case EPenancePlayerAnimState::Idle:
        return 0.0f;
    case EPenancePlayerAnimState::TurnInPlaceLeft:
    case EPenancePlayerAnimState::TurnInPlaceRight:
        return 1.0f;
    case EPenancePlayerAnimState::WalkBackward:
    case EPenancePlayerAnimState::WalkForward:
    case EPenancePlayerAnimState::StartWalkForward:
    case EPenancePlayerAnimState::StopWalkForward:
    default:
        return WalkPlayRate;
    }
}

float UABP_Player::GetActiveStartPosition() const
{
    return LocomotionState == EPenancePlayerAnimState::Idle ? IdleFeetTogetherPoseTime : 0.0f;
}

bool UABP_Player::IsActiveSequenceLooping() const
{
    return LocomotionState == EPenancePlayerAnimState::WalkForward || LocomotionState == EPenancePlayerAnimState::WalkBackward;
}

bool UABP_Player::IsActivelyPlayingLocomotion() const
{
    return LocomotionState == EPenancePlayerAnimState::StartWalkForward
        || LocomotionState == EPenancePlayerAnimState::WalkForward
        || LocomotionState == EPenancePlayerAnimState::WalkBackward
        || LocomotionState == EPenancePlayerAnimState::StopWalkForward
        || LocomotionState == EPenancePlayerAnimState::TurnInPlaceLeft
        || LocomotionState == EPenancePlayerAnimState::TurnInPlaceRight;
}

bool UABP_Player::AreRequiredAssetsLoaded() const
{
    return IdleFeetTogether != nullptr
        && StartWalkForward != nullptr
        && WalkForwardLoop != nullptr
        && WalkBackwardLoop != nullptr
        && StopWalkForward != nullptr
        && TurnInPlaceLeft != nullptr
        && TurnInPlaceRight != nullptr;
}
