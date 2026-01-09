
import requests
from .datasets import datasets, get_operation_from_alias
import json
import time
import pandas as pd

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

def download(alias, progress=True, format='df', datasets=datasets, **params):
        
    operation = get_operation_from_alias(alias)
    ds = datasets[datasets["operation"] == operation].iloc[0].to_dict()

    if "_from" in params:
        params['from'] = params.pop('_from')

                             
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

    if format == 'json':
        try:
            return json.loads(r.text['data'])
        
        except Exception as e:

            return json.loads(r.content)
            
    
    elif format == 'df':
        try:
            return pd.DataFrame(json.loads(r.text)['data'])
        
        except Exception as e:
            raise ValueError("Unable to download dataframe - try to download with format='json' instead. Error: " + str(e))




    


def validate_params(dataset, params):
    allowed = set(dataset["required_cols"] + dataset["optional_cols"])
    missing = set(dataset["required_cols"]) - set(params)
    extra = set(params) - allowed

    if missing:
        raise ValueError(f"Missing required parameters: {missing}")
    if extra:
        raise ValueError(f"Unknown parameters: {extra}, not in allowed columns {allowed}")


def request_with_retry(session, url, params, retries=5):
    last = None
    for i in range(retries):
        r = session.get(url, params=params)
        if r.status_code < 400:
            return r
        if r.status_code in (429, 500, 502, 503):
            last = r
            time.sleep(i + 1)
        else:
            raise ValueError(json.loads(r.content))
    last.raise_for_status()

def split_list_param(values, max_len):
    for i in range(0, len(values), max_len):
        yield values[i:i+max_len]

def datetime_chunks(start, end, max_days):
    if max_days is None:
        return [(start, end)]

    chunks = []
    cur = pd.to_datetime(start)
    end = pd.to_datetime(end)

    while cur < end:
        nxt = min(cur + pd.Timedelta(days=max_days), end)
        chunks.append((cur, nxt))
        cur = nxt

    return chunks
