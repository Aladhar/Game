#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimInstance.h"
#include "PenancePlayerAnimInstance.generated.h"

UCLASS(Blueprintable, BlueprintType)
class PENANCEDEMOUE_API UPenancePlayerAnimInstance : public UAnimInstance
{
    GENERATED_BODY()

public:
    virtual void NativeUpdateAnimation(float DeltaSeconds) override;

    UPROPERTY(BlueprintReadOnly, Category = "Penance|Locomotion")
    float Speed = 0.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Penance|Locomotion")
    bool bIsCrouched = false;

    UPROPERTY(BlueprintReadOnly, Category = "Penance|Locomotion")
    bool bIsAirborne = false;

    UPROPERTY(BlueprintReadOnly, Category = "Penance|Locomotion")
    bool bIsStrafing = false;

    UPROPERTY(BlueprintReadOnly, Category = "Penance|Locomotion")
    float GaitPlayRate = 1.0f;

    UPROPERTY(BlueprintReadOnly, Category = "Penance|Locomotion")
    float StrafePlayRate = 1.0f;
};
