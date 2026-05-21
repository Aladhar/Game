#include "PenancePlayerWalkPreviewActor.h"

#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/Pawn.h"
#include "HAL/PlatformMisc.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UObject/ConstructorHelpers.h"

DEFINE_LOG_CATEGORY_STATIC(LogPenancePlayerWalkPreview, Log, All);

APenancePlayerWalkPreviewActor::APenancePlayerWalkPreviewActor()
{
    PrimaryActorTick.bCanEverTick = true;

    PreviewMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("PreviewMesh"));
    SetRootComponent(PreviewMesh);

    static ConstructorHelpers::FObjectFinder<USkeletalMesh> MeshAsset(TEXT("/Game/Player/FirstPerson/SK_Player_FirstPersonBody.SK_Player_FirstPersonBody"));
    if (MeshAsset.Succeeded())
    {
        PreviewMesh->SetSkeletalMesh(MeshAsset.Object);
    }

    static ConstructorHelpers::FObjectFinder<UAnimSequence> VerifyWalkAnimAsset(TEXT("/Game/Player/FirstPerson/AN_Player_Walk_Verify.AN_Player_Walk_Verify"));
    if (VerifyWalkAnimAsset.Succeeded())
    {
        WalkAnimation = VerifyWalkAnimAsset.Object;
    }
    else
    {
        static ConstructorHelpers::FObjectFinder<UAnimSequence> ImportedWalkAnimAsset(TEXT("/Game/Player/FirstPerson/SK_Player_FirstPersonBody_Anim.SK_Player_FirstPersonBody_Anim"));
        if (ImportedWalkAnimAsset.Succeeded())
        {
            WalkAnimation = ImportedWalkAnimAsset.Object;
        }
    }

    PreviewMesh->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
    PreviewMesh->SetRelativeScale3D(FVector(1.65f));
    PreviewMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    PreviewMesh->VisibilityBasedAnimTickOption = EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
}

void APenancePlayerWalkPreviewActor::BeginPlay()
{
    Super::BeginPlay();

    SetPreviewWalking(false, 0.0f, 1.0f);

    if (FParse::Param(FCommandLine::Get(), TEXT("PenanceAnimPreviewSelfTest")))
    {
        StartSelfTest();
    }
}

void APenancePlayerWalkPreviewActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    if (!PreviewMesh)
    {
        return;
    }

    if (bSelfTestActive)
    {
        UpdateSelfTestPreview(DeltaSeconds);
        return;
    }

    UpdatePlayerMirroredPreview(DeltaSeconds);
}

void APenancePlayerWalkPreviewActor::SetPreviewWalking(bool bShouldWalk, float HorizontalSpeed, float DirectionSign)
{
    if (!PreviewMesh || !WalkAnimation)
    {
        return;
    }

    PreviewMesh->SetAnimationMode(EAnimationMode::AnimationSingleNode);

    if (bShouldWalk)
    {
        if (!PreviewMesh->IsPlaying())
        {
            PreviewMesh->SetAnimation(WalkAnimation);
            PreviewMesh->SetPosition(GetPreviewIdlePoseTime(), false);
            PreviewMesh->Play(true);
        }

        PreviewWalkBlendAlpha = FMath::Min(1.0f, PreviewWalkBlendAlpha + GetWorld()->GetDeltaSeconds() / 0.18f);
        const float BlendedRateScale = FMath::InterpEaseInOut(0.0f, 1.0f, PreviewWalkBlendAlpha, 2.0f);
        PreviewLastSignedPlayRate = FMath::Clamp(HorizontalSpeed / 250.0f, 0.75f, 1.25f) * (DirectionSign < 0.0f ? -1.0f : 1.0f);
        PreviewMesh->SetPlayRate(PreviewLastSignedPlayRate * BlendedRateScale);
    }
    else if (PreviewWalkBlendAlpha > 0.0f && PreviewMesh->IsPlaying())
    {
        PreviewWalkBlendAlpha = FMath::Max(0.0f, PreviewWalkBlendAlpha - GetWorld()->GetDeltaSeconds() / 0.16f);
        const float BlendedRateScale = FMath::InterpEaseInOut(0.0f, 1.0f, PreviewWalkBlendAlpha, 2.0f);
        PreviewMesh->SetPlayRate(PreviewLastSignedPlayRate * BlendedRateScale);
        if (PreviewWalkBlendAlpha <= KINDA_SMALL_NUMBER)
        {
            PreviewMesh->SetAnimation(WalkAnimation);
            PreviewMesh->SetPosition(GetPreviewIdlePoseTime(), false);
            PreviewMesh->Stop();
        }
    }
    else
    {
        PreviewMesh->SetAnimation(WalkAnimation);
        PreviewMesh->SetPosition(GetPreviewIdlePoseTime(), false);
        PreviewMesh->Stop();
        PreviewWalkBlendAlpha = 0.0f;
        PreviewLastSignedPlayRate = 1.0f;
    }

    bPreviewWalking = bShouldWalk;
}

