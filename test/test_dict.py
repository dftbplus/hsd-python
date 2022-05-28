#!/bin/env python3
#--------------------------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python                               #
#  Copyright (C) 2011 - 2022  DFTB+ developers group                                               #
#  Licensed under the BSD 2-clause license.                                                        #
#--------------------------------------------------------------------------------------------------#
#
"""Tests for the dictbuilder class"""

import io
import pytest
import hsd

# Some abbreviations
_HSD_LINE = hsd.HSD_ATTRIB_LINE
_HSD_EQUAL = hsd.HSD_ATTRIB_EQUAL
_HSD_NAME = hsd.HSD_ATTRIB_NAME


# General test list format for valid tests
# [("Test name", ([List of HSD events], expected dictionary outcome))]

# Tests without hsd attribute recording
_TESTS_NO_HSDATTRIB = [
    (
        "Simple", (
            "Test {}",
            {"Test": {}},
        )
    ),
    (
        "Data with quoted strings", (
            "O = SelectedShells { \"s\" \"p\" }",
            {"O": {"SelectedShells": ['"s"', '"p"']}},
        )
    ),
    (
        "Attribute containing comma", (
            "PolarRadiusCharge [AA^3,AA,] = {\n1.030000  3.800000  2.820000\n}",
            {"PolarRadiusCharge": [1.03, 3.8, 2.82], "PolarRadiusCharge.attrib": "AA^3,AA,"},
        )
    ),
    (
        "Duplicate node entry", (
            "a { b = 1 }\na { b = 2 }\n",
            {"a.attrib": [None, None], "a": [{"b": 1}, {"b": 2}]},
        )
    ),
    (
        "Duplicate value entry", (
            "a = 1\na = 2",
            {"a.attrib": [None, None], "a": [{None: 1}, {None: 2}]},
        )
    ),
]
_TESTS_NO_HSDATTRIB_NAMES, _TESTS_NO_HSDATTRIB_CASES = zip(*_TESTS_NO_HSDATTRIB)


# Tests with HSD attribute recording
# The input string should be formatted the same way as it comes out from the formatter since
# these tests are also used to test backwards direction (dictionary -> string).
_TESTS_HSDATTRIB = [
    (
        "Simple", (
            "Test {}\n",
            {"Test.hsdattrib": {_HSD_LINE: 0, _HSD_EQUAL: False}, "Test": {}}
        )
    ),
    (
        "Data with quoted strings", (
            "O = SelectedShells {\n  \"s\" \"p\"\n}\n",
            {
                "O.hsdattrib": {_HSD_EQUAL: True, _HSD_LINE: 0},
                "O": {
                    "SelectedShells.hsdattrib": {_HSD_LINE: 0, _HSD_EQUAL: False},
                    "SelectedShells": ['"s"', '"p"']
                    }
            }
        )
    ),
    (
        "Duplicate node", (
            "a {\n  b = 1\n}\na {\n  b = 2\n}\n",
            {
                "a.hsdattrib": [{_HSD_LINE: 0, _HSD_EQUAL: False},
                                {_HSD_LINE: 3, _HSD_EQUAL: False}],
                "a.attrib": [None, None],
                "a": [
                    {"b.hsdattrib": {_HSD_LINE: 1, _HSD_EQUAL: True}, "b": 1},
                    {"b.hsdattrib": {_HSD_LINE: 4, _HSD_EQUAL: True}, "b": 2}
                ]
            },
        )
    ),
    (
        "Duplicate value", (
            "a = 1\na = 2\n",
            {
                "a.hsdattrib": [{_HSD_LINE: 0, _HSD_EQUAL: True}, {_HSD_LINE: 1, _HSD_EQUAL: True}],
                "a.attrib": [None, None],
                "a": [{None: 1}, {None: 2}]
            },
        )
    ),
    (
        "Triple value with attrib", (
            "a = 1\na = 2\na [someunit] {\n  3\n}\n",
            {
                "a.hsdattrib": [{_HSD_LINE: 0, _HSD_EQUAL: True}, {_HSD_LINE: 1, _HSD_EQUAL: True},
                                {_HSD_LINE: 2, _HSD_EQUAL: False}],
                "a.attrib": [None, None, "someunit"],
                "a": [{None: 1}, {None: 2}, {None: 3}]
            },
        )
    ),

]
_TESTS_HSDATTRIB_NAMES, _TESTS_HSDATTRIB_CASES = zip(*_TESTS_HSDATTRIB)


