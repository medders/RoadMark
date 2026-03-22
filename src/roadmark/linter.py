"""Roadmap quality linter."""

from dataclasses import dataclass, field
from enum import StrEnum

from roadmark.models import Roadmap


class Severity(StrEnum):
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Issue:
    severity: Severity
    location: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.location}: {self.message}"


@dataclass
class LintResult:
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def lint(roadmap: Roadmap) -> LintResult:
    """Run all lint checks against *roadmap* and return a LintResult."""
    result = LintResult()
    _check_parse_warnings(roadmap, result)
    _check_columns(roadmap, result)
    _check_themes(roadmap, result)
    return result


def _check_parse_warnings(roadmap: Roadmap, result: LintResult) -> None:
    for warning in roadmap.parse_warnings:
        # Warnings are formatted as "location: message"
        location, _, message = warning.partition(": ")
        result.issues.append(Issue(Severity.WARNING, location, message))


def _check_columns(roadmap: Roadmap, result: LintResult) -> None:
    column_names = {c.name.lower() for c in roadmap.columns}

    for expected in ("now", "next", "later"):
        if expected not in column_names:
            result.issues.append(
                Issue(
                    Severity.ERROR,
                    "roadmap",
                    f"Missing required column: {expected!r}",
                )
            )

    for column in roadmap.columns:
        if not column.themes:
            result.issues.append(
                Issue(
                    Severity.WARNING,
                    f"column '{column.name}'",
                    "Column is empty",
                )
            )


def _check_themes(roadmap: Roadmap, result: LintResult) -> None:
    for column in roadmap.columns:
        for theme in column.themes:
            loc = f"column '{column.name}' > theme '{theme.name}'"

            if not theme.objectives and not theme.summary:
                result.issues.append(
                    Issue(
                        Severity.WARNING,
                        loc,
                        "Theme has no objectives or summary — add at least one",
                    )
                )

            if theme.status is None:
                result.issues.append(
                    Issue(
                        Severity.WARNING,
                        loc,
                        "Missing status field (planned/in-progress/blocked/in-review)",
                    )
                )

            if theme.status == "blocked":
                if not theme.objectives and not theme.summary:
                    result.issues.append(
                        Issue(
                            Severity.WARNING,
                            loc,
                            "Blocked theme has no explanation"
                            " — add a summary or objectives",
                        )
                    )

            if column.name.lower() in ("now", "next") and theme.confidence is None:
                result.issues.append(
                    Issue(
                        Severity.WARNING,
                        loc,
                        "Theme is missing a confidence level",
                    )
                )
