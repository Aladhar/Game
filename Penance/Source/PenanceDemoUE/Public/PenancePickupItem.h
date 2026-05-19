#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PenancePickupItem.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

UENUM(BlueprintType)
enum class EPenancePickupType : uint8
{
    Item,
    Note
};

UCLASS()
class PENANCEDEMOUE_API APenancePickupItem : public AActor
{
    GENERATED_BODY()

public:
    APenancePickupItem();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Pickup")
    TObjectPtr<UStaticMeshComponent> PickupMesh;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Penance|Pickup")
    TObjectPtr<UBoxComponent> InteractionBounds;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Pickup")
    FText ItemName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Pickup", meta = (MultiLine = true))
    FText ItemDescription;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Pickup")
    EPenancePickupType PickupType = EPenancePickupType::Item;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Pickup")
    bool bIsNote = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Penance|Pickup")
    FName PickupName;

    UFUNCTION(BlueprintCallable, Category = "Penance|Pickup")
    void Interact(AActor* Interactor);
};
