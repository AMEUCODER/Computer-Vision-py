"""Small, dependency-free parameter specification for image tools."""
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence


@dataclass(frozen=True)
class ParamSpec:
    name: str
    label: str
    kind: str
    default: Any
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    choices: Sequence[str] = field(default_factory=tuple)
    help: str = ""

    def __post_init__(self):
        if self.kind not in {"slider", "choice", "bool"}:
            raise ValueError(f"Unsupported parameter type: {self.kind}")
        if self.kind == "choice" and self.choices and self.default not in self.choices:
            raise ValueError(f"Default for {self.name!r} must be one of {self.choices!r}")
