#include "PenancePlayerAnimInstance.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"

void UPenancePlayerAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeUpdateAnimation(DeltaSeconds);
    const ACharacter* Character = Cast<ACharacter>(TryGetPawnOwner());
    const FVector Velocity = Character ? Character->GetVelocity() : FVector::ZeroVector;
    Speed = Velocity.Size2D();
    bIsCrouched = Character && Character->bIsCrouched;
    bIsAirborne = Character && Character->GetCharacterMovement()->IsFalling();

    const FVector LocalVelocity = Character
        ? Character->GetActorQuat().UnrotateVector(Velocity)
        : FVector::ZeroVector;
    bIsStrafing = Speed > 10.0f && FMath::Abs(LocalVelocity.Y) > FMath::Abs(LocalVelocity.X);
    GaitPlayRate = LocalVelocity.X < -10.0f ? -1.0f : 1.0f;
    // The loop covers 60 cm of stance travel per 0.8-second cycle.
    StrafePlayRate = FMath::Clamp(LocalVelocity.Y / 75.0f, -3.0f, 3.0f);
}
