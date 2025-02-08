#--------------------------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python                               #
#  Copyright (C) 2011 - 2025  DFTB+ developers group                                               #
#  Licensed under the BSD 2-clause license.                                                        #
#--------------------------------------------------------------------------------------------------#
#
"""
Contains an event handler base class.
"""

from abc import ABC, abstractmethod
from typing import Optional


class HsdEventHandler(ABC):
    """Abstract base class for handling HSD events."""

    @abstractmethod
    def open_tag(self, tagname: str, attrib: Optional[str],
                 hsdattrib: Optional[dict]):
        """Opens a tag.

        Args:
            tagname: Name of the tag which had been opened.
            attrib: String containing the attribute of the tag or None.
            hsdattrib: Dictionary of the options created during the processing
                in the hsd-parser.
        """

    @abstractmethod
    def close_tag(self, tagname: str):
        """Closes a tag.

        Args:
            tagname: Name of the tag which had been closed.
        """

    @abstractmethod
    def add_text(self, text: str):
        """Adds text (data) to the current tag.

        Args:
           text: Text in the current tag.
        """



class HsdEventPrinter(HsdEventHandler):
    """Minimal demonstration class for event handlers.

    This specifc implemenation prints the events. Subclassing instances
    should override the public methods to customize its behavior.
    """

    def __init__(self):
        """Initializes the default event printer."""
        self._indentlevel = 0
        self._indentstr = "  "


    def open_tag(self, tagname: str, attrib: str, hsdattrib: dict):
        indentstr = self._indentlevel * self._indentstr
        print(f"{indentstr}OPENING TAG: {tagname}")
        print(f"{indentstr}ATTRIBUTE: {attrib}")
        print(f"{indentstr}HSD ATTRIBUTE: {str(hsdattrib)}")
        self._indentlevel += 1


    def close_tag(self, tagname: str):
        self._indentlevel -= 1
        indentstr = self._indentlevel * self._indentstr
        print(f"{indentstr}CLOSING TAG: {tagname}")


    def add_text(self, text: str):
        indentstr = self._indentlevel * self._indentstr
        print(f"{indentstr}Received text: {text}")
