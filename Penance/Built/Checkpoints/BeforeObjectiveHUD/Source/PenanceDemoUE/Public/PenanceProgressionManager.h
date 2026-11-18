#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PenanceProgressionManager.generated.h"

UENUM(BlueprintType)
enum class EPenanceProgressionState : uint8
{
    Start,
    HouseDone,
    ParkDone,
    CulDeSacDone,
    ChurchDone,
    BasementDone,
    DemoDone
};

UCLASS()
class PENANCEDEMOUE_API APenanceProgressionManager : public AActor
{
    GENERATED_BODY()

public:
    APenanceProgressionManager();

    virtual void BeginPlay() override;

    UFUNCTION(BlueprintCallable, Category = "Penance|Progression")
    void HandleProgressionEvent(FName EventName, AActor* InstigatorActor);

    UFUNCTION(BlueprintCallable, Category = "Penance|Progression")
    void HandlePickup(FName PickupName, AActor* InstigatorActor);

    UFUNCTION(BlueprintCallable, Category = "Penance|Progression")
    void DebugResetProgression();

    UFUNCTION(BlueprintCallable, Category = "Penance|Progression")
    void DebugFireEvent(FName EventName);

    UFUNCTION(BlueprintCallable, Category = "Penance|Progression")
    void DebugPickup(FName PickupName);

    UFUNCTION(BlueprintCallable, Category = "Penance|Progression")
    FString GetProgressionStateName() const;

    UFUNCTION(BlueprintCallable, Category = "Penance|Progression")
    FText GetCurrentObjectiveText() const;

    UFUNCTION(BlueprintCallable, Category = "Penance|Progression")
    bool IsFinalHouseUnlocked() const { return bFinalHouseUnlocked; }

    UFUNCTION(BlueprintCallable, Category = "Penance|Progression")
    bool IsChurchNoticeInspected() const { return bChurchNoticeInspected; }

    static APenanceProgressionManager* Find(UWorld* World);

private:
    void SetState(EPenanceProgressionState NewState);
    void ApplyProgressionWorldState();
    void CompleteFirstHouse(AActor* InstigatorActor);
    void UnlockChurch();
    void UnlockFinalHouse(AActor* InstigatorActor);
    void CompleteDemo();
    void TeleportActorToGodotPosition(AActor* Actor, const FVector& GodotPosition) const;

    void SetImportedActorsActiveByName(const TArray<FString>& ExactNames, bool bActive) const;
    void SetImportedActorsActiveByPrefix(const TArray<FString>& NamePrefixes, bool bActive) const;
    void SetImportedActorsActive(const TFunctionRef<bool(const FString&)>& Predicate, bool bActive) const;
    static void SetActorActive(AActor* Actor, bool bActive);
    static bool ActorHasImportedName(const AActor* Actor, const FString& ImportedName);
    static bool ActorImportedNameStartsWith(const AActor* Actor, const FString& Prefix);
    static bool GetImportedNameFromActor(const AActor* Actor, FString& OutName);

    EPenanceProgressionState State = EPenanceProgressionState::Start;
    TSet<FName> FiredEvents;

    bool bFirstHouseApproached = false;
    bool bFirstHouseEntered = false;
    bool bFirstHouseComplete = false;
    bool bChurchNoticeInspected = false;
    bool bFinalHouseUnlocked = false;
    bool bDemoComplete = false;
};
