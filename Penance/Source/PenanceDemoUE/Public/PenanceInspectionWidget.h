#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Components/Button.h"
#include "PenanceInspectionWidget.generated.h"
class UPenanceInspectionComponent;class UImage;class UTextBlock;class UScrollBox;class UCanvasPanel;class UBorder;class UMaterialInstanceDynamic;class UWidgetTree;
UCLASS()
class PENANCEDEMOUE_API UPenanceInspectionThumbnailButton : public UButton
{
 GENERATED_BODY()
public:
 UPenanceInspectionThumbnailButton(const FObjectInitializer& Initializer = FObjectInitializer::Get());
 UPROPERTY() TObjectPtr<UPenanceInspectionComponent> Inspector;
 int32 ItemIndex=0;
 UFUNCTION() void Choose();
};
UCLASS()
class PENANCEDEMOUE_API UPenanceInspectionWidget : public UUserWidget
{
 GENERATED_BODY()
public:
 UPROPERTY(Transient,BlueprintReadOnly) TObjectPtr<UPenanceInspectionComponent> Inspector;
 static void BuildLayout(UWidgetTree* Tree);
 void Connect(UPenanceInspectionComponent* Component);
 UFUNCTION(BlueprintCallable) void Refresh();
 UFUNCTION() void ScrollUp();
 UFUNCTION() void ScrollDown();
 UFUNCTION() void ObjectTab();
 UFUNCTION() void FlipClicked();
 UFUNCTION() void CursorClicked();
 UFUNCTION() void OverlayClicked();
 UFUNCTION() void CloseClicked();
protected:
 virtual void NativeConstruct() override;
 virtual void NativeTick(const FGeometry& Geometry,float DeltaSeconds) override;
 virtual FReply NativeOnMouseWheel(const FGeometry& Geometry,const FPointerEvent& Event) override;
private:
 UPROPERTY(Transient) TObjectPtr<UMaterialInstanceDynamic> PreviewMaterial;
 UPROPERTY(Transient) TArray<TObjectPtr<UPenanceInspectionThumbnailButton>> Thumbnails;
 UPROPERTY(Transient) TArray<TObjectPtr<UBorder>> Frames;
 float Age=0;
};
