#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "PenanceHUD.generated.h"

UCLASS()
class PENANCEDEMOUE_API APenanceHUD : public AHUD
{
    GENERATED_BODY()

public:
    virtual void DrawHUD() override;

private:
    void DrawStaminaBar(class APenancePlayerCharacter* Player);
    void DrawInventory(class APenancePlayerCharacter* Player);
    void DrawInteractionHint(class APenancePlayerCharacter* Player);
};
