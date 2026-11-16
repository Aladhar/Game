#include "PenancePlayerAnimInstance.h"
#include "GameFramework/Pawn.h"

void UPenancePlayerAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeUpdateAnimation(DeltaSeconds);
    const APawn* OwningPawn = TryGetPawnOwner();
    Speed = OwningPawn ? OwningPawn->GetVelocity().Size2D() : 0.0f;
    bIsMoving = Speed > 5.0f;
}
