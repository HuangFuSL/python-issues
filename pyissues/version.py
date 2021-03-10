import collections
from typing import Iterable


class Version():

    def __init__(self, year: int, month: int, day: int, *args):
        self.version = collections.namedtuple(
            "version", ['year', 'month', 'day'])(year, month, day)

    def __str__(self):
        return "Python-issues version %s" % (".".join(map(str, self.version)), )

    def __repr__(self):
        return ".".join(map(str, self.version))

    def __eq__(self, o):
        if isinstance(o, str):
            return o == repr(self)
        elif isinstance(o, Iterable):
            return list(o) == list(self.version)
        else:
            return super().__eq__(o)


__version__ = Version(0, 0, 2)
