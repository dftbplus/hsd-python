#------------------------------------------------------------------------------#
#  hsd: package for manipulating HSD-formatted data                            #
#  Copyright (C) 2011 - 2020  DFTB+ developers group                           #
#                                                                              #
#  See the LICENSE file for terms of usage and distribution.                   #
#------------------------------------------------------------------------------#
#
"""
Contains the event-generating HSD-parser.
"""
from collections import OrderedDict
import hsd.common as common


__all__ = ["HsdParser", "HsdEventHandler",
           "SYNTAX_ERROR", "UNCLOSED_TAG_ERROR", "UNCLOSED_OPTION_ERROR",
           "UNCLOSED_QUOTATION_ERROR", "ORPHAN_TEXT_ERROR"]

SYNTAX_ERROR = 1
UNCLOSED_TAG_ERROR = 2
UNCLOSED_ATTRIB_ERROR = 3
UNCLOSED_QUOTATION_ERROR = 4
ORPHAN_TEXT_ERROR = 5

_GENERAL_SPECIALS = "{}[]<=\"'#;"
_ATTRIB_SPECIALS = "]\"'"


class HsdEventHandler:
    """Base class for event handler implementing simple printing"""

    def __init__(self):
        """Initializes the default event handler"""
        self._indentlevel = 0
        self._indentstr = "  "


    def open_tag(self, tagname, attrib, hsdoptions):
        """Handler which is called when a tag is opened.

        It should be overriden in the application to handle the event in a
        customized way.

        Args:
            tagname: Name of the tag which had been opened.
            attrib: String containing the attribute of the tag or None.
            hsdoptions: Dictionary of the options created during the processing
                in the hsd-parser.
        """
        indentstr = self._indentlevel * self._indentstr
        print("{}OPENING TAG: {}".format(indentstr, tagname))
        print("{}ATTRIBUTE: {}".format(indentstr, attrib))
        print("{}HSD OPTIONS: {}".format(indentstr, str(hsdoptions)))
        self._indentlevel += 1


    def close_tag(self, tagname):
        """Handler which is called when a tag is closed.

        It should be overriden in the application to handle the event in a
        customized way.

        Args:
            tagname: Name of the tag which had been closed.
        """
        indentstr = self._indentlevel * self._indentstr
        print("{}CLOSING TAG: {}".format(indentstr, tagname))
        self._indentlevel -= 1


    def add_text(self, text):
        """Handler which is called with the text found inside a tag.

        It should be overriden in the application to handle the event in a
        customized way.

        Args:
           text: Text in the current tag.
        """
        indentstr = self._indentlevel * self._indentstr
        print("{}Received text: {}".format(indentstr, text))


