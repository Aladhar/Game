#include "PenanceObjectiveTrigger.h"
#include "PenanceObjectiveSubsystem.h"
#include "Components/BoxComponent.h"
#include "Engine/GameInstance.h"
#include "Kismet/GameplayStatics.h"
APenanceObjectiveTrigger::APenanceObjectiveTrigger()
{
 PrimaryActorTick.bCanEverTick=false;Bounds=CreateDefaultSubobject<UBoxComponent>(TEXT("Bounds"));RootComponent=Bounds;Bounds->SetBoxExtent(FVector(200,200,160));
 Bounds->SetCollisionEnabled(ECollisionEnabled::QueryOnly);Bounds->SetCollisionResponseToAllChannels(ECR_Ignore);Bounds->SetCollisionResponseToChannel(ECC_Pawn,ECR_Overlap);Bounds->SetGenerateOverlapEvents(true);
}
void APenanceObjectiveTrigger::BeginPlay(){Super::BeginPlay();Bounds->OnComponentBeginOverlap.AddDynamic(this,&ThisClass::Entered);}
void APenanceObjectiveTrigger::Entered(UPrimitiveComponent*,AActor* Actor,UPrimitiveComponent*,int32,bool,const FHitResult&)
{
 if(Actor!=UGameplayStatics::GetPlayerPawn(this,0) || !GetGameInstance())return;
 auto* M=GetGameInstance()->GetSubsystem<UPenanceObjectiveSubsystem>();if(!M)return;
 if(bOptional)M->CompleteOptionalObjective(ObjectiveId);else M->CompleteSubObjective(ObjectiveId);
}
