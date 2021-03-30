from __future__ import annotations

import gzip
import io
import time
import lxml.etree
from typing import Iterable, Iterable, Mapping
from collections import abc

from . import base, const


def MappingIterWrapper(o: Mapping):
    for _ in o:
        yield o[_]


def domdump(o: Iterable[base.Issue]):
    ret_dom = lxml.etree.Element(
        "issues",
        items=str(len(o)), last_fetched=str(time.time())
    )
    issues_iter = MappingIterWrapper(o) if isinstance(o, Mapping) else o
    for issue in issues_iter:
        ret_dom.append(issue.dump())
    return ret_dom


def xmldump(o: Iterable[base.Issue], fp: io.IOBase | str) -> None:
    ret = domdump(o)
    data = lxml.etree.tostring(ret)
    if isinstance(fp, io.IOBase):
        fp.write(data)
    elif isinstance(fp, str):
        with open(fp, "w", encoding="utf-8") as file:
            file.write(data)


def xmldumpCompressed(o: Iterable[base.Issue], fp: io.IOBase | str, **kwargs) -> None:
    ret = domdump(o)
    data = gzip.compress(
        lxml.etree.tostring(ret),
        **kwargs
    )
    if isinstance(fp, io.IOBase):
        fp.write(data)
        fp.flush()
    elif isinstance(fp, str):
        with open(fp, "wb") as file:
            file.write(data)


def xmldumps(o: Iterable) -> str:
    return domdump(o).toxml()


def domload(dom, container: type = list) -> Iterable[base.Issue]:
    if dom.get('last_fetched') is not None:
        print("This content was saved at %s (local)." % (
            time.strftime(const._TIME_UNITS['second'], time.localtime(
                float(dom.get('last_fetched'))
            )),
        ))
    if not isinstance(container(), abc.Mapping):
        ret = []
        for child in dom:
            ret.append(base.Issue.load(child))
        return container(ret)
    else:
        ret = {}
        for child in dom:
            new_issue = base.Issue.load(child)
            ret[int(new_issue._id)] = new_issue
        return container(ret)


def xmlloads(s: str, container: type = list) -> Iterable[base.Issue]:
    dom = lxml.etree.fromstring(s)
    ret = domload(dom, container)
    del dom
    return ret


def xmlload(fp: str | io.IOBase, container: type = list) -> Iterable[base.Issue]:
    dom = lxml.etree.parse(fp)
    ret = domload(dom, container)
    del dom
    return ret


def xmlloadCompressed(fp: str | io.IOBase, container: type = list) -> Iterable[base.Issue]:
    if isinstance(fp, io.IOBase):
        data = gzip.decompress(fp.read()).decode(
            encoding="utf-8", errors="ignore")
        return xmlloads(data, container)
    elif isinstance(fp, str):
        with open(fp, "rb") as file:
            data = gzip.decompress(file.read()).decode(
                encoding="utf-8", errors="ignore")
            return xmlloads(data, container)
