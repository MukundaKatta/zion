"""Control boundary mapper — identifies where human oversight breaks down.

Sweeps across task complexity levels and classifies each into a control zone:
verified, uncertain, or uncontrollable.
"""

from __future__ import annotations

from datetime import datetime

from zion.boundary.complexity import ComplexityAnalyzer
from zion.models import ComplexityProfile, ControlMap, ControlZone, ZoneType


class ControlBoundaryMapper:
    """Maps the boundary between verifiable and uncontrollable AI behaviour.

    The mapper evaluates a range of complexity profiles and assigns each to
    one of three zones:

    * **Verified** — human oversight can reliably verify agent behaviour.
    * **Uncertain** — partial verification is possible but gaps exist.
    * **Uncontrollable** — complexity exceeds human oversight capacity.
    """

    def __init__(
        self,
        verified_ceiling: float = 0.35,
        uncertain_ceiling: float = 0.70,
    ) -> None:
        """
        Parameters
        ----------
        verified_ceiling:
            Complexity scores below this fall in the verified zone.
        uncertain_ceiling:
            Scores between ``verified_ceiling`` and this value fall in the
            uncertain zone. Above is uncontrollable.
        """
        self._verified_ceiling = verified_ceiling
        self._uncertain_ceiling = uncertain_ceiling
        self._analyzer = ComplexityAnalyzer()

    def map_boundary(
        self,
        task_profiles: list[ComplexityProfile] | None = None,
        sweep_steps: int = 10,
    ) -> ControlMap:
        """Generate a complete control map.

        Parameters
        ----------
        task_profiles:
            Optional explicit list of complexity profiles to classify. If
            not provided, a synthetic sweep is generated.
        sweep_steps:
            Number of steps for the synthetic sweep (used only when
            ``task_profiles`` is None).

        Returns
        -------
        ControlMap
        """
        profiles = task_profiles or self._generate_sweep(sweep_steps)
        zones = self._classify_profiles(profiles)
        boundary = self._find_boundary(profiles)

        return ControlMap(
            zones=zones,
            boundary_threshold=round(boundary, 4),
            generated_at=datetime.utcnow(),
            summary=self._build_summary(zones, boundary),
        )

    def classify(self, profile: ComplexityProfile) -> ZoneType:
        """Classify a single complexity profile into a control zone.

        Parameters
        ----------
        profile:
            The complexity profile to classify.

        Returns
        -------
        ZoneType
        """
        score = profile.overall_score
        if score <= self._verified_ceiling:
            return ZoneType.VERIFIED
        if score <= self._uncertain_ceiling:
            return ZoneType.UNCERTAIN
        return ZoneType.UNCONTROLLABLE

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_sweep(self, steps: int) -> list[ComplexityProfile]:
        """Create a range of synthetic task profiles for boundary mapping."""
        profiles: list[ComplexityProfile] = []
        for i in range(steps):
            t = i / max(steps - 1, 1)
            profiles.append(
                self._analyzer.analyze(
                    steps=max(1, int(t * 25)),
                    branching=max(1, int(t * 12)),
                    tools_required=int(t * 10),
                    ambiguity=t,
                    stakes=t,
                )
            )
        return profiles

    def _classify_profiles(self, profiles: list[ComplexityProfile]) -> list[ControlZone]:
        """Classify a batch of profiles and merge into zone descriptions."""
        zone_map: dict[ZoneType, list[float]] = {
            ZoneType.VERIFIED: [],
            ZoneType.UNCERTAIN: [],
            ZoneType.UNCONTROLLABLE: [],
        }

        for p in profiles:
            zone_type = self.classify(p)
            zone_map[zone_type].append(p.overall_score)

        zones: list[ControlZone] = []
        descriptions = {
            ZoneType.VERIFIED: "Human oversight can reliably verify agent behaviour.",
            ZoneType.UNCERTAIN: "Partial verification possible but gaps exist.",
            ZoneType.UNCONTROLLABLE: "Complexity exceeds human oversight capacity.",
        }
        oversight = {
            ZoneType.VERIFIED: ["direct review", "commitment verification", "behavioral hash"],
            ZoneType.UNCERTAIN: ["multi-agent verification", "behavioral hash", "selective audit"],
            ZoneType.UNCONTROLLABLE: ["handoff protocol required", "no reliable method"],
        }

        for zt in ZoneType:
            scores = zone_map.get(zt, [])
            if scores:
                zones.append(
                    ControlZone(
                        zone_type=zt,
                        complexity_range=(round(min(scores), 4), round(max(scores), 4)),
                        description=descriptions.get(zt, ""),
                        oversight_methods=oversight.get(zt, []),
                    )
                )

        return zones

    def _find_boundary(self, profiles: list[ComplexityProfile]) -> float:
        """Find the complexity score at which the verified zone ends."""
        verified_scores = [
            p.overall_score for p in profiles if self.classify(p) == ZoneType.VERIFIED
        ]
        if verified_scores:
            return max(verified_scores)
        return self._verified_ceiling

    @staticmethod
    def _build_summary(zones: list[ControlZone], boundary: float) -> str:
        zone_names = [z.zone_type.value for z in zones]
        return (
            f"Control boundary at complexity score {boundary:.2f}. "
            f"Zones identified: {', '.join(zone_names)}."
        )
