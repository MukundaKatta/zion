"""Oversight method effectiveness testing.

Evaluates how well different oversight strategies perform at varying
complexity levels.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from zion.boundary.complexity import ComplexityAnalyzer
from zion.models import ComplexityProfile


@dataclass
class OversightResult:
    """Result of testing an oversight method against a complexity profile."""
    method: str
    complexity_score: float
    effectiveness: float  # 0..1
    feasible: bool
    notes: str = ""


@dataclass
class OversightReport:
    """Aggregated report across methods and complexity levels."""
    results: list[OversightResult] = field(default_factory=list)
    best_method_by_complexity: dict[str, str] = field(default_factory=dict)
    summary: str = ""


class OversightTester:
    """Tests oversight methods against tasks of varying complexity.

    Each oversight method has an effectiveness curve that decays as task
    complexity increases. This tester evaluates multiple methods and
    identifies which is most effective at each complexity level.
    """

    # (max_effectiveness, decay_rate) — higher decay means faster falloff.
    OVERSIGHT_METHODS: dict[str, tuple[float, float]] = {
        "direct_review": (0.98, 3.0),
        "commitment_verification": (0.95, 2.0),
        "multi_agent_verification": (0.90, 1.5),
        "behavioral_hash": (0.85, 1.8),
        "selective_audit": (0.80, 1.2),
        "handoff_protocol": (0.70, 0.8),
    }

    def __init__(self) -> None:
        self._analyzer = ComplexityAnalyzer()

    def test_method(
        self,
        method: str,
        profile: ComplexityProfile,
    ) -> OversightResult:
        """Evaluate a single oversight method against a complexity profile.

        Parameters
        ----------
        method:
            Name of the oversight method.
        profile:
            Task complexity profile.

        Returns
        -------
        OversightResult
        """
        if method not in self.OVERSIGHT_METHODS:
            return OversightResult(
                method=method,
                complexity_score=profile.overall_score,
                effectiveness=0.0,
                feasible=False,
                notes=f"Unknown oversight method: {method}",
            )

        max_eff, decay = self.OVERSIGHT_METHODS[method]
        effectiveness = max_eff * max(0.0, 1.0 - decay * profile.overall_score)
        effectiveness = round(max(0.0, min(1.0, effectiveness)), 4)
        feasible = effectiveness > 0.3

        return OversightResult(
            method=method,
            complexity_score=round(profile.overall_score, 4),
            effectiveness=effectiveness,
            feasible=feasible,
            notes=(
                f"Effective at complexity {profile.overall_score:.2f}"
                if feasible
                else f"Ineffective at complexity {profile.overall_score:.2f}"
            ),
        )

    def test_all_methods(
        self,
        profile: ComplexityProfile,
    ) -> list[OversightResult]:
        """Test every known oversight method against a single profile.

        Parameters
        ----------
        profile:
            Task complexity profile.

        Returns
        -------
        list[OversightResult]
        """
        return [self.test_method(m, profile) for m in self.OVERSIGHT_METHODS]

    def generate_report(
        self,
        profiles: list[ComplexityProfile] | None = None,
        sweep_steps: int = 10,
    ) -> OversightReport:
        """Generate a full effectiveness report across complexity levels.

        Parameters
        ----------
        profiles:
            Optional explicit profiles. A synthetic sweep is used if None.
        sweep_steps:
            Steps for the synthetic sweep.

        Returns
        -------
        OversightReport
        """
        if profiles is None:
            profiles = [
                self._analyzer.analyze(
                    steps=max(1, int(t / max(sweep_steps - 1, 1) * 25)),
                    branching=max(1, int(t / max(sweep_steps - 1, 1) * 12)),
                    tools_required=int(t / max(sweep_steps - 1, 1) * 10),
                    ambiguity=t / max(sweep_steps - 1, 1),
                    stakes=t / max(sweep_steps - 1, 1),
                )
                for t in range(sweep_steps)
            ]

        all_results: list[OversightResult] = []
        best_by_complexity: dict[str, str] = {}

        for profile in profiles:
            results = self.test_all_methods(profile)
            all_results.extend(results)

            feasible = [r for r in results if r.feasible]
            if feasible:
                best = max(feasible, key=lambda r: r.effectiveness)
                key = f"{profile.overall_score:.2f}"
                best_by_complexity[key] = best.method

        return OversightReport(
            results=all_results,
            best_method_by_complexity=best_by_complexity,
            summary=(
                f"Tested {len(self.OVERSIGHT_METHODS)} methods across "
                f"{len(profiles)} complexity levels."
            ),
        )
