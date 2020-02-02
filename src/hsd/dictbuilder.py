#------------------------------------------------------------------------------#
#  hsd: package for manipulating HSD-formatted data                            #
#  Copyright (C) 2011 - 2020  DFTB+ developers group                           #
#                                                                              #
#  See the LICENSE file for terms of usage and distribution.                   #
#------------------------------------------------------------------------------#
#
"""
Contains an event-driven builder for dictionary based (JSON-like) structure
"""
import re
from .parser import HsdEventHandler

__all__ = ['HsdDictBuilder']


_TOKEN_PATTERN = re.compile(r"""
(?:\s*(?:^|(?<=\s))(?P<int>[+-]?[0-9]+)(?:\s*$|\s+))
|
(?:\s*(?:^|(?<=\s))
(?P<float>[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)(?:$|(?=\s+)))
|
(?:\s*(?:^|(?<=\s))(?P<logical>[Yy][Ee][Ss]|[Nn][Oo])(?:$|(?=\s+)))
|
(?:(?P<qstr>(?P<quote>['"]).*?(?P=quote)) | (?P<str>.+?)(?:$|\s+))
""", re.VERBOSE | re.MULTILINE)


class HsdDictBuilder(HsdEventHandler):
    """Deserializes HSD into nested dictionaries"""

    def __init__(self, flatten_data=False):
        HsdEventHandler.__init__(self)
        self._hsddict = {}
        self._curblock = self._hsddict
        self._parentblocks = []
        self._data = None
        self._flatten_data = flatten_data


    def open_tag(self, tagname, options, hsdoptions):
        for attrname, attrvalue in options.items():
            self._curblock[tagname + '.' + attrname] = attrvalue
        self._parentblocks.append(self._curblock)
        self._curblock = {}


    def close_tag(self, tagname):
        parentblock = self._parentblocks.pop(-1)
        prevcontent = parentblock.get(tagname)
        if prevcontent is not None and not isinstance(prevcontent, list):
            prevcontent = [prevcontent]
            parentblock[tagname] = prevcontent
        if self._data is None:
            content = self._curblock
        else:
            content = self._data
            self._data = None
        if prevcontent is None:
            parentblock[tagname] = content
        else:
            prevcontent.append(content)
        self._curblock = parentblock


    def add_text(self, text):
        self._data = self._text_to_data(text)


    @property
    def hsddict(self):
        """Returns the dictionary which has been built"""
        return self._hsddict


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
