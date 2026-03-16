"""Tests for the Zion protocol modules."""

from __future__ import annotations

import pytest

from zion.models import ActionLog, Plan, RiskLevel, VoteOutcome
from zion.protocols.behavioral_hash import BehavioralHasher
from zion.protocols.commitment import CommitmentScheme
from zion.protocols.handoff import HandoffProtocol
from zion.protocols.verification import MultiAgentVerifier


# ======================================================================
# CommitmentScheme
# ======================================================================

class TestCommitmentScheme:
    def test_commit_and_verify_matching_actions(self) -> None:
        scheme = CommitmentScheme()
        plan = Plan(
            plan_id="p1",
            steps=["read input", "process", "write output"],
            constraints=["no side effects"],
        )
        commitment = scheme.commit(plan)
        actions = ActionLog(
            plan_id="p1",
            actions=["read input", "process", "write output"],
        )
        assert scheme.verify(actions, commitment) is True

    def test_verify_rejects_wrong_actions(self) -> None:
        scheme = CommitmentScheme()
        plan = Plan(plan_id="p2", steps=["read", "write"])
        commitment = scheme.commit(plan)
        actions = ActionLog(plan_id="p2", actions=["read", "delete everything"])
        assert scheme.verify(actions, commitment) is False

    def test_verify_rejects_missing_actions(self) -> None:
        scheme = CommitmentScheme()
        plan = Plan(plan_id="p3", steps=["a", "b", "c"])
        commitment = scheme.commit(plan)
        actions = ActionLog(plan_id="p3", actions=["a"])
        assert scheme.verify(actions, commitment) is False

    def test_reveal_returns_original_plan(self) -> None:
        scheme = CommitmentScheme()
        plan = Plan(plan_id="p4", steps=["step1"])
        commitment = scheme.commit(plan)
        revealed = scheme.reveal(commitment)
        assert revealed is not None
        assert revealed.plan_id == "p4"
        assert revealed.steps == ["step1"]

    def test_reveal_unknown_commitment_returns_none(self) -> None:
        scheme = CommitmentScheme()
        from zion.models import CommitmentHash
        fake = CommitmentHash(hash_value="abc", nonce="xyz", plan_id="nope")
        assert scheme.reveal(fake) is None

    def test_commitment_hash_is_deterministic_for_same_nonce(self) -> None:
        scheme = CommitmentScheme()
        plan = Plan(plan_id="det", steps=["x"])
        c1 = scheme.commit(plan)
        # Internally the nonce differs each time, so hashes differ
        c2 = scheme.commit(plan)
        # Both should be valid but different
        assert c1.hash_value != c2.hash_value


# ======================================================================
# MultiAgentVerifier
# ======================================================================

class TestMultiAgentVerifier:
    def test_create_panel(self) -> None:
        v = MultiAgentVerifier()
        panel = v.create_verifier_panel(5, target_agent_id="agent-x")
        assert len(panel.verifier_ids) == 5
        assert panel.target_agent_id == "agent-x"

    def test_submit_and_reach_consensus(self) -> None:
        v = MultiAgentVerifier()
        panel = v.create_verifier_panel(3)
        for vid in panel.verifier_ids:
            from zion.models import VerifierVote
            v.submit_vote(
                panel.panel_id,
                VerifierVote(
                    verifier_id=vid,
                    target_agent_id="t",
                    vote=VoteOutcome.SAFE,
                    confidence=0.9,
                ),
            )
        result = v.reach_consensus(panel.panel_id)
        assert result.consensus == VoteOutcome.SAFE

    def test_evaluate_action_log(self) -> None:
        v = MultiAgentVerifier()
        panel = v.create_verifier_panel(3, target_agent_id="test")
        log = ActionLog(plan_id="eval", actions=["a", "b", "c"])
        votes = v.evaluate_action_log(panel, log)
        assert len(votes) == 3
        assert all(vote.vote == VoteOutcome.SAFE for vote in votes)

    def test_evaluate_empty_log_votes_unsafe(self) -> None:
        v = MultiAgentVerifier()
        panel = v.create_verifier_panel(3)
        log = ActionLog(plan_id="empty", actions=[])
        votes = v.evaluate_action_log(panel, log)
        assert all(vote.vote == VoteOutcome.UNSAFE for vote in votes)

    def test_invalid_panel_raises(self) -> None:
        v = MultiAgentVerifier()
        with pytest.raises(ValueError):
            v.reach_consensus("nonexistent")


