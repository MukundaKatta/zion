"""Adversarial testing — red teams, deception detection, hidden goal discovery."""

from zion.adversarial.deception import DeceptionDetector
from zion.adversarial.hidden_goals import HiddenGoalDetector
from zion.adversarial.red_team import RedTeamEnvironment

__all__ = [
    "RedTeamEnvironment",
    "DeceptionDetector",
    "HiddenGoalDetector",
]
