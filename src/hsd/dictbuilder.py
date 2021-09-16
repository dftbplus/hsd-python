#------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python           #
#  Copyright (C) 2011 - 2021  DFTB+ developers group                           #
#  Licensed under the BSD 2-clause license.                                    #
#------------------------------------------------------------------------------#
#
"""
Contains an event-driven builder for dictionary based (JSON-like) structure
"""
import re
from .common import ATTRIB_SUFFIX, HSD_ATTRIB_SUFFIX, HsdError
from .eventhandler import HsdEventHandler


_TOKEN_PATTERN = re.compile(r"""
(?:\s*(?:^|(?<=\s))(?P<int>[+-]?[0-9]+)(?:\s*$|\s+))
|
(?:\s*(?:^|(?<=\s))
(?P<float>[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)(?:$|(?=\s+)))
|
(?:\s*(?:^|(?<=\s))(?P<logical>[Yy][Ee][Ss]|[Nn][Oo])(?:$|(?=\s+)))
|
(?:\s*(?:(?P<qstr>(?P<quote>['"]).*?(?P=quote)) | (?P<str>.+?))(?:$|\s+))
""", re.VERBOSE | re.MULTILINE)


class HsdDictBuilder(HsdEventHandler):
    """Specific HSD event handler, which builds a nested Python dictionary.

    Args:
        flatten_data: Whether multiline data in the HSD input should be
            flattened into a single list. Othewise a list of lists is created,
            with one list for every line (default).
        include_hsd_attribs: Whether the HSD-attributes (processing related
            attributes, like original tag name, line information, etc.) should
            be stored.
    """

    def __init__(self, flatten_data: bool = False,
                 include_hsd_attribs: bool = False):
        super().__init__()
        self._hsddict = {}
        self._content = self._hsddict  # Content obtained for the current node
        self._parentblocks = []
        self._attribs = []
        self._flatten_data = flatten_data
        self._include_hsd_attribs = include_hsd_attribs


    @property
    def hsddict(self):
        """The dictionary which has been built"""
        return self._hsddict


    def open_tag(self, tagname, attrib, hsdattrib):
        self._attribs.append((attrib, hsdattrib))
        content = {} if self._content is None else self._content
        self._parentblocks.append(content)
        self._content = None


    def close_tag(self, tagname):
        attrib, hsdattrib = self._attribs.pop(-1)
        parentblock = self._parentblocks.pop(-1)
        prevcont = parentblock.get(tagname)
        if prevcont is not None:
            if isinstance(prevcont, dict) and isinstance(self._content, dict):
                prevcont = [prevcont]
                parentblock[tagname] = prevcont
            elif not (isinstance(prevcont, list)
                      and isinstance(prevcont[0], dict)):
                msg = f"Invalid duplicate occurance of node '{tagname}'"
                raise HsdError(msg)
        content = {} if self._content is None else self._content
        if prevcont is None:
            parentblock[tagname] = content
            if attrib:
                parentblock[tagname + ATTRIB_SUFFIX] = attrib
            if self._include_hsd_attribs:
                parentblock[tagname + HSD_ATTRIB_SUFFIX] = hsdattrib
        else:
            prevcont.append(content)
            prevattrib = parentblock.get(tagname + ATTRIB_SUFFIX)
            if not (prevattrib is None and attrib is None):
                msg = f"Duplicate node '{tagname}' should not carry attributes"
            if self._include_hsd_attribs:
                prevhsdattrib = parentblock.get(tagname + HSD_ATTRIB_SUFFIX)
                if isinstance(prevhsdattrib, list):
                    prevhsdattrib.append(hsdattrib)
                else:
                    parentblock[tagname + HSD_ATTRIB_SUFFIX] = [prevhsdattrib,
                                                                hsdattrib]
        self._content = parentblock


    def add_text(self, text):
        if self._content is not None:
            msg = f"Data appeared in an invalid context"
            raise HsdError(msg)
        self._content = self._text_to_data(text)


    def _text_to_data(self, txt):
        data = []
        for line in txt.split("\n"):
            if self._flatten_data:
                linedata = data
            else:
                linedata = []
            for match in _TOKEN_PATTERN.finditer(line.strip()):
                if match.group("int"):
                    linedata.append(int(match.group("int")))
                elif match.group("float"):
                    linedata.append(float(match.group("float")))
                elif match.group("logical"):
                    lowlog = match.group("logical").lower()
                    linedata.append(lowlog == "yes")
                elif match.group("str"):
                    linedata.append(match.group("str"))
                elif match.group("qstr"):
                    linedata.append(match.group("qstr"))
            if not self._flatten_data:
                data.append(linedata)
        if len(data) == 1:
            if isinstance(data[0], list) and len(data[0]) == 1:
                return data[0][0]
            return data[0]
        return data
