#include "PenancePickupItem.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "PenancePlayerCharacter.h"
#include "PenanceProgressionManager.h"

APenancePickupItem::APenancePickupItem()
{
    PrimaryActorTick.bCanEverTick = false;

    PickupMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PickupMesh"));
    RootComponent = PickupMesh;
    PickupMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    PickupMesh->SetCollisionObjectType(ECC_WorldDynamic);
    PickupMesh->SetCollisionResponseToAllChannels(ECR_Block);

    InteractionBounds = CreateDefaultSubobject<UBoxComponent>(TEXT("InteractionBounds"));
    InteractionBounds->SetupAttachment(PickupMesh);
    InteractionBounds->SetBoxExtent(FVector(70.0f, 70.0f, 70.0f));
    InteractionBounds->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    InteractionBounds->SetCollisionObjectType(ECC_WorldDynamic);
    InteractionBounds->SetCollisionResponseToAllChannels(ECR_Ignore);
    InteractionBounds->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);

    ItemName = FText::FromString(TEXT("Item"));
}

void APenancePickupItem::Interact(AActor* Interactor)
{
    APenancePlayerCharacter* Player = Cast<APenancePlayerCharacter>(Interactor);
    if (!Player)
    {
        return;
    }

    Player->AddInventoryEntry(ItemName, ItemDescription, bIsNote || PickupType == EPenancePickupType::Note);
    if (APenanceProgressionManager* Manager = APenanceProgressionManager::Find(GetWorld()))
    {
        Manager->HandlePickup(PickupName.IsNone() ? FName(*ItemName.ToString()) : PickupName, Player);
    }
    SetActorHiddenInGame(true);
    SetActorEnableCollision(false);
}
