#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "PenanceObjectiveTrackerWidget.generated.h"
class UBorder;class USizeBox;class UVerticalBox;class UPenanceObjectiveSubsystem;

UCLASS()
class PENANCEDEMOUE_API UPenanceObjectiveTrackerWidget : public UUserWidget
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance",meta=(ClampMin="0",ClampMax="0.2")) float BackgroundOpacity=.07f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance",meta=(ClampMin="260",ClampMax="520")) float TrackerWidth=420.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance") FLinearColor MainColor=FLinearColor(.83f,.83f,.79f,1.f);
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance") FLinearColor SubColor=FLinearColor(.63f,.64f,.62f,1.f);
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Appearance") FLinearColor OptionalColor=FLinearColor(.53f,.55f,.53f,1.f);
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Objectives") int32 RefreshCount=0;
 UPROPERTY(VisibleAnywhere,BlueprintReadOnly,Category="Objectives") int32 VisibleRowCount=0;
 UPROPERTY(meta=(BindWidgetOptional),BlueprintReadOnly) TObjectPtr<UBorder> TrackerPanel;
 UPROPERTY(meta=(BindWidgetOptional),BlueprintReadOnly) TObjectPtr<USizeBox> WidthBox;
 UPROPERTY(meta=(BindWidgetOptional),BlueprintReadOnly) TObjectPtr<UVerticalBox> ObjectiveRows;
 UFUNCTION(BlueprintCallable) void RefreshObjectives();
 UFUNCTION(BlueprintCallable) void ToggleDetails();
 UFUNCTION(BlueprintCallable) void SetDetailsExpanded(bool bExpanded);
protected:
 virtual void NativeConstruct() override;
 virtual void NativeDestruct() override;
private:
 UPROPERTY(Transient) TObjectPtr<UPenanceObjectiveSubsystem> Manager;
 FTimerHandle FadeTimer;
 double FadeStart=0;
 void FadeStep();
 void AddRow(const FString& Symbol,const FText& Text,int32 FontSize,FLinearColor Color,float Indent);
};
