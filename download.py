import requests
from .datasets import datasets, get_operation_from_alias
import json
import time
import pandas as pd
import sys

if 'ipykernel' in sys.modules:
    from tqdm.notebook import tqdm
else:
    from tqdm import tqdm




BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

def download(
    alias,
    progress=True,
    format="df",
    datasets=datasets,
    date_chunk_cols=None,
    **params,
):
    assert format in ('df','json'),'format must be one of: format="df" or format="json"'

    operation = get_operation_from_alias(alias)
    ds = datasets[datasets["operation"] == operation].iloc[0].to_dict()

    if "_from" in params:
        params = {**{'from':params.pop("_from")},**params}
    validate_params(ds, params)

    session = requests.Session()
    url = BASE_URL + ds["path"]

    output_format = ds.get('output_format',{})
    if format == 'df' and 'dataframe' not in output_format:
        raise ValueError('Please pass in format="json" to .download() function to download this data - format="df" not available.')

    # ---------- detect date chunking ----------
    dt_cols = get_date_chunk_cols(params, date_chunk_cols)

    max_day_chunksize = ds.get("_max_days",1)
    results = []

    # ---------- no date chunking ----------
    if not dt_cols:
        r = request_with_retry(session, url, params)
        return return_response(r, format)

    # ---------- compute chunks for queries with a to and from pair of params ----------
    elif len(dt_cols) == 2:

        def fetch(p):
            r = request_with_retry(session, url, p)
            return json.loads(r.content)["data"]
        
        from_col, to_col = dt_cols
        start = pd.to_datetime(params[from_col])
        end = pd.to_datetime(params[to_col])

        chunks = datetime_chunks(start, end, max_day_chunksize)
        for c_start, c_end in maybe_tqdm(chunks, enabled=progress):
            p = params.copy()
            if 'time' in from_col.lower():
                p[from_col] = c_start.isoformat()
                p[to_col] = c_end.isoformat()
            else:
                p[from_col] = c_start.strftime('%Y-%m-%d')
                p[to_col] = c_end.strftime('%Y-%m-%d')
            results.extend(fetch(p))

        return pd.DataFrame(results) if format == 'df' else results

    # ---------- compute chunks for queries with a Date or Time param ----------
    elif len(dt_cols) == 1:
        dt_col = dt_cols[0]
        def fetch(p):
            r = request_with_retry(session, url, p)
            return json.loads(r.content)["data"]
        
        dt_range = params[dt_col]

        for dt_value in maybe_tqdm(dt_range, enabled=progress):
            p = params.copy()
            if 'time' in dt_col.lower():
                p[dt_col] = dt_value.isoformat()
            else:
                p[dt_col] = dt_value.strftime('%Y-%m-%d')
            results.extend(fetch(p))

        return pd.DataFrame(results) if format == 'df' else results
            




    


def validate_params(dataset, params):
    allowed = set(dataset["required_cols"] + dataset["optional_cols"])
    missing = set(dataset["required_cols"]) - set(params)
    extra = set(params) - allowed

    if missing:
        raise ValueError(f"Missing required parameters: {missing}")
    if extra:
        raise ValueError(f"Unknown parameters: {extra}, not in allowed inputs {allowed}")


def request_with_retry(session, url, params, retries=5):
    last = None
    for i in range(retries):
        if '{' in url:
             session_url = url.replace('{','').replace('}','')
             for k,v in params.items():
                session_url = session_url.replace(k,v)
                r = session.get(session_url)

        else:
            r = session.get(url, params=params)
        if r.status_code < 400:
            return r
        if r.status_code in (429, 500, 502, 503):
            last = r
            time.sleep(i + 1)
        else:
            print('url:',url)
            print('params:',params)
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

def get_date_chunk_cols(params, date_chunk_cols=None) -> list[str]:
    """
    Returns a list of column names to use for date chunking.
    Length:
      - 2 → [from_col, to_col]
    """

    if date_chunk_cols:
        return date_chunk_cols

    keys = list(params.keys())

    from_cols = [k for k in keys if k.lower().endswith("from")]
    to_cols   = [k for k in keys if k.lower().endswith("to")]
    date_cols   = [k for k in keys if k.lower().endswith("date")]
    time_cols   = [k for k in keys if k.lower().endswith("time")]


    # Prefer explicit from/to pairs
    if len(from_cols) + len(to_cols) + len(date_cols) + len(time_cols) == 0:
        return []

    # Prefer explicit from/to pairs
    if len(from_cols) == 1 and len(to_cols) == 1:
        return [from_cols[0], to_cols[0]]

    if len(date_cols) == 1 and len(time_cols) == 0:
        return [date_cols[0]]
    
    if len(time_cols) == 1 and len(date_cols) == 0:
        return [time_cols[0]]

    else:
        raise ValueError(
            f"Multiple possible datetime columns to chunk on: "
            f"from={from_cols}, to={to_cols},  date={date_cols}, time={time_cols}, "
            "Please specify date_chunk_cols=[...] explicitly."
        )
    


def maybe_tqdm(iterable, enabled=True, **kwargs):
    if not enabled:
        return iterable
    else:
        return tqdm(iterable, **kwargs)
    
def load_func_table(response):
    return json.loads(r.content)["data"]

def load_func_array(response):
    return json.loads(r.content)["data"]

def return_response(response, format):

    assert format in ('df','json'),'format must be one of: format="df" or format="json"'

    json_response = json.loads(response.content)

    if format == 'df':
        return pd.DataFrame(json_response.get('data', json_response))
    
    # check if a dict
    elif isinstance(json_response, dict):
        return json_response.get('data', json_response)

    # anything else, return the straight json
    else:
        return json_response