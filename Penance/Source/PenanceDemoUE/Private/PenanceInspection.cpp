#include "PenanceInspection.h"
#include "PenanceInspectionWidget.h"
#include "PenancePlayerCharacter.h"
#include "PenanceObjectiveSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/PointLightComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/PlayerController.h"
#include "Framework/Application/SlateApplication.h"
#include "Framework/Application/IInputProcessor.h"
#include "InputCoreTypes.h"
#include "Blueprint/WidgetBlueprintLibrary.h"
#include "Engine/World.h"

// This exists only while inspecting. Preview key handling precedes the editor's
// Escape shortcut; raw relative pointer deltas never reach the gameplay camera.
class FPenanceInspectionInput final : public IInputProcessor
{
 TWeakObjectPtr<UPenanceInspectionComponent> Owner;
public:
 explicit FPenanceInspectionInput(UPenanceInspectionComponent* In):Owner(In){}
 virtual void Tick(float,FSlateApplication&,TSharedRef<ICursor>) override {}
 virtual bool HandleKeyDownEvent(FSlateApplication&,const FKeyEvent& E) override
 {
  if(!Owner.IsValid() || !Owner->bInspecting)return false;
  if(!E.IsRepeat() && Owner->ProcessKey(E.GetKey()))return true;
  const FKey K=E.GetKey();
  return K==EKeys::E || K==EKeys::W || K==EKeys::A || K==EKeys::S || K==EKeys::D || K==EKeys::SpaceBar || K==EKeys::LeftShift || K==EKeys::LeftControl || K==EKeys::C || K==EKeys::J || K==EKeys::T || K==EKeys::O;
 }
 virtual bool HandleMouseMoveEvent(FSlateApplication&,const FPointerEvent& E) override
 {
  if(!Owner.IsValid() || !Owner->bInspecting || Owner->bCursorMode)return false;
  Owner->RotateByMouse(E.GetCursorDelta());return true;
 }
 virtual bool HandleMouseButtonDownEvent(FSlateApplication&,const FPointerEvent&) override
 {return Owner.IsValid() && Owner->bInspecting && !Owner->bCursorMode;}
 virtual bool HandleMouseWheelOrGestureEvent(FSlateApplication&,const FPointerEvent& E,const FPointerEvent*) override
 {
  if(!Owner.IsValid() || !Owner->bInspecting || Owner->bCursorMode)return false;
  Owner->ZoomByWheel(E.GetWheelDelta());return true;
 }
};
APenanceInspectObject::APenanceInspectObject()
{
 PrimaryActorTick.bCanEverTick=false;ObjectMesh=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ObjectMesh"));RootComponent=ObjectMesh;
 ObjectMesh->SetMobility(EComponentMobility::Static);ObjectMesh->SetCollisionProfileName(TEXT("BlockAll"));
}
bool APenanceInspectObject::Interact(APenancePlayerCharacter* P){return P && P->Inspection && P->Inspection->OpenInspection(this);}
APenanceInspectionStage::APenanceInspectionStage()
{
 PrimaryActorTick.bCanEverTick=false;SetActorEnableCollision(false);
 auto* Root=CreateDefaultSubobject<USceneComponent>(TEXT("StageRoot"));RootComponent=Root;
 Preview=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Preview"));Preview->SetupAttachment(Root);Preview->SetMobility(EComponentMobility::Movable);Preview->SetCollisionEnabled(ECollisionEnabled::NoCollision);Preview->SetLightingChannels(false,true,false);Preview->SetCastShadow(true);
 Capture=CreateDefaultSubobject<USceneCaptureComponent2D>(TEXT("InspectionCamera"));Capture->SetupAttachment(Root);Capture->FOVAngle=40;Capture->CaptureSource=ESceneCaptureSource::SCS_SceneColorHDR;Capture->PrimitiveRenderMode=ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;Capture->bCaptureEveryFrame=false;Capture->bCaptureOnMovement=false;Capture->bAlwaysPersistRenderingState=true;
 Capture->ShowFlags.SetAtmosphere(false);Capture->ShowFlags.SetFog(false);Capture->ShowFlags.SetMotionBlur(false);Capture->ShowFlags.SetTemporalAA(false);
 Key=CreateDefaultSubobject<UPointLightComponent>(TEXT("WarmKey"));Fill=CreateDefaultSubobject<UPointLightComponent>(TEXT("SoftFill"));Rim=CreateDefaultSubobject<UPointLightComponent>(TEXT("EdgeLight"));
 for(auto* L:{Key.Get(),Fill.Get(),Rim.Get()}){L->SetupAttachment(Root);L->SetMobility(EComponentMobility::Movable);L->SetLightingChannels(false,true,false);L->SetAttenuationRadius(600);L->SetCastShadows(false);L->SetIntensityUnits(ELightUnits::Lumens);}
 Key->SetRelativeLocation(FVector(-90,-65,100));Key->SetIntensity(3800);Key->SetLightColor(FLinearColor(1,.79,.55));
 Fill->SetRelativeLocation(FVector(-80,100,15));Fill->SetIntensity(1700);Fill->SetLightColor(FLinearColor(.65,.74,1));
 Rim->SetRelativeLocation(FVector(45,-25,100));Rim->SetIntensity(2300);Rim->SetLightColor(FLinearColor(1,.66,.34));
}
void APenanceInspectionStage::Initialize()
{
 Target=NewObject<UTextureRenderTarget2D>(this);Target->RenderTargetFormat=RTF_RGBA16f;Target->ClearColor=FLinearColor::Transparent;Target->InitAutoFormat(1920,1200);Target->UpdateResourceImmediate(true);Capture->TextureTarget=Target;Capture->ShowOnlyComponent(Preview);
}
void APenanceInspectionStage::SetItem(UPenanceInspectItem* Item)
{
 Preview->SetStaticMesh(Item?Item->Mesh.Get():nullptr);
 if(Item && Item->Mesh)
 {
  const auto B=Item->Mesh->GetBounds();Preview->SetRelativeLocation(-B.Origin);
  const float Extent=FMath::Max3(B.BoxExtent.X,B.BoxExtent.Y,B.BoxExtent.Z);
  FitDistance=FMath::Max(20.f,Extent/(FMath::Tan(FMath::DegreesToRadians(Capture->FOVAngle*.5f))*(1200.f/1920.f))*1.15f);
 }
}
void APenanceInspectionStage::UpdateView(const FQuat& Rotation,float ZoomValue)
{
 Preview->SetRelativeRotation(Rotation);
 if(UStaticMesh* Mesh=Preview->GetStaticMesh())Preview->SetRelativeLocation(-Rotation.RotateVector(Mesh->GetBounds().Origin));
 Capture->SetRelativeLocation(FVector(-FitDistance/ZoomValue,0,0));Capture->SetRelativeRotation(FRotator::ZeroRotator);Capture->CaptureScene();
}
UPenanceInspectionComponent::UPenanceInspectionComponent(){PrimaryComponentTick.bCanEverTick=true;PrimaryComponentTick.bStartWithTickEnabled=false;}
bool UPenanceInspectionComponent::OpenInspection(APenanceInspectObject* Source)
{
 if(bInspecting || !Source || Source->Items.IsEmpty())return false;
 Player=Cast<APenancePlayerCharacter>(GetOwner());if(!Player.IsValid() || Player->IsInventoryOpen())return false;
 auto* PC=Cast<APlayerController>(Player->GetController());if(!PC || !PC->IsLocalController())return false;
 Items.Reset();for(const auto& I:Source->Items)if(IsValid(I) && I->Mesh)Items.Add(I);if(Items.IsEmpty())return false;
 SavedLocation=Player->GetActorLocation();SavedControlRotation=PC->GetControlRotation();bSavedCursor=PC->bShowMouseCursor;
 auto* Movement=Player->GetCharacterMovement();SavedMovementMode=Movement->MovementMode;SavedCustomMode=Movement->CustomMovementMode;Movement->StopMovementImmediately();Movement->DisableMovement();
 PC->SetIgnoreMoveInput(true);PC->SetIgnoreLookInput(true);Player->SetInspectionLock(true);
 FActorSpawnParameters Params;Params.ObjectFlags|=RF_Transient;Params.SpawnCollisionHandlingOverride=ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
 Stage=GetWorld()->SpawnActor<APenanceInspectionStage>(APenanceInspectionStage::StaticClass(),FVector(500000,500000,50000),FRotator::ZeroRotator,Params);Stage->Initialize();
 UClass* Class=LoadClass<UPenanceInspectionWidget>(nullptr,TEXT("/Game/UI/Inspection/WBP_ObjectInspection.WBP_ObjectInspection_C"));
 Widget=CreateWidget<UPenanceInspectionWidget>(PC,Class?Class:UPenanceInspectionWidget::StaticClass());
 bInspecting=true;bCursorMode=false;SelectedIndex=INDEX_NONE;OpenAge=0;Widget->Inspector=this;Widget->AddToPlayerScreen(100);Widget->Connect(this);
 InputProcessor=MakeShared<FPenanceInspectionInput>(this);FSlateApplication::Get().RegisterInputPreProcessor(InputProcessor,0);
 if(auto* M=GetWorld()->GetGameInstance()->GetSubsystem<UPenanceObjectiveSubsystem>())M->SetSuppressed(TEXT("ObjectInspection"),true);
 SelectItem(0);ApplyInputMode();SetComponentTickEnabled(true);UE_LOG(LogTemp,Display,TEXT("PENANCE_INSPECTION_OPEN %s"),*Items[0]->Title.ToString());return true;
}
void UPenanceInspectionComponent::CloseInspection()
{
 if(!bInspecting)return;bInspecting=false;
 if(InputProcessor.IsValid() && FSlateApplication::IsInitialized())FSlateApplication::Get().UnregisterInputPreProcessor(InputProcessor);InputProcessor.Reset();
 if(Widget){Widget->RemoveFromParent();Widget=nullptr;}if(Stage){Stage->Destroy();Stage=nullptr;}
 if(Player.IsValid())
 {
  auto* M=Player->GetCharacterMovement();M->StopMovementImmediately();M->SetMovementMode(SavedMovementMode,SavedCustomMode);
  if(auto* PC=Cast<APlayerController>(Player->GetController())){PC->SetControlRotation(SavedControlRotation);PC->SetIgnoreMoveInput(false);PC->SetIgnoreLookInput(false);PC->bShowMouseCursor=bSavedCursor;PC->SetInputMode(FInputModeGameOnly());}
  Player->SetInspectionLock(false);
 }
 if(GetWorld() && GetWorld()->GetGameInstance())GetWorld()->GetGameInstance()->GetSubsystem<UPenanceObjectiveSubsystem>()->SetSuppressed(TEXT("ObjectInspection"),false);
 Items.Reset();SelectedIndex=INDEX_NONE;SetComponentTickEnabled(false);UE_LOG(LogTemp,Display,TEXT("PENANCE_INSPECTION_CLOSED"));
}
void UPenanceInspectionComponent::ApplyInputMode()
{
 if(!Player.IsValid())return;auto* PC=Cast<APlayerController>(Player->GetController());if(!PC)return;
 bDiscardNextDelta=true;PC->bShowMouseCursor=bCursorMode;
 if(bCursorMode){FInputModeGameAndUI Mode;Mode.SetWidgetToFocus(Widget->TakeWidget());Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);Mode.SetHideCursorDuringCapture(false);PC->SetInputMode(Mode);}
 else{FInputModeGameOnly Mode;Mode.SetConsumeCaptureMouseDown(false);PC->SetInputMode(Mode);UWidgetBlueprintLibrary::SetFocusToGameViewport();}
 if(Widget)Widget->Refresh();
}
void UPenanceInspectionComponent::RotateByMouse(FVector2D D)
{
 if(!bInspecting || bCursorMode)return;
 if(bDiscardNextDelta){bDiscardNextDelta=false;return;}
 if(!FMath::IsFinite(D.X)||!FMath::IsFinite(D.Y))return;
 const float R=FMath::DegreesToRadians(RotationSensitivity);
 ObjectRotation=(FQuat(FVector::UpVector,-D.X*R)*FQuat(FVector::RightVector,D.Y*R)*ObjectRotation).GetNormalized();
}
void UPenanceInspectionComponent::ZoomByWheel(float D){if(bInspecting)TargetZoom=FMath::Clamp(TargetZoom*FMath::Pow(1.12f,D),.62f,1.6f);}
void UPenanceInspectionComponent::Flip(){if(bInspecting)ObjectRotation=(FQuat(FVector::UpVector,PI)*ObjectRotation).GetNormalized();}
void UPenanceInspectionComponent::ToggleCursor(){if(!bInspecting)return;bCursorMode=!bCursorMode;ApplyInputMode();}
bool UPenanceInspectionComponent::HasMemory() const{return Items.IsValidIndex(SelectedIndex) && Items[SelectedIndex]->MemoryMesh;}
void UPenanceInspectionComponent::ToggleMemory()
{
 if(!bInspecting || !HasMemory())return;bMemory=!bMemory;Stage->Preview->SetStaticMesh(bMemory?Items[SelectedIndex]->MemoryMesh:Items[SelectedIndex]->Mesh);if(Widget)Widget->Refresh();
}
void UPenanceInspectionComponent::SelectItem(int32 I)
{
 if(!bInspecting || !Items.IsValidIndex(I) || I==SelectedIndex)return;SelectedIndex=I;bMemory=false;ObjectRotation=Items[I]->InitialRotation.Quaternion();Zoom=TargetZoom=1;Stage->SetItem(Items[I]);if(Widget)Widget->Refresh();
}
bool UPenanceInspectionComponent::ProcessKey(FKey K)
{
 if(!bInspecting)return false;
 if(K==EKeys::Escape){CloseInspection();return true;}if(K==EKeys::Tab){ToggleCursor();return true;}if(K==EKeys::F){Flip();return true;}if(K==EKeys::R){ToggleMemory();return true;}return false;
}
void UPenanceInspectionComponent::TickComponent(float D,ELevelTick T,FActorComponentTickFunction* F)
{
 Super::TickComponent(D,T,F);if(!bInspecting)return;if(!Player.IsValid() || !Player->GetController()){CloseInspection();return;}
 Zoom=FMath::FInterpTo(Zoom,TargetZoom,D,ZoomSmoothing);if(Stage)Stage->UpdateView(ObjectRotation,Zoom);OpenAge+=D;
}
void UPenanceInspectionComponent::EndPlay(const EEndPlayReason::Type R){CloseInspection();Super::EndPlay(R);}
