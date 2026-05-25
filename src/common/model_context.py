"""Shared context objects for OPF model assembly and solve workflows."""

from dataclasses import dataclass, field
from typing import Any, Dict


class Namespace:
    """Simple attribute bag to keep backward compatibility with legacy code style.

    This keeps the old `self.data.foo` usage readable while allowing us to
    centralize model lifecycle state in one typed object.
    """

    pass


@dataclass
class ModelContext:
    """Container for the full OPF model state.

    Attributes:
        data: Input and derived network data.
        variables: Gurobi decision variable references.
        constraints: Gurobi constraint references grouped by type.
        results: Structured post-optimization tables and metadata.
        model: Underlying Gurobi model instance.
    """

    data: Namespace = field(default_factory=Namespace)
    variables: Namespace = field(default_factory=Namespace)
    constraints: Namespace = field(default_factory=Namespace)
    results: Namespace = field(default_factory=Namespace)
    model: Any = None

    def as_dict(self) -> Dict[str, Any]:
        """Return a dictionary view useful for debugging and serialization."""
        return {
            'data': self.data,
            'variables': self.variables,
            'constraints': self.constraints,
            'results': self.results,
            'model': self.model,
        }
