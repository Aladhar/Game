#include "PenanceHingedDoor.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"

APenanceHingedDoor::APenanceHingedDoor()
{
    PrimaryActorTick.bCanEverTick = true;

    HingeRoot = CreateDefaultSubobject<USceneComponent>(TEXT("HingeRoot"));
    RootComponent = HingeRoot;

    DoorMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DoorMesh"));
    DoorMesh->SetupAttachment(HingeRoot);
    DoorMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    DoorMesh->SetCollisionObjectType(ECC_WorldDynamic);
    DoorMesh->SetCollisionResponseToAllChannels(ECR_Block);

    InteractionBounds = CreateDefaultSubobject<UBoxComponent>(TEXT("InteractionBounds"));
    InteractionBounds->SetupAttachment(HingeRoot);
    InteractionBounds->SetBoxExtent(FVector(90.0f, 90.0f, 140.0f));
    InteractionBounds->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    InteractionBounds->SetCollisionObjectType(ECC_WorldDynamic);
    InteractionBounds->SetCollisionResponseToAllChannels(ECR_Ignore);
    InteractionBounds->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
}

void APenanceHingedDoor::BeginPlay()
{
    Super::BeginPlay();

    ClosedYaw = HingeRoot->GetRelativeRotation().Yaw;
    bIsOpen = bStartsOpen;
    TargetYaw = ClosedYaw + (bIsOpen ? OpenAngleDegrees : 0.0f);
    HingeRoot->SetRelativeRotation(FRotator(0.0f, TargetYaw, 0.0f));
}

void APenanceHingedDoor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    const FRotator CurrentRotation = HingeRoot->GetRelativeRotation();
    const float NewYaw = FMath::FInterpTo(CurrentRotation.Yaw, TargetYaw, DeltaSeconds, OpenSpeed);
    HingeRoot->SetRelativeRotation(FRotator(0.0f, NewYaw, 0.0f));
}

void APenanceHingedDoor::Interact(AActor* Interactor)
{
    bIsOpen = !bIsOpen;

    float Direction = 1.0f;
    if (bOpensAwayFromPlayer && Interactor)
    {
        const FVector ToInteractor = Interactor->GetActorLocation() - GetActorLocation();
        const float Side = FVector::DotProduct(GetActorRightVector(), ToInteractor.GetSafeNormal2D());
        Direction = Side >= 0.0f ? -1.0f : 1.0f;
    }

    TargetYaw = ClosedYaw + (bIsOpen ? OpenAngleDegrees * Direction : 0.0f);
}