# ======================================================================
# BehavioralHasher
# ======================================================================

class TestBehavioralHasher:
    def test_identical_logs_have_similarity_one(self) -> None:
        hasher = BehavioralHasher()
        log = ActionLog(plan_id="bh", actions=["read file", "write result"])
        sig1 = hasher.hash_behavior(log)
        sig2 = hasher.hash_behavior(log)
        assert hasher.compare_signatures(sig1, sig2) == pytest.approx(1.0)

    def test_different_logs_have_lower_similarity(self) -> None:
        hasher = BehavioralHasher()
        log1 = ActionLog(plan_id="a", actions=["read file", "read config"])
        log2 = ActionLog(plan_id="b", actions=["execute command", "send email"])
        sig1 = hasher.hash_behavior(log1)
        sig2 = hasher.hash_behavior(log2)
        assert hasher.compare_signatures(sig1, sig2) < 1.0

    def test_detect_anomaly_identical_is_not_anomalous(self) -> None:
        hasher = BehavioralHasher()
        log = ActionLog(plan_id="base", actions=["read x", "write y"])
        sig = hasher.hash_behavior(log)
        result = hasher.detect_anomaly(sig, sig)
        assert result.is_anomalous is False

    def test_detect_anomaly_different_pattern(self) -> None:
        hasher = BehavioralHasher()
        baseline_log = ActionLog(plan_id="bl", actions=["read a"] * 10)
        test_log = ActionLog(plan_id="tl", actions=["execute cmd"] * 10)
        baseline = hasher.hash_behavior(baseline_log)
        test_sig = hasher.hash_behavior(test_log)
        result = hasher.detect_anomaly(test_sig, baseline, threshold=0.9)
        assert result.is_anomalous is True


# ======================================================================
# HandoffProtocol
# ======================================================================

class TestHandoffProtocol:
    def test_should_handoff_high_complexity_high_risk(self) -> None:
        hp = HandoffProtocol()
        assert hp.should_handoff(0.8, RiskLevel.HIGH) is True

    def test_should_not_handoff_low_complexity_low_risk(self) -> None:
        hp = HandoffProtocol()
        assert hp.should_handoff(0.2, RiskLevel.LOW) is False

    def test_create_handoff_package(self) -> None:
        hp = HandoffProtocol()
        log = ActionLog(plan_id="hp-test", actions=["action1", "action2"])
        pkg = hp.create_handoff_package(
            agent_id="agent-1",
            action_log=log,
            risk_level=RiskLevel.MEDIUM,
            recommendations=["Review step 2"],
        )
        assert pkg.package_id
        assert "agent-1" in pkg.agent_state_summary
        assert len(pkg.recommendations) == 1

    def test_verify_handoff_package(self) -> None:
        hp = HandoffProtocol()
        log = ActionLog(plan_id="v", actions=["x"])
        pkg = hp.create_handoff_package(
            agent_id="a",
            action_log=log,
            risk_level=RiskLevel.HIGH,
            recommendations=["do something"],
        )
        assert hp.verify_handoff(pkg) is True

    def test_verify_rejects_incomplete_high_risk_package(self) -> None:
        hp = HandoffProtocol()
        log = ActionLog(plan_id="v", actions=["x"])
        pkg = hp.create_handoff_package(
            agent_id="a",
            action_log=log,
            risk_level=RiskLevel.HIGH,
        )
        # High risk with no recommendations should fail
        assert hp.verify_handoff(pkg) is False
