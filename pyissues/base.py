"""Base module of pyissues package

This module provides data model for issues and comments from the Python Issue
Tracker (https://bugs.python.org) with methods to save the issue in
base64-encoded XML format.
"""
from __future__ import annotations

import base64
import warnings
from typing import List

import lxml.etree

from . import const


class UnreadableXMLWarning(Exception):
    """Warning to be raised when fields are written into XML without base64
    encoded. Illegal characters such as b"\x01" will make the XML file generated
    unreadable.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return super().__str__()


class Comment():
    def __init__(self, url: str, author: str, content: str, date: str, username: str):
        self.url = url
        self.author = author
        self.content = content
        self.username = username
        self.date = date

    @staticmethod
    def get_fields() -> List[str]:
        """The following attributes are saved as attributes instead of text
        nodes in the XML document.
        """
        return ['url', 'author', 'date', 'username']

    def __repr__(self) -> str:
        return "<%s by %s>" % (self.url, self.author)

    def __str__(self) -> str:
        return self.content

    def __hash__(self) -> int:
        return hash(self.url)

    def __eq__(self, o) -> bool:
        return self.url == o.url


class Issue():
    def __init__(self, **kwargs):
        for key in const._ISSUE_FIELD:
            setattr(self, key, "" if key in const._ISSUE_ATTRIBUTES else [])
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self._id = str(self._id)

    def __repr__(self) -> str:
        return "<Issue at %s>" % (self._id)

    def __str__(self) -> str:
        return str(self.messages[0])

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, o) -> bool:
        return self._id == o._id

    @staticmethod
    def _encode(o: str) -> str:
        return base64.standard_b64encode(o.encode(encoding='utf-8')).decode()

    @staticmethod
    def _decode(o: str) -> str:
        return base64.standard_b64decode(o).decode(encoding="utf-8")

    def dump(self, encode: bool = True) -> lxml.etree.Element:
        if encode:
            encoder = self._encode
        else:
            encoder = str
            warnings.warn(UnreadableXMLWarning(
                "You are saving the non-base64-encoded data , the XML " +
                "document generated might be unreadable due to illegal " +
                "characters in the document."
            ))

        ret_node = lxml.etree.Element("issue")

        for attr in const._ISSUE_ATTRIBUTES:
            ret_node.set(attr, encoder(str(getattr(self, attr, ''))))

        for attr in const._ISSUE_MULTIPLE_ATTRIBUTES:
            for record in getattr(self, attr, None):
                new_node = lxml.etree.Element(attr)
                new_node.text = record
                ret_node.append(new_node)

        for attr in const._ISSUE_NODES:
            new_node = lxml.etree.Element(attr)
            for record in getattr(self, attr, None):
                new_sub_node = lxml.etree.Element(attr[:-1])
                for field in record:
                    new_sub_node.set(field, encoder(record[field]))
                new_node.append(new_sub_node)
            ret_node.append(new_node)

        for attr in const._ISSUE_COMPLEX:
            new_node = lxml.etree.Element(attr)
            for record in getattr(self, attr, None):
                new_sub_node = lxml.etree.Element(attr[:-1])
                for field in record.get_fields():
                    new_sub_node.set(field, getattr(record, field))
                new_sub_node.text = encoder(str(record))
                new_node.append(new_sub_node)
            ret_node.append(new_node)

        return ret_node

    def _load(self, root: lxml.etree._element, decode: bool = True):
        decoder = self._decode if decode else str
        attributes = root.attrib
        for attr in attributes:
            setattr(self, attr, decoder(attributes[attr]))
        data = {}
        for attr in const._ISSUE_MULTIPLE_ATTRIBUTES:
            data[attr] = []
        for attr in const._ISSUE_NODES:
            data[attr] = []
        for attr in const._ISSUE_COMPLEX:
            data[attr] = []

        for child in root:
            if child.tag in const._ISSUE_MULTIPLE_ATTRIBUTES:
                data[child.tag].append(child.text)
            elif child.tag in const._ISSUE_NODES:
                for subchild in child:
                    data[child.tag].append({
                        _: decoder(subchild.attrib[_]) for _ in subchild.attrib
                    })
            elif child.tag in const._ISSUE_COMPLEX:
                for subchild in child:
                    ret = {
                        _: subchild.attrib[_] for _ in dict(subchild.attrib)
                    }
                    try:
                        ret['content'] = decoder(subchild.text)
                    except:
                        ret['content'] = ""
                    data[child.tag].append(Comment(**ret))
        for _ in data:
            setattr(self, _, data[_])
        return self

    @staticmethod
    def load(root: lxml.etree._element, decode: bool = True) -> Issue:
        ret = Issue()
        return ret._load(root, decode)
