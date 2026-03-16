"""Cryptographic commitment schemes for agentic AI.

An agent commits to a plan *before* executing it. After execution, a verifier
can check whether the agent's actions matched the committed plan. This creates
a tamper-evident audit trail: any deviation from the committed plan is
detectable.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime

from zion.models import ActionLog, CommitmentHash, Plan


class CommitmentScheme:
    """SHA-256 based commit-reveal scheme for agent plans.

    Workflow
    --------
    1. Agent creates a ``Plan`` and calls ``commit(plan)``.
    2. The commitment hash is stored on an immutable ledger or shared with
       a human overseer.
    3. The agent executes its actions.
    4. A verifier calls ``verify(action_log, commitment)`` to check fidelity.
    5. At any time, ``reveal(commitment)`` exposes the original plan.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[Plan, str]] = {}  # plan_id -> (plan, nonce)

    def commit(self, plan: Plan) -> CommitmentHash:
        """Create a cryptographic commitment to a plan.

        Parameters
        ----------
        plan:
            The plan the agent intends to follow.

        Returns
        -------
        CommitmentHash
            An opaque hash that can later be verified against actual actions.
        """
        nonce = secrets.token_hex(32)
        payload = self._serialize_plan(plan, nonce)
        hash_value = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        self._store[plan.plan_id] = (plan, nonce)

        return CommitmentHash(
            hash_value=hash_value,
            nonce=nonce,
            plan_id=plan.plan_id,
            timestamp=datetime.utcnow(),
        )

    def verify(self, action_log: ActionLog, commitment: CommitmentHash) -> bool:
        """Verify that executed actions match the committed plan.

        Checks two things:
        1. The commitment hash is valid (not tampered with).
        2. The recorded actions match the plan steps.

        Parameters
        ----------
        action_log:
            The actions the agent actually executed.
        commitment:
            The commitment hash produced at plan time.

        Returns
        -------
        bool
            True if the actions faithfully follow the committed plan.
        """
        if commitment.plan_id not in self._store:
            return False

        plan, nonce = self._store[commitment.plan_id]

        # Re-derive hash to check integrity
        payload = self._serialize_plan(plan, nonce)
        expected_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if expected_hash != commitment.hash_value:
            return False

        # Check action fidelity — actions must cover all plan steps in order
        if len(action_log.actions) < len(plan.steps):
            return False

        for planned, actual in zip(plan.steps, action_log.actions):
            if not self._actions_match(planned, actual):
                return False

        return True

    def reveal(self, commitment: CommitmentHash) -> Plan | None:
        """Reveal the plan behind a commitment.

        Parameters
        ----------
        commitment:
            The commitment whose plan should be revealed.

        Returns
        -------
        Plan or None
            The original plan, or None if the commitment is unknown.
        """
        entry = self._store.get(commitment.plan_id)
        if entry is None:
            return None

        plan, nonce = entry

        # Verify hash integrity before revealing
        payload = self._serialize_plan(plan, nonce)
        expected_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if expected_hash != commitment.hash_value:
            return None

        return plan

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_plan(plan: Plan, nonce: str) -> str:
        """Deterministic serialisation of plan + nonce for hashing."""
        data = {
            "plan_id": plan.plan_id,
            "steps": plan.steps,
            "constraints": plan.constraints,
            "expected_outcomes": plan.expected_outcomes,
            "nonce": nonce,
        }
        return json.dumps(data, sort_keys=True, default=str)

    @staticmethod
    def _actions_match(planned: str, actual: str) -> bool:
        """Check whether an actual action matches the planned step.

        Uses normalised string comparison. In a production system this would
        use semantic similarity via an embedding model.
        """
        return planned.strip().lower() == actual.strip().lower()
