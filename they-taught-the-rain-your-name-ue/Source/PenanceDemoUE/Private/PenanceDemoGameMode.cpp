#include "PenanceDemoGameMode.h"

#include "PenanceHUD.h"
#include "PenancePlayerCharacter.h"

APenanceDemoGameMode::APenanceDemoGameMode()
{
    DefaultPawnClass = APenancePlayerCharacter::StaticClass();
    HUDClass = APenanceHUD::StaticClass();
}