void APenancePlayerWalkPreviewActor::UpdatePlayerMirroredPreview(float DeltaSeconds)
{
    APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
    const FVector PlayerVelocity = PlayerPawn ? FVector(PlayerPawn->GetVelocity().X, PlayerPawn->GetVelocity().Y, 0.0f) : FVector::ZeroVector;
    const float HorizontalSpeed = PlayerVelocity.Size();
    const bool bShouldWalk = HorizontalSpeed > 10.0f;
    float DirectionSign = 1.0f;

    if (PlayerPawn && bShouldWalk)
    {
        const FVector VelocityDirection = PlayerVelocity.GetSafeNormal();
        const float ForwardAmount = FVector::DotProduct(VelocityDirection, PlayerPawn->GetActorForwardVector());
        const float RightAmount = FVector::DotProduct(VelocityDirection, PlayerPawn->GetActorRightVector());
        DirectionSign = ForwardAmount < -0.35f && FMath::Abs(ForwardAmount) >= FMath::Abs(RightAmount) ? -1.0f : 1.0f;

        const FRotator TargetRotation = DirectionSign < 0.0f
            ? FRotator(0.0f, PlayerPawn->GetActorRotation().Yaw, 0.0f)
            : FRotator(0.0f, VelocityDirection.Rotation().Yaw, 0.0f);
        SetActorRotation(FMath::RInterpTo(GetActorRotation(), TargetRotation, DeltaSeconds, 10.0f));
    }

    SetPreviewWalking(bShouldWalk, HorizontalSpeed, DirectionSign);

    if (bShouldWalk)
    {
        const float PreviewSpeed = FMath::Clamp(HorizontalSpeed, 80.0f, 250.0f);
        AddActorWorldOffset(GetActorForwardVector() * DirectionSign * PreviewSpeed * DeltaSeconds, false);
    }
}

void APenancePlayerWalkPreviewActor::UpdateSelfTestPreview(float DeltaSeconds)
{
    SelfTestElapsed += DeltaSeconds;

    if (SelfTestElapsed < 0.8f)
    {
        SetPreviewWalking(false, 0.0f, 1.0f);
        bIdlePhaseAnimationPlayed = bIdlePhaseAnimationPlayed || PreviewMesh->IsPlaying();
        return;
    }

    if (SelfTestElapsed < 1.6f)
    {
        SetPreviewWalking(false, 0.0f, 1.0f);
        AddActorWorldRotation(FRotator(0.0f, 45.0f * DeltaSeconds, 0.0f));
        bTurnOnlyPhaseAnimationPlayed = bTurnOnlyPhaseAnimationPlayed || PreviewMesh->IsPlaying();
        return;
    }

    if (SelfTestElapsed < 3.0f)
    {
        if (MovePhaseStartLocation.IsZero())
        {
            MovePhaseStartLocation = GetActorLocation();
        }

        const float PreviewWalkSpeed = 180.0f;
        SetPreviewWalking(true, PreviewWalkSpeed, 1.0f);
        AddActorWorldOffset(GetActorForwardVector() * PreviewWalkSpeed * DeltaSeconds, false);

        const float CurrentAnimationTime = PreviewMesh->GetPosition();
        if (!bCapturedInitialAnimationTime)
        {
            InitialAnimationTime = CurrentAnimationTime;
            bCapturedInitialAnimationTime = true;
        }

        MaxAnimationTimeDelta = FMath::Max(MaxAnimationTimeDelta, FMath::Abs(CurrentAnimationTime - InitialAnimationTime));
        bMovePhaseAnimationPlayed = bMovePhaseAnimationPlayed || PreviewMesh->IsPlaying();
        return;
    }

    if (SelfTestElapsed < 4.4f)
    {
        if (ReversePhaseStartLocation.IsZero())
        {
            ReversePhaseStartLocation = GetActorLocation();
        }

        const float PreviewWalkSpeed = 160.0f;
        SetPreviewWalking(true, PreviewWalkSpeed, -1.0f);
        AddActorWorldOffset(GetActorForwardVector() * -PreviewWalkSpeed * DeltaSeconds, false);
        bReversePhaseAnimationPlayed = bReversePhaseAnimationPlayed || PreviewMesh->IsPlaying();
        return;
    }

    SetPreviewWalking(false, 0.0f, 1.0f);
    bStopPhaseAnimationPlayed = PreviewMesh->IsPlaying();
    FinalActorLocation = GetActorLocation();

    if (SelfTestElapsed >= 5.2f)
    {
        FinishSelfTest();
    }
}

