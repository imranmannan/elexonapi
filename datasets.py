
import pandas as pd
from pathlib import Path
from .registry import build_registry

DEFAULT_SPEC = Path(__file__).parent / "prod-insol-insights-api.yaml"

def datasets(openapi_path=None):
    path = openapi_path or DEFAULT_SPEC
    return pd.DataFrame(build_registry(path))
