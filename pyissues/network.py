from __future__ import annotations

import csv
import io
from typing import Callable, Dict, List

import bs4 as bs
import requests

from . import base, const, util

parsers: Dict[str, Callable] = {}


def field_parser(func: Callable) -> Callable:
    parsers[func.__name__] = func
    return func


@field_parser
def form(table: bs.element.Tag, issue: int) -> Dict[str, str]:
    n = [_.find_all("th") for _ in table.find_all('tr')]
    m = [_.find_all("td") for _ in table.find_all('tr')]
    return dict(zip(
        util.extract(*n, post=util.replace_space),
        util.extract(*m, post=util.format)
    ))


@field_parser
def files(table: bs.element.Tag, issue: int) -> Dict[str, List[Dict[str, str]]]:
    ret = []
    label_iter = iter(table.find_all('tr'))
    title = util.replace_space(next(label_iter).find('th').get_text())
    fields = util.extract(next(label_iter).find_all("th"),
                          post=util.replace_space)
    for record in label_iter:
        ret.append(dict(zip(fields, util.extract(
            record.find_all("td"), post=util.format, links=const._HOME_URL))))
    return {title: ret}


@field_parser
def messages(table: bs.element.Tag, issue: int) -> Dict[str, List[Dict[str, str]]]:
    ret = []
    fields = ['url', 'author', 'date', 'content']
    label_iter = iter(table.find_all('tr'))
    title = util.replace_space(next(label_iter).find('th').get_text())
    while True:
        try:
            meta = util.extract(next(label_iter).find_all(
                'th'), post=util.format, links=const._ISSUE_URL % (issue, ))
            meta += util.extract(next(label_iter).find_all('td'))
            newComment = dict(zip(fields, meta))
            newComment.update(**util.splitAuthor(newComment['author']))
            ret.append(base.Comment(**newComment))
        except StopIteration:
            break
    return {title: ret}


def parse_doc(document: str, page: int) -> Dict[str, str]:
    ret = {}
    whole_doc = bs.BeautifulSoup(document, features="lxml")
    for table in whole_doc.find_all('table'):
        if table['class'][0] in parsers:
            ret.update(**parsers[table['class'][0]](table, page))
    for keywd in const._ISSUE_MULTIPLE_ATTRIBUTES:
        ret[keywd] = ret[keywd].split(", ")
    for p in whole_doc.find_all('p'):
        result = p.find_all('strong')
        if len(result) in [4, 5]:
            ret['read_only'] = len(result) == 5
            for k, v in zip(const._METAFIELD, result):
                ret[k] = v.get_text()
            break
    for field in const._SPLIT_NEEDED:
        new_names = const._SPLIT_NEEDED[field]
        if field in ret:
            for i in ret[field]:
                i.update(**dict(zip(new_names, i[new_names[0]])))
        else:
            ret[field] = []
    return ret


def get_data(page: int) -> base.Issue:
    timeout = 10
    fail = 0
    while True:
        try:
            resp = requests.get(
                const._ISSUE_URL % (page, ), timeout=timeout
            ).content.decode(encoding="utf-8", errors="replace")
            ret = parse_doc(resp, page)
            break
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except requests.exceptions.Timeout as e:
            timeout += 5
            if timeout > 60:
                raise e
            print("Request for issue %d timeout, wait for %d seconds." %
                  (page, timeout))
        except Exception as e:
            fail += 1
            if fail >= 3:
                raise e
            print("Issue %d failed(%d), retrying." % (page, fail))
            return None
    ret.update(_id=page)
    return base.Issue(**ret)


async def async_get_data(page: int) -> base.Issue:
    return get_data(page)


def get_list() -> Dict[int, int]:
    issue_list = csv.reader(io.StringIO(requests.get(const._ISSUE_LIST).content.decode()[:-1]))
    next(issue_list)
    return {int(x): int(y) for x, y in issue_list}
