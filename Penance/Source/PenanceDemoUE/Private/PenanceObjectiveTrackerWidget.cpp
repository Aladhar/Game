#include "PenanceObjectiveTrackerWidget.h"
#include "PenanceObjectiveSubsystem.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Styling/CoreStyle.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"

void UPenanceObjectiveTrackerWidget::NativeConstruct()
{
 Super::NativeConstruct();SetIsFocusable(false);SetVisibility(ESlateVisibility::HitTestInvisible);
 // The saved Widget Blueprint supplies the editable designer tree. This native
 // fallback keeps the game usable if that asset is temporarily unavailable.
 if(!TrackerPanel || !ObjectiveRows || !WidthBox)
 {
  auto* Canvas=WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(),TEXT("RootLayout"));WidgetTree->RootWidget=Canvas;
  WidthBox=WidgetTree->ConstructWidget<USizeBox>(USizeBox::StaticClass(),TEXT("WidthBox"));
  auto* Slot=Canvas->AddChildToCanvas(WidthBox);Slot->SetAnchors(FAnchors(1,0));Slot->SetAlignment(FVector2D(1,0));Slot->SetPosition(FVector2D(-48,40));Slot->SetAutoSize(true);
  TrackerPanel=WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(),TEXT("TrackerPanel"));WidthBox->AddChild(TrackerPanel);TrackerPanel->SetPadding(FMargin(12,8));
  ObjectiveRows=WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("ObjectiveRows"));TrackerPanel->AddChild(ObjectiveRows);
 }
 WidthBox->SetWidthOverride(TrackerWidth);TrackerPanel->SetBrushColor(FLinearColor(.035f,.04f,.04f,BackgroundOpacity));
 if(GetGameInstance())Manager=GetGameInstance()->GetSubsystem<UPenanceObjectiveSubsystem>();
 if(Manager)Manager->OnObjectivesChanged.AddUniqueDynamic(this,&ThisClass::RefreshObjectives);
 RefreshObjectives();
}
void UPenanceObjectiveTrackerWidget::AddRow(const FString& Symbol,const FText& Text,int32 Size,FLinearColor Color,float Indent)
{
 auto* Row=WidgetTree->ConstructWidget<UHorizontalBox>();auto* RSlot=ObjectiveRows->AddChildToVerticalBox(Row);RSlot->SetPadding(FMargin(Indent,4,0,4));
 auto* MarkerBox=WidgetTree->ConstructWidget<USizeBox>();MarkerBox->SetWidthOverride(24);Row->AddChildToHorizontalBox(MarkerBox);
 auto* Marker=WidgetTree->ConstructWidget<UTextBlock>();Marker->SetText(FText::FromString(Symbol));Marker->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"),Size));Marker->SetColorAndOpacity(FSlateColor(Color));Marker->SetShadowOffset(FVector2D(0,1));Marker->SetShadowColorAndOpacity(FLinearColor(0,0,0,.55f));MarkerBox->AddChild(Marker);
 auto* Label=WidgetTree->ConstructWidget<UTextBlock>();Label->SetText(Text);Label->SetFont(FCoreStyle::GetDefaultFontStyle(TEXT("Regular"),Size));Label->SetColorAndOpacity(FSlateColor(Color));Label->SetShadowOffset(FVector2D(0,1));Label->SetShadowColorAndOpacity(FLinearColor(0,0,0,.55f));Label->SetAutoWrapText(true);Label->SetJustification(ETextJustify::Left);
 auto* TSlot=Row->AddChildToHorizontalBox(Label);TSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
 Row->SetVisibility(ESlateVisibility::HitTestInvisible);++VisibleRowCount;
}
void UPenanceObjectiveTrackerWidget::RefreshObjectives()
{
 ++RefreshCount;if(!ObjectiveRows || !Manager)return;
 ObjectiveRows->ClearChildren();VisibleRowCount=0;
 const auto& S=Manager->State;
 const bool bMainVisible=!S.MainId.IsNone() && (!S.bMainCompleted || Manager->RecentCompletions.ContainsByPredicate([&](const auto& E){return E.Id==S.MainId;}));
 if(bMainVisible)AddRow(S.bMainCompleted?TEXT("\u2713"):S.bExpanded?TEXT("\u2228"):TEXT("\u203a"),S.MainText,18,MainColor,0);
 if(S.bExpanded)
 {
  for(const auto& E:S.SubObjectives)if(E.bAvailable && !E.bCompleted)AddRow(TEXT("\u25cb"),E.Text,15,SubColor,24);
  int32 Shown=0;
  for(int32 I=Manager->RecentCompletions.Num()-1;I>=0 && Shown<2;--I)
  {
   const auto& E=Manager->RecentCompletions[I];
   if(!E.bAvailable || (E.Id==S.MainId && S.bMainCompleted))continue;
   AddRow(TEXT("\u2713"),E.Text,14,OptionalColor,24);++Shown;
  }
 }
 const bool bOptionalVisible=S.OptionalObjectives.ContainsByPredicate([&](const auto& E){return E.bAvailable && !E.bCompleted && E.Chapter<=S.Chapter && (E.ExpiresAfterChapter==0||S.Chapter<=E.ExpiresAfterChapter);});
 if(bOptionalVisible)
 {
  auto* Separator=WidgetTree->ConstructWidget<UBorder>();Separator->SetBrushColor(FLinearColor(.6f,.6f,.57f,.09f));
  auto* Thin=WidgetTree->ConstructWidget<USizeBox>();Thin->SetHeightOverride(1);Thin->AddChild(Separator);ObjectiveRows->AddChildToVerticalBox(Thin)->SetPadding(FMargin(0,7,0,5));
  for(const auto& E:S.OptionalObjectives)if(E.bAvailable && !E.bCompleted && E.Chapter<=S.Chapter && (E.ExpiresAfterChapter==0||S.Chapter<=E.ExpiresAfterChapter))AddRow(TEXT("\u203a"),FText::Format(NSLOCTEXT("Penance","OptionalObjective","Optional: {0}"),E.Text),14,OptionalColor,0);
 }
 SetVisibility(Manager->IsSuppressed()||VisibleRowCount==0?ESlateVisibility::Collapsed:ESlateVisibility::HitTestInvisible);
 if(GetWorld() && !Manager->IsSuppressed() && VisibleRowCount)
 {
  FadeStart=GetWorld()->GetTimeSeconds();TrackerPanel->SetRenderOpacity(.65f);
  GetWorld()->GetTimerManager().SetTimer(FadeTimer,this,&ThisClass::FadeStep,1.f/30.f,true);
 }
}
void UPenanceObjectiveTrackerWidget::FadeStep()
{
 if(!GetWorld())return;
 const float A=FMath::Clamp(float((GetWorld()->GetTimeSeconds()-FadeStart)/.25),0.f,1.f);
 if(TrackerPanel)TrackerPanel->SetRenderOpacity(FMath::Lerp(.65f,1.f,A));
 if(A>=1.f)GetWorld()->GetTimerManager().ClearTimer(FadeTimer);
}
void UPenanceObjectiveTrackerWidget::ToggleDetails(){if(Manager)Manager->ToggleExpanded();}
void UPenanceObjectiveTrackerWidget::SetDetailsExpanded(bool bExpanded){if(Manager)Manager->SetExpanded(bExpanded);}
void UPenanceObjectiveTrackerWidget::NativeDestruct()
{
 if(Manager)Manager->OnObjectivesChanged.RemoveDynamic(this,&ThisClass::RefreshObjectives);
 if(GetWorld())GetWorld()->GetTimerManager().ClearTimer(FadeTimer);Super::NativeDestruct();
}
