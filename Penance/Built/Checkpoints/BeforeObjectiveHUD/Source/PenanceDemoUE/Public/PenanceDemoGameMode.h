#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "PenanceDemoGameMode.generated.h"

UCLASS()
class PENANCEDEMOUE_API APenanceDemoGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    APenanceDemoGameMode();

    virtual void BeginPlay() override;
};
