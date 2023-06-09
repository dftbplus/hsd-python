#!/bin/env python3
# ------------------------------------------------------------------------------------------------ #
# hsd-python: package for manipulating HSD-formatted data in Python                                #
# Copyright (C) 2011 - 2023  DFTB+ developers group                                                #
# Licensed under the BSD 2-clause license.                                                         #
# ------------------------------------------------------------------------------------------------ #
#
"""Tests for the hsdwrappers module"""

import pytest
import numpy as np
import hsd

_DICT = {
    "Ham": {
        "Dftb": {
            "Scc": True,
            "Filling": {
                "Fermi": {
                    "Temp": 100,
                    "Temp.attrib": "K",
                }
            },
            "EField": {
                "PCharges": [
                    {"Coords": np.array([0.0, 1.0, 2.0, 3.0])},
                    {"Coords": np.array([0.0, -1.0, 2.0, 3.0])},
                ],
                "PCharges.attrib": ["Pointy", "Smeared"],
            },
        },
    },
}

_HSD_DICT = hsd.HsdDict.copy(_DICT)

_HSD_DICT_LOW = hsd.HsdDict.copy(_DICT, lower_names=True, save_names=True)


def test_tuple_path_access():
    assert _HSD_DICT["Ham", "Dftb", "Scc"].value == True
    coords = _HSD_DICT["Ham", "Dftb", "EField", "PCharges", 1, "Coords"].value
    assert np.all(np.isclose(coords, np.array([0.0, -1.0, 2.0, 3.0])))


def test_string_path_access():
    assert _HSD_DICT["Ham / Dftb / Scc"].value == True
    coords = _HSD_DICT["Ham / Dftb / EField / PCharges / 1 / Coords"].value
    assert np.all(np.isclose(coords, np.array([0.0, -1.0, 2.0, 3.0])))


def test_path_failure():
    with pytest.raises(KeyError) as exc:
        _HSD_DICT["Ham / dftb / Scc"]
    with pytest.raises(KeyError) as exc:
        _HSD_DICT["Ham / Dftb / EField / PCharges / 9 / Coords"].value


def test_self_equality():
    assert _HSD_DICT == _HSD_DICT
    assert _HSD_DICT_LOW == _HSD_DICT_LOW


def test_lowered_unequal_original():
    assert _HSD_DICT_LOW != _DICT


def test_lowered_access():
    assert _HSD_DICT_LOW["ham", "dftb", "scc"].value == True
    assert _HSD_DICT_LOW["Ham", "Dftb", "Scc"].value == True
    coords = _HSD_DICT_LOW["ham", "dftb", "efield", "pcharges", 1, "coords"].value
    assert np.all(np.isclose(coords, np.array([0.0, -1.0, 2.0, 3.0])))
    coords = _HSD_DICT_LOW["Ham", "Dftb", "EField", "PCharges", 1, "Coords"].value
    assert np.all(np.isclose(coords, np.array([0.0, -1.0, 2.0, 3.0])))


def test_attrib():
    assert _HSD_DICT_LOW["Ham", "Dftb", "Filling", "Fermi", "Temp"].attrib == "K"
    attribs = _HSD_DICT_LOW["ham / dftb / efield / pcharges"].attrib
    assert attribs == ["Pointy", "Smeared"]
    assert _HSD_DICT_LOW["ham / dftb / efield / pcharges / 0"].attrib == "Pointy"
    assert _HSD_DICT_LOW["ham / dftb / efield / pcharges / 1"].attrib == "Smeared"


def test_hsdattrib_name():
    name = _HSD_DICT_LOW["ham"].hsdattrib["name"]
    assert name == "Ham"
    hattrs = _HSD_DICT_LOW["HAM", "DFTB", "EFIELD", "PCHARGES"].hsdattrib
    assert len(hattrs) == 2
    assert hattrs[0]["name"] == "PCharges"
    assert hattrs[1]["name"] == "PCharges"


def test_setting_value():
    hdict = hsd.HsdDict.copy({"a1": {"b1": 1}})
    hdict["a1 / b1"] = 9
    val = hdict["a1 / b1"]
    assert val.value == 9
    assert val.attrib is None


