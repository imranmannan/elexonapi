
from .spec import load_openapi, extract_name_and_code, extract_parameters
from .constraints import extract_max_days

def build_registry(openapi_path):
    spec = load_openapi(openapi_path)
    datasets = []

    for path, methods in spec.get("paths", {}).items():
        get = methods.get("get")
        if not get:
            continue

        name, code = extract_name_and_code(get.get("summary", ""))
        required, optional, datetime_cols = extract_parameters(get.get("parameters", []))
        max_days = extract_max_days(get.get("description", ""))

        datasets.append({
            "name": name,
            "code": code,
            "description": get.get("description", ""),
            "path": path,
            "required_cols": required,
            "optional_cols": optional,
            "datetime_cols": datetime_cols,
            "_max_days": max_days,
        })

    return datasets
