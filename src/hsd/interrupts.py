#--------------------------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python                               #
#  Copyright (C) 2011 - 2023  DFTB+ developers group                                               #
#  Licensed under the BSD 2-clause license.                                                        #
#--------------------------------------------------------------------------------------------------#
#
"""
Contains hsd interrupts
"""

from hsd.common import unquote


class Interrupt:
    """General class for interrupts"""

    def __init__(self, file):
        self.file = unquote(file.strip())


class IncludeText(Interrupt):
    """class for dealing with text interrupts"""
    pass

class IncludeHsd(Interrupt):
    """class for dealing with hsd interrupts"""
    pass