def test_setting_hsdvalue():
    hdict = hsd.HsdDict.copy({"a1": {"b1": 1}})
    hdict["a1 / b1"] = hsd.HsdValue(9, "kg")
    val = hdict["a1 / b1"]
    assert val.value == 9
    assert val.attrib == "kg"
    assert hdict.value["a1"]["b1"] == 9
    assert hdict.value["a1"]["b1.attrib"] == "kg"


def test_del():
    inp = {
        "a1": {
            "b1": 1,
            "b1.attrib": "K",
            "b1.hsdattrib": {"name": "B1"},
            "b2": 2,
        },
    }
    hdict = hsd.HsdDict.copy(inp)
    del hdict["a1 / b1"]
    assert hdict == hsd.HsdDict.copy({"a1": {"b2": 2}})

    del hdict["a1 / b2"]
    assert hdict == hsd.HsdDict.copy({"a1": {}})

    del hdict["a1"]
    assert hdict == hsd.HsdDict.copy({})


def test_insert():
    inp = {
        "a1": [
            {"b1": 1},
            {"b3": 3},
        ],
        "a1.attrib": ["cm", "km"],
        "a1.hsdattrib": [{"name": "A1"}, {"name": "A1"}],
    }
    out = {
        "a1": [
            {"b1": 1},
            {"b2": 2},
            {"b3": 3},
        ],
        "a1.attrib": ["cm", "pc", "km"],
        "a1.hsdattrib": [{"name": "A1"}, {"name": "A1"}, {"name": "A1"}],
    }

    hdict = hsd.HsdDict.copy(inp, lower_names=True, save_names=True)
    newitem = hsd.HsdDict(
        {}, attrib="pc", hsdattrib={"name": "A1"}, lower_names=True, save_names=True
    )
    newitem["b2"] = hsd.HsdValue(2)
    a1list = hdict["A1"]
    a1list.insert(1, newitem)
    assert hdict == hsd.HsdDict.copy(out, lower_names=True, save_names=True)


def test_list_name_rewriting():
    inp = hsd.HsdDict({}, lower_names=True, save_names=True)
    out = {
        "a1": [{"b1": 1}, {"b2": 2}],
        "a1.hsdattrib": [{}, {}],
    }
    hsdlist = hsd.HsdList(
        [{"b1": 1}, {"b2": 2}], hsdattrib=[{"name": "A1"}, {"name": "A1"}]
    )
    inp["a1"] = hsdlist
    assert inp == hsd.HsdDict(out)


def test_get_item():
    inp = {"a": 1}
    hdict = hsd.HsdDict.copy(inp)
    assert hdict.get_item("a").value == 1
    assert hdict.get_item("b", default=hsd.HsdValue(23)).value == 23
    assert hdict == hsd.HsdDict(inp)


def test_set_item():
    inp = {"a": 1}
    hinp = hsd.wrap(inp)
    hinp.set_item("b", 2)
    assert hinp == hsd.HsdDict({"a": 1, "b": 2})
    with pytest.raises(KeyError):
        hinp.set_item("c / d", 3)
    hinp.set_item("c / d", 3, parents=True)
    assert hinp == hsd.HsdDict({"a": 1, "b": 2, "c": {"d": 3}})


def test_set_default_existing_key():
    inp = {"a": 1}
    hinp = hsd.wrap(inp)
    hinp2 = hsd.copy(hinp)
    val = hinp2.set_default("a", default=9)
    assert val == hsd.HsdValue(1)
    assert hinp2 == hinp


def test_set_default_missing_key():
    inp = {"a": 1}
    hinp = hsd.wrap(inp)
    val = hinp.set_default("b", default=9)
    assert val == 9
    assert hinp == hsd.HsdDict({"a": 1, "b": 9})


def test_set_default_missing_key_parents():
    inp = {"a": 1}
    hinp = hsd.wrap(inp)
    with pytest.raises(KeyError) as _:
        val = hinp.set_default("b/c", default=3)
    val = hinp.set_default("b/c", default=3, parents=True)
    assert val == 3
    assert hinp == hsd.HsdDict({"a": 1, "b": {"c": 3}})
