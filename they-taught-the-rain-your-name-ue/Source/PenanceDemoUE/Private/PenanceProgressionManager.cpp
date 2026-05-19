#include "PenanceProgressionManager.h"

#include "Components/PrimitiveComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"

namespace
{
const FVector TunnelStartGodot(-34.0f, -3.85f, -10.0f);
const FVector FinalHouseRoadGodot(0.0f, 1.1f, -70.0f);
}

APenanceProgressionManager::APenanceProgressionManager()
{
    PrimaryActorTick.bCanEverTick = false;
    Tags.AddUnique(TEXT("PenanceProgressionManager"));
}

void APenanceProgressionManager::BeginPlay()
{
    Super::BeginPlay();
    ApplyProgressionWorldState();
}

APenanceProgressionManager* APenanceProgressionManager::Find(UWorld* World)
{
    if (!World)
    {
        return nullptr;
    }

    for (TActorIterator<APenanceProgressionManager> It(World); It; ++It)
    {
        return *It;
    }
    return nullptr;
}

void APenanceProgressionManager::HandleProgressionEvent(FName EventName, AActor* InstigatorActor)
{
    const FString Event = EventName.ToString();

    if (Event == TEXT("Event_FirstHouse_FrontApproach"))
    {
        if (State == EPenanceProgressionState::Start && !bFirstHouseComplete)
        {
            bFirstHouseApproached = true;
        }
        return;
    }

    if (Event == TEXT("Event_FirstHouse_Entry"))
    {
        if (State == EPenanceProgressionState::Start && !bFirstHouseComplete)
        {
            bFirstHouseApproached = true;
            bFirstHouseEntered = true;
        }
        return;
    }

    if (Event == TEXT("Event_RoadsLoop_NorthExit_TeleportBeforeUnlock"))
    {
        if (!bFinalHouseUnlocked && InstigatorActor)
        {
            FVector Location = InstigatorActor->GetActorLocation();
            Location.X = -1800.0f;
            InstigatorActor->SetActorLocation(Location, false, nullptr, ETeleportType::TeleportPhysics);
        }
        return;
    }

    if (Event == TEXT("Event_Park_LightsFlicker"))
    {
        if (State == EPenanceProgressionState::HouseDone)
        {
            SetState(EPenanceProgressionState::ParkDone);
        }
        return;
    }

    if (Event == TEXT("Event_CulDeSac_LightningPenanceAngle"))
    {
        if (State == EPenanceProgressionState::ParkDone)
        {
            SetState(EPenanceProgressionState::CulDeSacDone);
            UnlockChurch();
        }
        return;
    }

    if (Event == TEXT("Event_Church_Threshold"))
    {
        if (State == EPenanceProgressionState::CulDeSacDone)
        {
            SetState(EPenanceProgressionState::ChurchDone);
        }
        return;
    }

    if (Event == TEXT("Event_Church_BasementEntrance"))
    {
        if (State == EPenanceProgressionState::ChurchDone && bChurchNoticeInspected)
        {
            TeleportActorToGodotPosition(InstigatorActor, TunnelStartGodot);
        }
        return;
    }

    if (Event == TEXT("Event_Tunnel_PressureStarts"))
    {
        if (State == EPenanceProgressionState::ChurchDone && bChurchNoticeInspected)
        {
            SetState(EPenanceProgressionState::BasementDone);
        }
        return;
    }

    if (Event == TEXT("Event_TunnelExit_FinalHouseBecomesReachable"))
    {
        if (State == EPenanceProgressionState::BasementDone)
        {
            UnlockFinalHouse(InstigatorActor);
        }
        return;
    }

    if (Event == TEXT("Event_FosterHouse_FinalApproach"))
    {
        if (State == EPenanceProgressionState::BasementDone && bFinalHouseUnlocked)
        {
            SetState(EPenanceProgressionState::DemoDone);
            CompleteDemo();
        }
    }
}

