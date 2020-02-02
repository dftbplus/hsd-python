#------------------------------------------------------------------------------#
#  hsd: package for manipulating HSD-formatted data                            #
#  Copyright (C) 2011 - 2020  DFTB+ developers group                           #
#                                                                              #
#  See the LICENSE file for terms of usage and distribution.                   #
#------------------------------------------------------------------------------#
#
"""
Implements common functionalities for the HSD package
"""


class HsdException(Exception):
    """Base class for exceptions in the HSD package."""
    pass


class HsdQueryError(HsdException):
    """Base class for errors detected by the HsdQuery object.


    Attributes:
        filename: Name of the file where error occured (or empty string).
        line: Line where the error occurred (or -1).
        tag: Name of the tag with the error (or empty string).
    """

    def __init__(self, msg="", node=None):
        """Initializes the exception.

        Args:
            msg: Error message
            node: HSD element where error occured (optional).
        """
        super().__init__(msg)
        if node is not None:
            self.tag = node.gethsd(HSDATTR_TAG, node.tag)
            self.file = node.gethsd(HSDATTR_FILE, -1)
            self.line = node.gethsd(HSDATTR_LINE, None)
        else:
            self.tag = ""
            self.file = -1
            self.line = None


class HsdParserError(HsdException):
    """Base class for parser related errors."""
    pass


def unquote(txt):
    """Giving string without quotes if enclosed in those."""
    if len(txt) >= 2 and (txt[0] in "\"'") and txt[-1] == txt[0]:
        return txt[1:-1]
    return txt


# Name for default attribute (when attribute name is not specified)
DEFAULT_ATTRIBUTE = "attribute"


HSDATTR_PROC = "processed"
HSDATTR_EQUAL = "equal"
HSDATTR_FILE = "file"
HSDATTR_LINE = "line"
HSDATTR_TAG = "tag"
