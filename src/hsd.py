#!/usr/bin/env python3
#------------------------------------------------------------------------------#
#  hsd: package for manipulating HSD-formatted data                            #
#  Copyright (C) 2020  Bálint Aradi, Universität Bremen                        #
#                                                                              #
#  See the LICENSE file for terms of usage and distribution.                   #
#------------------------------------------------------------------------------#
#
"""
Provides functionality to convert Python structures to HSD
"""
import io
import numpy as np

__all__ = ['dump', 'dumps']


_INDENT_STR = "  "

# String quoting delimiters (must be at least two)
_QUOTING_CHARS = "\"'"

# Suffix for appending attributes
_ATTRIBUTE_SUFFIX = ".attribute"


def dump(obj, fobj):
    """Serializes an object to a file in HSD format.

    Args:
        obj: Object to be serialized in HSD format
        fobj: File like object to write the result to.
    """

    if isinstance(obj, dict):
        _dump_dict(obj, fobj, "")
    else:
        msg = "Invalid object type"
        raise TypeError(msg)


def dumps(obj):
    """Serializes an object to string in HSD format.

    Args:
        obj: Object to serialize.

    Returns:
        HSD formatted string.
    """
    result = io.StringIO()
    dump(obj, result)
    return result.getvalue()


def _dump_dict(obj, fobj, indentstr):
    for key, value in obj.items():
        if key.endswith(_ATTRIBUTE_SUFFIX):
            if key[:-len(_ATTRIBUTE_SUFFIX)] in obj:
                continue
            else:
                msg = "Attribute '{}' without corresponding tag '{}'"\
                      .format(key, key[:-len(_ATTRIBUTE_SUFFIX)])
                raise ValueError(msg)
        attrib = obj.get(key + _ATTRIBUTE_SUFFIX)
        if attrib is None:
            attribstr = ""
        elif not isinstance(attrib, str):
            msg = "Invalid data type ({}) for '{}'"\
                  .format(str(type(attrib)), key + ".attribute")
            raise ValueError(msg)
        else:
            attribstr = " [" + attrib + "]"
        if isinstance(value, dict):
            if value:
                fobj.write("{}{}{} {{\n".format(indentstr, key, attribstr))
                _dump_dict(value, fobj, indentstr + _INDENT_STR)
                fobj.write("{}}}\n".format(indentstr))
            else:
                fobj.write("{}{}{} {{}}\n".format(indentstr, key, attribstr))
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            for item in value:
                fobj.write("{}{}{} {{\n".format(indentstr, key, attribstr))
                _dump_dict(item, fobj, indentstr + _INDENT_STR)
                fobj.write("{}}}\n".format(indentstr))
        else:
            valstr = _get_hsd_rhs(value, indentstr)
            fobj.write("{}{}{} {}\n"\
                     .format(indentstr, key, attribstr, valstr))


def _get_hsd_rhs(obj, indentstr):

    if isinstance(obj, list):
        objstr = _list_to_hsd(obj)
    elif isinstance(obj, np.ndarray):
        objstr = _list_to_hsd(obj.tolist())
    else:
        objstr = _item_to_hsd(obj)
    if "\n" in objstr:
        newline_indent = "\n" + indentstr + _INDENT_STR
        rhs = ("= {" + newline_indent + objstr.replace("\n", newline_indent)
               + "\n" + indentstr + "}")
    else:
        rhs = "= " + objstr
    return rhs


def _list_to_hsd(lst):
    if lst and isinstance(lst[0], list):
        lines = []
        for innerlist in lst:
            lines.append(" ".join([_item_to_hsd(item) for item in innerlist]))
        return "\n".join(lines)
    return " ".join([_item_to_hsd(item) for item in lst])


def _item_to_hsd(item):

    if isinstance(item, (int, float)):
        return str(item)
    elif isinstance(item, bool):
        return "Yes" if item else "No"
    elif isinstance(item, str):
        return _str_to_hsd(item)
    else:
        msg = "Data type {} can not be converted to HSD string"\
              .format(type(item))
        raise TypeError(msg)


def _str_to_hsd(string):
    is_present = [qc in string for qc in _QUOTING_CHARS]
    if sum(is_present) > 1:
        msg = "String '{}' can not be quoted correctly".format(string)
        raise ValueError(msg)
    delimiter = _QUOTING_CHARS[0] if not is_present[0] else _QUOTING_CHARS[1]
    return delimiter + string + delimiter



if __name__ == "__main__":
    INPUT = {
        "Driver": {},
        "Hamiltonian": {
            "DFTB": {
                "Scc": True,
                "SccTolerance": 1e-10,
                "MaxSccIterations": 1000,
                "Mixer": {
                    "Broyden": {}
                },
                "MaxAngularMomentum": {
                    "O": "p",
                    "H": "s"
                },
                "Filling": {
                    "Fermi": {
                        "Temperature": 1e-8,
                        "Temperature.attribute": "Kelvin"
                    }
                },
                "KPointsAndWeights": {
                    "SupercellFolding": [[2, 0, 0], [0, 2, 0], [0, 0, 2],
                                         [0.5, 0.5, 0.5]]
                },
                "ElectricField": {
                    "PointCharges": {
                        "CoordsAndCharges": np.array(
                            [[-0.94, -9.44, 1.2, 1.0],
                             [-0.94, -9.44, 1.2, -1.0]])
                    }
                },
                "SelectSomeAtoms": [1, 2, "3:-3"]
            }
        },
        "Analysis": {
            "ProjectStates": {
                "Region": [
                    {
                        "Atoms": [1, 2, 3],
                        "Label": "region1",
                    },
                    {
                        "Atoms": np.array([1, 2, 3]),
                        "Label": "region2",
                    }
                ]
            }
        }
    }
    print(dumps(INPUT))
