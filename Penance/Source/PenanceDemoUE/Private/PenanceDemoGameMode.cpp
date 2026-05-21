#include "PenanceDemoGameMode.h"

#include "Components/LightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/PointLight.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "PenanceHUD.h"
#include "PenancePlayerCharacter.h"
#include "PenancePlayerWalkPreviewActor.h"

APenanceDemoGameMode::APenanceDemoGameMode()
{
    DefaultPawnClass = APenancePlayerCharacter::StaticClass();
    HUDClass = APenanceHUD::StaticClass();
}

void APenanceDemoGameMode::BeginPlay()
{
    Super::BeginPlay();

    UWorld* World = GetWorld();
    if (!World || !World->GetMapName().Contains(TEXT("Player_WalkAnimation_Verify")))
    {
        return;
    }

    FActorSpawnParameters SpawnParameters;
    SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

    World->SpawnActor<APenancePlayerWalkPreviewActor>(
        APenancePlayerWalkPreviewActor::StaticClass(),
        FVector(260.0f, 0.0f, 0.0f),
        FRotator(0.0f, 180.0f, 0.0f),
        SpawnParameters);

    UStaticMesh* FloorMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Plane.Plane"));
    if (FloorMesh)
    {
        AStaticMeshActor* Floor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(),
            FVector(0.0f, 0.0f, -2.0f),
            FRotator::ZeroRotator,
            SpawnParameters);
        if (Floor && Floor->GetStaticMeshComponent())
        {
#if WITH_EDITOR
            Floor->SetActorLabel(TEXT("Runtime_Floor_PlayerWalkPreview"));
#endif
            Floor->GetStaticMeshComponent()->SetStaticMesh(FloorMesh);
            Floor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
            Floor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
            Floor->SetActorScale3D(FVector(10.0f, 10.0f, 1.0f));
        }
    }

    if (ADirectionalLight* KeyLight = World->SpawnActor<ADirectionalLight>(
        ADirectionalLight::StaticClass(),
        FVector(-120.0f, -220.0f, 520.0f),
        FRotator(-48.0f, 34.0f, 0.0f),
        SpawnParameters))
    {
#if WITH_EDITOR
        KeyLight->SetActorLabel(TEXT("Runtime_KeyLight_PlayerWalkPreview"));
#endif
        KeyLight->GetLightComponent()->SetIntensity(4.5f);
    }

    if (APointLight* FillLight = World->SpawnActor<APointLight>(
        APointLight::StaticClass(),
        FVector(-160.0f, 160.0f, 240.0f),
        FRotator::ZeroRotator,
        SpawnParameters))
    {
#if WITH_EDITOR
        FillLight->SetActorLabel(TEXT("Runtime_FillLight_PlayerWalkPreview"));
#endif
        if (UPointLightComponent* PointLightComponent = Cast<UPointLightComponent>(FillLight->GetLightComponent()))
        {
            PointLightComponent->SetIntensity(1800.0f);
            PointLightComponent->SetAttenuationRadius(800.0f);
        }
    }

    if (APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(World, 0))
    {
        PlayerPawn->SetActorLocation(FVector(-420.0f, 0.0f, 92.0f), false, nullptr, ETeleportType::TeleportPhysics);
        PlayerPawn->SetActorRotation(FRotator(0.0f, 0.0f, 0.0f));
    }

    if (APlayerController* PlayerController = UGameplayStatics::GetPlayerController(World, 0))
    {
        PlayerController->SetControlRotation(FRotator(0.0f, 0.0f, 0.0f));
    }
}
