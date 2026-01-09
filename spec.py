
import yaml
import re

CODE_RE = re.compile(r"\(([^)]+)\)$")

def load_openapi(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def extract_name_and_code(summary):
    match = CODE_RE.search(summary or "")
    code = match.group(1) if match else None
    name = summary.replace(f"({code})", "").strip() if code else summary
    return name, code

def extract_parameters(params):
    required, optional, datetime_cols = [], [], []
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
