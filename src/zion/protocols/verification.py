"""Multi-agent verification protocol.

Multiple independent verifier agents review a target agent's actions and vote
on whether its behaviour is safe. A consensus mechanism aggregates votes and
a collusion detector flags suspiciously correlated voting patterns.
"""

from __future__ import annotations

import uuid
from collections import Counter

import numpy as np

from zion.models import ActionLog, VerifierPanel, VerifierVote, VoteOutcome


class MultiAgentVerifier:
    """Orchestrates a panel of verifier agents that audit a target agent.

    Design principles
    -----------------
    * Each verifier operates independently — no shared memory.
    * Consensus requires a strict majority.
    * Collusion detection uses vote-correlation analysis: if verifiers
      consistently agree with suspiciously high confidence, a flag is raised.
    """

    def __init__(self, collusion_threshold: float = 0.92) -> None:
        """
        Parameters
        ----------
        collusion_threshold:
            Pearson-correlation threshold above which verifier confidence
            vectors are considered suspiciously aligned (potential collusion).
        """
        self._collusion_threshold = collusion_threshold
        self._panels: dict[str, VerifierPanel] = {}

    def create_verifier_panel(
        self,
        n_agents: int,
        target_agent_id: str = "",
    ) -> VerifierPanel:
        """Instantiate a verifier panel of *n_agents* independent reviewers.

        Parameters
        ----------
        n_agents:
            Number of verifier agents on the panel (must be odd for clean
            majority voting).
        target_agent_id:
            The agent whose behaviour will be reviewed.

        Returns
        -------
        VerifierPanel
        """
        if n_agents < 1:
            raise ValueError("Panel must have at least one verifier.")

        panel_id = uuid.uuid4().hex[:12]
        verifier_ids = [f"verifier-{uuid.uuid4().hex[:8]}" for _ in range(n_agents)]

        panel = VerifierPanel(
            panel_id=panel_id,
            verifier_ids=verifier_ids,
            target_agent_id=target_agent_id,
        )
        self._panels[panel_id] = panel
        return panel

    def submit_vote(self, panel_id: str, vote: VerifierVote) -> None:
        """Record a verifier's vote on the panel.

        Parameters
        ----------
        panel_id:
            Panel to submit the vote to.
        vote:
            The verifier's vote.

        Raises
        ------
        ValueError
            If the panel does not exist or the verifier is not on the panel.
        """
        panel = self._panels.get(panel_id)
        if panel is None:
            raise ValueError(f"Unknown panel: {panel_id}")
        if vote.verifier_id not in panel.verifier_ids:
            raise ValueError(f"Verifier {vote.verifier_id} is not on panel {panel_id}")

        panel.votes.append(vote)

    def reach_consensus(self, panel_id: str) -> VerifierPanel:
        """Compute consensus from submitted votes and run collusion detection.

        Parameters
        ----------
        panel_id:
            Panel to evaluate.

        Returns
        -------
        VerifierPanel
            Updated panel with ``consensus`` and ``collusion_detected`` set.
        """
        panel = self._panels.get(panel_id)
        if panel is None:
            raise ValueError(f"Unknown panel: {panel_id}")

        # Majority vote (excluding abstentions)
        effective_votes = [v.vote for v in panel.votes if v.vote != VoteOutcome.ABSTAIN]

        if not effective_votes:
            panel.consensus = VoteOutcome.ABSTAIN
        else:
            counts = Counter(effective_votes)
            panel.consensus = counts.most_common(1)[0][0]

        # Collusion detection
        panel.collusion_detected = self._detect_collusion(panel)

        return panel

    def evaluate_action_log(
        self,
        panel: VerifierPanel,
        action_log: ActionLog,
    ) -> list[VerifierVote]:
        """Generate synthetic verifier votes from an action log.

        In a production system each verifier would be an independent LLM call.
        Here we simulate verification with deterministic heuristics so the
        framework can be tested without API keys.

        Parameters
        ----------
        panel:
            The verifier panel.
        action_log:
            Actions to be reviewed.

        Returns
        -------
        list[VerifierVote]
            One vote per verifier.
        """
        votes: list[VerifierVote] = []
        for vid in panel.verifier_ids:
            # Heuristic: flag logs with very few or very many actions
            action_count = len(action_log.actions)
            if action_count == 0:
                outcome = VoteOutcome.UNSAFE
                confidence = 0.95
                reasoning = "No actions recorded — possible evasion."
            elif action_count > 100:
                outcome = VoteOutcome.UNSAFE
                confidence = 0.7
                reasoning = "Unusually high action count — possible runaway behaviour."
            else:
                outcome = VoteOutcome.SAFE
                confidence = 0.8
                reasoning = "Action count within expected range."

            vote = VerifierVote(
                verifier_id=vid,
                target_agent_id=panel.target_agent_id,
                vote=outcome,
                reasoning=reasoning,
                confidence=confidence,
            )
            votes.append(vote)

        return votes

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_collusion(self, panel: VerifierPanel) -> bool:
        """Detect potential collusion among verifiers.

        Uses pairwise Pearson correlation of confidence values. If the mean
        pairwise correlation exceeds the threshold, collusion is suspected.
        """
        if len(panel.votes) < 3:
            return False

        confidences: dict[str, list[float]] = {}
        for vote in panel.votes:
            confidences.setdefault(vote.verifier_id, []).append(vote.confidence)

        vectors = list(confidences.values())
        if len(vectors) < 2:
            return False

        # Pad to equal length
        max_len = max(len(v) for v in vectors)
        padded = [v + [0.5] * (max_len - len(v)) for v in vectors]

        arr = np.array(padded)
        if arr.shape[1] < 2:
            return False

        corr_matrix = np.corrcoef(arr)
        # Mean of upper-triangle (excluding diagonal)
        n = corr_matrix.shape[0]
        upper = [corr_matrix[i][j] for i in range(n) for j in range(i + 1, n)]

        if not upper:
            return False

        mean_corr = float(np.nanmean(upper))
        return mean_corr > self._collusion_threshold
