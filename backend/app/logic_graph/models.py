from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.enums import ErrorType, ScoreDimension


class LogicAbilityKind(str, Enum):
    CONCEPT_CRITERION = "concept_criterion"
    TRIGGER_PATTERN = "trigger_pattern"
    METHOD_STEP = "method_step"
    TRANSFORMATION_RULE = "transformation_rule"
    CALCULATION_SKILL = "calculation_skill"
    EXPRESSION_RULE = "expression_rule"
    CONDITION_RULE = "condition_rule"
    MISCONCEPTION_GUARD = "misconception_guard"
    SYNTHESIS_PATH = "synthesis_path"


class LogicAbilityRole(str, Enum):
    ATOMIC = "atomic"
    PREREQUISITE = "prerequisite"
    CONFUSION_GUARD = "confusion_guard"
    TRANSFER = "transfer"
    TRANSFER_NODE = "transfer_node"
    SYNTHESIS = "synthesis"
    SYNTHESIS_NODE = "synthesis_node"
    EXPRESSION = "expression"
    CONDITION = "condition"
    BOSS_CRITERION = "boss_criterion"


class LogicEdgeType(str, Enum):
    REQUIRES = "requires"
    SUPPORTS = "supports"
    CHECKS = "checks"
    CONTRASTS_WITH = "contrasts_with"
    DERIVES_TO = "derives_to"
    TRANSFORMS_TO = "transforms_to"
    COMMONLY_CONFUSED_WITH = "commonly_confused_with"
    ERROR_EVIDENCE_FOR = "error_evidence_for"
    REPAIRS = "repairs"
    BOSS_CHECKS = "boss_checks"
    BLOCKS = "blocks"
    TRANSFERS_TO = "transfers_to"


class LogicAbilityVisibilityPolicy(str, Enum):
    HIDDEN = "hidden"
    DIAGNOSIS_ONLY = "diagnosis_only"
    MAP_VISIBLE = "map_visible"


class AbilityEvidenceStatus(str, Enum):
    DEMONSTRATED = "demonstrated"
    WEAK = "weak"
    MISSING = "missing"
    CONTRADICTED = "contradicted"
    UNKNOWN = "unknown"


class LogicQualitySeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class LogicAbilitySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    kind: LogicAbilityKind
    role: LogicAbilityRole = LogicAbilityRole.ATOMIC
    owner_node_id: str
    why_exists: str = ""
    dimensions: list[ScoreDimension] = Field(default_factory=list)
    evidence_sources: list[str] = Field(default_factory=list)
    evidence_requirements: list[str] = Field(default_factory=list)
    positive_cues: list[str] = Field(default_factory=list)
    weak_cues: list[str] = Field(default_factory=list)
    contradiction_cues: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    minimum_positive_cues: int = Field(default=1, ge=0)
    diagnostic_weight: float = Field(default=1, ge=0, le=1)
    strong_evidence_required: bool = False
    confusion_peer_ids: list[str] = Field(default_factory=list)
    downstream_ability_ids: list[str] = Field(default_factory=list)
    repair_cues: list[str] = Field(default_factory=list)
    repair_target_node_id: str
    visibility_policy: LogicAbilityVisibilityPolicy = LogicAbilityVisibilityPolicy.DIAGNOSIS_ONLY
    visible: bool = False


class LogicEdgeSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    edge_type: LogicEdgeType
    source_id: str
    target_id: str
    label: str = ""
    reason: str = ""
    weight: float = Field(default=1, ge=0, le=1)
    visible: bool = False

    @field_validator("edge_type", mode="before")
    @classmethod
    def normalize_legacy_edge_type(cls, value: LogicEdgeType | str) -> LogicEdgeType | str:
        if isinstance(value, str) and value == "remediates":
            return LogicEdgeType.REPAIRS
        return value


class LogicGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = 1
    chapter_id: str
    title: str
    abilities: list[LogicAbilitySpec]
    edges: list[LogicEdgeSpec] = Field(default_factory=list)
    node_ability_map: dict[str, list[str]] = Field(default_factory=dict)
    error_ability_map: dict[ErrorType, list[str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_references(self) -> "LogicGraph":
        ability_ids = {ability.id for ability in self.abilities}
        if len(ability_ids) != len(self.abilities):
            raise ValueError("logic ability ids must be unique")

        for node_id, ids in self.node_ability_map.items():
            del node_id
            for ability_id in ids:
                if ability_id not in ability_ids:
                    raise ValueError(f"node_ability_map references unknown ability: {ability_id}")

        for error_type, ids in self.error_ability_map.items():
            del error_type
            for ability_id in ids:
                if ability_id not in ability_ids:
                    raise ValueError(f"error_ability_map references unknown ability: {ability_id}")

        for edge in self.edges:
            if edge.source_id not in ability_ids:
                raise ValueError(f"logic edge references unknown source ability: {edge.source_id}")
            if edge.target_id not in ability_ids:
                raise ValueError(f"logic edge references unknown target ability: {edge.target_id}")
        for ability in self.abilities:
            for peer_id in ability.confusion_peer_ids:
                if peer_id not in ability_ids:
                    raise ValueError(f"logic ability references unknown confusion peer: {peer_id}")
            for downstream_id in ability.downstream_ability_ids:
                if downstream_id not in ability_ids:
                    raise ValueError(f"logic ability references unknown downstream ability: {downstream_id}")
        return self

    def ability_by_id(self, ability_id: str) -> LogicAbilitySpec | None:
        for ability in self.abilities:
            if ability.id == ability_id:
                return ability
        return None

    def abilities_for_node(self, node_id: str) -> list[LogicAbilitySpec]:
        return [ability for ability in self._abilities_from_ids(self.node_ability_map.get(node_id, []))]

    def abilities_for_error(self, error_type: ErrorType | None) -> list[LogicAbilitySpec]:
        if error_type is None:
            return []
        return [ability for ability in self._abilities_from_ids(self.error_ability_map.get(error_type, []))]

    def _abilities_from_ids(self, ability_ids: list[str]) -> list[LogicAbilitySpec]:
        abilities: list[LogicAbilitySpec] = []
        for ability_id in ability_ids:
            ability = self.ability_by_id(ability_id)
            if ability is not None:
                abilities.append(ability)
        return abilities


class AbilityEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ability_id: str
    title: str
    kind: LogicAbilityKind
    role: LogicAbilityRole | None = None
    status: AbilityEvidenceStatus
    confidence: float = Field(ge=0, le=1)
    dimensions: list[ScoreDimension] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
    source_labels: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    repair_cues: list[str] = Field(default_factory=list)
    target_node_id: str
    upstream_ability_ids: list[str] = Field(default_factory=list)
    downstream_ability_ids: list[str] = Field(default_factory=list)
    contradiction_peer_ids: list[str] = Field(default_factory=list)


class LogicDiagnosisInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active: bool = False
    chapter_id: str | None = None
    primary_ability_id: str | None = None
    primary_target_node_id: str | None = None
    ability_evidence: list[AbilityEvidence] = Field(default_factory=list)
    ability_chain_summary: list[str] = Field(default_factory=list)
    repair_cues: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)
    learner_message: str = ""

    def public_payload(self) -> dict:
        return self.model_dump(
            mode="json",
            exclude_none=True,
            exclude={"ability_evidence": {"__all__": {"source_labels"}}},
        )


class LogicGraphQualityIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: LogicQualitySeverity
    code: str
    message: str
    node_id: str | None = None


class LogicGraphQualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter_id: str
    issue_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    issues: list[LogicGraphQualityIssue] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.error_count == 0