class HsdParser:
    """Event based parser for the HSD format.

    The methods `open_tag()`, `close_tag()`, `add_text()`
    and `_handle_error()` should be overridden by the actual application.
    """

    def __init__(self, eventhandler=None):
        """Initializes the parser.

        Args:
            eventhandler: Instance of the HsdEventHandler class or its children.
        """
        if eventhandler is None:
            self._eventhandler = HsdEventHandler()
        else:
            self._eventhandler = eventhandler

        self._fname = ""                   # Name of file being processed
        self._checkstr = _GENERAL_SPECIALS  # special characters to look for
        self._oldcheckstr = ""             # buffer fo checkstr
        self._opened_tags = []             # info about opened tags
        self._buffer = []                  # buffering plain text between lines
        self._attrib = None                # attribute for current tag
        self._hsdoptions = OrderedDict()   # hsd-options for current tag
        self._currline = 0                 # nr. of current line in file
        self._after_equal_sign = False    # last tag was opened with equal sign
        self._inside_attrib = False        # parser inside attrib specification
        self._inside_quote = False         # parser inside quotation
        self._has_child = False
        self._oldbefore = ""               # buffer for tagname


    def feed(self, fobj):
        """Feeds the parser with data.

        Args:
            fobj: File like object or name of a file containing the data.
        """
        isfilename = isinstance(fobj, str)
        if isfilename:
            fp = open(fobj, "r")
            self._fname = fobj
        else:
            fp = fobj
        for line in fp.readlines():
            self._parse(line)
            self._currline += 1
        if isfilename:
            fp.close()

        # Check for errors
        if self._opened_tags:
            line0 = self._opened_tags[-1][1]
        else:
            line0 = 0
        if self._inside_quote:
            self._error(UNCLOSED_QUOTATION_ERROR, (line0, self._currline))
        elif self._inside_attrib:
            self._error(UNCLOSED_ATTRIB_ERROR, (line0, self._currline))
        elif self._opened_tags:
            self._error(UNCLOSED_TAG_ERROR, (line0, line0))
        elif ("".join(self._buffer)).strip():
            self._error(ORPHAN_TEXT_ERROR, (line0, self._currline))


    def _parse(self, line):
        """Parses a given line."""

        while True:
            sign, before, after = _splitbycharset(line, self._checkstr)

            # End of line
            if not sign:
                if self._inside_quote:
                    self._buffer.append(before)
                elif self._after_equal_sign:
                    self._text("".join(self._buffer) + before.strip())
                    self._closetag()
                    self._after_equal_sign = False
                elif not self._inside_attrib:
                    self._buffer.append(before)
                elif before.strip():
                    self._error(SYNTAX_ERROR, (self._currline, self._currline))
                break

            # Special character is escaped
            elif before.endswith("\\") and not before.endswith("\\\\"):
                self._buffer.append(before + sign)

            # Equal sign
            elif sign == "=":
                # Ignore if followed by "{" (DFTB+ compatibility)
                if after.lstrip().startswith("{"):
                    # _oldbefore may already contain the tagname, if the
                    # tagname was followed by an attribute -> append
                    self._oldbefore += before
                else:
                    self._has_child = True
                    self._hsdoptions[common.HSDATTR_EQUAL] = True
                    self._starttag(before, False)
                    self._after_equal_sign = True

            # Opening tag by curly brace
            elif sign == "{":
                self._has_child = True
                self._starttag(before, self._after_equal_sign)
                self._buffer = []
                self._after_equal_sign = False

            # Closing tag by curly brace
            elif sign == "}":
                self._text("".join(self._buffer) + before)
                self._buffer = []
                # If 'test { a = 12 }' occurs, curly brace closes two tags
                if self._after_equal_sign:
                    self._after_equal_sign = False
                    self._closetag()
                self._closetag()

            # Closing tag by semicolon
            elif sign == ";" and self._after_equal_sign:
                self._after_equal_sign = False
                self._text(before)
                self._closetag()

            # Comment line
            elif sign == "#":
                self._buffer.append(before)
                after = ""

            # Opening attribute specification
            elif sign == "[":
                if "".join(self._buffer).strip():
                    self._error(SYNTAX_ERROR, (self._currline, self._currline))
                self._oldbefore = before
                self._buffer = []
                self._inside_attrib = True
                self._key = ""
                self._opened_tags.append(("[", self._currline, None))
                self._checkstr = _ATTRIB_SPECIALS

            # Closing attribute specification
            elif sign == "]":
                value = "".join(self._buffer) + before
                self._attrib = value.strip()
                self._inside_attrib = False
                self._buffer = []
                self._opened_tags.pop()
                self._checkstr = _GENERAL_SPECIALS

            # Quoting strings
            elif sign == "'" or sign == '"':
                if self._inside_quote:
                    self._checkstr = self._oldcheckstr
                    self._inside_quote = False
                    self._buffer.append(before + sign)
                    self._opened_tags.pop()
                else:
                    self._oldcheckstr = self._checkstr
                    self._checkstr = sign
                    self._inside_quote = True
                    self._buffer.append(before + sign)
                    self._opened_tags.append(('"', self._currline, None))

            # Interrupt
            elif sign == "<" and not self._after_equal_sign:
                txtinc = after.startswith("<<")
                hsdinc = after.startswith("<+")
                if txtinc:
                    self._text("".join(self._buffer) + before)
                    self._buffer = []
                    self._eventhandler.add_text(self._include_txt(after[2:]))
                    break
                elif hsdinc:
                    self._include_hsd(after[2:])
                    break
                else:
                    self._buffer.append(before + sign)

            else:
                self._error(SYNTAX_ERROR, (self._currline, self._currline))

            line = after


    def _text(self, text):
        stripped = text.strip()
        if stripped:
            self._eventhandler.add_text(stripped)


    def _starttag(self, tagname, closeprev):
        txt = "".join(self._buffer)
        if txt:
            self._text(txt)
        tagname_stripped = tagname.strip()
        if self._oldbefore:
            if tagname_stripped:
                self._error(SYNTAX_ERROR, (self._currline, self._currline))
            else:
                tagname_stripped = self._oldbefore.strip()
        if len(tagname_stripped.split()) > 1:
            self._error(SYNTAX_ERROR, (self._currline, self._currline))
        self._hsdoptions[common.HSDATTR_LINE] = self._currline
        #self._hsdoptions[common.HSDATTR_TAG] = tagname_stripped
        #tagname_stripped = tagname_stripped.lower()
        self._eventhandler.open_tag(tagname_stripped, self._attrib,
                                    self._hsdoptions)
        self._opened_tags.append(
            (tagname_stripped, self._currline, closeprev, self._has_child))
        self._buffer = []
        self._oldbefore = ""
        self._has_child = False
        self._attrib = None
        self._hsdoptions = OrderedDict()


    def _closetag(self):
        if not self._opened_tags:
            self._error(SYNTAX_ERROR, (0, self._currline))
        self._buffer = []
        tag, _, closeprev, self._has_child = self._opened_tags.pop()
        self._eventhandler.close_tag(tag)
        if closeprev:
            self._closetag()


    def _include_hsd(self, fname):
        fname = common.unquote(fname.strip())
        parser = HsdParser(defattrib=self._defattrib,
                           eventhandler=self._eventhandler)
        parser.feed(fname)


    @staticmethod
    def _include_txt(fname):
        fname = common.unquote(fname.strip())
        fp = open(fname, "r")
        txt = fp.read()
        fp.close()
        return txt


    def _error(self, errorcode, lines):
        error_msg = (
            "Parsing error ({}) between lines {} - {} in file '{}'.".format(
                errorcode, lines[0] + 1, lines[1] + 1, self._fname))
        raise common.HsdParserError(error_msg)



def _splitbycharset(txt, charset):
    """Splits a string at the first occurrence of a character in a set.

    Args:
        txt: Text to split.
        chars: Chars to look for.

    Returns:
        Tuple (char, before, after). Char is the character which had been found
        (or empty string if nothing was found). Before is the substring before
        the splitting character (or the entire string). After is the substring
        after the splitting character (or empty string).
    """
    for firstpos, char in enumerate(txt):
        if char in charset:
            return txt[firstpos], txt[:firstpos], txt[firstpos + 1:]
    return '', txt, ''
