"""Report generation — renders Zion audit results using Rich."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from zion.models import (
    ControlMap,
    DeceptionReport,
    RedTeamReport,
    ZionAuditReport,
    ZoneType,
)


class ReportGenerator:
    """Renders Zion audit reports to the terminal using Rich."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()

    def render(self, report: ZionAuditReport) -> None:
        """Render a full audit report."""
        self._render_header(report)

        if report.control_map:
            self._render_control_map(report.control_map)

        if report.deception_report:
            self._render_deception(report.deception_report)

        if report.red_team_report:
            self._render_red_team(report.red_team_report)

        self._render_summary(report)

    # ------------------------------------------------------------------
    # Section renderers
    # ------------------------------------------------------------------

    def _render_header(self, report: ZionAuditReport) -> None:
        header = Text()
        header.append("ZION AUDIT REPORT\n", style="bold white on blue")
        header.append(f"Agent: {report.agent_id}\n", style="bold")
        header.append(
            f"Protocols tested: {', '.join(report.protocols_tested)}\n"
        )
        header.append(f"Generated: {report.generated_at:%Y-%m-%d %H:%M UTC}")

        self._console.print(Panel(header, title="[bold]Zion[/bold]", border_style="blue"))

    def _render_control_map(self, cmap: ControlMap) -> None:
        table = Table(title="Control Boundary Map", border_style="cyan")
        table.add_column("Zone", style="bold")
        table.add_column("Complexity Range")
        table.add_column("Oversight Methods")
        table.add_column("Description")

        zone_styles = {
            ZoneType.VERIFIED: "green",
            ZoneType.UNCERTAIN: "yellow",
            ZoneType.UNCONTROLLABLE: "red",
        }

        for zone in cmap.zones:
            style = zone_styles.get(zone.zone_type, "white")
            table.add_row(
                Text(zone.zone_type.value.upper(), style=style),
                f"{zone.complexity_range[0]:.2f} - {zone.complexity_range[1]:.2f}",
                ", ".join(zone.oversight_methods),
                zone.description,
            )

        self._console.print(table)
        self._console.print(
            f"  Boundary threshold: [bold]{cmap.boundary_threshold:.2f}[/bold]\n"
        )

    def _render_deception(self, report: DeceptionReport) -> None:
        style = "red" if report.is_deceptive else "green"
        status = "DECEPTIVE" if report.is_deceptive else "CLEAN"

        panel_content = Text()
        panel_content.append(f"Status: {status}\n", style=f"bold {style}")
        panel_content.append(f"Score: {report.deception_score:.2f}\n")

        if report.detected_patterns:
            panel_content.append("Patterns: ")
            panel_content.append(
                ", ".join(p.value for p in report.detected_patterns) + "\n",
                style="yellow",
            )

        for item in report.evidence[:5]:
            panel_content.append(f"  - {item}\n", style="dim")

        self._console.print(
            Panel(panel_content, title="Deception Detection", border_style=style)
        )

    def _render_red_team(self, report: RedTeamReport) -> None:
        table = Table(title="Red Team Results", border_style="magenta")
        table.add_column("Metric", style="bold")
        table.add_column("Value")

        table.add_row("Total Rounds", str(report.total_rounds))
        table.add_row("Deviations", str(report.deviations))
        table.add_row(
            "Robustness",
            Text(
                f"{report.robustness_score:.1%}",
                style="green" if report.robustness_score > 0.9 else "red",
            ),
        )

        if report.attack_breakdown:
            for attack, count in report.attack_breakdown.items():
                table.add_row(f"  {attack}", str(count))

        self._console.print(table)

    def _render_summary(self, report: ZionAuditReport) -> None:
        risk_styles = {
            "low": "green",
            "medium": "yellow",
            "high": "red",
            "critical": "bold white on red",
        }
        style = risk_styles.get(report.overall_risk.value, "white")

        summary = Text()
        summary.append("Overall Risk: ", style="bold")
        summary.append(report.overall_risk.value.upper() + "\n", style=style)

        if report.recommendations:
            summary.append("\nRecommendations:\n", style="bold")
            for rec in report.recommendations:
                summary.append(f"  -> {rec}\n")

        self._console.print(
            Panel(summary, title="Summary", border_style="blue")
        )
