#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PenanceV5WorldDirector.generated.h"
class USkeletalMesh;
class UAnimSequence;
class ASkeletalMeshActor;

// Only placed in the independent V5 blockout. Existing progression is untouched.
UCLASS()
class PENANCEDEMOUE_API APenanceV5WorldDirector : public AActor
{
    GENERATED_BODY()
public:
    APenanceV5WorldDirector();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="V5|Slice") TArray<FVector> Checkpoints;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="V5|Slice") TArray<FString> Objectives;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="V5|Slice") float CheckpointRadius = 500.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="V5|Encounter") TObjectPtr<USkeletalMesh> EnemyMesh;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="V5|Encounter") TObjectPtr<UAnimSequence> IdleAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="V5|Encounter") TObjectPtr<UAnimSequence> ChaseAnimation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="V5|Encounter") FVector InteriorSilhouette = FVector(200120.f,0.f,0.f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="V5|Encounter") TArray<FVector> ChasePath;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="V5|Slice") int32 Stage = 0;
    UFUNCTION(BlueprintCallable, Category="V5|Slice") FString GetObjective() const;
private:
    void Advance();
    void PublishObjectives();
    void SuppressObjectives(bool bHidden);
    void SetTaggedActors(FName Tag, bool bActive);
    void ShowEnemy(const FVector& Position, UAnimSequence* Animation, float Yaw);
    UPROPERTY(Transient) TObjectPtr<ASkeletalMeshActor> Encounter;
    float EncounterTime = -1.f;
    bool bChasing = false;
};
