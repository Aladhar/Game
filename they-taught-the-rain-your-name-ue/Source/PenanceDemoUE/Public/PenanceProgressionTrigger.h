#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PenanceProgressionTrigger.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

UCLASS()
class PENANCEDEMOUE_API APenanceProgressionTrigger : public AActor
{
    GENERATED_BODY()

public:
    APenanceProgressionTrigger();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Progression")
    TObjectPtr<UBoxComponent> TriggerBounds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Progression")
    TObjectPtr<UStaticMeshComponent> DebugMesh;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Progression")
    FName TriggerName;

protected:
    virtual void BeginPlay() override;

private:
    UFUNCTION()
    void OnTriggerOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);
};
