#------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python           #
#  Copyright (C) 2011 - 2021  DFTB+ developers group                           #
#  Licensed under the BSD 2-clause license.                                    #
#------------------------------------------------------------------------------#
#
"""
Toolbox for reading, writing and manipulating HSD-data.
"""
from .dictbuilder import HsdDictBuilder
from .eventhandler import HsdEventHandler
from .io import load, load_string, dump, dump_string
from .parser import HsdParser
