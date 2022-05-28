#  hsd-python: package for manipulating HSD-formatted data in Python                               #
#  Copyright (C) 2011 - 2022  DFTB+ developers group                                               #
#  Licensed under the BSD 2-clause license.                                                        #
#--------------------------------------------------------------------------------------------------#
#
"""
Provides an event based formatter to create HSD dumps
"""

from typing import List, TextIO, Union
from hsd.common import HSD_ATTRIB_EQUAL, HSD_ATTRIB_NAME
from hsd.eventhandler import HsdEventHandler


_INDENT_STR = "  "


class HsdFormatter(HsdEventHandler):
    """Implements an even driven HSD formatter.

    Args:
        fobj: File like object to write the formatted output to.
        use_hsd_attribs: Whether HSD attributes passed to the formatter should
            be considered, when formatting the the output (default: True)
    """

    def __init__(self, fobj, use_hsd_attribs=True):
        super().__init__()
        self._fobj: TextIO = fobj
        self._use_hsd_attribs: bool = use_hsd_attribs
        self._level: int = 0
        self._indent_level: int = 0
        # Whether last node on current level should/was followed by an
        # equal sign. (None = unspeciefied)
        self._followed_by_equal: List[Union[bool, None]] = []
        self._nr_children: List[int] = [0]


    def open_tag(self, tagname: str, attrib: str, hsdattrib: dict):

        if attrib is None:
            attribstr = ""
        elif not isinstance(attrib, str):
            msg = f"Invalid attribute data type ({str(type(attrib))}) for "\
                f"'{tagname}'"
            raise ValueError(msg)
        else:
            attribstr = " [" + attrib + "]"

        if self._level and not self._nr_children[-1]:
            # Look up, whether previous (containing) node should be followed by
            # an equal sign
            equal = self._followed_by_equal[-1]
            if equal:
                self._fobj.write(" = ")
                indentstr = ""
            else:
                self._fobj.write(" {\n")
                self._indent_level += 1
                indentstr = self._indent_level * _INDENT_STR
        else:
            indentstr = self._indent_level * _INDENT_STR

        if self._use_hsd_attribs and hsdattrib is not None:
            tagname = hsdattrib.get(HSD_ATTRIB_NAME, tagname)

        self._fobj.write(f"{indentstr}{tagname}{attribstr}")

        # Previous (containing) node has now one children more
        self._nr_children[-1] += 1

        # Currently opened node has no children so far.
        self._nr_children.append(0)
        self._level += 1

        equal = None
        if hsdattrib is not None and self._use_hsd_attribs:
            equal = hsdattrib.get(HSD_ATTRIB_EQUAL)
        self._followed_by_equal.append(equal)


    def close_tag(self, tagname: str):

        nr_children = self._nr_children.pop(-1)
        equal = self._followed_by_equal.pop(-1)
        if not nr_children:
            self._fobj.write(" {}\n")
        elif not equal:
            self._indent_level -= 1
            indentstr = self._indent_level * _INDENT_STR
            self._fobj.write(f"{indentstr}}}\n")
        self._level -= 1


    def add_text(self, text: str):

        equal = self._followed_by_equal[-1]
        multiline = "\n" in text
        if equal is None and not multiline:
            if len(self._followed_by_equal) > 1:
                equal = not self._followed_by_equal[-2]
            else:
                equal = True
        if equal:
            self._fobj.write(" = ")
            self._followed_by_equal[-1] = True
        else:
            self._indent_level += 1
            indentstr = self._indent_level *  _INDENT_STR
            self._fobj.write(f" {{\n{indentstr}")
            text = text.replace("\n", "\n" + indentstr)

        self._fobj.write(text)
        self._fobj.write("\n")
        self._nr_children[-1] += 1
