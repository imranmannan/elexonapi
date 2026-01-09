
import re

MAX_DAYS_RE = re.compile(r"(maximum|max)\s+(\d+)\s+day", re.I)

def extract_max_days(description):
    if not description:
        return None
    m = MAX_DAYS_RE.search(description)
    return int(m.group(2)) if m else None
