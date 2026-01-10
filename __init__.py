
"""elexonapi

Top-level package exports and convenience behaviour.
"""

from __future__ import annotations

from .datasets import datasets, browse, help
from .download import ElexonClient

# Emit a mild user-facing warning (not a print) to make `_from` usage clear
import warnings
warnings.warn("elexonapi: Use `_from` instead of the Python reserved word `from` when supplying date ranges.", stacklevel=2)

__all__ = ["datasets", "browse", "help", "ElexonClient"]