void APenanceProgressionManager::HandlePickup(FName PickupName, AActor* InstigatorActor)
{
    const FString Pickup = PickupName.ToString();

    if (Pickup.Contains(TEXT("Pickup_BlankFamilyPhoto")))
    {
        bFirstHouseApproached = true;
        bFirstHouseEntered = true;
        CompleteFirstHouse(InstigatorActor);
        return;
    }

    if (Pickup.Contains(TEXT("Pickup_InternalHandlingNotice")))
    {
        bChurchNoticeInspected = true;
        if (State == EPenanceProgressionState::ChurchDone)
        {
            TeleportActorToGodotPosition(InstigatorActor, TunnelStartGodot);
        }
        ApplyProgressionWorldState();
    }
}

void APenanceProgressionManager::DebugResetProgression()
{
    State = EPenanceProgressionState::Start;
    FiredEvents.Reset();
    bFirstHouseApproached = false;
    bFirstHouseEntered = false;
    bFirstHouseComplete = false;
    bChurchNoticeInspected = false;
    bFinalHouseUnlocked = false;
    bDemoComplete = false;
    ApplyProgressionWorldState();
}

void APenanceProgressionManager::DebugFireEvent(FName EventName)
{
    HandleProgressionEvent(EventName, nullptr);
}

void APenanceProgressionManager::DebugPickup(FName PickupName)
{
    HandlePickup(PickupName, nullptr);
}

FString APenanceProgressionManager::GetProgressionStateName() const
{
    switch (State)
    {
    case EPenanceProgressionState::Start:
        return TEXT("START");
    case EPenanceProgressionState::HouseDone:
        return TEXT("HOUSE_DONE");
    case EPenanceProgressionState::ParkDone:
        return TEXT("PARK_DONE");
    case EPenanceProgressionState::CulDeSacDone:
        return TEXT("CUL_DE_SAC_DONE");
    case EPenanceProgressionState::ChurchDone:
        return TEXT("CHURCH_DONE");
    case EPenanceProgressionState::BasementDone:
        return TEXT("BASEMENT_DONE");
    case EPenanceProgressionState::DemoDone:
        return TEXT("DEMO_DONE");
    default:
        return TEXT("UNKNOWN");
    }
}

FText APenanceProgressionManager::GetCurrentObjectiveText() const
{
    switch (State)
    {
    case EPenanceProgressionState::Start:
        return bFirstHouseEntered
            ? FText::FromString(TEXT("First Lit House: inspect the photo on the table."))
            : FText::FromString(TEXT("Arrival Street: follow the wet road toward the warm house light."));
    case EPenanceProgressionState::HouseDone:
        return FText::FromString(TEXT("Park Lure: follow the failing park lamp and the drain."));
    case EPenanceProgressionState::ParkDone:
        return FText::FromString(TEXT("Cul-de-sac: follow the bell after the lightning."));
    case EPenanceProgressionState::CulDeSacDone:
        return FText::FromString(TEXT("Church: the door is open. Enter the community center."));
    case EPenanceProgressionState::ChurchDone:
        return bChurchNoticeInspected
            ? FText::FromString(TEXT("Storm Drain: descend through the basement passage."))
            : FText::FromString(TEXT("Church: inspect the internal handling notice."));
    case EPenanceProgressionState::BasementDone:
        return bFinalHouseUnlocked
            ? FText::FromString(TEXT("Foster House: approach the remembered house."))
            : FText::FromString(TEXT("Storm Drain: keep moving through the buried path."));
    case EPenanceProgressionState::DemoDone:
        return FText::FromString(TEXT("Demo Complete"));
    default:
        return FText::GetEmpty();
    }
}

void APenanceProgressionManager::SetState(EPenanceProgressionState NewState)
{
    if (static_cast<uint8>(NewState) < static_cast<uint8>(State) && State != EPenanceProgressionState::DemoDone)
    {
        return;
    }

    State = NewState;
    ApplyProgressionWorldState();
}

