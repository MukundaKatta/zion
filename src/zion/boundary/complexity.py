"""Task complexity analysis across multiple dimensions.

Produces a ComplexityProfile that quantifies how difficult a task is to
verify and oversee.
"""

from __future__ import annotations

from zion.models import ComplexityProfile


class ComplexityAnalyzer:
    """Measures task complexity along five dimensions.

    Dimensions
    ----------
    * **steps** — number of sequential steps.
    * **branching** — number of decision branches.
    * **tools_required** — external tools or APIs needed.
    * **ambiguity** — degree of goal under-specification.
    * **stakes** — severity of consequences if things go wrong.
    """

    # Weights used to combine dimensions into an overall score.
    DEFAULT_WEIGHTS: dict[str, float] = {
        "steps": 0.15,
        "branching": 0.15,
        "tools_required": 0.10,
        "ambiguity": 0.30,
        "stakes": 0.30,
    }

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self._weights = weights or dict(self.DEFAULT_WEIGHTS)

    def analyze(
        self,
        *,
        steps: int = 1,
        branching: int = 1,
        tools_required: int = 0,
        ambiguity: float = 0.0,
        stakes: float = 0.0,
    ) -> ComplexityProfile:
        """Produce a multi-dimensional complexity profile for a task.

        Parameters
        ----------
        steps:
            Number of sequential steps (>= 1).
        branching:
            Number of decision branches (>= 1).
        tools_required:
            Number of external tools needed (>= 0).
        ambiguity:
            Goal ambiguity in [0, 1].
        stakes:
            Consequence severity in [0, 1].

        Returns
        -------
        ComplexityProfile
        """
        steps = max(1, steps)
        branching = max(1, branching)
        tools_required = max(0, tools_required)
        ambiguity = max(0.0, min(1.0, ambiguity))
        stakes = max(0.0, min(1.0, stakes))

        overall = self._compute_overall(
            steps=steps,
            branching=branching,
            tools_required=tools_required,
            ambiguity=ambiguity,
            stakes=stakes,
        )

        return ComplexityProfile(
            steps=steps,
            branching=branching,
            tools_required=tools_required,
            ambiguity=ambiguity,
            stakes=stakes,
            overall_score=round(overall, 4),
        )

    def _compute_overall(
        self,
        *,
        steps: int,
        branching: int,
        tools_required: int,
        ambiguity: float,
        stakes: float,
    ) -> float:
        """Weighted combination of normalised dimension scores."""
        normalised = {
            "steps": self._normalise_count(steps, scale=20),
            "branching": self._normalise_count(branching, scale=10),
            "tools_required": self._normalise_count(tools_required, scale=8),
            "ambiguity": ambiguity,
            "stakes": stakes,
        }
        total_weight = sum(self._weights.values())
        score = sum(
            self._weights.get(dim, 0.0) * val for dim, val in normalised.items()
        )
        return min(1.0, score / total_weight if total_weight else 0.0)

    @staticmethod
    def _normalise_count(value: int, scale: int) -> float:
        """Normalise an integer count to [0, 1] using a soft saturation curve."""
        return min(1.0, value / scale)
