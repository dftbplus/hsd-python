#--------------------------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python                               #
#  Copyright (C) 2011 - 2021  DFTB+ developers group
                   #                    # BSD 2-clause license.
                    #
#--------------------------------------------------------------------------------------------------#
#
"""
Toolbox for reading, writing and manipulating HSD-data.
"""
from hsd.common import HSD_ATTRIB_LINE, HSD_ATTRIB_EQUAL, HSD_ATTRIB_SUFFIX,\
     HSD_ATTRIB_NAME, HsdError
from hsd.dict import HsdDictBuilder, HsdDictWalker
from hsd.eventhandler import HsdEventHandler, HsdEventPrinter
from hsd.formatter import HsdFormatter
from hsd.io import load, load_string, dump, dump_string
from hsd.parser import HsdParser

__version__ = '0.1'
