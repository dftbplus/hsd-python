#!/bin/env python3
#------------------------------------------------------------------------------#
#  hsd: package for manipulating HSD-formatted data                            #
#  Copyright (C) 2011 - 2020  DFTB+ developers group                           #
#                                                                              #
#  See the LICENSE file for terms of usage and distribution.                   #
#------------------------------------------------------------------------------#
#
import io
import pytest
import hsd

_OPEN_TAG_EVENT = 1
_CLOSE_TAG_EVENT = 2
_ADD_TEXT_EVENT = 3

_HSD_LINE = 'line'
_HSD_EQUAL = 'equal'

_TESTS = [
    # Simple test
    ("""Test {} """,
     [(_OPEN_TAG_EVENT, "Test", None, {_HSD_LINE: 0}),
      (_CLOSE_TAG_EVENT, "Test"),
     ]
    ),

    # Test data with quoted strings
    ("""O = SelectedShells { "s" "p" }""",
     [(_OPEN_TAG_EVENT, "O", None, {_HSD_LINE: 0, _HSD_EQUAL: True}),
      (_OPEN_TAG_EVENT, 'SelectedShells', None, {_HSD_LINE: 0}),
      (_ADD_TEXT_EVENT, '"s" "p"'),
      (_CLOSE_TAG_EVENT, 'SelectedShells'),
      (_CLOSE_TAG_EVENT, 'O'),
     ]
    ),

    # Test attribute containing comma
    ("""PolarRadiusCharge [AA^3,AA,] = {\n1.030000  3.800000  2.820000\n}""",
     [(_OPEN_TAG_EVENT, "PolarRadiusCharge", "AA^3,AA,", {_HSD_LINE: 0, }),
      (_ADD_TEXT_EVENT, '1.030000  3.800000  2.820000'),
      (_CLOSE_TAG_EVENT, 'PolarRadiusCharge'),
     ]
    ),
]


class _TestEventHandler(hsd.HsdEventHandler):

    def __init__(self):
        self.events = []

    def open_tag(self, tagname, attrib, hsdoptions):
        self.events.append((_OPEN_TAG_EVENT, tagname, attrib, hsdoptions))

    def close_tag(self, tagname):
        self.events.append((_CLOSE_TAG_EVENT, tagname))

    def add_text(self, text):
        self.events.append((_ADD_TEXT_EVENT, text))


@pytest.mark.parametrize("hsd_input,expected_events", _TESTS)
def test_parser_events(hsd_input, expected_events):
    testhandler = _TestEventHandler()
    parser = hsd.HsdParser(eventhandler=testhandler)
    hsdfile = io.StringIO(hsd_input)
    parser.feed(hsdfile)
    assert testhandler.events == expected_events
