from __future__ import annotations

import gzip
from io import IOBase
from typing import Iterable, Iterable, Mapping
from xml.dom import minidom
from collections import abc

from . import base

def MappingIterWrapper(o: Mapping):
    for _ in o:
        yield o[_]

def domdump(o: Iterable[base.Issue]) -> minidom.Document:
    ret_dom = minidom.getDOMImplementation().createDocument(None, 'issues', None)
    issues = ret_dom.documentElement
    issues.setAttribute("items", str(len(o)))
    issues_iter = MappingIterWrapper(o) if isinstance(o, Mapping) else o
    for issue in issues_iter:
        issues.appendChild(issue.dumpxml().documentElement)
    return ret_dom


def xmldump(o: Iterable[base.Issue], fp: IOBase | str) -> None:
    ret = domdump(o)
    data = ret.toxml()
    if isinstance(fp, IOBase):
        fp.write(data)
    elif isinstance(fp, str):
        with open(fp, "w", encoding="utf-8") as file:
            file.write(data)


def xmldumpCompressed(o: Iterable[base.Issue], fp: IOBase | str, **kwargs) -> None:
    ret = domdump(o)
    data = gzip.compress(
        ret.toxml().encode(encoding="utf-8", errors="xmlcharrefreplace"),
        **kwargs
    )
    if isinstance(fp, IOBase):
        fp.write(data)
        fp.flush()
    elif isinstance(fp, str):
        with open(fp, "wb") as file:
            file.write(data)


def xmldumps(o: Iterable) -> str:
    return domdump(o).toxml()


def domload(dom, container: type = list) -> Iterable[base.Issue]:
    root = dom.documentElement
    if not isinstance(container(), abc.Mapping):
        ret = []
        for Node in root.childNodes:
            if Node.nodeName == "issue":
                ret.append(base.Issue().loadFromNode(Node))
        return container(ret)
    else:
        ret = {}
        for Node in root.childNodes:
            if Node.nodeName == "issue":
                new_issue = base.Issue().loadFromNode(Node)
                ret[int(new_issue._id)] = new_issue
        return container(ret)


def xmlloads(s: str, container: type = list) -> Iterable[base.Issue]:
    dom = minidom.parseString(s)
    return domload(dom, container)


def xmlload(fp: str | IOBase, container: type = list) -> Iterable[base.Issue]:
    dom = minidom.parse(fp)
    return domload(dom, container)


def xmlloadCompressed(fp: str | IOBase, container: type = list) -> Iterable[base.Issue]:
    if isinstance(fp, IOBase):
        data = gzip.decompress(fp.read()).decode(encoding="utf-8", errors="ignore")
        return xmlloads(data,container)
    elif isinstance(fp, str):
        with open(fp, "rb") as file:
            data = gzip.decompress(file.read()).decode(encoding="utf-8", errors="ignore")
            return xmlloads(data, container)
