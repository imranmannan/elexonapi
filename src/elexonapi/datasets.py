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

operation_aliases = datasets[["operation", "name", "code"]].to_records()


def get_operation_from_alias(
    alias: str,
    operation_aliases=operation_aliases,
) -> str:
    for alias_list in operation_aliases:
        if alias in alias_list:
            return alias_list[1]

    raise ValueError(
        (
            "Alias %r not found. Provide the operation id, name, or code. "
            "Run `ElexonClient().datasets` to list datasets, or see the "
            "`elexonapi.datasets.datasets` object for details."
        )
        % (alias,)
    )


def browse(datasets: pd.DataFrame = datasets) -> Any:
    return itables.show(
        datasets,
        classes="display compact",
        columnDefs=[{"className": "dt-left", "targets": "_all"}],
    )


def help(alias: str, datasets: pd.DataFrame = datasets) -> dict[str, Any]:
    operation = get_operation_from_alias(alias)
    ds_raw = datasets[datasets["operation"] == operation].iloc[0].to_dict()
    # Ensure the resulting dict has `str` keys for accurate typing with mypy
    ds: dict[str, Any] = {str(k): v for k, v in ds_raw.items()}
    print(ds["description"])
    return ds
