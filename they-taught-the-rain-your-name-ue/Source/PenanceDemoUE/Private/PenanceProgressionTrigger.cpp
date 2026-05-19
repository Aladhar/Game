#include "PenanceProgressionTrigger.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "PenancePlayerCharacter.h"
#include "PenanceProgressionManager.h"

APenanceProgressionTrigger::APenanceProgressionTrigger()
{
    PrimaryActorTick.bCanEverTick = false;

    TriggerBounds = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerBounds"));
    RootComponent = TriggerBounds;
    TriggerBounds->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    TriggerBounds->SetCollisionObjectType(ECC_WorldDynamic);
    TriggerBounds->SetCollisionResponseToAllChannels(ECR_Ignore);
    TriggerBounds->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);

    DebugMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DebugMesh"));
    DebugMesh->SetupAttachment(TriggerBounds);
    DebugMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    DebugMesh->SetHiddenInGame(true);
}

void APenanceProgressionTrigger::BeginPlay()
{
    Super::BeginPlay();
    TriggerBounds->OnComponentBeginOverlap.AddDynamic(this, &APenanceProgressionTrigger::OnTriggerOverlap);
}

void APenanceProgressionTrigger::OnTriggerOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
    if (!OtherActor || !OtherActor->IsA<APenancePlayerCharacter>())
    {
        return;
    }

    if (APenanceProgressionManager* Manager = APenanceProgressionManager::Find(GetWorld()))
    {
        Manager->HandleProgressionEvent(TriggerName, OtherActor);
    }
}
