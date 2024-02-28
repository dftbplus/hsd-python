#--------------------------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python                               #
#  Copyright (C) 2011 - 2024  DFTB+ developers group                                               #
#  Licensed under the BSD 2-clause license.                                                        #
#--------------------------------------------------------------------------------------------------#
#
"""
Contains the event-generating HSD-parser.
"""
from typing import Optional, TextIO, Union
from hsd import common
from hsd.eventhandler import HsdEventHandler, HsdEventPrinter


SYNTAX_ERROR = 1
UNCLOSED_TAG_ERROR = 2
UNCLOSED_ATTRIB_ERROR = 3
UNCLOSED_QUOTATION_ERROR = 4
ORPHAN_TEXT_ERROR = 5

_GENERAL_SPECIALS = "{}[]<=\"'#;"

_ATTRIB_SPECIALS = "]\"'"


class HsdParser:
    """Event based parser for the HSD format.

    Arguments:
        eventhandler: Object which should handle the HSD-events triggered
            during parsing. When not specified, HsdEventPrinter() is used.

    Examples:
        >>> from io import StringIO
        >>> dictbuilder = hsd.HsdDictBuilder()
        >>> parser = hsd.HsdParser(eventhandler=dictbuilder)
        >>> hsdfile = StringIO(\"\"\"
        ... Hamiltonian {
        ...     Dftb {
        ...         Scc = Yes
        ...         Filling = Fermi {
        ...             Temperature [Kelvin] = 100
        ...         }
        ...     }
        ... }
        ... \"\"\")
        >>> parser.parse(hsdfile)
        >>> dictbuilder.hsddict
        {'Hamiltonian': {'Dftb': {'Scc': True, 'Filling': {'Fermi':
        {'Temperature': 100, 'Temperature.attrib': 'Kelvin'}}}}}
    """

    def __init__(self, eventhandler: Optional[HsdEventHandler] = None):
        """Initializes the parser.

        Args:
            eventhandler: Instance of the HsdEventHandler class or its children.
        """
        if eventhandler is None:
            self._eventhandler = HsdEventPrinter()
        else:
            self._eventhandler = eventhandler

        self._fname = ""                   # name of file being processed
        self._checkstr = _GENERAL_SPECIALS # special characters to look for
        self._oldcheckstr = ""             # buffer fo checkstr
        self._opened_tags = []             # info about opened tags
        self._buffer = []                  # buffering plain text between lines
        self._attrib = None                # attribute for current tag
        self._hsdattrib = {}               # hsd-options for current tag
        self._currline = 0                 # nr. of current line in file
        self._after_equal_sign = False     # last tag was opened with equal sign
        self._inside_attrib = False        # parser inside attrib specification
        self._inside_quote = False         # parser inside quotation
        self._has_child = True             # Whether current node has a child already
        self._has_text = False             # whether current node contains text already
        self._oldbefore = ""               # buffer for tagname


    def parse(self, fobj: Union[TextIO, str]):
        """Parses the provided file-like object.

        The parser will process the data and trigger the corresponding events
        in the eventhandler which was passed at initialization.

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
                    if before.strip().startswith("$"):
                        self._eventhandler.retrieve_tag(before)
                        before = ""
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
                if after.lstrip().startswith("{"):                    # _oldbefore may already contain the tagname, if the                    # tagname was followed by an attribute -> append
                    self._oldbefore += before
                else:
                    self._hsdattrib[common.HSD_ATTRIB_EQUAL] = True
                    self._starttag(before, False)
                    self._after_equal_sign = True

            # Opening tag by curly brace
            elif sign == "{":
                #self._has_child = True
                self._hsdattrib[common.HSD_ATTRIB_EQUAL] = False
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
                self._opened_tags.append(("[", self._currline, None, None, None))
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
            elif sign in ("'", '"'):
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
                    self._opened_tags.append(('"', self._currline, None, None, None))

            # Interrupt
            elif sign == "<" and not self._after_equal_sign:
                txtinc = after.startswith("<<")
                hsdinc = after.startswith("<+")
                if txtinc:
                    self._text("".join(self._buffer) + before)
                    self._buffer = []
                    self._eventhandler.add_text(self._include_txt(after[2:]))
                    break
                if hsdinc:
                    self._include_hsd(after[2:])
                    break
                self._buffer.append(before + sign)

            else:
                self._error(SYNTAX_ERROR, (self._currline, self._currline))

            line = after


    def _text(self, text):
        stripped = text.strip()
        if stripped:
            if self._has_child:
                self._error(SYNTAX_ERROR, (self._currline, self._currline))
            self._eventhandler.add_text(stripped)
            self._has_text = True


    def _starttag(self, tagname, closeprev):
        txt = "".join(self._buffer)
        if txt:
            self._text(txt)
        if self._has_text:
            self._error(SYNTAX_ERROR, (self._currline, self._currline))
        tagname_stripped = tagname.strip()
        if self._oldbefore:
            if tagname_stripped:
                self._error(SYNTAX_ERROR, (self._currline, self._currline))
            else:
                tagname_stripped = self._oldbefore.strip()
        if len(tagname_stripped.split()) > 1:
            self._error(SYNTAX_ERROR, (self._currline, self._currline))
        self._hsdattrib[common.HSD_ATTRIB_LINE] = self._currline
        self._eventhandler.open_tag(tagname_stripped, self._attrib,
                                    self._hsdattrib)
        self._opened_tags.append(
            (tagname_stripped, self._currline, closeprev, True, False))
        self._has_child = False
        self._buffer = []
        self._oldbefore = ""
        self._attrib = None
        self._hsdattrib = {}


    def _closetag(self):
        if not self._opened_tags:
            self._error(SYNTAX_ERROR, (0, self._currline))
        self._buffer = []
        tag, _, closeprev, self._has_child, self._has_text = self._opened_tags.pop()
        self._eventhandler.close_tag(tag)
        if closeprev:
            self._closetag()


    def _include_hsd(self, fname):
        fname = common.unquote(fname.strip())
        parser = HsdParser(eventhandler=self._eventhandler)
        parser.parse(fname)


    @staticmethod
    def _include_txt(fname):
        fname = common.unquote(fname.strip())
        with open(fname, "r") as fp:
            txt = fp.read()
        return txt


    def _error(self, errorcode, lines):
        error_msg = (
            "Parsing error ({}) between lines {} - {} in file '{}'.".format(
                errorcode, lines[0] + 1, lines[1] + 1, self._fname))
        raise common.HsdError(error_msg)



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
