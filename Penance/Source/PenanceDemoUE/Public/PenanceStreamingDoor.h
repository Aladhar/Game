#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PenanceStreamingDoor.generated.h"

class UPrimitiveComponent;
class UBoxComponent;
class USphereComponent;
class UStaticMeshComponent;
class ULevelStreamingDynamic;
class ACharacter;

// V7.1: Single-player prototype; the outdoor entrance owns the interior streaming instance.
UCLASS()
class PENANCEDEMOUE_API APenanceStreamingDoor : public AActor
{
    GENERATED_BODY()

public:
    APenanceStreamingDoor();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Penance|Streaming")
    void Interact(AActor* Interactor);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Penance|Streaming")
    bool ExteriorEntrance = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Penance|Streaming")
    FString InteriorLevelName = TEXT("/Game/Maps/Interiors/House01_Interior");

    // Interior level is authored near (0,0,0) and loaded far from the outdoor map.
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Penance|Streaming")
    FVector InteriorWorldOffset = FVector(200000.0f, 0.0f, 0.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Penance|Streaming")
    FVector InteriorEntryLocal = FVector(-390.0f, 0.0f, 100.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Penance|Streaming")
    FVector ExteriorExitWorld = FVector(-790.0f, 0.0f, 100.0f);

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Penance|Streaming")
    TObjectPtr<UStaticMeshComponent> DoorMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Penance|Streaming")
    TObjectPtr<UBoxComponent> InteractionBounds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Penance|Streaming")
    TObjectPtr<USphereComponent> PreloadRadius;

private:
    UPROPERTY(Transient)
    TObjectPtr<ULevelStreamingDynamic> InteriorStream;

    TWeakObjectPtr<ACharacter> PendingCharacter;
    bool bPlayerInside = false;
    bool bPlayerNearby = false;
    float FadeRemaining = 0.0f;
    float UnloadRemaining = -1.0f;

    enum class EState : uint8 { Idle, WaitForLoad, FadeIntoHouse, FadeOutOfHouse };
    EState State = EState::Idle;

    UFUNCTION()
    void OnPreloadBegin(UPrimitiveComponent* Component, AActor* OtherActor,
                        UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep,
                        const FHitResult& SweepResult);
    UFUNCTION()
    void OnPreloadEnd(UPrimitiveComponent* Component, AActor* OtherActor,
                      UPrimitiveComponent* OtherComp, int32 OtherBodyIndex);

    void StartPreload();
    void RequestExit(ACharacter* Character);
    void BeginFade(bool bEntering);
    void CompleteTeleport();
    void UnloadInterior();
    void CancelTransition();
};
