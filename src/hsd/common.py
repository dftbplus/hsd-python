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


class HsdParserError(HsdException):
    """Base class for parser related errors."""


def unquote(txt):
    """Giving string without quotes if enclosed in those."""
    if len(txt) >= 2 and (txt[0] in "\"'") and txt[-1] == txt[0]:
        return txt[1:-1]
    return txt


# Name for default attribute (when attribute name is not specified)
DEFAULT_ATTRIBUTE = "unit"

# Suffix to mark attribute
ATTRIB_SUFFIX = ".attrib"

# Length of the attribute suffix
LEN_ATTRIB_SUFFIX = len(ATTRIB_SUFFIX)

# Suffix to mark hsd processing attributes
HSD_ATTRIB_SUFFIX = ".hsdattrib"

# Lengths of hsd processing attribute suffix
LEN_HSD_ATTRIB_SUFFIX = len(HSD_ATTRIB_SUFFIX)


HSD_ATTRIB_LINE = "line"

HSD_ATTRIB_EQUAL = "equal"

HSD_ATTRIB_TAG = "tag"