#include "PenanceV6InstancedSet.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
APenanceV6InstancedSet::APenanceV6InstancedSet()
{
 PrimaryActorTick.bCanEverTick=false;
 Instances=CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("Instances"));RootComponent=Instances;
 Instances->SetMobility(EComponentMobility::Static);Instances->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 Instances->SetCullDistances(18000,32000);Instances->SetCanEverAffectNavigation(false);
}
