#include "PenanceStreamingDoor.h"

#include "Camera/PlayerCameraManager.h"
#include "Components/BoxComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/LevelStreamingDynamic.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"

APenanceStreamingDoor::APenanceStreamingDoor()
{
    PrimaryActorTick.bCanEverTick = true;

    DoorMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DoorMesh"));
    RootComponent = DoorMesh;
    DoorMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    DoorMesh->SetCollisionResponseToAllChannels(ECR_Block);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded())
    {
        DoorMesh->SetStaticMesh(Cube.Object);
    }
    DoorMesh->SetRelativeScale3D(FVector(0.12f, 1.10f, 2.15f));

    InteractionBounds = CreateDefaultSubobject<UBoxComponent>(TEXT("InteractionBounds"));
    InteractionBounds->SetupAttachment(DoorMesh);
    InteractionBounds->SetBoxExtent(FVector(36.0f, 90.0f, 120.0f));
    InteractionBounds->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    InteractionBounds->SetCollisionResponseToAllChannels(ECR_Ignore);
    InteractionBounds->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);

    PreloadRadius = CreateDefaultSubobject<USphereComponent>(TEXT("PreloadRadius"));
    PreloadRadius->SetupAttachment(DoorMesh);
    PreloadRadius->SetSphereRadius(900.0f);
    PreloadRadius->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    PreloadRadius->SetCollisionResponseToAllChannels(ECR_Ignore);
    PreloadRadius->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
}

void APenanceStreamingDoor::BeginPlay()
{
    Super::BeginPlay();
    // Sphere scale follows the root, so force its world scale back to 1.
    PreloadRadius->SetWorldScale3D(FVector::OneVector);
    InteractionBounds->SetWorldScale3D(FVector::OneVector);
    PreloadRadius->SetCollisionEnabled(ExteriorEntrance ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    if (ExteriorEntrance)
    {
        PreloadRadius->OnComponentBeginOverlap.AddDynamic(this, &APenanceStreamingDoor::OnPreloadBegin);
        PreloadRadius->OnComponentEndOverlap.AddDynamic(this, &APenanceStreamingDoor::OnPreloadEnd);
    }
    SetActorTickEnabled(ExteriorEntrance);
}

void APenanceStreamingDoor::OnPreloadBegin(UPrimitiveComponent*, AActor* Actor, UPrimitiveComponent*,
                                          int32, bool, const FHitResult&)
{
    if (Actor && Actor == UGameplayStatics::GetPlayerPawn(this, 0))
    {
        bPlayerNearby = true;
        UnloadRemaining = -1.0f;
        StartPreload();
    }
}

void APenanceStreamingDoor::OnPreloadEnd(UPrimitiveComponent*, AActor* Actor, UPrimitiveComponent*, int32)
{
    if (Actor && Actor == UGameplayStatics::GetPlayerPawn(this, 0))
    {
        bPlayerNearby = false;
        if (!bPlayerInside && State == EState::Idle) UnloadRemaining = 3.0f;
    }
}

void APenanceStreamingDoor::StartPreload()
{
    if (!ExteriorEntrance || InteriorStream) return;

    bool bSuccess = false;
    InteriorStream = ULevelStreamingDynamic::LoadLevelInstance(
        this, InteriorLevelName, InteriorWorldOffset, FRotator::ZeroRotator, bSuccess);
    if (!bSuccess || !InteriorStream)
    {
        InteriorStream = nullptr;
        UE_LOG(LogTemp, Error, TEXT("Penance V7.1: couldn't stream %s"), *InteriorLevelName);
        return;
    }
    InteriorStream->SetShouldBeLoaded(true);
    InteriorStream->SetShouldBeVisible(true);
    UE_LOG(LogTemp, Log, TEXT("Penance V7.1: preloading interior %s"), *InteriorLevelName);
}

void APenanceStreamingDoor::Interact(AActor* Interactor)
{
    ACharacter* Character = Cast<ACharacter>(Interactor);
    if (!Character) return;

    if (!ExteriorEntrance)
    {
        // Exit door lives in the streamed interior; the exterior doorway owns streaming.
        for (TActorIterator<APenanceStreamingDoor> It(GetWorld()); It; ++It)
        {
            if (It->ExteriorEntrance)
            {
                It->RequestExit(Character);
                return;
            }
        }
        UE_LOG(LogTemp, Warning, TEXT("Penance V7.1: no exterior entrance to return to"));
        return;
    }

    if (State != EState::Idle || bPlayerInside) return;
    PendingCharacter = Character;
    StartPreload();
    if (!InteriorStream) { CancelTransition(); return; }
    UnloadRemaining = -1.0f;
    State = EState::WaitForLoad;
    UE_LOG(LogTemp, Log, TEXT("Penance V7.1: entrance requested; waiting for visible interior"));
}

void APenanceStreamingDoor::RequestExit(ACharacter* Character)
{
    if (!ExteriorEntrance || !bPlayerInside || State != EState::Idle || !Character) return;
    PendingCharacter = Character;
    BeginFade(false);
}

void APenanceStreamingDoor::BeginFade(bool bEntering)
{
    if (!PendingCharacter.IsValid()) { CancelTransition(); return; }
    APlayerController* PC = Cast<APlayerController>(PendingCharacter->GetController());
    if (!PC || !PC->PlayerCameraManager) { CancelTransition(); return; }
    State = bEntering ? EState::FadeIntoHouse : EState::FadeOutOfHouse;
    FadeRemaining = 0.28f;
    PC->PlayerCameraManager->StartCameraFade(0.f, 1.f, 0.28f, FLinearColor::Black, false, true);
}

void APenanceStreamingDoor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!ExteriorEntrance) return;

    if (State == EState::WaitForLoad)
    {
        if (!PendingCharacter.IsValid()) { CancelTransition(); return; }
        if (InteriorStream && InteriorStream->IsLevelLoaded() && InteriorStream->IsLevelVisible())
        {
            BeginFade(true);
        }
    }
    else if (State == EState::FadeIntoHouse || State == EState::FadeOutOfHouse)
    {
        FadeRemaining -= DeltaSeconds;
        if (FadeRemaining <= 0.f) CompleteTeleport();
    }

    if (UnloadRemaining > 0.f && State == EState::Idle && !bPlayerInside && !bPlayerNearby)
    {
        UnloadRemaining -= DeltaSeconds;
        if (UnloadRemaining <= 0.f) UnloadInterior();
    }
}

