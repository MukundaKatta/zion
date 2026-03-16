"""Behavioral hashing — compress agent behaviour into verifiable signatures.

A BehavioralSignature is a compact fingerprint of an agent's action log. Two
signatures can be compared for similarity, and new signatures can be checked
against a baseline to detect anomalous behaviour shifts.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from math import sqrt

from zion.models import ActionLog, AnomalyResult, BehavioralSignature


class BehavioralHasher:
    """Generates and compares behavioural signatures for agent action logs.

    The feature vector encodes normalised action-type frequencies so that
    signatures from different-length logs remain comparable.
    """

    # Canonical action categories used as feature-vector dimensions.
    ACTION_CATEGORIES: list[str] = [
        "read",
        "write",
        "execute",
        "query",
        "communicate",
        "plan",
        "decide",
        "delegate",
        "observe",
        "other",
    ]

    def hash_behavior(self, action_log: ActionLog) -> BehavioralSignature:
        """Compress an action log into a behavioural signature.

        Parameters
        ----------
        action_log:
            The actions to fingerprint.

        Returns
        -------
        BehavioralSignature
        """
        feature_vector = self._build_feature_vector(action_log.actions)
        payload = json.dumps(
            {"plan_id": action_log.plan_id, "features": feature_vector},
            sort_keys=True,
        )
        sig_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        return BehavioralSignature(
            signature=sig_hash,
            action_count=len(action_log.actions),
            feature_vector=feature_vector,
        )

    def compare_signatures(
        self,
        sig1: BehavioralSignature,
        sig2: BehavioralSignature,
    ) -> float:
        """Compute cosine similarity between two behavioural signatures.

        Parameters
        ----------
        sig1, sig2:
            Signatures to compare.

        Returns
        -------
        float
            Cosine similarity in [0.0, 1.0]. 1.0 means identical profiles.
        """
        return self._cosine_similarity(sig1.feature_vector, sig2.feature_vector)

    def detect_anomaly(
        self,
        signature: BehavioralSignature,
        baseline: BehavioralSignature,
        threshold: float = 0.75,
    ) -> AnomalyResult:
        """Check whether *signature* deviates significantly from *baseline*.

        Parameters
        ----------
        signature:
            The signature under test.
        baseline:
            The expected baseline signature.
        threshold:
            Similarity below this value is considered anomalous.

        Returns
        -------
        AnomalyResult
        """
        similarity = self.compare_signatures(signature, baseline)
        anomaly_score = 1.0 - similarity

        deviation_dims: list[str] = []
        for i, category in enumerate(self.ACTION_CATEGORIES):
            if i < len(signature.feature_vector) and i < len(baseline.feature_vector):
                diff = abs(signature.feature_vector[i] - baseline.feature_vector[i])
                if diff > 0.15:
                    deviation_dims.append(category)

        is_anomalous = similarity < threshold

        return AnomalyResult(
            is_anomalous=is_anomalous,
            anomaly_score=round(anomaly_score, 4),
            deviation_dimensions=deviation_dims,
            details=(
                f"Cosine similarity {similarity:.4f} vs threshold {threshold}. "
                f"Deviating dimensions: {deviation_dims or 'none'}."
            ),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_feature_vector(self, actions: list[str]) -> list[float]:
        """Map raw action strings to a normalised frequency vector."""
        counts = Counter(self._classify(a) for a in actions)
        total = max(sum(counts.values()), 1)
        return [counts.get(cat, 0) / total for cat in self.ACTION_CATEGORIES]

    @staticmethod
    def _classify(action: str) -> str:
        """Classify an action string into one of the canonical categories."""
        lower = action.lower()
        keywords: dict[str, list[str]] = {
            "read": ["read", "fetch", "load", "get", "retrieve"],
            "write": ["write", "save", "store", "update", "set"],
            "execute": ["execute", "run", "invoke", "call", "perform"],
            "query": ["query", "search", "lookup", "find", "ask"],
            "communicate": ["send", "notify", "email", "message", "respond"],
            "plan": ["plan", "schedule", "outline", "draft"],
            "decide": ["decide", "choose", "select", "evaluate", "judge"],
            "delegate": ["delegate", "assign", "hand off", "forward"],
            "observe": ["observe", "monitor", "watch", "track", "log"],
        }
        for category, kws in keywords.items():
            if any(kw in lower for kw in kws):
                return category
        return "other"

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Cosine similarity between two vectors."""
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = sqrt(sum(x * x for x in a))
        mag_b = sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return max(0.0, min(1.0, dot / (mag_a * mag_b)))
