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
from typing import List, Tuple, Union
from hsd.common import np, ATTRIB_SUFFIX, HSD_ATTRIB_SUFFIX, HsdError,\
    QUOTING_CHARS, SPECIAL_CHARS
from hsd.eventhandler import HsdEventHandler, HsdEventPrinter

_ItemType = Union[float, int, bool, str]

_DataType = Union[_ItemType, List[_ItemType]]

# Pattern to transform HSD string values into actual Python data types
_TOKEN_PATTERN = re.compile(r"""
# Integer
(?:\s*(?:^|(?<=\s))(?P<int>[+-]?[0-9]+)(?:\s*$|\s+))
|
# Floating point
(?:\s*(?:^|(?<=\s))
(?P<float>[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)(?:$|(?=\s+)))
|
# Logical (Yes/No)
(?:\s*(?:^|(?<=\s))(?P<logical>[Yy][Ee][Ss]|[Nn][Oo])(?:$|(?=\s+)))
|
# Quoted string
(?:\s*(?:(?P<qstr>(?P<quote>['"]).*?(?P=quote))
|
# Unquoted string
(?P<str>.+?))(?:$|\s+))
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
        self._hsddict: dict = {}
        self._curblock: dict = self._hsddict
        self._parentblocks: List[dict] = []
        self._data: Union[None, _DataType] = None
        self._attribs: List[Tuple[str, dict]] = []
        self._flatten_data: bool = flatten_data
        self._include_hsd_attribs: bool = include_hsd_attribs


    @property
    def hsddict(self):
        """The dictionary which has been built"""
        return self._hsddict


    def open_tag(self, tagname, attrib, hsdattrib):
        if self._data is not None:
            msg = f"Node '{tagname}' opened in an invalid context"
            raise HsdError(msg)
        self._attribs.append((attrib, hsdattrib))
        self._parentblocks.append(self._curblock)
        self._curblock = {}


    def close_tag(self, tagname):
        attrib, hsdattrib = self._attribs.pop(-1)
        parentblock = self._parentblocks.pop(-1)
        prevcont = parentblock.get(tagname)
        if self._data is not None:
            if prevcont is None:
                parentblock[tagname] = self._data
            elif isinstance(prevcont, list) and len(prevcont) > 0 and isinstance(prevcont[0], dict):
                prevcont.append({None: self._data})
            elif isinstance(prevcont, dict):
                parentblock[tagname] = [prevcont, {None: self._data}]
            else:
                parentblock[tagname] = [{None: prevcont}, {None: self._data}]
        else:
            if prevcont is None:
                parentblock[tagname] = self._curblock
            elif isinstance(prevcont, list) and len(prevcont) > 0 and isinstance(prevcont[0], dict):
                prevcont.append(self._curblock)
            elif isinstance(prevcont, dict):
                parentblock[tagname] = [prevcont, self._curblock]
            else:
                parentblock[tagname] = [{None: prevcont}, self._curblock]

        if prevcont is None:
            if attrib:
                parentblock[tagname + ATTRIB_SUFFIX] = attrib
            if self._include_hsd_attribs:
                parentblock[tagname + HSD_ATTRIB_SUFFIX] = hsdattrib
        else:
            prevattrib = parentblock.get(tagname + ATTRIB_SUFFIX)
            if isinstance(prevattrib, list):
                prevattrib.append(attrib)
            else:
                parentblock[tagname + ATTRIB_SUFFIX] = [prevattrib, attrib]
                print(f"parentblock[{tagname} + {ATTRIB_SUFFIX}] = [{prevattrib}, {attrib}]")

            if self._include_hsd_attribs:
                prevhsdattrib = parentblock.get(tagname + HSD_ATTRIB_SUFFIX)
                if isinstance(prevhsdattrib, list):
                    prevhsdattrib.append(hsdattrib)
                else:
                    parentblock[tagname + HSD_ATTRIB_SUFFIX] = [prevhsdattrib,
                                                                hsdattrib]
        self._curblock = parentblock
        self._data = None


    def add_text(self, text):
        if self._curblock or self._data is not None:
            msg = "Data appeared in an invalid context"
            raise HsdError(msg)
        self._data = self._text_to_data(text)


    def _text_to_data(self, txt: str) -> _DataType:
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



class HsdDictWalker:
    """Walks through a Python dictionary and triggers HSD events.

    Args:
        eventhandler: Event handler dealing with the HSD events generated while
            walking through the dictionary. When not specified, the events
            are printed.
    """

    def __init__(self, eventhandler: HsdEventHandler = None):

        if eventhandler is None:
            self._eventhandler: HsdEventHandler = HsdEventPrinter()
        else:
            self._eventhandler: HsdEventHandler = eventhandler


    def walk(self, dictobj):
        """Walks through the directory and generates HSD events.

        Args:
            dictobj: Directory to walk through.
        """

        for key, value in dictobj.items():

            if key.endswith(ATTRIB_SUFFIX) or key.endswith(HSD_ATTRIB_SUFFIX):
                continue

            hsdattrib = dictobj.get(key + HSD_ATTRIB_SUFFIX)
            attrib = dictobj.get(key + ATTRIB_SUFFIX)

            if isinstance(value, dict):

                self._eventhandler.open_tag(key, attrib, hsdattrib)
                self.walk(value)
                self._eventhandler.close_tag(key)

            elif isinstance(value, list) and value and isinstance(value[0], dict):
                for ind, item in enumerate(value):
                    hsdattr = hsdattrib[ind] if hsdattrib else None
                    attr = attrib[ind] if attrib else None
                    self._eventhandler.open_tag(key, attr, hsdattr)
                    if None in item:
                        self._eventhandler.add_text(_to_text(item[None]))
                    else:
                        self.walk(item)
                    self._eventhandler.close_tag(key)

            else:
                self._eventhandler.open_tag(key, attrib, hsdattrib)
                self._eventhandler.add_text(_to_text(value))
                self._eventhandler.close_tag(key)


def _to_text(obj):

    if isinstance(obj, list):
        objstr = _list_to_hsd(obj)
    elif np is not None and isinstance(obj, np.ndarray):
        objstr = _list_to_hsd(obj.tolist())
    else:
        objstr = _item_to_hsd(obj)
    return objstr


def _list_to_hsd(lst):
    if lst and isinstance(lst[0], list):
        lines = []
        for innerlist in lst:
            lines.append(" ".join([_item_to_hsd(item) for item in innerlist]))
        return "\n".join(lines)
    return " ".join([_item_to_hsd(item) for item in lst])


def _item_to_hsd(item):

    if isinstance(item, bool):
        return "Yes" if item else "No"
    if isinstance(item, (int, float)):
        return str(item)
    if isinstance(item, str):
        return _str_to_hsd(item)
    msg = "Data type {} can not be converted to HSD string"\
            .format(type(item))
    raise TypeError(msg)


def _str_to_hsd(string):
    present = [qc in string for qc in QUOTING_CHARS]
    nquotetypes = sum(present)
    delimiter = ""
    if not nquotetypes and True in [sc in string for sc in SPECIAL_CHARS]:
        delimiter = QUOTING_CHARS[0]
    elif nquotetypes == 1 and string[0] not in QUOTING_CHARS:
        delimiter = QUOTING_CHARS[1] if present[0] else QUOTING_CHARS[0]
    elif nquotetypes > 1:
        msg = "String '{}' can not be quoted correctly".format(string)
        raise ValueError(msg)
    return delimiter + string + delimiter
