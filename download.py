
import requests
from .datasets import datasets
from .validation import validate_params
from .http import request_with_retry
from .looping import split_list_param

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

def download(code, progress=True, **params):
    df = datasets()
    ds = df[df["code"] == code].iloc[0].to_dict()

    validate_params(ds, params)

    session = requests.Session()
    url = BASE_URL + ds["path"]

    # Handle row-limit via list splitting (e.g. bmUnit)
    for k, v in params.items():
        if isinstance(v, list) and len(v) > 10:
            results = []
            for sub in split_list_param(v, 10):
                p = params.copy()
                p[k] = sub
                r = request_with_retry(session, url, p)
                results.append(r.text)
            return results

    r = request_with_retry(session, url, params)
    return r.text
