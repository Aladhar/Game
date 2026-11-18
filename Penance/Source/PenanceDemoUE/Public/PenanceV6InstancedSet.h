#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PenanceV6InstancedSet.generated.h"
class UHierarchicalInstancedStaticMeshComponent;
// Simple saved HISM container: no ticking, AI, or gameplay behavior.
UCLASS()
class PENANCEDEMOUE_API APenanceV6InstancedSet : public AActor
{
 GENERATED_BODY()
public:
 APenanceV6InstancedSet();
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="V6|Environment") TObjectPtr<UHierarchicalInstancedStaticMeshComponent> Instances;
};
