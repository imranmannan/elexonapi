
import pandas as pd
from pathlib import Path
from .registry import build_registry

DEFAULT_SPEC = Path(__file__).parent / "prod-insol-insights-api.json"

def get_datasets(openapi_path=None):
    path = openapi_path or DEFAULT_SPEC                  
    return  pd.DataFrame(build_registry(path))

datasets = get_datasets()

operation_aliases = datasets[['operation','name','code']].to_records()

def get_operation_from_alias(alias, operation_aliases=operation_aliases):
    for alias_list in operation_aliases:
        if alias in alias_list:
            return alias_list[1]
    
    raise ValueError(f'{alias} not in alias list.')
            

           