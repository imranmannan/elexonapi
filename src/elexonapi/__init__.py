"""elexonapi

Top-level package exports and convenience behaviour for the installed package.
"""

from __future__ import annotations

from .datasets import datasets, browse, help
from .download import ElexonClient

import warnings

_warn_msg = (
    "elexonapi: Use `_from` instead of the Python reserved word "
    "`from` when supplying date ranges."
)
warnings.warn(_warn_msg, stacklevel=2)

__version__ = "0.1.3"
__all__ = ["datasets", "browse", "help", "ElexonClient", "__version__"]
