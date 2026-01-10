"""elexonapi.registry

Utilities to build an internal dataset registry from an OpenAPI spec.
"""

from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any, Dict, List, Optional, Tuple


CODE_RE = re.compile(r"\(([^\[\]]*)\)$")
MAX_DAYS_RE = re.compile(r"maximum data output range of (\d+) days", re.I)


def build_registry(openapi_path: Path | str) -> List[Dict[str, Any]]:
    spec = load_openapi(openapi_path)
    datasets: List[Dict[str, Any]] = []

    for path, methods in spec.get("paths", {}).items():
        get = methods.get("get")
        if not get:
            continue

        if "stream" in path:
            continue

        name, code = extract_name_and_code(get.get("summary", ""))

        if "This endpoint is obsolete" in name:
            continue

        path_split = path.split("/")
        category = path_split[1]
        subcategory = path_split[2] if len(path_split) > 2 else None

        required, optional, datetime_cols = extract_parameters(get.get("parameters", []))
        max_days = extract_max_days(get.get("description", ""))

        operation = get.get("operationId", "")

        if not code or code in [d["code"] for d in datasets]:
            code = operation

        code = re.sub(r"\s*,\s*", "_", code)

        example_response = extract_response_structure(get.get("responses", {}))

        if isinstance(example_response, dict):
            output_format = "json or dataframe"
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
    if not description:
        return None

    m = MAX_DAYS_RE.search(description)
    return int(m.group(1)) if m else None


def load_openapi(path: Path | str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


def extract_name_and_code(summary: Optional[str]) -> Tuple[str, Optional[str]]:
    match = CODE_RE.search(summary or "")
    code = match.group(1) if match else None
    name = summary.replace(f"({code})", "").strip() if code else (summary or "")
    return name, code


def extract_parameters(params: List[Dict[str, Any]]) -> Tuple[List[str], List[str], List[str]]:
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
    example = responses.get("200", {}).get("content", {}).get("application/json", {}).get("example", {})

    if isinstance(example, dict):
        return example.get("data", example)

    return example
