"""elexonapi.registry

Utilities to build an internal dataset registry from an OpenAPI spec.

This module inspects the provided OpenAPI JSON and extracts metadata for
available endpoints (name, code, operation id, path, required/optional
parameters, datetime columns and sample responses).
"""

from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any, Dict, List, Optional, Tuple


CODE_RE = re.compile(r"\(([^\[\]]*)\)$")
MAX_DAYS_RE = re.compile(r"maximum data output range of (\d+) days", re.I)


def build_registry(openapi_path: Path | str) -> List[Dict[str, Any]]:
    """Build a list of dataset metadata dictionaries from an OpenAPI JSON file.

    Args:
        openapi_path: Path to an OpenAPI JSON file (string or Path).

    Returns:
        A list of dictionaries where each dict contains metadata for a dataset
        endpoint (name, code, operation, path, required/optional params, etc.).
    """
    spec = load_openapi(openapi_path)
    datasets: List[Dict[str, Any]] = []

    for path, methods in spec.get("paths", {}).items():
        get = methods.get("get")
        if not get:
            # Only consider GET endpoints
            continue

        if "stream" in path:
            # Skip streaming endpoints
            continue

        name, code = extract_name_and_code(get.get("summary", ""))

        # Skip obsolete endpoints
        if "This endpoint is obsolete" in name:
            continue

        path_split = path.split("/")
        category = path_split[1]
        subcategory = path_split[2] if len(path_split) > 2 else None

        required, optional, datetime_cols = extract_parameters(get.get("parameters", []))
        max_days = extract_max_days(get.get("description", ""))

        operation = get.get("operationId", "")

        # If no code found or it's a duplicate, use the operation id to ensure uniqueness
        if not code or code in [d["code"] for d in datasets]:
            code = operation

        # Sanitize code to be a single word (replace commas and whitespace with underscore)
        code = re.sub(r"\s*,\s*", "_", code)

        example_response = extract_response_structure(get.get("responses", {}))
        
        if not isinstance(example_response,str) and len(example_response) > 0 and (isinstance(example_response,dict)) or isinstance(next(iter(example_response), None),dict):
            output_format = 'json or dataframe'        
        else:
            output_format = "json"

        description = get.get("description", "").replace("\n", " ")

        datasets.append({
            "name": name,
            "code": code,
            "operation": operation,
            "category": category,
            "subcategory": subcategory,
            "description": description,
            "path": path,
            "required_cols": required,
            "optional_cols": optional,
            "datetime_cols": datetime_cols,
            "max_days_data_limit_in_raw_query": max_days,
            "example_response": example_response,
            "output_format": output_format,
        })

    return datasets


def extract_max_days(description: Optional[str]) -> Optional[int]:
    """Extract maximum days mentioned in a description string.

    Returns the integer number of days if mentioned (e.g. "maximum data output range of 7 days"),
    otherwise returns None.
    """
    if not description:
        return None

    m = MAX_DAYS_RE.search(description)
    return int(m.group(1)) if m else None


def load_openapi(path: Path | str) -> Dict[str, Any]:
    """Load and parse the OpenAPI JSON file from disk."""
    with open(path, "r") as f:
        return json.load(f)


def extract_name_and_code(summary: Optional[str]) -> Tuple[str, Optional[str]]:
    """Extract a user-friendly name and code from an OpenAPI summary.

    The code is expected to be in parentheses at the end of the summary. If no
    code is present the returned code is None.
    """
    match = CODE_RE.search(summary or "")
    code = match.group(1) if match else None
    name = summary.replace(f"({code})", "").strip() if code else (summary or "")
    return name, code


def extract_parameters(params: List[Dict[str, Any]]) -> Tuple[List[str], List[str], List[str]]:
    """Extract required, optional and datetime parameter names from OpenAPI param list."""
    required: List[str] = []
    optional: List[str] = []
    datetime_cols: List[str] = []

    for p in params:
        name = p["name"]
        schema = p.get("schema", {})
        if schema.get("format") in {"date", "date-time"}:
            datetime_cols.append(name)
        if p.get("required", False):
            required.append(name)
        else:
            optional.append(name)

    return required, optional, datetime_cols


def extract_response_structure(responses: Dict[str, Any]) -> Any:
    """Return an example response structure for the 200 response if available.

    If a response example has a `data` key, that data is returned, otherwise the
    raw example is returned. If no example exists an empty object is returned.
    """
    example = responses.get("200", {}).get("content", {}).get("application/json", {}).get("example", {})

    if isinstance(example, dict):
        return example.get("data", example)

    return example
