#------------------------------------------------------------------------------#
#  hsd: package for manipulating HSD-formatted data                            #
#  Copyright (C) 2011 - 2020  DFTB+ developers group                           #
#                                                                              #
#  See the LICENSE file for terms of usage and distribution.                   #
#------------------------------------------------------------------------------#
#
"""
Central module for the hsd package
"""
from .dump import dump, dumps
from .parser import HsdParser
from .dictbuilder import HsdDictBuilder

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
