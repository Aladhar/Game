#include "PenancePlayerAssetLibrary.h"

#if WITH_EDITOR
#include "Animation/BlendSpace.h"
#include "Animation/BlendSpace1D.h"
#include "AnimNodes/AnimNode_BlendSpacePlayer.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimData/IAnimationDataController.h"
#include "EnhancedActionKeyMapping.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputCoreTypes.h"
#include "Engine/SkeletalMesh.h"
#include "Materials/MaterialInterface.h"
#include "AnimationGraph.h"
#include "Animation/AnimBlueprint.h"
#include "AnimGraphNode_BlendSpacePlayer.h"
#include "AnimGraphNode_Root.h"
#include "AnimGraphNode_SequencePlayer.h"
#include "AnimGraphNode_Slot.h"
#include "AnimGraphNode_TwoWayBlend.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphPin.h"
#include "K2Node_VariableGet.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "PenancePlayerAnimInstance.h"
#include "UObject/UnrealType.h"
#endif

bool UPenancePlayerAssetLibrary::BuildPlayerInputMappings()
{
#if WITH_EDITOR
    UInputMappingContext* Context = LoadObject<UInputMappingContext>(nullptr, TEXT("/Game/Player/Input/IMC_Player.IMC_Player"));
    UInputAction* Move = LoadObject<UInputAction>(nullptr, TEXT("/Game/Player/Input/IA_Move.IA_Move"));
    UInputAction* Look = LoadObject<UInputAction>(nullptr, TEXT("/Game/Player/Input/IA_Look.IA_Look"));
    UInputAction* Sprint = LoadObject<UInputAction>(nullptr, TEXT("/Game/Player/Input/IA_Sprint.IA_Sprint"));
    UInputAction* Crouch = LoadObject<UInputAction>(nullptr, TEXT("/Game/Player/Input/IA_Crouch.IA_Crouch"));
    UInputAction* Interact = LoadObject<UInputAction>(nullptr, TEXT("/Game/Player/Input/IA_Interact.IA_Interact"));
    UInputAction* Jump = LoadObject<UInputAction>(nullptr, TEXT("/Game/Player/Input/IA_Jump.IA_Jump"));
    UInputAction* Inventory = LoadObject<UInputAction>(nullptr, TEXT("/Game/Player/Input/IA_Inventory.IA_Inventory"));
    UInputAction* TestShot = LoadObject<UInputAction>(nullptr, TEXT("/Game/Player/Input/IA_TestShot.IA_TestShot"));
    if (!Context || !Move || !Look || !Sprint || !Crouch || !Interact || !Jump || !Inventory || !TestShot)
    {
        UE_LOG(LogTemp, Error, TEXT("Penance Enhanced Input mapping is missing an action or context."));
        return false;
    }

    Context->Modify();
    Context->UnmapAll();
    auto Map = [Context](const UInputAction* Action, const FKey& Key, bool bSwizzleY = false, bool bNegate = false)
    {
        FEnhancedActionKeyMapping& Mapping = Context->MapKey(Action, Key);
        if (bSwizzleY)
        {
            UInputModifierSwizzleAxis* Swizzle = NewObject<UInputModifierSwizzleAxis>(Context);
            Swizzle->Order = EInputAxisSwizzle::YXZ;
            Mapping.Modifiers.Add(Swizzle);
        }
        if (bNegate)
        {
            UInputModifierNegate* Negate = NewObject<UInputModifierNegate>(Context);
            Mapping.Modifiers.Add(Negate);
        }
    };

    Map(Move, EKeys::W, true);
    Map(Move, EKeys::S, true, true);
    Map(Move, EKeys::A, false, true);
    Map(Move, EKeys::D);
    Map(Look, EKeys::MouseX);
    Map(Look, EKeys::MouseY, true);
    Map(Sprint, EKeys::LeftShift);
    Map(Crouch, EKeys::LeftControl);
    Map(Crouch, EKeys::C);
    Map(Interact, EKeys::E);
    Map(Jump, EKeys::SpaceBar);
    Map(Inventory, EKeys::J);
    Map(TestShot, EKeys::T);
    Context->MarkPackageDirty();
    return true;
#else
    return false;
#endif
}

