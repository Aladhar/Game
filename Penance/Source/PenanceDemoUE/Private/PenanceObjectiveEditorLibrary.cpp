#include "PenanceObjectiveEditorLibrary.h"
#include "PenanceObjectiveTrackerWidget.h"
#include "PenanceHUD.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/SizeBox.h"
#include "Components/VerticalBox.h"
#include "Engine/UserInterfaceSettings.h"
#include "GameFramework/PlayerController.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/BufferArchive.h"
#include "Slate/WidgetRenderer.h"
#include "Widgets/Layout/SDPIScaler.h"
#include "Widgets/Layout/SBorder.h"
#include "Brushes/SlateColorBrush.h"
#include "RenderingThread.h"
#include "UnrealClient.h"
#if WITH_EDITOR
#include "WidgetBlueprint.h"
#include "Editor.h"
#include "PlayInEditorDataTypes.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Settings/LevelEditorPlaySettings.h"
#endif
bool UPenanceObjectiveEditorLibrary::BuildTrackerBlueprint(UBlueprint* Blueprint)
{
#if WITH_EDITOR
 auto* BP=Cast<UWidgetBlueprint>(Blueprint);if(!BP || !BP->ParentClass->IsChildOf(UPenanceObjectiveTrackerWidget::StaticClass()) || BP->WidgetTree->RootWidget)return false;
 auto* Tree=BP->WidgetTree.Get();
 auto* Canvas=Tree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(),TEXT("RootLayout"));Tree->RootWidget=Canvas;Canvas->SetVisibility(ESlateVisibility::HitTestInvisible);
 auto* Width=Tree->ConstructWidget<USizeBox>(USizeBox::StaticClass(),TEXT("WidthBox"));Width->bIsVariable=true;Width->SetWidthOverride(420);
 auto* Slot=Canvas->AddChildToCanvas(Width);Slot->SetAnchors(FAnchors(1,0));Slot->SetAlignment(FVector2D(1,0));Slot->SetPosition(FVector2D(-48,40));Slot->SetAutoSize(true);
 auto* Border=Tree->ConstructWidget<UBorder>(UBorder::StaticClass(),TEXT("TrackerPanel"));Border->bIsVariable=true;Border->SetPadding(FMargin(12,8));Border->SetBrushColor(FLinearColor(.035f,.04f,.04f,.07f));Border->SetVisibility(ESlateVisibility::HitTestInvisible);Width->AddChild(Border);
 auto* Rows=Tree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(),TEXT("ObjectiveRows"));Rows->bIsVariable=true;Border->AddChild(Rows);
 BP->MarkPackageDirty();FKismetEditorUtilities::CompileBlueprint(BP);return BP->Status!=BS_Error;
#else
 return false;
#endif
}
bool UPenanceObjectiveEditorLibrary::ConfigurePlayerPlaySettings()
{
#if WITH_EDITOR
 auto* Settings=GetMutableDefault<ULevelEditorPlaySettings>();Settings->GameGetsMouseControl=true;Settings->LastExecutedPlayModeType=PlayMode_InViewPort;Settings->LastExecutedPlayModeLocation=PlayLocation_DefaultPlayerStart;Settings->SaveConfig();return true;
#else
 return false;
#endif
}
bool UPenanceObjectiveEditorLibrary::RenderTrackerLayout(APlayerController* Player,FIntPoint Resolution,const FString& Filename,FLinearColor Backdrop)
{
 if(!Player || Resolution.X<320 || Resolution.Y<240)return false;
 auto* HUD=Cast<APenanceHUD>(Player->GetHUD());if(!HUD || !HUD->ObjectiveTracker)return false;
 auto* Widget=CreateWidget<UPenanceObjectiveTrackerWidget>(Player,HUD->ObjectiveTracker->GetClass());if(!Widget)return false;
 const float Scale=GetDefault<UUserInterfaceSettings>()->GetDPIScaleBasedOnSize(Resolution);
 FSlateColorBrush Background(Backdrop);
 TSharedRef<SWidget> Layout=SNew(SBorder).BorderImage(&Background).Padding(0)[SNew(SDPIScaler).DPIScale(Scale)[Widget->TakeWidget()]];
 Widget->ForceLayoutPrepass();if(Widget->TrackerPanel)Widget->TrackerPanel->SetRenderOpacity(1);
 FWidgetRenderer Renderer(false,true);auto* Target=Renderer.DrawWidget(Layout,FVector2D(Resolution));FlushRenderingCommands();
 FBufferArchive Data;const bool bOK=Target && FImageUtils::ExportRenderTarget2DAsPNG(Target,Data) && FFileHelper::SaveArrayToFile(Data,*Filename);
 Widget->ReleaseSlateResources(true);return bOK;
}
void UPenanceObjectiveEditorLibrary::CaptureGameplay(const FString& Filename){FScreenshotRequest::RequestScreenshot(Filename,true,false);}

bool UPenanceObjectiveEditorLibrary::BeginValidationPlay(int32 Width,int32 Height)
{
#if WITH_EDITOR
 auto* Settings=GetMutableDefault<ULevelEditorPlaySettings>();Settings->NewWindowWidth=Width;Settings->NewWindowHeight=Height;
 FRequestPlaySessionParams Params;Params.WorldType=EPlaySessionWorldType::PlayInEditor;GEditor->RequestPlaySession(Params);return true;
#else
 return false;
#endif
}
