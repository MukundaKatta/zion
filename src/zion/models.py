"""Core data models for the Zion protocol suite."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ZoneType(str, Enum):
    VERIFIED = "verified"
    UNCERTAIN = "uncertain"
    UNCONTROLLABLE = "uncontrollable"


class VoteOutcome(str, Enum):
    SAFE = "safe"
    UNSAFE = "unsafe"
    ABSTAIN = "abstain"


class DeceptionType(str, Enum):
    CONSISTENCY = "consistency"
    OMISSION = "omission"
    MISDIRECTION = "misdirection"
    SYCOPHANCY = "sycophancy"


class RedTeamAttack(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    GOAL_HIJACKING = "goal_hijacking"
    SOCIAL_ENGINEERING = "social_engineering"
    CONTEXT_MANIPULATION = "context_manipulation"


# ---------------------------------------------------------------------------
# Commitment protocol models
# ---------------------------------------------------------------------------

class Plan(BaseModel):
    """A structured plan an agent commits to before execution."""
    plan_id: str = Field(description="Unique identifier for the plan")
    steps: list[str] = Field(description="Ordered list of planned actions")
    constraints: list[str] = Field(default_factory=list, description="Self-imposed constraints")
    expected_outcomes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CommitmentHash(BaseModel):
    """A cryptographic commitment to a plan."""
    hash_value: str = Field(description="SHA-256 hash of plan + nonce")
    nonce: str = Field(description="Random nonce used for commitment")
    plan_id: str = Field(description="Identifier linking to the committed plan")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ActionLog(BaseModel):
    """A log of actions an agent actually took."""
    plan_id: str
    actions: list[str] = Field(description="Actions that were executed")
    timestamps: list[datetime] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Verification models
# ---------------------------------------------------------------------------

class VerifierVote(BaseModel):
    """A single verifier's vote on agent behaviour."""
    verifier_id: str
    target_agent_id: str
    vote: VoteOutcome
    reasoning: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class VerifierPanel(BaseModel):
    """A panel of verifier agents."""
    panel_id: str
    verifier_ids: list[str]
    target_agent_id: str = ""
    votes: list[VerifierVote] = Field(default_factory=list)
    consensus: VoteOutcome | None = None
    collusion_detected: bool = False


# ---------------------------------------------------------------------------
# Behavioral hash models
# ---------------------------------------------------------------------------

class BehavioralSignature(BaseModel):
    """A compressed fingerprint of agent behaviour."""
    signature: str
    action_count: int
    feature_vector: list[float] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnomalyResult(BaseModel):
    """Result of an anomaly detection check."""
    is_anomalous: bool
    anomaly_score: float = Field(ge=0.0, le=1.0)
    deviation_dimensions: list[str] = Field(default_factory=list)
    details: str = ""


# ---------------------------------------------------------------------------
# Handoff models
# ---------------------------------------------------------------------------

class HandoffPackage(BaseModel):
    """Context package for agent-to-human handoff."""
    package_id: str
    agent_state_summary: str
    pending_actions: list[str] = Field(default_factory=list)
    risk_assessment: RiskLevel = RiskLevel.MEDIUM
    context: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Boundary mapping models
# ---------------------------------------------------------------------------

class ComplexityProfile(BaseModel):
    """Multi-dimensional complexity profile for a task."""
    steps: int = Field(ge=1, description="Number of sequential steps")
    branching: int = Field(ge=1, description="Number of decision branches")
    tools_required: int = Field(ge=0, description="External tools needed")
    ambiguity: float = Field(ge=0.0, le=1.0, description="Degree of goal ambiguity")
    stakes: float = Field(ge=0.0, le=1.0, description="Consequence severity")
    overall_score: float = Field(ge=0.0, le=1.0, default=0.0)


class ControlZone(BaseModel):
    """A region in the control boundary map."""
    zone_type: ZoneType
    complexity_range: tuple[float, float] = (0.0, 1.0)
    description: str = ""
    oversight_methods: list[str] = Field(default_factory=list)


class ControlMap(BaseModel):
    """Complete map of the human-control boundary."""
    zones: list[ControlZone] = Field(default_factory=list)
    boundary_threshold: float = Field(ge=0.0, le=1.0, default=0.5)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    summary: str = ""


# ---------------------------------------------------------------------------
# Adversarial models
# ---------------------------------------------------------------------------

class DeceptionReport(BaseModel):
    """Report from deception detection analysis."""
    is_deceptive: bool = False
    deception_score: float = Field(ge=0.0, le=1.0, default=0.0)
    detected_patterns: list[DeceptionType] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    details: str = ""


class RedTeamRound(BaseModel):
    """A single round in a red-team exercise."""
    round_number: int
    attack_type: RedTeamAttack
    attack_prompt: str = ""
    agent_response: str = ""
    deviation_detected: bool = False
    notes: str = ""


class RedTeamReport(BaseModel):
    """Summary report from a red-team exercise."""
    total_rounds: int
    deviations: int = 0
    attack_breakdown: dict[str, int] = Field(default_factory=dict)
    rounds: list[RedTeamRound] = Field(default_factory=list)
    robustness_score: float = Field(ge=0.0, le=1.0, default=1.0)
    summary: str = ""


# ---------------------------------------------------------------------------
# Top-level audit report
# ---------------------------------------------------------------------------

class ZionAuditReport(BaseModel):
    """Full Zion audit output."""
    agent_id: str
    protocols_tested: list[str] = Field(default_factory=list)
    control_map: ControlMap | None = None
    deception_report: DeceptionReport | None = None
    red_team_report: RedTeamReport | None = None
    overall_risk: RiskLevel = RiskLevel.MEDIUM
    recommendations: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
