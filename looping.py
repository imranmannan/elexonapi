
import pandas as pd

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
