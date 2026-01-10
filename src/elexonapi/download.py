"""elexonapi.download

Provide a lightweight `ElexonClient` class that encapsulates a
`requests.Session` and exposes `download(...)` alongside convenience
accessors for `datasets`, `help` and `browse`.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

import json
import time

import pandas as pd
import requests
from typing import Any as _Any

from .datasets import (
    datasets as _default_datasets,
    get_operation_from_alias,
    browse as browse_fn,
    help as help_fn,
)

# Import tqdm dynamically via importlib so the type is not inferred as
# two different concrete types (``tqdm`` vs ``tqdm.notebook``) during
# static analysis.
from importlib import import_module

try:
    _mod = import_module("tqdm.notebook")
    _tqdm = getattr(_mod, "tqdm")
except Exception:
    _mod = import_module("tqdm")
    _tqdm = getattr(_mod, "tqdm")

# Expose a single name and avoid a strict type for mypy
tqdm: _Any = _tqdm


BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"


class ElexonClient:
    def __init__(
        self,
        base_url: str = BASE_URL,
        session: Optional[requests.Session] = None,
        datasets: Optional[pd.DataFrame] = None,
    ) -> None:
        self.base_url = base_url
        self.session = session or requests.Session()
        self._datasets = (
            datasets if datasets is not None else _default_datasets
        )

    @property
    def datasets(self) -> pd.DataFrame:
        return self._datasets

    def browse(self) -> Any:
        return browse_fn(datasets=self._datasets)

    def help(self, alias: str) -> dict:
        return help_fn(alias, datasets=self._datasets)

    def _resolve_operation(self, alias: str) -> str:
        operation_aliases = self._datasets[
            ["operation", "name", "code"]
        ].to_records()
        return get_operation_from_alias(
            alias, operation_aliases=operation_aliases
        )

    def download(
        self,
        alias: str,
        *,
        progress: bool = True,
        format: str = "df",
        date_chunk_cols: Optional[List[str]] = None,
        **params: Any,
    ) -> Any:
        if format not in ("df", "json"):
            raise ValueError('format must be "df" or "json"')

        operation = self._resolve_operation(alias)
        ds_raw = (
            self._datasets[self._datasets["operation"] == operation]
            .iloc[0]
            .to_dict()
        )
        # Ensure dict keys are `str` for mypy compatibility
        ds: dict[str, Any] = {str(k): v for k, v in ds_raw.items()}

        if "_from" in params:
            params = {**{"from": params.pop("_from")}, **params}

        validate_params(ds, params)

        url = self.base_url + ds["path"]

        output_format = ds.get("output_format", "")
        if format == "df" and "dataframe" not in output_format:
            raise ValueError(
                'This dataset does not support format="df". '
                'Use format="json" to retrieve the raw data.'
            )

        dt_cols = get_date_chunk_cols(params, date_chunk_cols)
        max_day_chunksize = ds.get("_max_days", 1)
        results: List[Dict[str, Any]] = []

        if not dt_cols:
            r = request_with_retry(self.session, url, params)
            return return_response(r, format)

        if len(dt_cols) == 2:

            def fetch(p: Dict[str, Any]) -> List[Dict[str, Any]]:
                r = request_with_retry(self.session, url, p)
                return json.loads(r.content)["data"]

            from_col, to_col = dt_cols
            start = pd.to_datetime(params[from_col])
            end = pd.to_datetime(params[to_col])

            chunks = datetime_chunks(start, end, max_day_chunksize)
            for c_start, c_end in maybe_tqdm(chunks, enabled=progress):
                p = params.copy()
                if "time" in from_col.lower():
                    p[from_col] = c_start.isoformat()
                    p[to_col] = c_end.isoformat()
                else:
                    p[from_col] = c_start.strftime("%Y-%m-%d")
                    p[to_col] = c_end.strftime("%Y-%m-%d")
                results.extend(fetch(p))

            return pd.DataFrame(results) if format == "df" else results

        if len(dt_cols) == 1:
            dt_col = dt_cols[0]

            def fetch(p: Dict[str, Any]) -> List[Dict[str, Any]]:
                r = request_with_retry(self.session, url, p)
                return json.loads(r.content)["data"]

            dt_range = params[dt_col]

            for dt_value in maybe_tqdm(dt_range, enabled=progress):
                p = params.copy()
                if "time" in dt_col.lower():
                    p[dt_col] = dt_value.isoformat()
                else:
                    p[dt_col] = dt_value.strftime("%Y-%m-%d")
                results.extend(fetch(p))

            return pd.DataFrame(results) if format == "df" else results


def validate_params(dataset: Dict[str, Any], params: Dict[str, Any]) -> None:
    allowed = set(dataset["required_cols"] + dataset["optional_cols"])
    missing = set(dataset["required_cols"]) - set(params)
    extra = set(params) - allowed

    if missing:
        raise ValueError(f"Missing required parameters: {sorted(missing)}")
    if extra:
        raise ValueError(
            ("Unknown parameters: %r. Allowed inputs are: %r")
            % (sorted(extra), sorted(allowed))
        )


def request_with_retry(
    session: requests.Session,
    url: str,
    params: Dict[str, Any],
    retries: int = 5,
) -> requests.Response:
    last: Optional[requests.Response] = None

    for i in range(retries):
        if "{" in url and "}" in url:
            session_url = url.replace("{", "").replace("}", "")
            for k, v in params.items():
                session_url = session_url.replace(k, str(v))
            r = session.get(session_url)
        else:
            r = session.get(url, params=params)

        if r.status_code < 400:
            return r

        if r.status_code in (429, 500, 502, 503):
            last = r
            time.sleep(i + 1)
        else:
            try:
                error_payload = json.loads(r.content)
            except Exception:
                error_payload = r.text
            raise ValueError(
                {
                    "url": url,
                    "params": params,
                    "error": error_payload,
                }
            )

    if last is not None:
        last.raise_for_status()

    raise RuntimeError("request failed after retries")


def split_list_param(values: List[Any], max_len: int) -> Iterable[List[Any]]:
    for i in range(0, len(values), max_len):
        yield values[i: i + max_len]


def datetime_chunks(
    start: pd.Timestamp,
    end: pd.Timestamp,
    max_days: Optional[int],
) -> List[Tuple[pd.Timestamp, pd.Timestamp]]:
    if max_days is None:
        return [(start, end)]

    chunks: List[Tuple[pd.Timestamp, pd.Timestamp]] = []
    cur = pd.to_datetime(start)
    end = pd.to_datetime(end)

    while cur < end:
        nxt = min(cur + pd.Timedelta(days=max_days), end)
        chunks.append((cur, nxt))
        cur = nxt

    return chunks


def get_date_chunk_cols(
    params: Dict[str, Any],
    date_chunk_cols: Optional[List[str]] = None,
) -> List[str]:
    if date_chunk_cols:
        return date_chunk_cols

    keys = list(params.keys())
    from_cols = [k for k in keys if k.lower().endswith("from")]
    to_cols = [k for k in keys if k.lower().endswith("to")]
    date_cols = [k for k in keys if k.lower().endswith("date")]
    time_cols = [k for k in keys if k.lower().endswith("time")]

    if len(from_cols) + len(to_cols) + len(date_cols) + len(time_cols) == 0:
        return []

    if len(from_cols) == 1 and len(to_cols) == 1:
        return [from_cols[0], to_cols[0]]

    if len(date_cols) == 1 and len(time_cols) == 0:
        return [date_cols[0]]

    if len(time_cols) == 1 and len(date_cols) == 0:
        return [time_cols[0]]

    raise ValueError(
        (
            "Multiple possible datetime columns to chunk on: "
            f"from={from_cols}, to={to_cols}, "
            f"date={date_cols}, time={time_cols}. "
            "Please specify date_chunk_cols=[...] explicitly."
        )
    )


def maybe_tqdm(
    iterable: Iterable[Any],
    enabled: bool = True,
    **kwargs: Any,
) -> Iterable[Any]:
    if not enabled:
        return iterable
    return tqdm(iterable, **kwargs)


def load_func_table(response: requests.Response) -> List[Dict[str, Any]]:
    return json.loads(response.content)["data"]


def load_func_array(response: requests.Response) -> List[Dict[str, Any]]:
    return json.loads(response.content)["data"]


def return_response(response: requests.Response, format: str) -> Any:
    if format not in ("df", "json"):
        raise ValueError('format must be "df" or "json"')

    json_response = json.loads(response.content)

    if format == "df":
        return pd.DataFrame(json_response.get("data", json_response))

    if isinstance(json_response, dict):
        return json_response.get("data", json_response)

    return json_response
