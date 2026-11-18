#include "PenanceInspectionEditorLibrary.h"
#include "PenanceInspection.h"
#include "PenanceInspectionWidget.h"
#include "Blueprint/WidgetTree.h"
#include "PenancePlayerCharacter.h"
#include "Engine/Font.h"
#include "Engine/FontFace.h"
#include "Engine/TextureRenderTarget2D.h"
#include "GameFramework/PlayerController.h"
#include "InputKeyEventArgs.h"
#include "Framework/Application/SlateApplication.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "Serialization/BufferArchive.h"
#include "Slate/WidgetRenderer.h"
#include "RenderingThread.h"
#if WITH_EDITOR
#include "WidgetBlueprint.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "AssetRegistry/AssetRegistryModule.h"
#endif
bool UPenanceInspectionEditorLibrary::BuildWidget(UBlueprint* Blueprint)
{
#if WITH_EDITOR
 auto* BP=Cast<UWidgetBlueprint>(Blueprint);if(!BP || !BP->ParentClass->IsChildOf(UPenanceInspectionWidget::StaticClass()))return false;
 if(!BP->WidgetTree->RootWidget)UPenanceInspectionWidget::BuildLayout(BP->WidgetTree);
 BP->MarkPackageDirty();FKismetEditorUtilities::CompileBlueprint(BP);return BP->Status!=BS_Error;
#else
 return false;
#endif
}
UFont* UPenanceInspectionEditorLibrary::ImportInspectionFont(const FString& Filename,const FString& AssetPath)
{
#if WITH_EDITOR
 if(auto* Existing=LoadObject<UFont>(nullptr,*(AssetPath+TEXT(".")+FPaths::GetBaseFilename(AssetPath))))return Existing;
 TArray<uint8> Bytes;if(!FFileHelper::LoadFileToArray(Bytes,*Filename))return nullptr;
 const FString FacePath=AssetPath+TEXT("_Face");auto* FP=CreatePackage(*FacePath);auto* Face=NewObject<UFontFace>(FP,*FPaths::GetBaseFilename(FacePath),RF_Public|RF_Standalone);Face->SourceFilename=Filename;Face->LoadingPolicy=EFontLoadingPolicy::Inline;Face->FontFaceData=FFontFaceData::MakeFontFaceData(MoveTemp(Bytes));Face->CacheSubFaces();FAssetRegistryModule::AssetCreated(Face);Face->MarkPackageDirty();
 auto* P=CreatePackage(*AssetPath);auto* Font=NewObject<UFont>(P,*FPaths::GetBaseFilename(AssetPath),RF_Public|RF_Standalone);Font->FontCacheType=EFontCacheType::Runtime;FTypefaceEntry Entry(FName(TEXT("Regular")));Entry.Font=FFontData(Face);Font->GetMutableInternalCompositeFont().DefaultTypeface.Fonts.Add(Entry);FAssetRegistryModule::AssetCreated(Font);Font->MarkPackageDirty();return Font;
#else
 return nullptr;
#endif
}
bool UPenanceInspectionEditorLibrary::SendGameKey(APlayerController* P,FKey K,bool Down){return P && P->InputKey(FInputKeyEventArgs(nullptr,FInputDeviceId::CreateFromInternalId(0),K,Down?IE_Pressed:IE_Released,FPlatformTime::Cycles64()));}
bool UPenanceInspectionEditorLibrary::SendInspectKey(APlayerController* P,FKey K)
{
 if(!P || !FSlateApplication::IsInitialized())return false;
 return FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(K,FModifierKeysState(),0,false,0,0));
}
bool UPenanceInspectionEditorLibrary::SendInspectMouse(APlayerController* P,FVector2D D)
{
 if(!P || !FSlateApplication::IsInitialized())return false;
 const FVector2D Pos=FSlateApplication::Get().GetCursorPos();
 // Same relative pointer event used by the inspection preprocessor, with no buttons down.
 FPointerEvent E(0,Pos+D,Pos,TSet<FKey>(),EKeys::Invalid,0,FModifierKeysState());return FSlateApplication::Get().ProcessMouseMoveEvent(E,true);
}
bool UPenanceInspectionEditorLibrary::SendInspectWheel(APlayerController* P,float Delta)
{
 auto* Pawn=P?Cast<APenancePlayerCharacter>(P->GetPawn()):nullptr;if(!Pawn || !Pawn->Inspection || !Pawn->Inspection->bInspecting)return false;
 Pawn->Inspection->ZoomByWheel(Delta);return true;
}
bool UPenanceInspectionEditorLibrary::RenderInspection(APlayerController* PC,FIntPoint Resolution,const FString& Filename)
{
 auto* P=PC?Cast<APenancePlayerCharacter>(PC->GetPawn()):nullptr;if(!P || !P->Inspection || !P->Inspection->Widget)return false;
 auto* Clone=CreateWidget<UPenanceInspectionWidget>(PC,P->Inspection->Widget->GetClass());Clone->Inspector=P->Inspection;auto Slate=Clone->TakeWidget();Clone->Connect(P->Inspection);Clone->ForceLayoutPrepass();Clone->SetRenderOpacity(1);
 FWidgetRenderer Renderer(false,true);auto* Target=Renderer.DrawWidget(Slate,FVector2D(Resolution));FlushRenderingCommands();FBufferArchive Data;const bool Good=Target && FImageUtils::ExportRenderTarget2DAsPNG(Target,Data) && FFileHelper::SaveArrayToFile(Data,*Filename);Clone->ReleaseSlateResources(true);return Good;
}
