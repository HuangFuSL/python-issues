from __future__ import annotations

import operator
import re
from typing import Dict, List, Optional

from . import const

stripper = operator.methodcaller("strip")


def replace_space(o: str) -> str:
    return re.sub("\(.*?\)", "", o).lower().strip().replace(" ", "_")


def url_join(a: str, b: str) -> str:
    if a[-1] == '/' and b[0] in '/#':
        return a[:-1] + b
    elif not (a[-1] == '/' or b[0] in '/#'):
        return a + '/' + b
    else:
        return a + b


def format(o: str) -> str | List[str]:
    try:
        return _format(o, re.findall("(.*?):", o)[0])
    except IndexError:
        return _format(o, "")

def splitAuthor(o: str) -> Dict[str, str]:
    try:
        id, = re.findall("\((.*?)\)", o)
    except ValueError:
        id = ""
    return {
        "author": re.sub("\(.*?\)", "", o).strip(),
        "username": id
    }


def _format(o: str, type_: str) -> str | List[str]:
    if type_ == 'Author':
        o = re.sub("^Author:", "", o)
        o = re.sub("\*", "", o)
    elif type_ == 'Date':
        o = re.sub("^Date:", "", o)
    elif ",\n   " in o:
        return o.split(",\n   ")
    return o.strip()


def extract(*args, post=None, links: Optional[str] = None) -> List[str]:
    ret = []
    for o in args:
        for _ in o:
            if not _.find_all("a") or links is None:
                value = _.get_text().strip()
                value = re.sub(":$", "", value)
                ret.append(value)
            elif isinstance(links, str):
                url = _.find("a")['href']
                if url and 'http' not in url:
                    # Issue 10932 will receive empty urls.
                    url = url_join(links, url)
                ret.append(url)

    ret = map(stripper, ret)
    return list(ret if post is None else map(post, ret))
