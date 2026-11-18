#include "PenanceV5WorldDirector.h"
#include "Animation/AnimSequence.h"
#include "Components/SceneComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Engine.h"
#include "Animation/SkeletalMeshActor.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"

APenanceV5WorldDirector::APenanceV5WorldDirector()
{
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickInterval = 0.1f;
}
void APenanceV5WorldDirector::BeginPlay()
{
    Super::BeginPlay();
    SetTaggedActors(TEXT("V5_AfterHouse"), false);
    SetTaggedActors(TEXT("V5_ParkShortcutBarrier"), true);
    SetTaggedActors(TEXT("V5_EstateBarrier"), true);
}
FString APenanceV5WorldDirector::GetObjective() const
{
    return Objectives.IsValidIndex(Stage) ? Objectives[Stage] : TEXT("The ridge is quiet. V5 preview complete — explore or restart Play.");
}
void APenanceV5WorldDirector::SetTaggedActors(FName Tag, bool bActive)
{
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
        if (It->ActorHasTag(Tag)) { It->SetActorHiddenInGame(!bActive); It->SetActorEnableCollision(bActive); }
}
void APenanceV5WorldDirector::ShowEnemy(const FVector& Position, UAnimSequence* Animation, float Yaw)
{
    if (Encounter) Encounter->Destroy();
    Encounter = nullptr;
    if (!EnemyMesh || !Animation) return;
    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    Encounter = GetWorld()->SpawnActor<ASkeletalMeshActor>(Position, FRotator(0.f,Yaw,0.f), Params);
    if (Encounter)
    {
        USkeletalMeshComponent* Mesh = Encounter->GetSkeletalMeshComponent();
        Mesh->SetMobility(EComponentMobility::Movable);
        Mesh->SetSkeletalMeshAsset(EnemyMesh);
        Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Mesh->PlayAnimation(Animation, true);
        EncounterTime = 0.f;
    }
}
void APenanceV5WorldDirector::Advance()
{
    ++Stage;
    UE_LOG(LogTemp, Display, TEXT("PENANCE_V5_STAGE %d: %s"), Stage, *GetObjective());
    if (Stage == 1) ShowEnemy(InteriorSilhouette, IdleAnimation, 180.f);
    if (Stage == 2)
    {
        if (Encounter) Encounter->Destroy(); Encounter = nullptr; EncounterTime = -1.f;
        SetTaggedActors(TEXT("V5_AfterHouse"), true);
    }
    if (Stage == 3) SetTaggedActors(TEXT("V5_ParkShortcutBarrier"), false);
    if (Stage == 6 && ChasePath.Num() > 1)
    {
        ShowEnemy(ChasePath[0], ChaseAnimation, 90.f); bChasing = true;
    }
    if (Stage == 7)
    {
        SetTaggedActors(TEXT("V5_EstateBarrier"), false);
        if (Encounter) Encounter->Destroy(); Encounter = nullptr; EncounterTime = -1.f; bChasing = false;
    }
}
void APenanceV5WorldDirector::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    APawn* Player = UGameplayStatics::GetPlayerPawn(this,0);
    if (!Player) return;
    if (GEngine) GEngine->AddOnScreenDebugMessage(12005,0.25f,FColor(225,214,181),GetObjective());
    const FVector Position = Player->GetActorLocation();
    if (Stage == 0 && Position.X > 150000.f) Advance();
    else if (Stage == 1 && Position.X < 100000.f) Advance();
    else if (Stage >= 2 && Checkpoints.IsValidIndex(Stage) && FVector::Dist2D(Position,Checkpoints[Stage]) < CheckpointRadius
        && FMath::Abs(Position.Z-Checkpoints[Stage].Z) < 230.f) Advance();
    if (Encounter && EncounterTime >= 0.f)
    {
        EncounterTime += DeltaSeconds;
        if (bChasing)
        {
            float Distance = EncounterTime * 160.f;
            bool bPlaced = false;
            for (int32 I=1; I<ChasePath.Num(); ++I)
            {
                const float Segment = FVector::Distance(ChasePath[I-1],ChasePath[I]);
                if (Distance <= Segment)
                {
                    Encounter->SetActorLocation(FMath::Lerp(ChasePath[I-1],ChasePath[I],Distance/FMath::Max(Segment,1.f)));
                    Encounter->SetActorRotation((ChasePath[I]-ChasePath[I-1]).Rotation()); bPlaced = true; break;
                }
                Distance -= Segment;
            }
            if (!bPlaced) { Encounter->Destroy(); Encounter = nullptr; EncounterTime = -1.f; bChasing = false; }
        }
        else if (EncounterTime > 9.f) { Encounter->Destroy(); Encounter = nullptr; EncounterTime = -1.f; }
    }
}
