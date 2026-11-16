#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "PenancePlayerAssetLibrary.generated.h"

class UAnimMontage;
class UAnimSequence;
class UMaterialInterface;
class USkeletalMesh;

UCLASS()
class PENANCEDEMOUE_API UPenancePlayerAssetLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Penance|Editor")
    static bool BuildPlayerAnimationGraph();

    UFUNCTION(BlueprintCallable, Category = "Penance|Editor")
    static bool BuildPlayerInputMappings();

    UFUNCTION(BlueprintCallable, Category = "Penance|Editor")
    static bool AssignSkeletalMeshMaterial(USkeletalMesh* Mesh, int32 Slot, UMaterialInterface* Material);

    UFUNCTION(BlueprintCallable, Category = "Penance|Editor")
    static bool UseRecoveredReaction(UAnimMontage* Montage, UAnimSequence* Clip);

    // Frame-major transforms: each frame has one local pose for every bone.
    UFUNCTION(BlueprintCallable, Category = "Penance|Editor")
    static bool WritePlayerPoseClip(UAnimSequence* Clip, int32 FrameRate,
        const TArray<FName>& Bones, const TArray<FTransform>& LocalPoses);
};