void APenanceProgressionManager::CompleteFirstHouse(AActor* InstigatorActor)
{
    if (bFirstHouseComplete)
    {
        return;
    }

    bFirstHouseComplete = true;
    SetState(EPenanceProgressionState::HouseDone);
}

void APenanceProgressionManager::UnlockChurch()
{
    SetImportedActorsActiveByName({TEXT("Church_RustedDoorBlocker_LockedUntilCulDeSac")}, false);
    ApplyProgressionWorldState();
}

void APenanceProgressionManager::UnlockFinalHouse(AActor* InstigatorActor)
{
    if (bFinalHouseUnlocked)
    {
        return;
    }

    bFinalHouseUnlocked = true;
    ApplyProgressionWorldState();

    if (InstigatorActor && InstigatorActor->GetActorLocation().Z < -100.0f)
    {
        TeleportActorToGodotPosition(InstigatorActor, FinalHouseRoadGodot);
    }
}

void APenanceProgressionManager::CompleteDemo()
{
    bDemoComplete = true;
    SetImportedActorsActiveByPrefix({TEXT("Penance_FarLightning_AuthoredCarrier")}, true);
}

void APenanceProgressionManager::ApplyProgressionWorldState()
{
    const bool bPastHouse = State != EPenanceProgressionState::Start;
    const bool bPastPark = static_cast<uint8>(State) >= static_cast<uint8>(EPenanceProgressionState::ParkDone);
    const bool bPastCulDeSac = static_cast<uint8>(State) >= static_cast<uint8>(EPenanceProgressionState::CulDeSacDone);
    const bool bAtOrPastChurch = static_cast<uint8>(State) >= static_cast<uint8>(EPenanceProgressionState::ChurchDone);
    const bool bAtOrPastBasement = static_cast<uint8>(State) >= static_cast<uint8>(EPenanceProgressionState::BasementDone);

    SetImportedActorsActiveByName({TEXT("RouteGate_ToPark_BlockedUntilHouse")}, !bPastHouse);
    SetImportedActorsActiveByName({TEXT("RouteGate_ToCulDeSac_BlockedUntilPark")}, !bPastPark);
    SetImportedActorsActiveByName({TEXT("RouteGate_ToChurch_BlockedUntilCulDeSac")}, !bPastCulDeSac);
    SetImportedActorsActiveByName({TEXT("Church_RustedDoorBlocker_LockedUntilCulDeSac")}, !bPastCulDeSac);
    SetImportedActorsActiveByName({TEXT("RouteGate_ToBasement_BlockedUntilChurch")}, !(bAtOrPastBasement || bChurchNoticeInspected));

    SetImportedActorsActiveByPrefix({TEXT("SoftBlock_ToPark_StormSheetUntilPhoto")}, !bPastHouse);
    SetImportedActorsActiveByPrefix({TEXT("SoftBlock_ToCulDeSac_FloodedConnectorUntilPark")}, !bPastPark);
    SetImportedActorsActiveByPrefix({TEXT("SoftBlock_EastLoop_FloodedStreetUntilCulDeSac"), TEXT("SoftBlock_ToChurch_ClothWallUntilCulDeSac")}, !bPastCulDeSac);
    SetImportedActorsActiveByPrefix({TEXT("SoftBlock_ToBasement_ChainedStairUntilChurch")}, !(bAtOrPastBasement || bChurchNoticeInspected));
    SetImportedActorsActiveByPrefix({TEXT("SoftFunnel_WestLoop_"), TEXT("SoftFunnel_CulDeSac_")}, !bPastCulDeSac);
    SetImportedActorsActiveByPrefix({TEXT("SoftFunnel_EastLoop_")}, !bAtOrPastChurch);

    SetImportedActorsActiveByName({TEXT("FirstHouse_FalseWall_BecomesDoor")}, !bFirstHouseComplete);
    SetImportedActorsActiveByName({TEXT("FirstHouse_NewDoor_AppearsWhereWallWas")}, bFirstHouseComplete);

    SetImportedActorsActiveByName({TEXT("FinalHouse_RustedGate_BlocksEarlyRoute")}, !bFinalHouseUnlocked);
    SetImportedActorsActiveByName({TEXT("FinalHouse_RoadExtension_AppearsLater")}, bFinalHouseUnlocked);
}

