#!/bin/env python3
#--------------------------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python                               #
#  Copyright (C) 2011 - 2023  DFTB+ developers group                                               #
#  Licensed under the BSD 2-clause license.                                                        #
#--------------------------------------------------------------------------------------------------#
#
import io
import pytest
import hsd

_OPEN_TAG_EVENT = 1
_CLOSE_TAG_EVENT = 2
_ADD_TEXT_EVENT = 3

_HSD_LINE = hsd.HSD_ATTRIB_LINE
_HSD_EQUAL = hsd.HSD_ATTRIB_EQUAL
_HSD_NAME = hsd.HSD_ATTRIB_NAME

_VALID_TESTS = [
    (
        "Simple", (
            """Test {} """,
            [
                (_OPEN_TAG_EVENT, "Test", None, {_HSD_LINE: 0, _HSD_EQUAL: False}),
                (_CLOSE_TAG_EVENT, "Test"),
            ]
        )
    ),
    (
        "Data with quoted strings", (
            """O = SelectedShells { "s" "p" }""",
            [
                (_OPEN_TAG_EVENT, "O", None, {_HSD_LINE: 0, _HSD_EQUAL: True}),
                (_OPEN_TAG_EVENT, 'SelectedShells', None, {_HSD_LINE: 0, _HSD_EQUAL: False}),
                (_ADD_TEXT_EVENT, '"s" "p"'),
                (_CLOSE_TAG_EVENT, 'SelectedShells'),
                (_CLOSE_TAG_EVENT, 'O'),
            ]
        )
    ),
    (
        "Attribute containing comma", (
            """PolarRadiusCharge [AA^3,AA,] = {\n1.030000  3.800000  2.820000\n}""",
            [
                (_OPEN_TAG_EVENT, "PolarRadiusCharge", "AA^3,AA,",
                 {_HSD_LINE: 0, _HSD_EQUAL: False}),
                (_ADD_TEXT_EVENT, '1.030000  3.800000  2.820000'),
                (_CLOSE_TAG_EVENT, 'PolarRadiusCharge'),
            ]
        )
    ),
    (
        "Variable", (
            """$Variable = 12\nValue = $Variable\n""",
            [
                (_OPEN_TAG_EVENT, "$Variable", None, {_HSD_LINE: 0, _HSD_EQUAL: True}),
                (_ADD_TEXT_EVENT, "12"),
                (_CLOSE_TAG_EVENT, "$Variable"),
                (_OPEN_TAG_EVENT, "Value", None, {_HSD_LINE: 1, _HSD_EQUAL: True}),
                (_ADD_TEXT_EVENT, "$Variable"),
                (_CLOSE_TAG_EVENT, "Value")
            ]
        )
    ),
]

_VALID_TEST_NAMES, _VALID_TEST_CASES = zip(*_VALID_TESTS)


_FAILING_TESTS = [
    (
        "Node-less data", (
            """a = 2\n15\n"""
        )
    ),
    (
        "Node-less data at start", (
            """15\na = 2\na = 4\n"""
        )
    ),
    (
        "Node-less data in child", (
            """a {\n12\nb = 5\n}\n"""
        )
    ),
    (
        "Quoted tag name", (
            """\"mytag\" = 12\n"""
        )
    ),

]

_FAILING_TEST_NAMES, _FAILING_TEST_CASES = zip(*_FAILING_TESTS)


class _TestEventHandler(hsd.HsdEventHandler):

    def __init__(self):
        self.events = []

    def open_tag(self, tagname, attrib, hsdattrib):
        self.events.append((_OPEN_TAG_EVENT, tagname, attrib, hsdattrib))

    def close_tag(self, tagname):
        self.events.append((_CLOSE_TAG_EVENT, tagname))

    def add_text(self, text):
        self.events.append((_ADD_TEXT_EVENT, text))


@pytest.mark.parametrize(
    "hsd_input,expected_events",
    _VALID_TEST_CASES,
    ids=_VALID_TEST_NAMES
)
def test_parser_events(hsd_input, expected_events):
    """Test valid parser events"""
    testhandler = _TestEventHandler()
    parser = hsd.HsdParser(eventhandler=testhandler)
    hsdfile = io.StringIO(hsd_input)
    parser.parse(hsdfile)
    assert testhandler.events == expected_events


@pytest.mark.parametrize(
    "hsd_input",
    _FAILING_TEST_CASES,
    ids=_FAILING_TEST_NAMES
)
def test_parser_exceptions(hsd_input):
    """Test exception raised by the parser"""
    testhandler = _TestEventHandler()
    parser = hsd.HsdParser(eventhandler=testhandler)
    hsdfile = io.StringIO(hsd_input)
    with pytest.raises(hsd.HsdError):
        parser.parse(hsdfile)