void APenancePlayerWalkPreviewActor::StartSelfTest()
{
    bSelfTestActive = true;
    bCapturedInitialAnimationTime = false;
    bPreviewWalking = false;
    bIdlePhaseAnimationPlayed = false;
    bTurnOnlyPhaseAnimationPlayed = false;
    bMovePhaseAnimationPlayed = false;
    bReversePhaseAnimationPlayed = false;
    bStopPhaseAnimationPlayed = false;
    SelfTestElapsed = 0.0f;
    InitialAnimationTime = 0.0f;
    MaxAnimationTimeDelta = 0.0f;
    PreviewWalkBlendAlpha = 0.0f;
    PreviewLastSignedPlayRate = 1.0f;
    InitialActorLocation = GetActorLocation();
    MovePhaseStartLocation = FVector::ZeroVector;
    ReversePhaseStartLocation = FVector::ZeroVector;
    FinalActorLocation = GetActorLocation();
    SelfTestLines.Reset();
    SelfTestErrors.Reset();

    SelfTestLines.Add(TEXT("PLAYER_WALK_ANIMATION_PREVIEW_SELF_TEST_REPORT"));
    SelfTestLines.Add(FString::Printf(TEXT("Map: %s"), GetWorld() ? *GetWorld()->GetName() : TEXT("None")));
    SelfTestLines.Add(FString::Printf(TEXT("Actor: %s"), *GetName()));
    SelfTestLines.Add(FString::Printf(TEXT("Mesh: %s"), PreviewMesh && PreviewMesh->GetSkeletalMeshAsset() ? *PreviewMesh->GetSkeletalMeshAsset()->GetPathName() : TEXT("None")));
    SelfTestLines.Add(FString::Printf(TEXT("Animation: %s"), WalkAnimation ? *WalkAnimation->GetPathName() : TEXT("None")));
    SelfTestLines.Add(FString::Printf(TEXT("AnimationLength: %.3f"), WalkAnimation ? WalkAnimation->GetPlayLength() : 0.0f));
    SelfTestLines.Add(FString::Printf(TEXT("SampledKeys: %d"), WalkAnimation ? WalkAnimation->GetNumberOfSampledKeys() : 0));
    SelfTestLines.Add(FString::Printf(TEXT("InitialActorLocation: %s"), *InitialActorLocation.ToString()));

    UE_LOG(LogPenancePlayerWalkPreview, Display, TEXT("Started player walk animation preview self-test."));
}

