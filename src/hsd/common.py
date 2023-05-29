#--------------------------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python                               #
#  Copyright (C) 2011 - 2023  DFTB+ developers group                                               #
#  Licensed under the BSD 2-clause license.                                                        #
#--------------------------------------------------------------------------------------------------#
#
"""
Implements common functionalities for the HSD package
"""
try:
    import numpy as np
except ModuleNotFoundError:
    np = None



class HsdError(Exception):
    """Base class for exceptions in the HSD package."""


def unquote(txt):
    """Giving string without quotes if enclosed in those."""
    if len(txt) >= 2 and (txt[0] in "\"'") and txt[-1] == txt[0]:
        return txt[1:-1]
    return txt


# Name for default attribute (when attribute name is not specified)
DEFAULT_ATTRIBUTE = "unit"

# HSD attribute containing the original tag name
HSD_ATTRIB_NAME = "name"

# HSD attribute containing the line number
HSD_ATTRIB_LINE = "line"

# HSD attribute marking that a node is equal to its only child (instead of
# containing it)
HSD_ATTRIB_EQUAL = "equal"

# String quoting delimiters (must be at least two)
QUOTING_CHARS = "\"'"

# Special characters
SPECIAL_CHARS = "{}[]= "
