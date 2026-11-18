#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "Components/ActorComponent.h"
#include "GameFramework/Actor.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "PenanceInspection.generated.h"
class UStaticMesh;class UTexture2D;class UStaticMeshComponent;class USceneCaptureComponent2D;class UTextureRenderTarget2D;class UPointLightComponent;class UPenanceInspectionWidget;class APenancePlayerCharacter;class IInputProcessor;

// One reusable item definition. No inventory/story state is stored in the viewer.
UCLASS(BlueprintType)
class PENANCEDEMOUE_API UPenanceInspectItem : public UDataAsset
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Inspection") FText Title;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Inspection",meta=(MultiLine=true)) FText Description;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Inspection",meta=(MultiLine=true)) FText Thought;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Inspection") TObjectPtr<UStaticMesh> Mesh;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Inspection") TObjectPtr<UTexture2D> Thumbnail;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Inspection|Optional Memory") TObjectPtr<UStaticMesh> MemoryMesh;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Inspection|Optional Memory") TObjectPtr<UTexture2D> MemoryThumbnail;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Inspection") FRotator InitialRotation=FRotator(4,8,-8);
};

UCLASS()
class PENANCEDEMOUE_API APenanceInspectObject : public AActor
{
 GENERATED_BODY()
public:
 APenanceInspectObject();
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly) TObjectPtr<UStaticMeshComponent> ObjectMesh;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Inspection") TArray<TObjectPtr<UPenanceInspectItem>> Items;
 UFUNCTION(BlueprintCallable) bool Interact(APenancePlayerCharacter* Player);
};

// Transient render stage: only the selected mesh is captured. Never saved in a level.
UCLASS(Transient,NotPlaceable)
class PENANCEDEMOUE_API APenanceInspectionStage : public AActor
{
 GENERATED_BODY()
public:
 APenanceInspectionStage();
 UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> Preview;
 UPROPERTY(VisibleAnywhere) TObjectPtr<USceneCaptureComponent2D> Capture;
 UPROPERTY(VisibleAnywhere) TObjectPtr<UPointLightComponent> Key;
 UPROPERTY(VisibleAnywhere) TObjectPtr<UPointLightComponent> Fill;
 UPROPERTY(VisibleAnywhere) TObjectPtr<UPointLightComponent> Rim;
 UPROPERTY(Transient) TObjectPtr<UTextureRenderTarget2D> Target;
 float FitDistance=200;
 void Initialize();
 void SetItem(UPenanceInspectItem* Item);
 void UpdateView(const FQuat& Rotation,float Zoom);
};

UCLASS(ClassGroup=(Penance),meta=(BlueprintSpawnableComponent))
class PENANCEDEMOUE_API UPenanceInspectionComponent : public UActorComponent
{
 GENERATED_BODY()
public:
 UPenanceInspectionComponent();
 virtual void EndPlay(const EEndPlayReason::Type Reason) override;
 virtual void TickComponent(float DeltaTime,ELevelTick Tick,FActorComponentTickFunction* Function) override;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Inspection",meta=(ClampMin="0.05",ClampMax="2")) float RotationSensitivity=.32f;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Inspection",meta=(ClampMin="1",ClampMax="25")) float ZoomSmoothing=14.f;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Inspection") bool bInspecting=false;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Inspection") bool bCursorMode=false;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Inspection") bool bMemory=false;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Inspection") int32 SelectedIndex=INDEX_NONE;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Inspection") float Zoom=1;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Inspection") float TargetZoom=1;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Inspection") FQuat ObjectRotation=FQuat::Identity;
 UPROPERTY(Transient,BlueprintReadOnly) TObjectPtr<UPenanceInspectionWidget> Widget;
 UPROPERTY(Transient,BlueprintReadOnly) TObjectPtr<APenanceInspectionStage> Stage;
 UPROPERTY(Transient,BlueprintReadOnly) TArray<TObjectPtr<UPenanceInspectItem>> Items;
 UFUNCTION(BlueprintCallable) bool OpenInspection(APenanceInspectObject* Source);
 UFUNCTION(BlueprintCallable) void CloseInspection();
 UFUNCTION(BlueprintCallable) void RotateByMouse(FVector2D Delta);
 UFUNCTION(BlueprintCallable) void ZoomByWheel(float Delta);
 UFUNCTION(BlueprintCallable) void Flip();
 UFUNCTION(BlueprintCallable) void ToggleCursor();
 UFUNCTION(BlueprintCallable) void ToggleMemory();
 UFUNCTION(BlueprintCallable) void SelectItem(int32 Index);
 UFUNCTION(BlueprintPure) bool HasMemory() const;
 bool ProcessKey(FKey Key);
 void ApplyInputMode();
private:
 TSharedPtr<IInputProcessor> InputProcessor;
 TWeakObjectPtr<APenancePlayerCharacter> Player;
 FVector SavedLocation;
 FRotator SavedControlRotation;
 EMovementMode SavedMovementMode=MOVE_Walking;
 uint8 SavedCustomMode=0;
 bool bSavedCursor=false;
 bool bDiscardNextDelta=true;
 float OpenAge=0;
};
