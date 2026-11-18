#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "PenanceObjectiveTrigger.generated.h"
class UBoxComponent;
UCLASS()
class PENANCEDEMOUE_API APenanceObjectiveTrigger : public AActor
{
 GENERATED_BODY()
public:
 APenanceObjectiveTrigger();
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly) TObjectPtr<UBoxComponent> Bounds;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Objectives") FName ObjectiveId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Objectives") bool bOptional=false;
protected:
 virtual void BeginPlay() override;
private:
 UFUNCTION() void Entered(UPrimitiveComponent* Component,AActor* Actor,UPrimitiveComponent* Other,int32 Body,bool bSweep,const FHitResult& Hit);
};
