#include "PenanceDemoGameMode.h"

#include "PenancePlayerCharacter.h"

APenanceDemoGameMode::APenanceDemoGameMode()
{
    DefaultPawnClass = APenancePlayerCharacter::StaticClass();
}
