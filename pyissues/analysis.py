from __future__ import annotations

import time
from typing import Dict, List

from pyissues import base, const

_TIME_UNITS = {
    'year': "%Y",
    'month': "%Y-%m",
    'day': "%Y-%m-%d",
    'hour': "%Y-%m-%d %H:00:00",
    'minute': "%Y-%m-%d %H:%M:00",
}
_TIME_FIELDS = ['created', 'last_changed']

def make_table(
    o: List[base.Issue], *, time_unit: str = 'month'
) -> Dict[str, List]:
    if time_unit not in _TIME_UNITS:
        raise ValueError("Time unit should be " + ", ".join(_TIME_UNITS))

    ret: Dict[str, List] = {}

    for field in const._ISSUE_ATTRIBUTES:
        new_field = []
        for _ in o:
            val = getattr(_, field)
            if val:
                new_field.append(val)
            else:
                new_field.append(None)
        ret[field] = new_field
    for field in const._ISSUE_MULTIPLE_ATTRIBUTES:
        new_field = []
        for _ in o:
            val = getattr(_, field)
            if val:
                new_field.append(frozenset(val))
            else:
                new_field.append(None)
        ret[field] = new_field

    for field in _TIME_FIELDS:
        new_field = []
        for _ in ret[field]:
            try:
                new_field.append(time.strftime(
                    _TIME_UNITS[time_unit],
                    time.strptime(_, "%Y-%m-%d %H:%M")
                ))
            except TypeError:
                new_field.append(None)
        ret[field] = new_field

    return ret

def collect_comments(o: List[base.Issue]):
    ret = {}
    for issue in o:
        ret[int(issue._id)] = [str(_) for _ in issue.messages]
    
    return ret
