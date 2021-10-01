#------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python           #
#  Copyright (C) 2011 - 2021  DFTB+ developers group                           #
#  Licensed under the BSD 2-clause license.                                    #
#------------------------------------------------------------------------------#
#
"""
Toolbox for reading, writing and manipulating HSD-data.
"""
from .common import HSD_ATTRIB_LINE, HSD_ATTRIB_EQUAL, HSD_ATTRIB_SUFFIX,\
     HSD_ATTRIB_NAME, HsdError
from .dict import HsdDictBuilder, HsdDictWalker
from .eventhandler import HsdEventHandler, HsdEventPrinter
from .formatter import HsdFormatter
from .io import load, load_string, dump, dump_string
from .parser import HsdParser
