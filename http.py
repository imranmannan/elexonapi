
import time
import requests

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
            r.raise_for_status()
    last.raise_for_status()