bool UPenancePlayerAssetLibrary::AssignSkeletalMeshMaterial(USkeletalMesh* Mesh, int32 Slot, UMaterialInterface* Material)
{
#if WITH_EDITOR
    if (!Mesh || !Mesh->GetMaterials().IsValidIndex(Slot) || !Material)
    {
        return false;
    }
    Mesh->Modify();
    Mesh->GetMaterials()[Slot].MaterialInterface = Material;
    Mesh->MarkPackageDirty();
    return true;
#else
    return false;
#endif
}

bool UPenancePlayerAssetLibrary::UseRecoveredReaction(UAnimMontage* Montage, UAnimSequence* Clip)
{
#if WITH_EDITOR
    if (!Montage || !Clip || Montage->GetSkeleton() != Clip->GetSkeleton() ||
        Montage->SlotAnimTracks.Num() != 1 || Montage->SlotAnimTracks[0].AnimTrack.AnimSegments.Num() != 1)
    {
        return false;
    }

    FAnimSegment& Segment = Montage->SlotAnimTracks[0].AnimTrack.AnimSegments[0];
    UAnimSequenceBase* Previous = Segment.GetAnimReference();
    if (!Previous || !FMath::IsNearlyEqual(Previous->GetPlayLength(), Clip->GetPlayLength(), 0.01f))
    {
        return false;
    }

    Montage->Modify();
    Segment.SetAnimReference(Clip);
    Montage->RefreshCacheData();
    Montage->MarkPackageDirty();
    return true;
#else
    return false;
#endif
}

bool UPenancePlayerAssetLibrary::WritePlayerPoseClip(UAnimSequence* Clip, int32 FrameRate,
    const TArray<FName>& Bones, const TArray<FTransform>& LocalPoses)
{
#if WITH_EDITOR
    const int32 BoneCount = Bones.Num();
    if (!Clip || FrameRate <= 0 || BoneCount == 0 || LocalPoses.Num() % BoneCount != 0 ||
        LocalPoses.Num() / BoneCount < 2)
    {
        return false;
    }

    const int32 KeyCount = LocalPoses.Num() / BoneCount;
    IAnimationDataController& Controller = Clip->GetController();
    Controller.OpenBracket(FText::FromString(TEXT("Author Penance pose keys")), false);
    Controller.SetFrameRate(FFrameRate(FrameRate, 1), false);
    Controller.SetNumberOfFrames(FFrameNumber(KeyCount - 1), false);

    bool bSuccess = true;
    for (int32 BoneIndex = 0; BoneIndex < BoneCount; ++BoneIndex)
    {
        TArray<FVector> Positions, Scales;
        TArray<FQuat> Rotations;
        for (int32 Frame = 0; Frame < KeyCount; ++Frame)
        {
            const FTransform& Transform = LocalPoses[Frame * BoneCount + BoneIndex];
            Positions.Add(Transform.GetTranslation());
            Rotations.Add(Transform.GetRotation().GetNormalized());
            Scales.Add(Transform.GetScale3D());
        }
        if (!Controller.AddBoneCurve(Bones[BoneIndex], false) ||
            !Controller.SetBoneTrackKeys(Bones[BoneIndex], Positions, Rotations, Scales, false))
        {
            bSuccess = false;
            break;
        }
    }
    Controller.CloseBracket(false);
    return bSuccess;
#else
    return false;
#endif
}

