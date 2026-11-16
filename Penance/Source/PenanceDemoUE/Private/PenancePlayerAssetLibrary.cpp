#include "PenancePlayerAssetLibrary.h"

#if WITH_EDITOR
#include "Animation/BlendSpace.h"
#include "Animation/BlendSpace1D.h"
#include "AnimNodes/AnimNode_BlendSpacePlayer.h"
#include "Animation/AnimSequence.h"
#include "EnhancedActionKeyMapping.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "InputCoreTypes.h"
#include "AnimationGraph.h"
#include "Animation/AnimBlueprint.h"
#include "AnimGraphNode_BlendSpacePlayer.h"
#include "AnimGraphNode_LocalRefPose.h"
#include "AnimGraphNode_Root.h"
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

bool UPenancePlayerAssetLibrary::BuildPlayerAnimationGraph()
{
#if WITH_EDITOR
    UAnimBlueprint* AnimBP = LoadObject<UAnimBlueprint>(nullptr, TEXT("/Game/Player/Animations/ABP_PenancePlayer.ABP_PenancePlayer"));
    UBlendSpace1D* BlendSpace = LoadObject<UBlendSpace1D>(nullptr, TEXT("/Game/Player/Animations/BS_PlayerMovement.BS_PlayerMovement"));
    UAnimSequence* Walk = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/MeshyPlayer/Untitled_Anim_Armature_Walk_Forward.Untitled_Anim_Armature_Walk_Forward"));
    UAnimSequence* Jog = LoadObject<UAnimSequence>(nullptr, TEXT("/Game/Player/MeshyPlayer/Untitled_Anim_Armature_Jogging_Forward.Untitled_Anim_Armature_Jogging_Forward"));
    if (!AnimBP || !BlendSpace || !Walk || !Jog)
    {
        UE_LOG(LogTemp, Error, TEXT("Penance player animation setup is missing a required asset."));
        return false;
    }

    BlendSpace->Modify();
    while (BlendSpace->GetNumberOfBlendSamples() > 0)
    {
        BlendSpace->DeleteSample(BlendSpace->GetNumberOfBlendSamples() - 1);
    }
    FStructProperty* BlendParametersProperty = FindFProperty<FStructProperty>(UBlendSpace::StaticClass(), TEXT("BlendParameters"));
    if (!BlendParametersProperty) return false;
    FBlendParameter* SpeedAxis = reinterpret_cast<FBlendParameter*>(BlendParametersProperty->ContainerPtrToValuePtr<uint8>(BlendSpace));
    SpeedAxis->DisplayName = TEXT("Speed");
    SpeedAxis->Min = 0.0f;
    SpeedAxis->Max = 420.0f;
    SpeedAxis->GridNum = 4;
    SpeedAxis->bSnapToGrid = false;
    SpeedAxis->bWrapInput = false;
    BlendSpace->AddSample(Walk, FVector(200.0f, 0.0f, 0.0f));
    BlendSpace->AddSample(Jog, FVector(420.0f, 0.0f, 0.0f));
    BlendSpace->ValidateSampleData();
    BlendSpace->MarkPackageDirty();

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

    FGraphNodeCreator<UAnimGraphNode_LocalRefPose> RefCreator(*Graph);
    UAnimGraphNode_LocalRefPose* RefPose = RefCreator.CreateNode(false);
    RefPose->Node.SetRefPoseType(EIT_LocalSpace);
    RefCreator.Finalize();

    FGraphNodeCreator<UAnimGraphNode_BlendSpacePlayer> BlendCreator(*Graph);
    UAnimGraphNode_BlendSpacePlayer* BlendPlayer = BlendCreator.CreateNode(false);
    FObjectProperty* BlendAssetProperty = FindFProperty<FObjectProperty>(FAnimNode_BlendSpacePlayer::StaticStruct(), TEXT("BlendSpace"));
    if (!BlendAssetProperty) return false;
    BlendAssetProperty->SetObjectPropertyValue_InContainer(&BlendPlayer->Node, BlendSpace);
    BlendCreator.Finalize();

    FGraphNodeCreator<UAnimGraphNode_TwoWayBlend> BlendMotionCreator(*Graph);
    UAnimGraphNode_TwoWayBlend* BlendMotion = BlendMotionCreator.CreateNode(false);
    BlendMotion->BlendNode.AlphaInputType = EAnimAlphaInputType::Bool;
    BlendMotion->BlendNode.AlphaBoolBlend.BlendInTime = 0.2f;
    BlendMotion->BlendNode.AlphaBoolBlend.BlendOutTime = 0.2f;
    BlendMotionCreator.Finalize();

    FGraphNodeCreator<UAnimGraphNode_Slot> SlotCreator(*Graph);
    UAnimGraphNode_Slot* Slot = SlotCreator.CreateNode(false);
    Slot->Node.SlotName = TEXT("DefaultSlot");
    SlotCreator.Finalize();

    FGraphNodeCreator<UK2Node_VariableGet> SpeedGetterCreator(*Graph);
    UK2Node_VariableGet* SpeedGetter = SpeedGetterCreator.CreateNode(false);
    SpeedGetter->VariableReference.SetSelfMember(GET_MEMBER_NAME_CHECKED(UPenancePlayerAnimInstance, Speed));
    SpeedGetterCreator.Finalize();

    FGraphNodeCreator<UK2Node_VariableGet> MovingGetterCreator(*Graph);
    UK2Node_VariableGet* MovingGetter = MovingGetterCreator.CreateNode(false);
    MovingGetter->VariableReference.SetSelfMember(GET_MEMBER_NAME_CHECKED(UPenancePlayerAnimInstance, bIsMoving));
    MovingGetterCreator.Finalize();

    auto LinkPins = [Graph](UEdGraphNode* SourceNode, const TCHAR* SourceName, UEdGraphNode* TargetNode, const TCHAR* TargetName)
    {
        UEdGraphPin* SourcePin = SourceNode ? SourceNode->FindPin(FName(SourceName)) : nullptr;
        UEdGraphPin* TargetPin = TargetNode ? TargetNode->FindPin(FName(TargetName)) : nullptr;
        return SourcePin && TargetPin && Graph->GetSchema()->TryCreateConnection(SourcePin, TargetPin);
    };

    const bool bLinked =
        LinkPins(RefPose, TEXT("Pose"), BlendMotion, TEXT("A")) &&
        LinkPins(BlendPlayer, TEXT("Pose"), BlendMotion, TEXT("B")) &&
        LinkPins(BlendMotion, TEXT("Pose"), Slot, TEXT("Source")) &&
        LinkPins(Slot, TEXT("Pose"), Root, TEXT("Result")) &&
        LinkPins(SpeedGetter, TEXT("Speed"), BlendPlayer, TEXT("X")) &&
        LinkPins(MovingGetter, TEXT("bIsMoving"), BlendMotion, TEXT("bAlphaBoolEnabled"));

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
