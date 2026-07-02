from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import ErrorType, PassState, ScoreDimension
from app.core.schemas import ScoringRubric


class MicroNodeType(str, Enum):
    CONCEPT = "concept"
    TRIGGER = "trigger"
    METHOD = "method"
    TRANSFORMATION = "transformation"
    CALCULATION = "calculation"
    EXPRESSION = "expression"


class ChallengeTaskType(str, Enum):
    MICRO_NODE = "micro_node"
    MACRO_CHALLENGE = "macro_challenge"


class ChallengeStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    ACTIVE = "active"
    MASTERED = "mastered"
    FAILED = "failed"


class NetworkEdgeType(str, Enum):
    CONTAINS = "contains"
    PREREQUISITE = "prerequisite"
    CONFUSION = "confusion"
    SYNTHESIS = "synthesis"
    UNLOCK = "unlock"
    REPAIR = "repair"
    SUPPORT = "support"
    BRIDGE = "bridge"
    GATEWAY = "gateway"
    ASSESSES = "assesses"
    BOSS_COVERS = "boss_covers"
    BLOCKS = "blocks"
    TRANSFERS_TO = "transfers_to"


class GuideNodeKind(str, Enum):
    FOUNDATION_ANCHOR = "foundation_anchor"
    BRIDGE = "bridge"
    GATEWAY = "gateway"
    WARNING_BEACON = "warning_beacon"
    BOSS_GATE = "boss_gate"


class ChallengeAttemptLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    micro_node: int = Field(default=5, ge=1)
    macro_challenge: int = Field(default=3, ge=1)


class MacroNodeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    knowledge_node_id: str


class MicroNodeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    macro_node_id: str
    type: MicroNodeType
    title: str
    description: str = ""
    default_dimensions: list[ScoreDimension] = Field(default_factory=list)


class MacroChallengeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    macro_node_id: str
    title: str
    covers_micro_nodes: list[str]
    target_dimensions: list[ScoreDimension] = Field(default_factory=list)


class AtomNodeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    micro_node_id: str
    title: str
    description: str = ""
    dimensions: list[ScoreDimension] = Field(default_factory=list)
    repair_cues: list[str] = Field(default_factory=list)


class CompareNodeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    node_ids: list[str]
    description: str = ""
    focus_dimensions: list[ScoreDimension] = Field(default_factory=list)
    confusion_cues: list[str] = Field(default_factory=list)


class GuideNodeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: GuideNodeKind
    title: str
    description: str = ""
    related_node_ids: list[str] = Field(default_factory=list)
    focus_dimensions: list[ScoreDimension] = Field(default_factory=list)
    map_hint: str = ""
    trainable: bool = False


class NetworkEdgeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    edge_type: NetworkEdgeType
    source_id: str
    target_id: str
    label: str = ""
    reason: str = ""
    semantic_weight: float = Field(default=1, ge=0, le=1)
    decision_role: Literal["navigation", "progression", "repair", "diagnostic", "advisory"] = "navigation"
    visible: bool = True


class UnlockEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    from_macro_node_id: str
    to_micro_node_ids: list[str] = Field(default_factory=list)


class ChallengeGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter_id: str
    title: str
    attempt_limits: ChallengeAttemptLimits = Field(default_factory=ChallengeAttemptLimits)
    macro_nodes: list[MacroNodeSpec]
    micro_nodes: list[MicroNodeSpec]
    macro_challenges: list[MacroChallengeSpec]
    atom_nodes: list[AtomNodeSpec] = Field(default_factory=list)
    compare_nodes: list[CompareNodeSpec] = Field(default_factory=list)
    guide_nodes: list[GuideNodeSpec] = Field(default_factory=list)
    typed_edges: list[NetworkEdgeSpec] = Field(default_factory=list)
    contains: dict[str, list[str]]
    unlock_edges: list[UnlockEdge] = Field(default_factory=list)
    error_to_micro_mapping: dict[ErrorType, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_graph_references(self) -> "ChallengeGraph":
        macro_ids = {node.id for node in self.macro_nodes}
        micro_ids = {node.id for node in self.micro_nodes}
        challenge_ids = {challenge.id for challenge in self.macro_challenges}
        atom_ids = {node.id for node in self.atom_nodes}
        compare_ids = {node.id for node in self.compare_nodes}
        guide_ids = {node.id for node in self.guide_nodes}
        known_network_ids = macro_ids | micro_ids | challenge_ids | atom_ids | compare_ids | guide_ids

        for macro_id, contained_micro_ids in self.contains.items():
            if macro_id not in macro_ids:
                raise ValueError(f"contains references unknown macro node: {macro_id}")
            for micro_id in contained_micro_ids:
                if micro_id not in micro_ids:
                    raise ValueError(f"contains references unknown micro node: {micro_id}")

        for micro in self.micro_nodes:
            if micro.macro_node_id not in macro_ids:
                raise ValueError(f"micro node references unknown macro node: {micro.id}")

        for challenge in self.macro_challenges:
            if challenge.macro_node_id not in macro_ids:
                raise ValueError(f"macro challenge references unknown macro node: {challenge.id}")
            for micro_id in challenge.covers_micro_nodes:
                if micro_id not in micro_ids:
                    raise ValueError(f"macro challenge covers unknown micro node: {challenge.id}")

        for atom in self.atom_nodes:
            if atom.micro_node_id not in micro_ids:
                raise ValueError(f"atom node references unknown micro node: {atom.id}")

        for compare in self.compare_nodes:
            if len(compare.node_ids) < 2:
                raise ValueError(f"compare node must compare at least two nodes: {compare.id}")
            for node_id in compare.node_ids:
                if node_id not in known_network_ids:
                    raise ValueError(f"compare node references unknown node: {node_id}")

        for guide in self.guide_nodes:
            if guide.trainable:
                raise ValueError(f"guide node must not be trainable: {guide.id}")
            for node_id in guide.related_node_ids:
                if node_id not in known_network_ids:
                    raise ValueError(f"guide node references unknown node: {node_id}")

        for edge in self.typed_edges:
            if edge.source_id not in known_network_ids:
                raise ValueError(f"typed edge references unknown source node: {edge.source_id}")
            if edge.target_id not in known_network_ids:
                raise ValueError(f"typed edge references unknown target node: {edge.target_id}")

        for edge in self.unlock_edges:
            if edge.from_macro_node_id not in macro_ids:
                raise ValueError(f"unlock edge references unknown source macro node: {edge.from_macro_node_id}")
            for micro_id in edge.to_micro_node_ids:
                if micro_id not in micro_ids:
                    raise ValueError(f"unlock edge references unknown target micro node: {micro_id}")

        if len(atom_ids) != len(self.atom_nodes):
            raise ValueError("atom node ids must be unique")
        if len(compare_ids) != len(self.compare_nodes):
            raise ValueError("compare node ids must be unique")
        if len(guide_ids) != len(self.guide_nodes):
            raise ValueError("guide node ids must be unique")
        if len(challenge_ids) != len(self.macro_challenges):
            raise ValueError("macro challenge ids must be unique")
        return self


class ChallengeQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    owner_id: str
    task_type: ChallengeTaskType
    node_id: str
    title: str
    stem: str
    prompt_markdown: str
    answer_format: str = "expression_with_reasoning"
    response_step_mode: str = "required"
    difficulty: str = "standard"
    hints_public: list[str] = Field(default_factory=list)
    target_dimensions: list[ScoreDimension] = Field(default_factory=list)
    target_dimension_mode: Literal["supplement", "override"] = "supplement"
    expected_answer: str | None = None
    answer_aliases: list[str] = Field(default_factory=list)
    rubric: ScoringRubric | None = None
    solution_outline: str | None = None
    validator_config: dict[str, Any] = Field(default_factory=dict)


class ChallengeQuestionBank(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter_id: str
    questions: list[ChallengeQuestion]


class ChallengeTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_type: ChallengeTaskType
    task_id: str
    macro_node_id: str
    question_id: str | None = None


class ChallengeNodeProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ChallengeStatus = ChallengeStatus.LOCKED
    attempts_used: int = 0
    failed_cycles: int = 0


class ChallengeMasteryState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mastery_score: float = Field(default=0, ge=0, le=100)
    confidence: float = Field(default=0, ge=0, le=1)
    stability: float = Field(default=0, ge=0, le=1)
    evidence_count: int = Field(default=0, ge=0)
    weak_dimensions: list[ScoreDimension] = Field(default_factory=list)
    recent_root_causes: list[ErrorType] = Field(default_factory=list)
    last_pass_state: PassState | None = None
    visual_state: str = "locked"


class ChallengeProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter_id: str
    session_id: str
    macro_nodes: dict[str, ChallengeNodeProgress]
    micro_nodes: dict[str, ChallengeNodeProgress]
    macro_challenges: dict[str, ChallengeNodeProgress]
    mastery: dict[str, ChallengeMasteryState] = Field(default_factory=dict)
    current_task: ChallengeTask | None = None
    completed: bool = False


class ChallengeEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pass_state: PassState
    root_cause: ErrorType | None = None
    repair_target_node_id: str | None = None
    coach_payload: dict[str, Any]
