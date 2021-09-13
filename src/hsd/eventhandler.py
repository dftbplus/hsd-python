#------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python           #
#  Copyright (C) 2011 - 2021  DFTB+ developers group                           #
#  Licensed under the BSD 2-clause license.                                    #
#------------------------------------------------------------------------------#
#
"""
Contains an event handler base class.
"""


class HsdEventHandler:
    """Base class for event handlers.

    This specifc implemenation prints the events. Subclassing instances
    should override the public methods to customize its behavior.
    """

    def __init__(self):
        """Initializes the default event handler"""
        self._indentlevel = 0
        self._indentstr = "  "


    def open_tag(self, tagname: str, attrib: str, hsdattrib: dict):
        """Opens a tag.

        Args:
            tagname: Name of the tag which had been opened.
            attrib: String containing the attribute of the tag or None.
            hsdattrib: Dictionary of the options created during the processing
                in the hsd-parser.
        """
        indentstr = self._indentlevel * self._indentstr
        print("{}OPENING TAG: {}".format(indentstr, tagname))
        print("{}ATTRIBUTE: {}".format(indentstr, attrib))
        print("{}HSD ATTRIBUTE: {}".format(indentstr, str(hsdattrib)))
        self._indentlevel += 1


    def close_tag(self, tagname: str):
        """Closes a tag.

        Args:
            tagname: Name of the tag which had been closed.
        """
        indentstr = self._indentlevel * self._indentstr
        print("{}CLOSING TAG: {}".format(indentstr, tagname))
        self._indentlevel -= 1


    def add_text(self, text: str):
        """Adds text (data) to the current tag.

        Args:
           text: Text in the current tag.
        """
        indentstr = self._indentlevel * self._indentstr
        print("{}Received text: {}".format(indentstr, text))
