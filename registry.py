import json
import re

CODE_RE = re.compile(r'\(([^\[\]]*)\)$')
MAX_DAYS_RE = re.compile(r"maximum data output range of (\d+) days", re.I)

def build_registry(openapi_path):
    spec = load_openapi(openapi_path)
    datasets = []

    for path, methods in spec.get("paths", {}).items():
        get = methods.get("get")
        if not get:
            continue

        if 'stream' in path:
            continue
        
        name, code = extract_name_and_code(get.get("summary", ""))

        # if 'This endpoint is obsolete'  or 'This endpoint has been moved' in name:
        if 'This endpoint is obsolete' in name:
            continue
        
        path_split = path.split('/')
        category = path_split[1]
        subcategory = path_split[2] if len(path_split) > 2 else None

        required, optional, datetime_cols = extract_parameters(get.get("parameters", []))
        max_days = extract_max_days(get.get("description", ""))

        operation = get.get("operationId", "")


        if not code or code in [d['code'] for d in datasets]:
            code = operation

        # replace (whitespace)commas(whitespace) with underscores in code to make into one word
        code = re.sub(r"\s*,\s*", '_', code)


        example_response = extract_response_structure(get.get("responses", {}))
        
        if not isinstance(example_response,str) and len(example_response) > 0 and (isinstance(example_response,dict)) or isinstance(next(iter(example_response), None),dict):
            output_format = 'json or dataframe'        
        else:
            output_format = 'json'
        



        datasets.append({
            "name": name,
            "code": code,
            'operation': operation,
            "category": category,
            "subcategory": subcategory,
            "description": get.get("description", ""),
            "path": path,
            "required_cols": required,
            "optional_cols": optional,
            "datetime_cols": datetime_cols,
            "max_days_data_limit_in_raw_query": max_days,
            "example_response": example_response,
            "output_format":output_format,

        })

    return datasets


def extract_max_days(description):
    if not description:
        return None
    m = MAX_DAYS_RE.search(description)
    return int(m.group(1)) if m else None

def load_openapi(path):
    with open(path, "r") as f:
        return json.load(f)

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

def extract_response_structure(responses) -> dict:
    example = responses.get("200",{}).get('content',{}).get('application/json',{}).get('example',{})
    
    if isinstance(example, dict):
        return example.get('data', example)
    
    else:
        return example