void APenanceStreamingDoor::CompleteTeleport()
{
    ACharacter* Character = PendingCharacter.Get();
    if (!Character) { CancelTransition(); return; }
    APlayerController* PC = Cast<APlayerController>(Character->GetController());
    const bool bEnter = State == EState::FadeIntoHouse;
    const FVector Target = bEnter ? (InteriorWorldOffset + InteriorEntryLocal) : ExteriorExitWorld;
    const FRotator Facing(0.f, bEnter ? 0.f : 180.f, 0.f);

    // In a prototype this destination is fixed. Later a save/checkpoint system owns it.
    if (!Character->TeleportTo(Target, Facing, false, true))
    {
        UE_LOG(LogTemp, Error, TEXT("Penance V7.1: teleport failed"));
        CancelTransition();
        return;
    }
    Character->GetCharacterMovement()->StopMovementImmediately();
    if (PC) PC->SetControlRotation(Facing);
    bPlayerInside = bEnter;
    PendingCharacter.Reset();
    State = EState::Idle;
    if (PC && PC->PlayerCameraManager)
    {
        PC->PlayerCameraManager->StartCameraFade(1.f, 0.f, 0.30f, FLinearColor::Black, false, false);
    }
    UE_LOG(LogTemp, Log, TEXT("Penance V7.1: %s House 1"), bEnter ? TEXT("entered") : TEXT("exited"));
    if (!bEnter && !bPlayerNearby) UnloadRemaining = 3.f;
}

void APenanceStreamingDoor::UnloadInterior()
{
    if (!InteriorStream) return;
    InteriorStream->SetShouldBeVisible(false);
    InteriorStream->SetShouldBeLoaded(false);
    InteriorStream->SetIsRequestingUnloadAndRemoval(true);
    InteriorStream = nullptr;
    UnloadRemaining = -1.f;
    UE_LOG(LogTemp, Log, TEXT("Penance V7.1: interior unload requested"));
}

void APenanceStreamingDoor::CancelTransition()
{
    PendingCharacter.Reset();
    State = EState::Idle;
    APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0);
    if (PC && PC->PlayerCameraManager) PC->PlayerCameraManager->StopCameraFade();
}
