"""elexonapi.datasets

User-facing helpers to inspect and query the in-package dataset registry.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import itables

from .registry import build_registry

DEFAULT_SPEC = Path(__file__).parent / "prod-insol-insights-api.json"

def get_datasets(openapi_path: Path | str | None = None) -> pd.DataFrame:
    """Return the registry as a pandas DataFrame.

    The optional ``openapi_path`` allows loading a different spec for tests.
    """

    path = openapi_path or DEFAULT_SPEC
    return pd.DataFrame(build_registry(path))

datasets: pd.DataFrame = get_datasets()

# Simple record array of (index, operation, name, code) for alias resolution
operation_aliases = datasets[["operation", "name", "code"]].to_records()

def get_operation_from_alias(
    alias: str,
    operation_aliases=operation_aliases,
) -> str:
    """Resolve an alias to the canonical `operation` identifier.

    The alias can be any of the `operation`, `name` or `code` fields. If the
    alias is not found a `ValueError` is raised describing the problem.
    """
    for alias_list in operation_aliases:
        # `alias_list` is a record where fields are:
        # (index, operation, name, code)
        if alias in alias_list:
            # operation is the second item in the record (index is first)
            return alias_list[1]

    raise ValueError(
        (
            "Alias %r not found. Provide the operation id, name, or code. "
            "Run `ElexonClient().datasets` to list datasets, or see the "
            "`elexonapi.datasets.datasets` object for details."
        ) % (alias,)
    )


def browse(datasets: pd.DataFrame = datasets) -> Any:
    """Display an interactive table of datasets using `itables`.

    Intended for use inside Jupyter notebooks to quickly inspect available
    datasets and their required parameters.
    """

    return itables.show(
        datasets,
        classes="display compact",
        columnDefs=[{"className": "dt-left", "targets": "_all"}],
    )


def help(alias: str, datasets: pd.DataFrame = datasets) -> dict[str, Any]:
    """Print and return the metadata dictionary for a dataset alias.

    Returns the same dictionary stored inside the registry produced by
    `build_registry`.
    """
    operation = get_operation_from_alias(alias)
    ds = datasets[datasets["operation"] == operation].iloc[0].to_dict()
    print(ds["description"])
    return ds