# Tests with HSD attribute recording and tag name lowering switched on
# The input string should be formatted the same way as it comes out from the formatter since
# these tests are also used to test backwards direction (dictionary -> string).
_TESTS_HSDATTRIB_LOWER = [
    (
        "Simple", (
            "Test {}\n",
            {"test.hsdattrib": {_HSD_NAME: "Test", _HSD_LINE: 0, _HSD_EQUAL: False}, "test": {}}
        )
    ),
]
_TESTS_HSDATTRIB_LOWER_NAMES, _TESTS_HSDATTRIB_LOWER_CASES = zip(*_TESTS_HSDATTRIB_LOWER)


@pytest.mark.parametrize(
    "hsdstr,hsddict",
    _TESTS_NO_HSDATTRIB_CASES,
    ids=_TESTS_NO_HSDATTRIB_NAMES
)
def test_dict_builder_nohsdattr(hsdstr, hsddict):
    """Test transformation from hsd to dictionary without HSD attributes."""
    dictbuilder = hsd.HsdDictBuilder(include_hsd_attribs=False)
    parser = hsd.HsdParser(eventhandler=dictbuilder)
    fobj = io.StringIO(hsdstr)
    parser.parse(fobj)
    assert dictbuilder.hsddict == hsddict


@pytest.mark.parametrize(
    "hsdstr,hsddict",
    _TESTS_HSDATTRIB_CASES,
    ids=_TESTS_HSDATTRIB_NAMES
)
def test_dict_builder_hsdattr(hsdstr, hsddict):
    """Test transformation from hsd to dictionary with HSD attributes."""
    dictbuilder = hsd.HsdDictBuilder(include_hsd_attribs=True)
    parser = hsd.HsdParser(eventhandler=dictbuilder)
    fobj = io.StringIO(hsdstr)
    parser.parse(fobj)
    assert dictbuilder.hsddict == hsddict


@pytest.mark.parametrize(
    "hsdstr,hsddict",
    _TESTS_HSDATTRIB_LOWER_CASES,
    ids=_TESTS_HSDATTRIB_LOWER_NAMES
)
def test_dict_builder_hsdattr_lower(hsdstr, hsddict):
    """Test transformation from hsd to dictionary with HSD attributes and case lowering."""
    dictbuilder = hsd.HsdDictBuilder(include_hsd_attribs=True, lower_tag_names=True)
    parser = hsd.HsdParser(eventhandler=dictbuilder)
    fobj = io.StringIO(hsdstr)
    parser.parse(fobj)
    assert dictbuilder.hsddict == hsddict


@pytest.mark.parametrize(
    "hsdstr,hsddict",
    _TESTS_HSDATTRIB_CASES,
    ids=_TESTS_HSDATTRIB_NAMES
)
def test_dict_walker_hsdattr(hsdstr, hsddict):
    """Test transformation from dictionary to string using HSD attributes."""
    output = io.StringIO()
    formatter = hsd.HsdFormatter(output, use_hsd_attribs=True)
    dictwalker = hsd.HsdDictWalker(formatter)
    dictwalker.walk(hsddict)
    assert output.getvalue() == hsdstr


@pytest.mark.parametrize(
    "hsdstr,hsddict",
    _TESTS_HSDATTRIB_LOWER_CASES,
    ids=_TESTS_HSDATTRIB_LOWER_NAMES
)
def test_dict_walker_hsdattr_lower(hsdstr, hsddict):
    """Test transformation from dictionary to string using HSD attributes."""
    output = io.StringIO()
    formatter = hsd.HsdFormatter(output, use_hsd_attribs=True)
    dictwalker = hsd.HsdDictWalker(formatter)
    dictwalker.walk(hsddict)
    assert output.getvalue() == hsdstr
