#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PenanceHingedDoor.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

UCLASS()
class PENANCEDEMOUE_API APenanceHingedDoor : public AActor
{
    GENERATED_BODY()

public:
    APenanceHingedDoor();

    virtual void Tick(float DeltaSeconds) override;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Door")
    TObjectPtr<USceneComponent> HingeRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Door")
    TObjectPtr<UStaticMeshComponent> DoorMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Door")
    TObjectPtr<UBoxComponent> InteractionBounds;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Door")
    float OpenAngleDegrees = 92.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Door")
    float OpenSpeed = 7.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Door")
    bool bStartsOpen = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Door")
    bool bOpensAwayFromPlayer = true;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Door")
    bool bIsOpen = false;

    UFUNCTION(BlueprintCallable, Category = "Penance|Door")
    void Interact(AActor* Interactor);

protected:
    virtual void BeginPlay() override;

private:
    float ClosedYaw = 0.0f;
    float TargetYaw = 0.0f;
};
