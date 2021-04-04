"""CLI Interface

CLI Interface for python-issues. Base usage:

python -m pyissues [SUB-COMMAND] [ARGS]

Available sub-commands:

* check     Check whether the issue list is updatable
* fix       Fix the missing issue in the list
* load      Load all of the issues into the memory
* rebuild   Refetch the metadata and all of the issues
* refetch   Refetch all of the issues using the metadata
* show      Display the specified issue
* update    Update the metadata and issue list
* version   Display the version

Available arguments:

--fullupdate, -fu   Refetch and update all of the open issues
    --threads, -t   Number of threads to be used
       --meta, -m   Specify the location of metadata file
       --data, -d   Specify the location of data file
      --issue, -i   Specify the issue to be displayed
      --width, -w   Specify the command-line window size

If Python is initiated with argument `-i`, the returned value will be stored in
`ret` local variable.
"""
from __future__ import annotations

import argparse
import functools
import io
import json
import multiprocessing
import operator
import os
import sys
import time
from typing import Any, Callable, Dict, Iterable, List, Set

from . import base as base
from . import cli as cli
from . import const as const
from . import io as issuesIO
from . import network as network
from . import version as _version

sub_commands: Dict[str, Callable] = {}


def sub_command(o: Callable) -> Callable:
    """Decorator for the subcommand

    Parameter:

    - `o`: `Callable`, the subcommand

    Returns: `Callabel`, the original subcommand
    """
    sub_commands[o.__name__] = o
    return o


def is_compressed(_: str) -> str:
    return _[-2:] == "gz"


def compare_meta(
    old: List[Set[int]], new: List[Set[int]], fullupdate: bool = True
) -> Set[int]:
    """Compare two metadata

    Parameters: 

    - `old`: `List[Set[int]]`, the old metadata
    - `new`: `List[Set[int]]`, the new metadata
    - `fullupdate`: `bool`, if `True`, all of the open issues will be included
    """

    def _numbering(start: int = 1) -> str:
        i = start
        while True:
            yield str(i) + "."
            i += 1

    number = _numbering(1)
    sub = new[0] - old[0]
    print(next(number), "%d issues newly added." % (len(sub)))
    print("  ", ", ".join([
        str(len(sub & new[_])) + " " + const._STATUS[_] for _ in range(1, 5)
    ]), end=".\n")
    for i in range(2, 5):
        print(next(number), "%d open issues are now %s" %
              (len(old[1] & new[i]), const._STATUS[i]), end=".\n")
    return new[0] - old[0] | new[0 if fullupdate else 2] - old[2]


def reshape_meta(o: Dict[int | str, int]) -> List[Set[int]]:
    """Convert the CSV data to sets

    Parameters:

    - `o`: `Dict[int | str, int]`, data to be converted

    Returns: `List[Set[int]]`

    - The first set contains ID of all issues;
    - The second set contains ID of closed issues;
    - The third set contains ID of open issues;
    - The fourth set contains ID of pending issues;
    - The fifth set contains ID of languishing issues.
    """
    ret: List[Set[int]] = [set() for _ in range(5)]
    for i in o:
        ret[o[i]].add(int(i))
    ret[0] = functools.reduce(operator.or_, ret[1:])
    return ret


def update_meta(
    meta: Dict[int, int], path: str | io.IOBase = "meta.json"
) -> None:
    """Save the data to local JSON file

    Parameters:

    - `meta`: Dict[int, int], CSV data
    - `path`: `str` or `io.IOBase`, the filename

    Returns: `None`
    """
    if isinstance(path, str) and path:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(meta, file)
    elif isinstance(path, io.IOBase):
        json.dump(meta, path)


def refresh_meta(
    new: Dict[int, int],
    path: str | io.IOBase | None = "meta.json",
    fullupdate: bool = True
) -> Set[int]:
    if isinstance(path, str) and path:
        with open(path, "r", encoding="utf-8") as file:
            old = json.load(file)
    elif isinstance(path, io.IOBase):
        old = json.load(path)
    elif isinstance(path, dict):
        old = path
    else:
        old = {}
    old = reshape_meta(old)
    new = reshape_meta(new)
    return compare_meta(old, new, fullupdate)


def fetch(records: Iterable[int], threads: int | None = 16) -> List[base.Issue]:
    print("Fetching %d issues from bugs.python.org" % (len(records), ))
    if threads is not None:
        threads = int(threads)
    with multiprocessing.Pool(threads) as pool:
        start = time.time()
        ret = pool.map(network.get_data, map(int, records))
        end = time.time()
    ret = list(filter(lambda _: _ is not None, ret))
    print("%d issues fetched in %s" %
          (len(ret), time.strftime("%H:%M:%S", time.gmtime(end - start)))
          )
    return ret


