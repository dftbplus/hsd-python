#------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python           #
#  Copyright (C) 2011 - 2021  DFTB+ developers group                           #
#  Licensed under the BSD 2-clause license.                                    #
#------------------------------------------------------------------------------#
#
"""
Implements common functionalities for the HSD package
"""


class HsdError(Exception):
    """Base class for exceptions in the HSD package."""


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