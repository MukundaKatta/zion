"""Agent-to-human handoff protocol.

Defines *when* an agent should cede control to a human, *what* context to
provide, and *how* to verify that the handoff was successful.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from zion.models import (
    ActionLog,
    HandoffPackage,
    RiskLevel,
)


# Risk thresholds: complexity score above which handoff is required.
_RISK_THRESHOLDS: dict[RiskLevel, float] = {
    RiskLevel.LOW: 0.85,
    RiskLevel.MEDIUM: 0.60,
    RiskLevel.HIGH: 0.35,
    RiskLevel.CRITICAL: 0.10,
}


class HandoffProtocol:
    """Formal agent-to-human transition protocol.

    The protocol guarantees that:
    1. Handoff is triggered before the agent operates beyond its verified zone.
    2. The human receives a structured context package.
    3. The handoff itself is logged and verifiable.
    """

    def __init__(self, risk_thresholds: dict[RiskLevel, float] | None = None) -> None:
        self._thresholds = risk_thresholds or dict(_RISK_THRESHOLDS)
        self._handoff_log: list[HandoffPackage] = []

    def should_handoff(
        self,
        complexity_score: float,
        risk_level: RiskLevel,
    ) -> bool:
        """Determine whether control should be handed to a human.

        Parameters
        ----------
        complexity_score:
            Overall task complexity in [0, 1].
        risk_level:
            Current assessed risk level.

        Returns
        -------
        bool
            True if the agent should stop and hand off to a human.
        """
        threshold = self._thresholds.get(risk_level, 0.5)
        return complexity_score >= threshold

    def create_handoff_package(
        self,
        agent_id: str,
        action_log: ActionLog,
        risk_level: RiskLevel = RiskLevel.MEDIUM,
        recommendations: list[str] | None = None,
    ) -> HandoffPackage:
        """Build a structured context package for the human recipient.

        Parameters
        ----------
        agent_id:
            Identifier for the agent ceding control.
        action_log:
            Actions taken so far.
        risk_level:
            Assessed risk level at the point of handoff.
        recommendations:
            Optional agent recommendations for the human.

        Returns
        -------
        HandoffPackage
        """
        pending = self._infer_pending_actions(action_log)
        summary = self._summarize_state(agent_id, action_log)

        package = HandoffPackage(
            package_id=uuid.uuid4().hex[:12],
            agent_state_summary=summary,
            pending_actions=pending,
            risk_assessment=risk_level,
            context={
                "agent_id": agent_id,
                "actions_completed": len(action_log.actions),
                "plan_id": action_log.plan_id,
            },
            recommendations=recommendations or [],
            timestamp=datetime.utcnow(),
        )

        self._handoff_log.append(package)
        return package

    def verify_handoff(self, package: HandoffPackage) -> bool:
        """Verify that a handoff package is complete and well-formed.

        Parameters
        ----------
        package:
            The handoff package to verify.

        Returns
        -------
        bool
            True if the package contains all required context.
        """
        if not package.agent_state_summary:
            return False
        if not package.package_id:
            return False
        if package.risk_assessment in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            if not package.recommendations:
                return False
        return True

    @property
    def handoff_history(self) -> list[HandoffPackage]:
        """Return the full handoff log for audit purposes."""
        return list(self._handoff_log)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_pending_actions(action_log: ActionLog) -> list[str]:
        """Infer what actions remain based on the log's metadata."""
        planned = action_log.metadata.get("planned_steps", [])
        completed = set(a.strip().lower() for a in action_log.actions)
        return [s for s in planned if s.strip().lower() not in completed]

    @staticmethod
    def _summarize_state(agent_id: str, action_log: ActionLog) -> str:
        """Generate a human-readable state summary."""
        n = len(action_log.actions)
        last_action = action_log.actions[-1] if action_log.actions else "none"
        return (
            f"Agent {agent_id} completed {n} action(s) under plan "
            f"'{action_log.plan_id}'. Last action: '{last_action}'."
        )
