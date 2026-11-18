#include "PenanceObjectiveSubsystem.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/GameInstance.h"

void UPenanceObjectiveSubsystem::ResetObjectives()
{
 if(GetWorld()) GetWorld()->GetTimerManager().ClearTimer(CompletionTimer);
 State=FPenanceObjectiveSnapshot(); RecentCompletions.Reset(); CompletionDeadlines.Reset(); SuppressionReasons.Reset(); OnObjectivesChanged.Broadcast();
}
void UPenanceObjectiveSubsystem::SetMainObjective(FName Id,FText Text,int32 Chapter)
{
 if(Id.IsNone()) return;
 const bool bNew=State.MainId!=Id;
 if(!bNew && State.MainText.EqualTo(Text) && State.Chapter==Chapter) return;
 if(bNew) { State.SubObjectives.Reset();State.bMainCompleted=State.CompletedIds.Contains(Id); }
 State.MainId=Id;State.MainText=Text;State.Chapter=FMath::Clamp(Chapter,1,14);
 State.OptionalObjectives.RemoveAll([this](const FPenanceObjectiveEntry& E){return E.ExpiresAfterChapter>0 && State.Chapter>E.ExpiresAfterChapter;});
 OnObjectivesChanged.Broadcast();
}
void UPenanceObjectiveSubsystem::AdvanceMainObjective(FName Id,FText Text,int32 Chapter)
{
 if(State.MainId!=Id && !State.MainId.IsNone()) CompleteMainObjective();
 SetMainObjective(Id,Text,Chapter);
}
void UPenanceObjectiveSubsystem::CompleteMainObjective()
{
 if(State.MainId.IsNone() || State.bMainCompleted) return;
 State.bMainCompleted=true;State.CompletedIds.AddUnique(State.MainId);
 FPenanceObjectiveEntry Entry;Entry.Id=State.MainId;Entry.Text=State.MainText;Entry.Chapter=State.Chapter;Entry.bCompleted=true;
 QueueCompletion(Entry);OnObjectivesChanged.Broadcast();
}
void UPenanceObjectiveSubsystem::AddSubObjective(FName Id,FText Text,bool bAvailable)
{
 if(Id.IsNone() || State.CompletedIds.Contains(Id)) return;
 FPenanceObjectiveEntry* E=State.SubObjectives.FindByPredicate([&](const auto& X){return X.Id==Id;});
 if(!E) E=&State.SubObjectives.AddDefaulted_GetRef();
 E->Id=Id;E->Text=Text;E->Chapter=State.Chapter;E->bAvailable=bAvailable;OnObjectivesChanged.Broadcast();
}
void UPenanceObjectiveSubsystem::RemoveSubObjective(FName Id)
{
 const int32 Removed=State.SubObjectives.RemoveAll([&](const auto& E){return E.Id==Id;})+RecentCompletions.RemoveAll([&](const auto& E){return E.Id==Id;});
 CompletionDeadlines.Remove(Id);ScheduleExpiry();if(Removed)OnObjectivesChanged.Broadcast();
}
void UPenanceObjectiveSubsystem::AddOptionalObjective(FName Id,FText Text,int32 Chapter,int32 ExpiresAfterChapter,bool bAvailable)
{
 if(Id.IsNone() || State.CompletedIds.Contains(Id)) return;
 FPenanceObjectiveEntry* E=State.OptionalObjectives.FindByPredicate([&](const auto& X){return X.Id==Id;});
 if(!E) E=&State.OptionalObjectives.AddDefaulted_GetRef();
 E->Id=Id;E->Text=Text;E->Chapter=FMath::Clamp(Chapter,1,14);E->ExpiresAfterChapter=ExpiresAfterChapter;E->bAvailable=bAvailable;OnObjectivesChanged.Broadcast();
}
void UPenanceObjectiveSubsystem::RemoveOptionalObjective(FName Id)
{
 const int32 Removed=State.OptionalObjectives.RemoveAll([&](const auto& E){return E.Id==Id;})+RecentCompletions.RemoveAll([&](const auto& E){return E.Id==Id;});
 CompletionDeadlines.Remove(Id);ScheduleExpiry();if(Removed)OnObjectivesChanged.Broadcast();
}
bool UPenanceObjectiveSubsystem::CompleteEntry(TArray<FPenanceObjectiveEntry>& Entries,FName Id)
{
 auto* E=Entries.FindByPredicate([&](const auto& X){return X.Id==Id;});
 if(!E || !E->bAvailable || E->bCompleted || E->Chapter>State.Chapter) return false;
 E->bCompleted=true;State.CompletedIds.AddUnique(Id);QueueCompletion(*E);OnObjectivesChanged.Broadcast();return true;
}
bool UPenanceObjectiveSubsystem::CompleteSubObjective(FName Id){return CompleteEntry(State.SubObjectives,Id);}
bool UPenanceObjectiveSubsystem::CompleteOptionalObjective(FName Id){return CompleteEntry(State.OptionalObjectives,Id);}
void UPenanceObjectiveSubsystem::SetObjectiveAvailable(FName Id,bool bAvailable)
{
 bool bChanged=false;
 for(auto* Entries:{&State.SubObjectives,&State.OptionalObjectives,&RecentCompletions}) for(auto& E:*Entries) if(E.Id==Id && E.bAvailable!=bAvailable){E.bAvailable=bAvailable;bChanged=true;}
 if(bChanged) OnObjectivesChanged.Broadcast();
}
void UPenanceObjectiveSubsystem::SetExpanded(bool bExpanded)
{if(State.bExpanded!=bExpanded){State.bExpanded=bExpanded;OnObjectivesChanged.Broadcast();}}
void UPenanceObjectiveSubsystem::ToggleExpanded(){SetExpanded(!State.bExpanded);}
void UPenanceObjectiveSubsystem::SetSuppressed(FName Reason,bool bSuppressed)
{
 const bool bBefore=IsSuppressed();if(bSuppressed) SuppressionReasons.Add(Reason);else SuppressionReasons.Remove(Reason);
 if(bBefore!=IsSuppressed()) OnObjectivesChanged.Broadcast();
}
void UPenanceObjectiveSubsystem::QueueCompletion(const FPenanceObjectiveEntry& Entry)
{
 RecentCompletions.RemoveAll([&](const auto& E){return E.Id==Entry.Id;});RecentCompletions.Add(Entry);
 CompletionDeadlines.Add(Entry.Id,(GetWorld()?GetWorld()->GetTimeSeconds():0)+CompletionDisplaySeconds);ScheduleExpiry();
}
void UPenanceObjectiveSubsystem::ScheduleExpiry()
{
 UWorld* World=GetWorld();if(!World)return;
 World->GetTimerManager().ClearTimer(CompletionTimer);
 double Next=MAX_dbl;for(const auto& E:CompletionDeadlines)Next=FMath::Min(Next,E.Value);
 if(Next!=MAX_dbl)World->GetTimerManager().SetTimer(CompletionTimer,this,&ThisClass::ExpireCompletions,FMath::Max(.01,Next-World->GetTimeSeconds()),false);
}
void UPenanceObjectiveSubsystem::ExpireCompletions()
{
 const double Now=GetWorld()?GetWorld()->GetTimeSeconds():MAX_dbl;
 TArray<FName> Expired;for(const auto& E:CompletionDeadlines)if(E.Value<=Now+.02)Expired.Add(E.Key);
 for(FName Id:Expired)CompletionDeadlines.Remove(Id);
 RecentCompletions.RemoveAll([&](const auto& E){return Expired.Contains(E.Id);});
 State.SubObjectives.RemoveAll([&](const auto& E){return E.bCompleted && Expired.Contains(E.Id);});
 State.OptionalObjectives.RemoveAll([&](const auto& E){return E.bCompleted && Expired.Contains(E.Id);});
 ScheduleExpiry();OnObjectivesChanged.Broadcast();
}
void UPenanceObjectiveSubsystem::RestoreSnapshot(const FPenanceObjectiveSnapshot& Snapshot)
{
 ResetObjectives();State=Snapshot;State.Chapter=FMath::Clamp(State.Chapter,1,14);
 if(State.bMainCompleted && !State.MainId.IsNone())State.CompletedIds.AddUnique(State.MainId);
 for(auto* Entries:{&State.SubObjectives,&State.OptionalObjectives})
 {
  for(const auto& E:*Entries)if(E.bCompleted)State.CompletedIds.AddUnique(E.Id);
  Entries->RemoveAll([](const auto& E){return E.bCompleted;});
 }
 State.OptionalObjectives.RemoveAll([this](const auto& E){return E.ExpiresAfterChapter>0&&State.Chapter>E.ExpiresAfterChapter;});
 OnObjectivesChanged.Broadcast();
}
void UPenanceObjectiveSubsystem::Deinitialize(){if(GetWorld())GetWorld()->GetTimerManager().ClearTimer(CompletionTimer);Super::Deinitialize();}

UPenanceObjectiveSubsystem* UPenanceObjectiveSubsystem::GetObjectiveManager(UObject* Context)
{
 auto* Instance=UGameplayStatics::GetGameInstance(Context);return Instance?Instance->GetSubsystem<UPenanceObjectiveSubsystem>():nullptr;
}