void APenanceProgressionManager::TeleportActorToGodotPosition(AActor* Actor, const FVector& GodotPosition) const
{
    if (!Actor)
    {
        return;
    }

    const FVector UnrealLocation(-GodotPosition.Z * 100.0f, GodotPosition.X * 100.0f, GodotPosition.Y * 100.0f);
    Actor->SetActorLocation(UnrealLocation, false, nullptr, ETeleportType::TeleportPhysics);
    if (ACharacter* Character = Cast<ACharacter>(Actor))
    {
        Character->GetCharacterMovement()->StopMovementImmediately();
    }
}

void APenanceProgressionManager::SetImportedActorsActiveByName(const TArray<FString>& ExactNames, bool bActive) const
{
    SetImportedActorsActive(
        [&ExactNames](const FString& ImportedName)
        {
            return ExactNames.Contains(ImportedName);
        },
        bActive
    );
}

void APenanceProgressionManager::SetImportedActorsActiveByPrefix(const TArray<FString>& NamePrefixes, bool bActive) const
{
    SetImportedActorsActive(
        [&NamePrefixes](const FString& ImportedName)
        {
            for (const FString& Prefix : NamePrefixes)
            {
                if (ImportedName.StartsWith(Prefix))
                {
                    return true;
                }
            }
            return false;
        },
        bActive
    );
}

void APenanceProgressionManager::SetImportedActorsActive(const TFunctionRef<bool(const FString&)>& Predicate, bool bActive) const
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    for (TActorIterator<AActor> It(World); It; ++It)
    {
        FString ImportedName;
        if (GetImportedNameFromActor(*It, ImportedName) && Predicate(ImportedName))
        {
            SetActorActive(*It, bActive);
        }
    }
}

void APenanceProgressionManager::SetActorActive(AActor* Actor, bool bActive)
{
    if (!Actor)
    {
        return;
    }

    Actor->SetActorHiddenInGame(!bActive);
    Actor->SetActorEnableCollision(bActive);

    TArray<UActorComponent*> PrimitiveComponents = Actor->K2_GetComponentsByClass(UPrimitiveComponent::StaticClass());
    for (UActorComponent* Component : PrimitiveComponents)
    {
        if (UPrimitiveComponent* Primitive = Cast<UPrimitiveComponent>(Component))
        {
            Primitive->SetCollisionEnabled(bActive ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
            Primitive->SetHiddenInGame(!bActive);
        }
    }
}

bool APenanceProgressionManager::ActorHasImportedName(const AActor* Actor, const FString& ImportedName)
{
    FString ExistingName;
    return GetImportedNameFromActor(Actor, ExistingName) && ExistingName == ImportedName;
}

bool APenanceProgressionManager::ActorImportedNameStartsWith(const AActor* Actor, const FString& Prefix)
{
    FString ExistingName;
    return GetImportedNameFromActor(Actor, ExistingName) && ExistingName.StartsWith(Prefix);
}

bool APenanceProgressionManager::GetImportedNameFromActor(const AActor* Actor, FString& OutName)
{
    if (!Actor)
    {
        return false;
    }

    for (const FName& Tag : Actor->Tags)
    {
        const FString TagString = Tag.ToString();
        if (TagString.StartsWith(TEXT("ImportedName_")))
        {
            OutName = TagString.RightChop(13);
            return true;
        }
    }

    return false;
}