bool UPenancePlayerAssetLibrary::BuildPlayerAnimationGraph()
{
#if WITH_EDITOR
    UAnimBlueprint* AnimBP = LoadObject<UAnimBlueprint>(nullptr, TEXT("/Game/Player/Animations/ABP_PenancePlayer.ABP_PenancePlayer"));
    UBlendSpace1D* BlendSpace = LoadObject<UBlendSpace1D>(nullptr, TEXT("/Game/Player/Animations/BS_PlayerMovement.BS_PlayerMovement"));
    UBlendSpace1D* CrouchSpace = LoadObject<UBlendSpace1D>(nullptr, TEXT("/Game/Player/Animations/BS_PlayerCrouch.BS_PlayerCrouch"));
    UAnimSequence* Idle = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/Animations/AN_PlayerIdle.AN_PlayerIdle"));
    UAnimSequence* CrouchIdle = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/Animations/AN_PlayerCrouchIdle.AN_PlayerCrouchIdle"));
    UAnimSequence* CrouchWalk = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/Animations/AN_PlayerCrouchWalk.AN_PlayerCrouchWalk"));
    UAnimSequence* Walk = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/MeshyPlayer/Untitled_Anim_Armature_Walk_Forward.Untitled_Anim_Armature_Walk_Forward"));
    UAnimSequence* Jog = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/Animations/AN_PlayerJog.AN_PlayerJog"));
    UAnimSequence* Strafe = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/Animations/AN_PlayerStrafe.AN_PlayerStrafe"));
    UAnimSequence* Airborne = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/Animations/AN_PlayerAirborne.AN_PlayerAirborne"));
    if (!AnimBP || !BlendSpace || !CrouchSpace || !Idle || !CrouchIdle || !CrouchWalk || !Walk || !Jog || !Strafe || !Airborne)
    {
        UE_LOG(LogTemp, Error, TEXT("Penance player animation setup is missing a required asset."));
        return false;
    }

    auto CheckBlend = [](UBlendSpace1D* Space, float Speed, UAnimSequence* Expected)
    {
        int32 Segment = INDEX_NONE;
        TArray<FBlendSampleData> Samples;
        return Space->GetSamplesFromBlendInput(FVector(Speed, 0.0, 0.0), Samples, Segment, true) &&
            Samples.ContainsByPredicate([Expected](const FBlendSampleData& Sample)
            {
                return Sample.Animation == Expected && Sample.GetClampedWeight() > 0.99f;
            });
    };
    UE_LOG(LogTemp, Display, TEXT("Penance stored walk sample evaluable before rebuild: %s"),
        CheckBlend(BlendSpace, 200.0f, Walk) ? TEXT("yes") : TEXT("no"));

    auto ConfigureBlend = [](UBlendSpace1D* Space, float MaxSpeed, const TArray<TPair<float, UAnimSequence*>>& Samples)
    {
        Space->Modify();
        while (Space->GetNumberOfBlendSamples() > 0)
        {
            Space->DeleteSample(Space->GetNumberOfBlendSamples() - 1);
        }

        FStructProperty* Property = FindFProperty<FStructProperty>(UBlendSpace::StaticClass(), TEXT("BlendParameters"));
        if (!Property)
        {
            return false;
        }
        FBlendParameter* Axis = Property->ContainerPtrToValuePtr<FBlendParameter>(Space);
        Axis->DisplayName = TEXT("Speed");
        Axis->Min = 0.0f;
        Axis->Max = MaxSpeed;
        Axis->GridNum = 4;
        Axis->bSnapToGrid = false;
        Axis->bWrapInput = false;
        for (const TPair<float, UAnimSequence*>& Sample : Samples)
        {
            if (Space->AddSample(Sample.Value, FVector(Sample.Key, 0.0, 0.0)) == INDEX_NONE)
            {
                return false;
            }
        }

        // Adding samples does not regenerate the segments used for runtime evaluation.
        Space->ResampleData();
        Space->MarkPackageDirty();
        return true;
    };
    if (!ConfigureBlend(BlendSpace, 420.0f, {{0.0f, Idle}, {200.0f, Walk}, {420.0f, Jog}})
        || !ConfigureBlend(CrouchSpace, 140.0f, {{0.0f, CrouchIdle}, {140.0f, CrouchWalk}})
        || !CheckBlend(BlendSpace, 0.0f, Idle) || !CheckBlend(BlendSpace, 200.0f, Walk)
        || !CheckBlend(BlendSpace, 420.0f, Jog) || !CheckBlend(CrouchSpace, 0.0f, CrouchIdle)
        || !CheckBlend(CrouchSpace, 140.0f, CrouchWalk))
    {
        UE_LOG(LogTemp, Error, TEXT("Penance runtime blend samples failed verification."));
        return false;
    }

    TArray<UEdGraph*> BlueprintGraphs;
    AnimBP->GetAllGraphs(BlueprintGraphs);
    UEdGraph* Graph = nullptr;
    for (UEdGraph* Candidate : BlueprintGraphs)
    {
        if (Candidate && Candidate->GetClass()->GetName() == TEXT("AnimationGraph"))
        {
            Graph = Candidate;
            break;
        }
    }
    if (!Graph)
    {
        UE_LOG(LogTemp, Error, TEXT("Penance player Anim Blueprint has no AnimGraph."));
        return false;
    }

    UAnimGraphNode_Root* Root = nullptr;
    // Remove from a snapshot because Graph->RemoveNode mutates Graph->Nodes.
    const TArray<UEdGraphNode*> ExistingNodes = Graph->Nodes;
    for (UEdGraphNode* ExistingNode : ExistingNodes)
    {
        if (UAnimGraphNode_Root* ExistingRoot = Cast<UAnimGraphNode_Root>(ExistingNode))
        {
            Root = ExistingRoot;
        }
        else
        {
            Graph->RemoveNode(ExistingNode);
        }
    }
    if (!Root)
    {
        UE_LOG(LogTemp, Error, TEXT("Penance player AnimGraph has no Output Pose node."));
        return false;
    }

    auto ExposePlayRate = [](UAnimGraphNode_Base* Node)
    {
        for (FOptionalPinFromProperty& Pin : Node->ShowPinForProperties)
        {
            if (Pin.PropertyName == TEXT("PlayRate"))
            {
                Pin.bShowPin = true;
            }
        }
        Node->ReconstructNode();
    };

    auto AddBlendPlayer = [Graph, &ExposePlayRate](UBlendSpace1D* Space, int32 Y)
    {
        FGraphNodeCreator<UAnimGraphNode_BlendSpacePlayer> Creator(*Graph);
        UAnimGraphNode_BlendSpacePlayer* Node = Creator.CreateNode(false);
        Node->Node.SetBlendSpace(Space);
        Node->NodePosX = -850;
        Node->NodePosY = Y;
        Creator.Finalize();
        ExposePlayRate(Node);
        return Node;
    };
    UAnimGraphNode_BlendSpacePlayer* BlendPlayer = AddBlendPlayer(BlendSpace, -320);
    UAnimGraphNode_BlendSpacePlayer* CrouchPlayer = AddBlendPlayer(CrouchSpace, 190);

    auto AddSequence = [Graph](UAnimSequence* Clip, int32 X, int32 Y)
    {
        FGraphNodeCreator<UAnimGraphNode_SequencePlayer> Creator(*Graph);
        UAnimGraphNode_SequencePlayer* Node = Creator.CreateNode(false);
        Node->Node.SetSequence(Clip);
        Node->NodePosX = X;
        Node->NodePosY = Y;
        Creator.Finalize();
        return Node;
    };
    UAnimGraphNode_SequencePlayer* StrafePlayer = AddSequence(Strafe, -850, -70);
    ExposePlayRate(StrafePlayer);
    UAnimGraphNode_SequencePlayer* AirbornePlayer = AddSequence(Airborne, -245, 290);

    auto AddTransition = [Graph](int32 X, int32 Y, float Seconds)
    {
        FGraphNodeCreator<UAnimGraphNode_TwoWayBlend> Creator(*Graph);
        UAnimGraphNode_TwoWayBlend* Node = Creator.CreateNode(false);
        Node->BlendNode.AlphaInputType = EAnimAlphaInputType::Bool;
        Node->BlendNode.AlphaBoolBlend.BlendInTime = Seconds;
        Node->BlendNode.AlphaBoolBlend.BlendOutTime = Seconds;
        Node->NodePosX = X;
        Node->NodePosY = Y;
        Creator.Finalize();
        return Node;
    };
    UAnimGraphNode_TwoWayBlend* GroundStrafe = AddTransition(-540, -250, 0.15f);
    UAnimGraphNode_TwoWayBlend* GroundCrouch = AddTransition(-245, -110, 0.2f);
    UAnimGraphNode_TwoWayBlend* InAir = AddTransition(55, 0, 0.12f);

    Root->NodePosX = 620;
    Root->NodePosY = 0;
    FGraphNodeCreator<UAnimGraphNode_Slot> SlotCreator(*Graph);
    UAnimGraphNode_Slot* Slot = SlotCreator.CreateNode(false);
    Slot->Node.SlotName = TEXT("DefaultSlot");
    Slot->NodePosX = 350;
    SlotCreator.Finalize();

    auto AddGetter = [Graph](FName Name, int32 X, int32 Y)
    {
        FGraphNodeCreator<UK2Node_VariableGet> Creator(*Graph);
        UK2Node_VariableGet* Node = Creator.CreateNode(false);
        Node->VariableReference.SetSelfMember(Name);
        Node->NodePosX = X;
        Node->NodePosY = Y;
        Creator.Finalize();
        return Node;
    };
    UK2Node_VariableGet* SpeedGetter = AddGetter(GET_MEMBER_NAME_CHECKED(UPenancePlayerAnimInstance, Speed), -1110, -260);
    UK2Node_VariableGet* GaitRateGetter = AddGetter(GET_MEMBER_NAME_CHECKED(UPenancePlayerAnimInstance, GaitPlayRate), -1110, -200);
    UK2Node_VariableGet* StrafeRateGetter = AddGetter(GET_MEMBER_NAME_CHECKED(UPenancePlayerAnimInstance, StrafePlayRate), -1110, 0);
    UK2Node_VariableGet* StrafingGetter = AddGetter(GET_MEMBER_NAME_CHECKED(UPenancePlayerAnimInstance, bIsStrafing), -850, -410);
    UK2Node_VariableGet* CrouchGetter = AddGetter(GET_MEMBER_NAME_CHECKED(UPenancePlayerAnimInstance, bIsCrouched), -540, 145);
    UK2Node_VariableGet* AirborneGetter = AddGetter(GET_MEMBER_NAME_CHECKED(UPenancePlayerAnimInstance, bIsAirborne), -245, 215);

    auto LinkPins = [Graph](UEdGraphNode* SourceNode, const TCHAR* SourceName, UEdGraphNode* TargetNode, const TCHAR* TargetName)
    {
        UEdGraphPin* SourcePin = SourceNode ? SourceNode->FindPin(FName(SourceName)) : nullptr;
        UEdGraphPin* TargetPin = TargetNode ? TargetNode->FindPin(FName(TargetName)) : nullptr;
        return SourcePin && TargetPin && Graph->GetSchema()->TryCreateConnection(SourcePin, TargetPin);
    };

    const bool bLinked =
        LinkPins(BlendPlayer, TEXT("Pose"), GroundStrafe, TEXT("A")) &&
        LinkPins(StrafePlayer, TEXT("Pose"), GroundStrafe, TEXT("B")) &&
        LinkPins(GroundStrafe, TEXT("Pose"), GroundCrouch, TEXT("A")) &&
        LinkPins(CrouchPlayer, TEXT("Pose"), GroundCrouch, TEXT("B")) &&
        LinkPins(GroundCrouch, TEXT("Pose"), InAir, TEXT("A")) &&
        LinkPins(AirbornePlayer, TEXT("Pose"), InAir, TEXT("B")) &&
        LinkPins(InAir, TEXT("Pose"), Slot, TEXT("Source")) &&
        LinkPins(Slot, TEXT("Pose"), Root, TEXT("Result")) &&
        LinkPins(SpeedGetter, TEXT("Speed"), BlendPlayer, TEXT("X")) &&
        LinkPins(SpeedGetter, TEXT("Speed"), CrouchPlayer, TEXT("X")) &&
        LinkPins(GaitRateGetter, TEXT("GaitPlayRate"), BlendPlayer, TEXT("PlayRate")) &&
        LinkPins(GaitRateGetter, TEXT("GaitPlayRate"), CrouchPlayer, TEXT("PlayRate")) &&
        LinkPins(StrafeRateGetter, TEXT("StrafePlayRate"), StrafePlayer, TEXT("PlayRate")) &&
        LinkPins(StrafingGetter, TEXT("bIsStrafing"), GroundStrafe, TEXT("bAlphaBoolEnabled")) &&
        LinkPins(CrouchGetter, TEXT("bIsCrouched"), GroundCrouch, TEXT("bAlphaBoolEnabled")) &&
        LinkPins(AirborneGetter, TEXT("bIsAirborne"), InAir, TEXT("bAlphaBoolEnabled"));

    if (!bLinked)
    {
        UE_LOG(LogTemp, Error, TEXT("Penance player AnimGraph node pins did not connect as expected."));
        return false;
    }

    Graph->NotifyGraphChanged();
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(AnimBP);
    FKismetEditorUtilities::CompileBlueprint(AnimBP);
    AnimBP->MarkPackageDirty();
    return AnimBP->Status != BS_Error;
#else
    return false;
#endif
}
