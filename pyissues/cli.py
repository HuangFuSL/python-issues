from __future__ import annotations

import itertools
from typing import Dict, Iterable, List

from . import base

_WIDTH = 80


table_config = [
    {"tabs": 1, "cells": [
        {"type": "str", "name": "title", "prefix": "Title: "}
    ]},
    {"tabs": 2, "cells": [
        {"type": "str", "name": "type", "prefix": "Type: "},
        {"type": "str", "name": "stage", "prefix": "Stage: "}
    ]},
    {"tabs": 2, "cells": [
        {"type": "list", "name": "components",
            "prefix": "Components: ", "sep": ", "},
        {"type": "list", "name": "versions", "prefix": "Versions: ", "sep": ", "},
    ]},
    {"tabs": 2, "cells": [
        {"type": "str", "name": "status", "prefix": "Status: "},
        {"type": "str", "name": "resolution", "prefix": "Resolution: "},
    ]},
    {"tabs": 2, "cells": [
        {"type": "str", "name": "dependencies", "prefix": "Dependencies: "},
        {"type": "str", "name": "superseder", "prefix": "Superseder: "},
    ]},
    {"tabs": 2, "cells": [
        {"type": "str", "name": "assigned_to", "prefix": "Assigned To: "},
        {"type": "list", "name": "nosy_list", "prefix": "Nosy List: ", "sep": ", "},
    ]},
    {"tabs": 2, "cells": [
        {"type": "str", "name": "priority", "prefix": "Priority: "},
        {"type": "list", "name": "keywords", "prefix": "Keywords: ", "sep": ", "},
    ]},
]

message_config = [
    {"tabs": 2, "cells": [
        {"type": "str", "name": "author", "prefix": "Author: "},
        {"type": "str", "name": "date", "prefix": "Date: "},
    ]},
    {"tabs": 1, "cells": [
        {"type": "str", "name": "content", "prefix": "Content: "}
    ]},
]


def _nonstop(o: object, length: int | None = None) -> object:
    if length is not None:
        for i in range(length):
            yield o
    else:
        while True:
            yield o


def _get_horiz_line(
        tabs_up: List[int] = list(),
        tabs_down: List[int] = list(),
        length: int = _WIDTH,
        char: str = "-") -> str:
    splits, ret = set(), ""
    base = 0
    for i in tabs_up:
        base += 3 + i
        splits.add(base)
    base = 0
    for i in tabs_down:
        base += 3 + i
        splits.add(base)
    splits.add(0)
    for _ in range(length):
        ret += "+" if _ in splits else char
    return ret


def _get_verti_line(tabs: int):
    return "| " + " | ".join(_nonstop("%s", tabs)) + " |"


def _get_tab_width(
        tabs: int,
        width: int = _WIDTH,
        field: int = 0) -> Iterable[int]:
    splits = tabs + 1
    spaces = splits * 2 - 2
    a, b = divmod(width - splits - spaces, tabs)
    return [a + (1 if _ < b else 0) - field for _ in range(tabs)]


def _line_splitter(o: str, length: int) -> str:
    i, j, ret = 0, 0, ""
    while i < len(o):
        try:
            while o[i] == " ":
                i += 1
        except IndexError:
            break
        ret = o[i: i + length].strip(" ")
        if (len(ret) < length):
            yield ret.ljust(length, " ")
        else:
            try:
                j = ret.rindex(" ")
            except ValueError:
                yield ret.ljust(length, " ")
            else:
                i -= len(ret) - j
                yield ret[:j].ljust(length, " ")
        i += length


def _str_splitter(o: str, length: int) -> str:
    result = itertools.starmap(
        _line_splitter, zip(o.splitlines(), _nonstop(length))
    )
    for _ in result:
        i = 0
        for ret in _:
            yield ret
            i += 1
        if i > 1:
            yield " " * length


def _merger(*fields, tabs: int, width: List[int]) -> Iterable[str]:
    matrix = list(itertools.starmap(_str_splitter, zip(fields, width)))
    flag, line = True, []
    while flag:
        flag = False
        line.clear()
        for i in range(tabs):
            try:
                line.append(next(matrix[i]))
                flag = True
            except StopIteration:
                line.append(" " * width[i])
        if flag:
            yield _get_verti_line(tabs) % tuple(line)


def _process_tab(tab: Dict, **kwargs):
    if tab["type"] == "str":
        return tab["prefix"] + kwargs[tab["name"]]
    elif tab["type"] == "list":
        return tab["prefix"] + tab["sep"].join(kwargs[tab["name"]])


def make_table(
        config: List[Dict], *,
        omit_last_line: bool = False,
        last_line: List[int] = [],
        line_width: int = _WIDTH,
        **kwargs):
    last_line = []
    char = "="
    for _ in config:
        width = _get_tab_width(_["tabs"], width=line_width)
        print(_get_horiz_line(last_line, width, length=line_width, char=char))
        last_line = width
        data = []
        for tab in _["cells"]:
            data.append(_process_tab(tab, **kwargs))
        print(*_merger(*data, tabs=_["tabs"], width=width), sep="\n")
        char = "-"
    if not omit_last_line:
        print(_get_horiz_line(last_line, [], length=line_width, char="="))
    return last_line


def display(o: base.Issue, *, width: int = _WIDTH) -> None:
    last_line = make_table(
        table_config,
        omit_last_line=True,
        line_width=width,
        **vars(o)
    )
    for _ in o.messages:
        last_line = make_table(
            message_config,
            omit_last_line=True,
            last_line=last_line,
            line_width=width,
            **vars(_)
        )
    print(_get_horiz_line(last_line, [], length=width, char="="), flush=True)
