#include "PenanceInspectionWidget.h"
#include "PenanceInspection.h"
#include "Blueprint/WidgetTree.h"
#include "Components/BackgroundBlur.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/ScaleBox.h"
#include "Components/SizeBox.h"
#include "Components/Image.h"
#include "Components/TextBlock.h"
#include "Components/ScrollBox.h"
#include "Components/ScrollBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/Font.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Styling/CoreStyle.h"

namespace InspectUI
{
 const FLinearColor Ivory(.77f,.72f,.62f,1),Muted(.39f,.36f,.30f,1),Amber(.95f,.57f,.26f,1);
 UCanvasPanelSlot* At(UCanvasPanel* C,UWidget* W,FVector2D Pos,FVector2D Size){auto* S=C->AddChildToCanvas(W);S->SetPosition(Pos);S->SetSize(Size);return S;}
 UBorder* Line(UWidgetTree* T,UCanvasPanel* C,FString Name,FVector2D P,FVector2D S,FLinearColor Color)
 {auto* B=T->ConstructWidget<UBorder>(UBorder::StaticClass(),FName(Name));B->SetPadding(0);B->SetBrushColor(Color);B->SetVisibility(ESlateVisibility::HitTestInvisible);At(C,B,P,S);return B;}
 FSlateFontInfo Font(int Size,bool Hand=false)
 {
  auto* F=LoadObject<UFont>(nullptr,Hand?TEXT("/Game/UI/Inspection/Fonts/F_InspectionHand.F_InspectionHand"):TEXT("/Game/UI/Inspection/Fonts/F_InspectionSerif.F_InspectionSerif"));
  return F?FSlateFontInfo(F,Size):FCoreStyle::GetDefaultFontStyle(TEXT("Regular"),Size);
 }
 UTextBlock* Text(UWidgetTree* T,UCanvasPanel* C,FString Name,FString Value,FVector2D P,FVector2D Size,int FS,FLinearColor Color=Ivory,bool Hand=false)
 {auto* W=T->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(),FName(Name));W->SetText(FText::FromString(Value));W->SetFont(Font(FS,Hand));W->SetColorAndOpacity(Color);W->SetAutoWrapText(true);W->SetVisibility(ESlateVisibility::HitTestInvisible);At(C,W,P,Size);return W;}
 UButton* Button(UWidgetTree* T,UCanvasPanel* C,FString Name,FString Label,FVector2D P,FVector2D Size,int FS,FLinearColor Color=Ivory)
 {
  auto* W=T->ConstructWidget<UPenanceInspectionThumbnailButton>(UPenanceInspectionThumbnailButton::StaticClass(),FName(Name));FButtonStyle S;S.Normal.DrawAs=ESlateBrushDrawType::NoDrawType;S.Hovered=S.Normal;S.Pressed=S.Normal;S.Disabled=S.Normal;S.NormalPadding=FMargin(0);S.PressedPadding=FMargin(0);W->SetStyle(S);
  auto* L=T->ConstructWidget<UTextBlock>();L->SetText(FText::FromString(Label));L->SetFont(Font(FS));L->SetColorAndOpacity(Color);L->SetJustification(ETextJustify::Center);W->AddChild(L);At(C,W,P,Size);return W;
 }
 void Key(UWidgetTree* T,UCanvasPanel* C,FString Name,FString Value,float X,float Y,float Width=28)
 {
  Line(T,C,Name+TEXT("Border"),{X,Y},{Width,29},FLinearColor(.61,.55,.44,.7));Line(T,C,Name+TEXT("Fill"),{X+1,Y+1},{Width-2,27},FLinearColor(.015,.012,.009,1));auto* L=Text(T,C,Name,Value,{X,Y-1},{Width,30},22);L->SetJustification(ETextJustify::Center);
 }
}
UPenanceInspectionThumbnailButton::UPenanceInspectionThumbnailButton(const FObjectInitializer& I):Super(I){InitIsFocusable(false);}
void UPenanceInspectionThumbnailButton::Choose(){if(Inspector)Inspector->SelectItem(ItemIndex);}
void UPenanceInspectionWidget::BuildLayout(UWidgetTree* T)
{
 using namespace InspectUI;
 auto* Root=T->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(),TEXT("InspectionRoot"));T->RootWidget=Root;
 auto* Blur=T->ConstructWidget<UBackgroundBlur>();Blur->SetBlurStrength(9);auto* BS=At(Root,Blur,{0,0},{0,0});BS->SetAnchors(FAnchors(0,0,1,1));BS->SetOffsets(FMargin(0));
 auto* Shade=T->ConstructWidget<UImage>();auto* ShadeMaterial=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/UI/Inspection/M_InspectionShade.M_InspectionShade"));
 if(ShadeMaterial)Shade->SetBrushFromMaterial(ShadeMaterial);else Shade->SetColorAndOpacity(FLinearColor(.014,.010,.008,.9));
 Shade->SetVisibility(ESlateVisibility::HitTestInvisible);auto* SS=At(Root,Shade,{0,0},{0,0});SS->SetAnchors(FAnchors(0,0,1,1));SS->SetOffsets(FMargin(0));
 auto* Scale=T->ConstructWidget<UScaleBox>();Scale->SetStretch(EStretch::ScaleToFit);auto* Slot=At(Root,Scale,{0,0},{0,0});Slot->SetAnchors(FAnchors(0,0,1,1));Slot->SetOffsets(FMargin(0));
 auto* Fixed=T->ConstructWidget<USizeBox>();Fixed->SetWidthOverride(1680);Fixed->SetHeightOverride(945);Scale->AddChild(Fixed);
 auto* C=T->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(),TEXT("ReferenceCanvas"));Fixed->AddChild(C);
 Text(T,C,TEXT("PenanceLogo"),TEXT("P  E  N  A  N  C  E"),{50,30},{260,38},20);
 Line(T,C,TEXT("LogoStroke"),{145,15},{1,62},FLinearColor(.65,.48,.27,.6));
 Key(T,C,TEXT("TopQ"),TEXT("Q"),443,22);Key(T,C,TEXT("TopE"),TEXT("E"),1208,22);
 Button(T,C,TEXT("ObjectTab"),TEXT("OBJECT"),{514,17},{118,36},25);
 auto* Glow=T->ConstructWidget<UImage>();auto* GM=LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/UI/Inspection/M_InspectionGlow.M_InspectionGlow"));if(GM)Glow->SetBrushFromMaterial(GM);Glow->SetVisibility(ESlateVisibility::HitTestInvisible);At(C,Glow,{490,46},{166,16});
 for(auto Def:{TPair<FString,float>(TEXT("RECOLLECTIONS"),674),{TEXT("JOURNAL"),923},{TEXT("MAP"),1090}})
 {auto* B=Button(T,C,Def.Key+TEXT("Tab"),Def.Key,{Def.Value,18},{Def.Key==TEXT("RECOLLECTIONS")?190.f:110.f,35},24,Muted);B->SetIsEnabled(false);B->SetToolTipText(FText::FromString(TEXT("Unavailable")));}
 for(float X:{655.f,892.f,1055.f})Line(T,C,TEXT("TopDivider")+FString::SanitizeFloat(X),{X,28},{1,14},FLinearColor(.4,.33,.23,.16));
 Button(T,C,TEXT("ScrollUp"),TEXT("⌃"),{85,126},{44,35},34);Button(T,C,TEXT("ScrollDown"),TEXT("⌄"),{85,603},{44,35},34);
 auto* Strip=T->ConstructWidget<UScrollBox>(UScrollBox::StaticClass(),TEXT("ItemStrip"));Strip->SetScrollBarVisibility(ESlateVisibility::Collapsed);Strip->SetAnimateWheelScrolling(true);At(C,Strip,{36,174},{146,407});
 auto* Image=T->ConstructWidget<UImage>(UImage::StaticClass(),TEXT("ObjectPreview"));Image->SetVisibility(ESlateVisibility::HitTestInvisible);At(C,Image,{205,105},{1120,716});
 Line(T,C,TEXT("RightHairline"),{1330,157},{1,485},FLinearColor(.35,.29,.22,.16));
 Text(T,C,TEXT("ObjectTitle"),TEXT(""),{1366,151},{300,41},27);
 Line(T,C,TEXT("TitleRule"),{1366,190},{300,1},FLinearColor(.43,.38,.30,.42));
 Text(T,C,TEXT("ObjectDescription"),TEXT(""),{1366,207},{288,69},23,FLinearColor(.58,.54,.46,1));
 Line(T,C,TEXT("ThoughtRule"),{1366,282},{300,1},FLinearColor(.43,.38,.30,.42));
 auto* ThoughtHeading=Text(T,C,TEXT("ThoughtHeading"),TEXT("T H O U G H T S"),{1366,308},{285,28},20,Muted);
 Text(T,C,TEXT("ObjectThought"),TEXT(""),{1366,345},{286,105},29,Ivory,true);
 Line(T,C,TEXT("MemoryRule"),{1366,463},{300,1},FLinearColor(.43,.38,.30,.42));
 Text(T,C,TEXT("MemoryHeading"),TEXT("◇  M E M O R Y   O V E R L A Y"),{1366,492},{300,30},19,Muted);
 auto* Current=T->ConstructWidget<UImage>(UImage::StaticClass(),TEXT("CurrentMemory"));At(C,Current,{1371,542},{128,92});Current->SetVisibility(ESlateVisibility::HitTestInvisible);
 auto* Previous=T->ConstructWidget<UImage>(UImage::StaticClass(),TEXT("PreviousMemory"));At(C,Previous,{1526,542},{128,92});Previous->SetVisibility(ESlateVisibility::HitTestInvisible);
 Text(T,C,TEXT("CurrentCaption"),TEXT("Current"),{1400,640},{115,27},21);
 Text(T,C,TEXT("PreviousCaption"),TEXT("Unavailable"),{1540,640},{125,27},21,Muted);
 // Thin waveform decoration is visible in the reference; it is not an audio control.
 Line(T,C,TEXT("WaveBaseline"),{50,885},{295,1},FLinearColor(.55,.52,.45,.18));
 for(int I=0;I<108;++I){const float A=(.5f+.5f*FMath::Sin(I*1.93f))*FMath::Pow(FMath::Sin((I+1)*PI/110),2)*20;Line(T,C,TEXT("Wave")+FString::FromInt(I),{50+I*2.7f,885-A*.5f},{1,FMath::Max(1.f,A)},FLinearColor(.55,.52,.45,.2));}
 Text(T,C,TEXT("ObservationSubtitle"),TEXT(""),{400,816},{850,35},25,Ivory,true)->SetJustification(ETextJustify::Center);
 // Compact mouse symbols drawn from widget lines; no dependency on a pictogram font.
 for(float X:{507.f,653.f})
 {
  Line(T,C,TEXT("MouseOuter")+FString::SanitizeFloat(X),{X,887},{17,29},FLinearColor(.62,.57,.47,1));Line(T,C,TEXT("MouseInner")+FString::SanitizeFloat(X),{X+1,888},{15,27},FLinearColor(.015,.012,.009,1));Line(T,C,TEXT("MouseSplit")+FString::SanitizeFloat(X),{X,899},{17,1},FLinearColor(.62,.57,.47,1));Line(T,C,TEXT("MouseWheel")+FString::SanitizeFloat(X),{X+8,888},{1,10},Ivory);
 }
 Text(T,C,TEXT("RotateControl"),TEXT("Rotate"),{540,886},{83,31},23);Text(T,C,TEXT("ZoomControl"),TEXT("Zoom"),{686,886},{81,31},23);
 Key(T,C,TEXT("FlipKey"),TEXT("F"),782,886);Button(T,C,TEXT("FlipAction"),TEXT("Flip"),{820,884},{55,34},23);
 Key(T,C,TEXT("OverlayKey"),TEXT("R"),915,886);Button(T,C,TEXT("OverlayAction"),TEXT("Overlay"),{950,884},{94,34},23);
 Key(T,C,TEXT("CloseKey"),TEXT("Esc"),1078,886,38);Button(T,C,TEXT("CloseAction"),TEXT("Close"),{1123,884},{75,34},23);
 for(float X:{625.f,758.f,889.f,1054.f})Line(T,C,TEXT("BottomDivider")+FString::SanitizeFloat(X),{X,894},{1,14},FLinearColor(.43,.38,.30,.35));
 Button(T,C,TEXT("CursorAction"),TEXT("Tab  ·  Cursor"),{1210,887},{120,27},18,Muted);
}
void UPenanceInspectionWidget::NativeConstruct()
{
 Super::NativeConstruct();SetIsFocusable(true);
 if(!WidgetTree->RootWidget)BuildLayout(WidgetTree);
 // AddDynamic requires method tokens, so keep these explicit for UHT/reflection.
 if(auto* B=Cast<UButton>(GetWidgetFromName(TEXT("ScrollUp"))))B->OnClicked.AddDynamic(this,&ThisClass::ScrollUp);
 if(auto* B=Cast<UButton>(GetWidgetFromName(TEXT("ScrollDown"))))B->OnClicked.AddDynamic(this,&ThisClass::ScrollDown);
 if(auto* B=Cast<UButton>(GetWidgetFromName(TEXT("ObjectTab"))))B->OnClicked.AddDynamic(this,&ThisClass::ObjectTab);
 if(auto* B=Cast<UButton>(GetWidgetFromName(TEXT("FlipAction"))))B->OnClicked.AddDynamic(this,&ThisClass::FlipClicked);
 if(auto* B=Cast<UButton>(GetWidgetFromName(TEXT("OverlayAction"))))B->OnClicked.AddDynamic(this,&ThisClass::OverlayClicked);
 if(auto* B=Cast<UButton>(GetWidgetFromName(TEXT("CloseAction"))))B->OnClicked.AddDynamic(this,&ThisClass::CloseClicked);
 if(auto* B=Cast<UButton>(GetWidgetFromName(TEXT("CursorAction"))))B->OnClicked.AddDynamic(this,&ThisClass::CursorClicked);
}
void UPenanceInspectionWidget::Connect(UPenanceInspectionComponent* C)
{
 Inspector=C;auto* Strip=Cast<UScrollBox>(GetWidgetFromName(TEXT("ItemStrip")));if(!Strip)return;Strip->ClearChildren();Frames.Reset();Thumbnails.Reset();
 for(int I=0;I<C->Items.Num();++I)
 {
  auto* Box=WidgetTree->ConstructWidget<USizeBox>();Box->SetWidthOverride(136);Box->SetHeightOverride(96);
  auto* Slot=Cast<UScrollBoxSlot>(Strip->AddChild(Box));Slot->SetPadding(FMargin(3,2,3,7));
  auto* Frame=WidgetTree->ConstructWidget<UBorder>();Frame->SetPadding(FMargin(2));Box->AddChild(Frame);Frames.Add(Frame);
  auto* B=WidgetTree->ConstructWidget<UPenanceInspectionThumbnailButton>();B->Inspector=C;B->ItemIndex=I;B->OnClicked.AddDynamic(B,&UPenanceInspectionThumbnailButton::Choose);Frame->AddChild(B);Thumbnails.Add(B);
  FButtonStyle Style;Style.Normal.DrawAs=ESlateBrushDrawType::NoDrawType;Style.Hovered=Style.Normal;Style.Pressed=Style.Normal;Style.Disabled=Style.Normal;B->SetStyle(Style);
  auto* Thumb=WidgetTree->ConstructWidget<UImage>();Thumb->SetBrushFromTexture(C->Items[I]->Thumbnail,true);B->AddChild(Thumb);
 }
 PreviewMaterial=UMaterialInstanceDynamic::Create(LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/UI/Inspection/M_InspectionComposite.M_InspectionComposite")),this);
 if(PreviewMaterial && C->Stage){PreviewMaterial->SetTextureParameterValue(TEXT("Preview"),C->Stage->Target);Cast<UImage>(GetWidgetFromName(TEXT("ObjectPreview")))->SetBrushFromMaterial(PreviewMaterial);}
 Refresh();
}
void UPenanceInspectionWidget::Refresh()
{
 if(!Inspector || !Inspector->Items.IsValidIndex(Inspector->SelectedIndex))return;
 auto* Item=Inspector->Items[Inspector->SelectedIndex].Get();
 auto Set=[&](const TCHAR* N,const FText& V){if(auto* T=Cast<UTextBlock>(GetWidgetFromName(FName(N))))T->SetText(V);};
 Set(TEXT("ObjectTitle"),Item->Title);Set(TEXT("ObjectDescription"),Item->Description);Set(TEXT("ObjectThought"),Item->Thought);Set(TEXT("ObservationSubtitle"),Item->Thought);
 for(int I=0;I<Frames.Num();++I){Frames[I]->SetBrushColor(I==Inspector->SelectedIndex?FLinearColor(.75,.40,.16,.9):FLinearColor(.16,.12,.08,.35));Thumbnails[I]->SetRenderOpacity(I==Inspector->SelectedIndex?1:.43f);}
 for(const TCHAR* Name:{TEXT("ScrollUp"),TEXT("ScrollDown")})if(auto* B=GetWidgetFromName(Name)){B->SetIsEnabled(Thumbnails.Num()>4);B->SetRenderOpacity(Thumbnails.Num()>4?.8f:.2f);}
 if(auto* I=Cast<UImage>(GetWidgetFromName(TEXT("CurrentMemory")))){I->SetBrushFromTexture(Item->Thumbnail);I->SetRenderOpacity(.55);}
 if(auto* I=Cast<UImage>(GetWidgetFromName(TEXT("PreviousMemory")))){if(Item->MemoryThumbnail)I->SetBrushFromTexture(Item->MemoryThumbnail);else I->SetColorAndOpacity(FLinearColor(.06,.055,.045,.35));}
 if(auto* B=GetWidgetFromName(TEXT("OverlayAction")))B->SetIsEnabled(Inspector->HasMemory());
 for(const TCHAR* N:{TEXT("OverlayKeyBorder"),TEXT("OverlayKeyFill"),TEXT("OverlayKey"),TEXT("OverlayAction")})if(auto* W=GetWidgetFromName(N))W->SetRenderOpacity(Inspector->HasMemory()?1:.3f);
 Set(TEXT("PreviousCaption"),FText::FromString(Inspector->HasMemory()?TEXT("Previous?"):TEXT("Unavailable")));
 if(auto* B=Cast<UButton>(GetWidgetFromName(TEXT("CursorAction"))))if(auto* T=Cast<UTextBlock>(B->GetContent()))T->SetText(FText::FromString(Inspector->bCursorMode?TEXT("Tab  ·  Rotate"):TEXT("Tab  ·  Cursor")));
}
void UPenanceInspectionWidget::NativeTick(const FGeometry& G,float D){Super::NativeTick(G,D);Age+=D;SetRenderOpacity(FMath::Clamp(Age/.16f,0.f,1.f));if(auto* S=GetWidgetFromName(TEXT("ObservationSubtitle")))S->SetRenderOpacity(FMath::Clamp((5.f-Age)/.7f,0.f,1.f));}
FReply UPenanceInspectionWidget::NativeOnMouseWheel(const FGeometry& G,const FPointerEvent& E){if(Inspector)Inspector->ZoomByWheel(E.GetWheelDelta());return FReply::Handled();}
void UPenanceInspectionWidget::ScrollUp(){if(auto* S=Cast<UScrollBox>(GetWidgetFromName(TEXT("ItemStrip"))))S->SetScrollOffset(FMath::Max(0.f,S->GetScrollOffset()-100));}
void UPenanceInspectionWidget::ScrollDown(){if(auto* S=Cast<UScrollBox>(GetWidgetFromName(TEXT("ItemStrip"))))S->SetScrollOffset(S->GetScrollOffset()+100);}
void UPenanceInspectionWidget::ObjectTab(){Refresh();}
void UPenanceInspectionWidget::FlipClicked(){if(Inspector)Inspector->Flip();}
void UPenanceInspectionWidget::CursorClicked(){if(Inspector)Inspector->ToggleCursor();}
void UPenanceInspectionWidget::OverlayClicked(){if(Inspector)Inspector->ToggleMemory();}
void UPenanceInspectionWidget::CloseClicked(){if(Inspector)Inspector->CloseInspection();}
