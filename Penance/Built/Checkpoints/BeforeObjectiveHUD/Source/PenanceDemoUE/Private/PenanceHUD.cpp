#include "PenanceHUD.h"

#include "CanvasItem.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "PenancePlayerCharacter.h"
#include "PenanceProgressionManager.h"

void APenanceHUD::DrawHUD()
{
    Super::DrawHUD();

    APenancePlayerCharacter* Player = Cast<APenancePlayerCharacter>(GetOwningPawn());
    if (!Player || !Canvas)
    {
        return;
    }

    DrawStaminaBar(Player);
    if (APenanceProgressionManager* Manager = APenanceProgressionManager::Find(GetWorld()))
    {
        FCanvasTextItem Objective(
            FVector2D(32.0f, 28.0f),
            Manager->GetCurrentObjectiveText(),
            GEngine->GetSmallFont(),
            FLinearColor(0.82f, 0.82f, 0.76f, 0.95f)
        );
        Canvas->DrawItem(Objective);
    }
    DrawInteractionHint(Player);
    if (Player->IsInventoryOpen())
    {
        DrawInventory(Player);
    }
}

void APenanceHUD::DrawStaminaBar(APenancePlayerCharacter* Player)
{
    const float Ratio = Player->GetStaminaRatio();
    const FVector2D Size(260.0f, 18.0f);
    const FVector2D Pos(32.0f, Canvas->ClipY - 54.0f);

    FCanvasTileItem Back(Pos, Size, FLinearColor(0.025f, 0.025f, 0.028f, 0.9f));
    Back.BlendMode = SE_BLEND_Translucent;
    Canvas->DrawItem(Back);

    FCanvasTileItem Fill(Pos + FVector2D(2.0f, 2.0f), FVector2D((Size.X - 4.0f) * Ratio, Size.Y - 4.0f), FLinearColor(0.72f, 0.62f, 0.38f, 0.95f));
    Fill.BlendMode = SE_BLEND_Translucent;
    Canvas->DrawItem(Fill);

    FCanvasTextItem Label(Pos + FVector2D(0.0f, -24.0f), FText::FromString(TEXT("STAMINA")), GEngine->GetSmallFont(), FLinearColor(0.78f, 0.78f, 0.72f, 0.92f));
    Canvas->DrawItem(Label);
}

void APenanceHUD::DrawInteractionHint(APenancePlayerCharacter* Player)
{
    const FText Hint = Player->GetCurrentInteractionHint();
    if (Hint.IsEmpty())
    {
        return;
    }

    FCanvasTextItem Text(FVector2D(Canvas->ClipX * 0.5f - 72.0f, Canvas->ClipY * 0.62f), Hint, GEngine->GetMediumFont(), FLinearColor(0.88f, 0.82f, 0.68f, 0.95f));
    Canvas->DrawItem(Text);
}

void APenanceHUD::DrawInventory(APenancePlayerCharacter* Player)
{
    const FVector2D Pos(Canvas->ClipX * 0.5f - 310.0f, Canvas->ClipY * 0.5f - 220.0f);
    const FVector2D Size(620.0f, 440.0f);

    FCanvasTileItem Panel(Pos, Size, FLinearColor(0.012f, 0.012f, 0.014f, 0.92f));
    Panel.BlendMode = SE_BLEND_Translucent;
    Canvas->DrawItem(Panel);

    FCanvasTextItem Title(Pos + FVector2D(28.0f, 24.0f), FText::FromString(TEXT("NOTES / INVENTORY")), GEngine->GetMediumFont(), FLinearColor(0.88f, 0.82f, 0.68f, 1.0f));
    Canvas->DrawItem(Title);

    const TArray<FString>& Notes = Player->GetCollectedNotes();
    const TArray<FString>& Items = Player->GetInventoryItems();
    float Y = Pos.Y + 74.0f;

    FCanvasTextItem NotesHeader(FVector2D(Pos.X + 28.0f, Y), FText::FromString(TEXT("Notes")), GEngine->GetSmallFont(), FLinearColor(0.75f, 0.75f, 0.72f, 1.0f));
    Canvas->DrawItem(NotesHeader);
    Y += 26.0f;

    if (Notes.IsEmpty())
    {
        FCanvasTextItem Empty(FVector2D(Pos.X + 42.0f, Y), FText::FromString(TEXT("- No notes collected")), GEngine->GetSmallFont(), FLinearColor(0.5f, 0.5f, 0.5f, 1.0f));
        Canvas->DrawItem(Empty);
        Y += 24.0f;
    }
    for (const FString& Note : Notes)
    {
        FCanvasTextItem Line(FVector2D(Pos.X + 42.0f, Y), FText::FromString(FString(TEXT("- ")) + Note), GEngine->GetSmallFont(), FLinearColor(0.82f, 0.8f, 0.74f, 1.0f));
        Canvas->DrawItem(Line);
        Y += 24.0f;
    }

    Y += 22.0f;
    FCanvasTextItem ItemsHeader(FVector2D(Pos.X + 28.0f, Y), FText::FromString(TEXT("Inventory")), GEngine->GetSmallFont(), FLinearColor(0.75f, 0.75f, 0.72f, 1.0f));
    Canvas->DrawItem(ItemsHeader);
    Y += 26.0f;

    if (Items.IsEmpty())
    {
        FCanvasTextItem Empty(FVector2D(Pos.X + 42.0f, Y), FText::FromString(TEXT("- No items collected")), GEngine->GetSmallFont(), FLinearColor(0.5f, 0.5f, 0.5f, 1.0f));
        Canvas->DrawItem(Empty);
    }
    for (const FString& Item : Items)
    {
        FCanvasTextItem Line(FVector2D(Pos.X + 42.0f, Y), FText::FromString(FString(TEXT("- ")) + Item), GEngine->GetSmallFont(), FLinearColor(0.82f, 0.8f, 0.74f, 1.0f));
        Canvas->DrawItem(Line);
        Y += 24.0f;
    }
}
