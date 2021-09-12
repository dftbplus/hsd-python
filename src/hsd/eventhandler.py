"""Contains an event handler base class."""


class HsdEventHandler:
    """Base class for event handler implementing simple printing"""

    def __init__(self):
        """Initializes the default event handler"""
        self._indentlevel = 0
        self._indentstr = "  "


    def open_tag(self, tagname, attrib, hsdattrib):
        """Handler which is called when a tag is opened.

        It should be overriden in the application to handle the event in a
        customized way.

        Args:
            tagname: Name of the tag which had been opened.
            attrib: String containing the attribute of the tag or None.
            hsdattrib: Dictionary of the options created during the processing
                in the hsd-parser.
        """
        indentstr = self._indentlevel * self._indentstr
        print("{}OPENING TAG: {}".format(indentstr, tagname))
        print("{}ATTRIBUTE: {}".format(indentstr, attrib))
        print("{}HSD OPTIONS: {}".format(indentstr, str(hsdattrib)))
        self._indentlevel += 1


    def close_tag(self, tagname):
        """Handler which is called when a tag is closed.

        It should be overriden in the application to handle the event in a
        customized way.

        Args:
            tagname: Name of the tag which had been closed.
        """
        indentstr = self._indentlevel * self._indentstr
        print("{}CLOSING TAG: {}".format(indentstr, tagname))
        self._indentlevel -= 1


    def add_text(self, text):
        """Handler which is called with the text found inside a tag.

        It should be overriden in the application to handle the event in a
        customized way.

        Args:
           text: Text in the current tag.
        """
        indentstr = self._indentlevel * self._indentstr
        print("{}Received text: {}".format(indentstr, text))
