#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "GameFramework/SaveGame.h"
#include "TimerManager.h"
#include "PenanceObjectiveSubsystem.generated.h"

USTRUCT(BlueprintType)
struct FPenanceObjectiveEntry
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName Id;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FText Text;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Chapter = 1;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 ExpiresAfterChapter = 0;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bCompleted = false;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bAvailable = true;
};
USTRUCT(BlueprintType)
struct FPenanceObjectiveSnapshot
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName MainId;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FText MainText;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Chapter = 1;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bMainCompleted = false;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bExpanded = true;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FPenanceObjectiveEntry> SubObjectives;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FPenanceObjectiveEntry> OptionalObjectives;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> CompletedIds;
};
UCLASS(BlueprintType)
class PENANCEDEMOUE_API UPenanceObjectiveSaveGame : public USaveGame
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FPenanceObjectiveSnapshot Objectives;
};
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FPenanceObjectivesChanged);
UCLASS()
class PENANCEDEMOUE_API UPenanceObjectiveSubsystem : public UGameInstanceSubsystem
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintPure,meta=(WorldContext="Context")) static UPenanceObjectiveSubsystem* GetObjectiveManager(UObject* Context);
 UPROPERTY(BlueprintAssignable) FPenanceObjectivesChanged OnObjectivesChanged;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly) FPenanceObjectiveSnapshot State;
 UPROPERTY(VisibleAnywhere, BlueprintReadOnly) TArray<FPenanceObjectiveEntry> RecentCompletions;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Objectives", meta=(ClampMin="0.5",ClampMax="10")) float CompletionDisplaySeconds = 3.f;
 UFUNCTION(BlueprintCallable) void ResetObjectives();
 UFUNCTION(BlueprintCallable) void SetMainObjective(FName Id, FText Text, int32 Chapter);
 UFUNCTION(BlueprintCallable) void AdvanceMainObjective(FName Id, FText Text, int32 Chapter);
 UFUNCTION(BlueprintCallable) void CompleteMainObjective();
 UFUNCTION(BlueprintCallable) void AddSubObjective(FName Id, FText Text, bool bAvailable = true);
 UFUNCTION(BlueprintCallable) void RemoveSubObjective(FName Id);
 UFUNCTION(BlueprintCallable) bool CompleteSubObjective(FName Id);
 UFUNCTION(BlueprintCallable) void AddOptionalObjective(FName Id, FText Text, int32 Chapter, int32 ExpiresAfterChapter = 0, bool bAvailable = true);
 UFUNCTION(BlueprintCallable) void RemoveOptionalObjective(FName Id);
 UFUNCTION(BlueprintCallable) bool CompleteOptionalObjective(FName Id);
 UFUNCTION(BlueprintCallable) void SetObjectiveAvailable(FName Id, bool bAvailable);
 UFUNCTION(BlueprintCallable) void SetExpanded(bool bExpanded);
 UFUNCTION(BlueprintCallable) void ToggleExpanded();
 UFUNCTION(BlueprintCallable) void SetSuppressed(FName Reason, bool bSuppressed);
 UFUNCTION(BlueprintPure) bool IsSuppressed() const { return SuppressionReasons.Num()>0; }
 UFUNCTION(BlueprintPure) bool IsObjectiveCompleted(FName Id) const { return State.CompletedIds.Contains(Id); }
 UFUNCTION(BlueprintPure) FPenanceObjectiveSnapshot CaptureSnapshot() const { return State; }
 UFUNCTION(BlueprintCallable) void RestoreSnapshot(const FPenanceObjectiveSnapshot& Snapshot);
 virtual void Deinitialize() override;
private:
 TSet<FName> SuppressionReasons;
 TMap<FName,double> CompletionDeadlines;
 FTimerHandle CompletionTimer;
 void QueueCompletion(const FPenanceObjectiveEntry& Entry);
 void ExpireCompletions();
 void ScheduleExpiry();
 bool CompleteEntry(TArray<FPenanceObjectiveEntry>& Entries,FName Id);
};