void APenancePlayerWalkPreviewActor::FinishSelfTest()
{
    bSelfTestActive = false;

    const float CurrentAnimationTime = PreviewMesh ? PreviewMesh->GetPosition() : 0.0f;
    const float ForwardDistance = FVector::Dist2D(ReversePhaseStartLocation, MovePhaseStartLocation);
    const float ReverseDistance = FVector::Dist2D(FinalActorLocation, ReversePhaseStartLocation);

    SelfTestLines.Add(FString::Printf(TEXT("InitialAnimationTime: %.5f"), InitialAnimationTime));
    SelfTestLines.Add(FString::Printf(TEXT("CurrentAnimationTime: %.5f"), CurrentAnimationTime));
    SelfTestLines.Add(FString::Printf(TEXT("MaxAnimationTimeDelta: %.5f"), MaxAnimationTimeDelta));
    SelfTestLines.Add(FString::Printf(TEXT("ComponentIsPlaying: %s"), PreviewMesh && PreviewMesh->IsPlaying() ? TEXT("true") : TEXT("false")));
    SelfTestLines.Add(FString::Printf(TEXT("MovePhaseStartLocation: %s"), *MovePhaseStartLocation.ToString()));
    SelfTestLines.Add(FString::Printf(TEXT("ReversePhaseStartLocation: %s"), *ReversePhaseStartLocation.ToString()));
    SelfTestLines.Add(FString::Printf(TEXT("FinalActorLocation: %s"), *FinalActorLocation.ToString()));
    SelfTestLines.Add(FString::Printf(TEXT("ForwardDistance2D: %.3f"), ForwardDistance));
    SelfTestLines.Add(FString::Printf(TEXT("ReverseDistance2D: %.3f"), ReverseDistance));
    SelfTestLines.Add(FString::Printf(TEXT("IdlePhaseAnimationPlayed: %s"), bIdlePhaseAnimationPlayed ? TEXT("true") : TEXT("false")));
    SelfTestLines.Add(FString::Printf(TEXT("TurnOnlyPhaseAnimationPlayed: %s"), bTurnOnlyPhaseAnimationPlayed ? TEXT("true") : TEXT("false")));
    SelfTestLines.Add(FString::Printf(TEXT("MovePhaseAnimationPlayed: %s"), bMovePhaseAnimationPlayed ? TEXT("true") : TEXT("false")));
    SelfTestLines.Add(FString::Printf(TEXT("ReversePhaseAnimationPlayed: %s"), bReversePhaseAnimationPlayed ? TEXT("true") : TEXT("false")));
    SelfTestLines.Add(FString::Printf(TEXT("StopPhaseAnimationPlayed: %s"), bStopPhaseAnimationPlayed ? TEXT("true") : TEXT("false")));
    SelfTestLines.Add(TEXT(""));
    SelfTestLines.Add(TEXT("Acceptance checks:"));

    AppendSelfTestCheck(TEXT("preview mesh component exists"), PreviewMesh != nullptr);
    AppendSelfTestCheck(TEXT("preview mesh uses first-person body skeletal mesh"), PreviewMesh && PreviewMesh->GetSkeletalMeshAsset() && PreviewMesh->GetSkeletalMeshAsset()->GetPathName().Contains(TEXT("/Game/Player/FirstPerson/SK_Player_FirstPersonBody")));
    AppendSelfTestCheck(TEXT("walk animation asset exists"), WalkAnimation != nullptr);
    AppendSelfTestCheck(TEXT("walk animation has playable length"), WalkAnimation && WalkAnimation->GetPlayLength() > 0.1f);
    AppendSelfTestCheck(TEXT("walk animation has multiple sampled keys"), WalkAnimation && WalkAnimation->GetNumberOfSampledKeys() > 1);
    AppendSelfTestCheck(TEXT("idle does not play walk animation"), !bIdlePhaseAnimationPlayed);
    AppendSelfTestCheck(TEXT("turning in place does not play walk animation"), !bTurnOnlyPhaseAnimationPlayed);
    AppendSelfTestCheck(TEXT("movement plays walk animation"), bMovePhaseAnimationPlayed);
    AppendSelfTestCheck(TEXT("forward movement physically translates preview actor"), ForwardDistance > 120.0f);
    AppendSelfTestCheck(TEXT("reverse movement physically translates preview actor"), ReverseDistance > 100.0f);
    AppendSelfTestCheck(TEXT("reverse movement plays walk animation"), bReversePhaseAnimationPlayed);
    AppendSelfTestCheck(TEXT("stop phase stops walk animation"), !bStopPhaseAnimationPlayed && PreviewMesh && !PreviewMesh->IsPlaying());
    AppendSelfTestCheck(TEXT("animation time advanced during play"), MaxAnimationTimeDelta > 0.05f);

    SelfTestLines.Add(TEXT(""));
    SelfTestLines.Add(TEXT("Errors:"));
    if (SelfTestErrors.IsEmpty())
    {
        SelfTestLines.Add(TEXT("- none"));
    }
    else
    {
        for (const FString& Error : SelfTestErrors)
        {
            SelfTestLines.Add(FString::Printf(TEXT("- %s"), *Error));
        }
    }

    const FString ReportPath = FPaths::ProjectSavedDir() / TEXT("PlayerWalkAnimationPreviewSelfTestReport.txt");
    FFileHelper::SaveStringArrayToFile(SelfTestLines, *ReportPath);
    UE_LOG(LogPenancePlayerWalkPreview, Display, TEXT("Finished player walk animation preview self-test. Report=%s Errors=%d"), *ReportPath, SelfTestErrors.Num());
    FPlatformMisc::RequestExit(false);
}

void APenancePlayerWalkPreviewActor::AppendSelfTestCheck(const FString& Label, bool bPassed)
{
    SelfTestLines.Add(FString::Printf(TEXT("%s - %s"), bPassed ? TEXT("PASS") : TEXT("FAIL"), *Label));
    if (!bPassed)
    {
        SelfTestErrors.Add(Label);
    }
}

float APenancePlayerWalkPreviewActor::GetPreviewIdlePoseTime() const
{
    return WalkAnimation ? WalkAnimation->GetPlayLength() * 0.25f : 0.0f;
}