def write(
    obj: List[base.Issue], path: str = "issues.xml.gz"
) -> List[base.Issue]:
    if is_compressed(path):
        issuesIO.xmldumpCompressed(obj, path)
    else:
        issuesIO.xmldump(obj, path)
    print("%d issues written to %s" % (len(obj), path))
    return obj


@sub_command
def rebuild(
        *, metafile: str = "meta.json", threads: int | None = None, **kwargs):
    print("Fetching list.")
    new_list = network.get_list()
    update = set()
    with open(metafile, "w+") as file:
        json.dump({}, file)
        file.seek(0)
        update = refresh_meta(new_list, file)
        json.dump(new_list, file)
    print("Fetching issues.")
    return write(fetch(update, threads))


@sub_command
def refetch(
        *, metafile: str = "meta.json", threads: int | None = None, **kwargs):
    with open(metafile, "r") as file:
        update = refresh_meta(json.load(file), {})
    print("%d issues loaded." % (len(update), ))
    print("Fetching issues.")
    return write(fetch(update, threads))


@sub_command
def check(*, metafile: str = "meta.json", **kwargs):
    print("Fetching list.")
    new_list = network.get_list()
    update = set()
    with open(metafile, "r") as file:
        update = refresh_meta(new_list, file)
    return update


@sub_command
def fix(*,
        metafile: str = "meta.json",
        datafile: str = "issues.xml.gz",
        threads: int | None = None,
        **kwargs
        ):
    print("Loading list,")
    with open(metafile, "r") as file:
        update = refresh_meta(json.load(file), {})
    print("Loading issues.")
    issues = issuesIO.xmlloadCompressed(datafile)
    issuesID = {int(_._id) for _ in issues}
    print("%d issues not fetched." % (len(update - issuesID), ))
    issues.extend(fetch(update - issuesID, threads))
    return write(issues)


@sub_command
def update(*,
           fullupdate: bool = False,
           metafile: str = "meta.json",
           datafile: str = "issues.xml.gz",
           threads: int | None = None, **kwargs):
    print("Loading list.")
    new_list = network.get_list()
    update = refresh_meta(new_list, metafile, fullupdate=fullupdate)
    if update:
        print("Loading issues.")
        issues = issuesIO.xmlloadCompressed(datafile, dict)
        new_issues = fetch(update, threads)
        for _ in new_issues:
            issues[int(_._id)] = _
        write(issues)
        update_meta(new_list)
    else:
        print("No change detected.")
        return None


@sub_command
def load(*, datafile: str = "issues.xml.gz", **kwargs):
    print("Loading issues.")
    issues = issuesIO.xmlloadCompressed(datafile, dict)
    print("Loaded issues are saved in `ret`")
    return issues


@sub_command
def version(**kwargs):
    print(_version.__version__)


@sub_command
def show(*, datafile: str = "issues.xml.gz", _id: int, width: int, **kwargs):
    print("Loading issues.")
    issues = issuesIO.xmlloadCompressed(datafile, dict)
    if _id is not None:
        _id = int(_id)
    if width is not None:
        width = int(width)
    cli.display(issues[_id], width=width)


def main(*args) -> Any:
    try:
        user_root = os.environ['HOME']
    except KeyError:
        user_root = os.environ['USERPROFILE']
    config_path = os.path.join(user_root, ".pyissues")
    if not os.path.exists(os.path.join(user_root, ".pyissues")):
        os.mkdir(config_path)
    os.chdir(config_path)

    parser = argparse.ArgumentParser(description="Python issues tool")
    parser.add_argument(
        '--fullupdate', '-fu',
        action='store_const', dest='fullupdate', const=True, default=None)
    parser.add_argument(
        '--threads', '-t',
        nargs='?', dest='threads', default=None)
    parser.add_argument(
        '--meta', '-m',
        nargs='?', dest='metafile', default='meta.json')
    parser.add_argument(
        '--data', '-d',
        nargs='?', dest='datafile', default='issues.xml.gz')
    parser.add_argument(
        '--issue', '-i',
        nargs='?', dest='_id', default=None)
    parser.add_argument(
        '--width', '-w',
        nargs='?', dest='width', default="80")

    if not args:
        return
    else:
        return sub_commands[args[0]](**vars(parser.parse_args(args[1:])))


if __name__ == "__main__":
    try:
        if len(sys.argv) >= 2:
            ret = main(*(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(0)
