"""elexonapi

Top-level package exports and convenience behaviour for the installed package.
"""

from __future__ import annotations

from .datasets import datasets, browse, help
from .download import ElexonClient

import warnings
warnings.warn("elexonapi: Use `_from` instead of the Python reserved word `from` when supplying date ranges.", stacklevel=2)

__version__ = "0.1.2"
__all__ = ["datasets", "browse", "help", "ElexonClient", "__version__"]