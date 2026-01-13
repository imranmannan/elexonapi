import pytest
import pandas as pd
from elexonapi.download import ElexonClient


def test_client_has_datasets():
    client = ElexonClient()
    assert hasattr(client, "datasets")
    assert isinstance(client.datasets, pd.DataFrame)


def test_get_operation_from_alias():
    client = ElexonClient()
    # pick an existing operation from the registry
    op = client.datasets.iloc[0]["operation"]
    # help() returns a dict containing operation equal to op
    h = client.help(op)
    assert h["operation"] == op


def test_validate_params_missing():
    from elexonapi.download import validate_params

    # craft a minimal dataset metadata with required cols
    ds = {"required_cols": ["a", "b"], "optional_cols": ["c"]}
    with pytest.raises(ValueError, match="Missing required parameters"):
        validate_params(ds, {"a": 1})


def test_get_date_chunk_cols():
    from elexonapi.download import get_date_chunk_cols

    # No date keys
    assert get_date_chunk_cols({}) == []
    # explicit from/to
    assert get_date_chunk_cols({"from": "x", "to": "y"}) == ["from", "to"]
    # single date
    assert get_date_chunk_cols({"date": "x"}) == ["date"]


# More tests (e.g., chunking behaviour) would normally mock requests.Session
# Here we check datetime_chunks behaviour


def test_datetime_chunks():
    from elexonapi.download import datetime_chunks
    import pandas as pd

    start = pd.to_datetime("2023-01-01")
    end = pd.to_datetime("2023-01-10")
    chunks = datetime_chunks(start, end, 3)
    assert all(len(c) == 2 for c in chunks)
    # ensure chunks cover the whole range
    assert chunks[0][0] == start
    assert chunks[-1][1] == end
