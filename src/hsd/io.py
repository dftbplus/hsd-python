#  hsd-python: package for manipulating HSD-formatted data in Python           #
#  Copyright (C) 2011 - 2021  DFTB+ developers group                           #
#  Licensed under the BSD 2-clause license.                                    #
#------------------------------------------------------------------------------#
#
"""
Provides functionality to dump Python structures to HSD
"""
import io
try:
    import numpy as np
except ModuleNotFoundError:
    np = None
from typing import Union, TextIO

from .common import \
    ATTRIB_SUFFIX, HSD_ATTRIB_SUFFIX, LEN_ATTRIB_SUFFIX, LEN_HSD_ATTRIB_SUFFIX
from .dictbuilder import HsdDictBuilder
from .parser import HsdParser


_INDENT_STR = "  "

# String quoting delimiters (must be at least two)
_QUOTING_CHARS = "\"'"

# Special characters
_SPECIAL_CHARS = "{}[]= "


def load(hsdfile: Union[TextIO, str], lower_tag_names: bool = False,
         include_hsd_attribs: bool = False, flatten_data: bool = False) -> dict:
    """Loads a file with HSD-formatted data into a Python dictionary

    Args:
        hsdfile: Name of file or file like object to read the HSD data from
        lower_tag_names: When set, all tag names will be converted to lower-case
            (practical, when input should be treated case insensitive.) If
            ``include_hsd_attribs`` is set, the original tag name will be
            stored among the HSD attributes.
        include_hsd_attribs: Whether the HSD-attributes (processing related
            attributes, like original tag name, line information, etc.) should
            be stored.
        flatten_data: Whether multiline data in the HSD input should be
            flattened into a single list. Othewise a list of lists is created,
            with one list for every line (default).

    Returns:
        Dictionary representing the HSD data.

    Examples:
        See :func:`hsd.load_string` for examples of usage.
    """
    dictbuilder = HsdDictBuilder(flatten_data=flatten_data,
                                 include_hsd_attribs=include_hsd_attribs)
    parser = HsdParser(eventhandler=dictbuilder,
                       lower_tag_names=lower_tag_names)
    if isinstance(hsdfile, str):
        with open(hsdfile, "r") as hsdfile:
            parser.feed(hsdfile)
    else:
        parser.feed(hsdfile)
    return dictbuilder.hsddict


def load_string(hsdstr: str, lower_tag_names: bool = False,
         include_hsd_attribs: bool = False, flatten_data: bool = False) -> dict:
    """Loads a string with HSD-formatted data into a Python dictionary.

    Args:
        hsdstr: String with HSD-formatted data.
        lower_tag_names: When set, all tag names will be converted to lower-case
            (practical, when input should be treated case insensitive.) If
            ``include_hsd_attribs`` is set, the original tag name will be
            stored among the HSD attributes.
        include_hsd_attribs: Whether the HSD-attributes (processing related
            attributes, like original tag name, line information, etc.) should
            be stored.
        flatten_data: Whether multiline data in the HSD input should be
            flattened into a single list. Othewise a list of lists is created,
            with one list for every line (default).

    Returns:
        Dictionary representing the HSD data.

    Examples:
        >>> hsdstr = \"\"\"
        ... Dftb {
        ...   Scc = Yes
        ...   Filling {
        ...     Fermi {
        ...       Temperature [Kelvin] = 100
        ...     }
        ...   }
        ... }
        ... \"\"\"
        >>> hsd.load_string(hsdstr)
        {'Dftb': {'Scc': True, 'Filling': {'Fermi': {'Temperature.attrib': 'Kelvin', 'Temperature': 100}}}}

        In order to ease the case-insensitive handling of the input, the tag
        names can be converted to lower case during reading using the
        ``lower_tag_names`` option.

        >>> hsd.load_string(hsdstr, lower_tag_names=True)
        {'dftb': {'scc': True, 'filling': {'fermi': {'temperature.attrib': 'Kelvin', 'temperature': 100}}}}

        The original tag names (together with additional information like the
        line number of a tag) can be recorded, if the ``include_hsd_attribs``
        option is set:

        >>> data = hsd.load_string(hsdstr, lower_tag_names=True, include_hsd_attribs=True)

        Each tag in the dictionary will have a corresponding ".hsdattrib" entry
        with the recorded data:

        >>> data["dftb.hsdattrib"]
        {'line': 1, 'tag': 'Dftb'}

        This additional data can be then also used to format the tags in the
        original style, when writing the data in HSD-format again. Compare:

        >>> hsd.dump_string(data)
        'dftb {\\n  scc = Yes\\n  filling {\\n    fermi {\\n      temperature [Kelvin] = 100\\n    }\\n  }\\n}\\n'

        versus

        >>> hsd.dump_string(data, use_hsd_attribs=True)
        'Dftb {\\n  Scc = Yes\\n  Filling {\\n    Fermi {\\n      Temperature [Kelvin] = 100\\n    }\\n  }\\n}\\n'

    """
    fobj = io.StringIO(hsdstr)
    return load(fobj, lower_tag_names, include_hsd_attribs, flatten_data)


def dump(data: dict, hsdfile: Union[TextIO, str],
         use_hsd_attribs: bool = False):
    """Dumps data to a file in HSD format.

    Args:
        data: Dictionary like object to be written in HSD format
        hsdfile: Name of file or file like object to write the result to.
        use_hsd_attribs: Whether HSD attributes in the data structure should
            be used to format the output.

            This option can be used to for example to restore original tag
            names, if the file was loaded with the ``lower_tag_names`` and
            ``include_hsd_attribs`` options set.

    Raises:
        TypeError: if object is not a dictionary instance.

    Examples:

        See :func:`hsd.load_string` for an example.
    """
    if not isinstance(data, dict):
        msg = "Invalid object type"
        raise TypeError(msg)
    if isinstance(hsdfile, str):
        with open(hsdfile, "w") as hsdfile:
            _dump_dict(data, hsdfile, "", use_hsd_attribs=use_hsd_attribs)
    else:
        _dump_dict(data, hsdfile, "", use_hsd_attribs=use_hsd_attribs)


def dump_string(data: dict, use_hsd_attribs: bool = False) -> str:
    """Serializes an object to string in HSD format.

    Args:
        data: Dictionary like object to be written in HSD format.
        use_hsd_attribs: Whether HSD attributes of the data structure should
            be used to format the output (e.g. to restore original mixed case
            tag names)

    Returns:
        HSD formatted string.

    Examples:
        >>> hsdtree = {
        ...     'Dftb': {
        ...         'Scc': True,
        ...         'Filling': {
        ...             'Fermi': {
        ...                 'Temperature': 100,
        ...                 'Temperature.attrib': 'Kelvin'
        ...             }
        ...         }
        ...     }
        ... }
        >>> hsd.dump_string(hsdtree)
        'Dftb {\\n  Scc = Yes\\n  Filling {\\n    Fermi {\\n      Temperature [Kelvin] = 100\\n    }\\n  }\\n}\\n'

        See also :func:`hsd.load_string` for an example.

    """
    result = io.StringIO()
    dump(data, result, use_hsd_attribs=use_hsd_attribs)
    return result.getvalue()


def _dump_dict(obj, fobj, indentstr, use_hsd_attribs):
    for key, value in obj.items():
        if key.endswith(ATTRIB_SUFFIX):
            if key[:-LEN_ATTRIB_SUFFIX] in obj:
                continue
            else:
                msg = "Attribute '{}' without corresponding tag '{}'"\
                      .format(key, key[:-len(ATTRIB_SUFFIX)])
                raise ValueError(msg)
        if key.endswith(HSD_ATTRIB_SUFFIX):
            if key[:-LEN_HSD_ATTRIB_SUFFIX] in obj: continue
            else:
                msg = "HSD attribute '{}' without corresponding tag '{}'"\
                      .format(key, key[:-len(HSD_ATTRIB_SUFFIX)])
                raise ValueError(msg)
        attrib = obj.get(key + ATTRIB_SUFFIX)
        if attrib is None:
            attribstr = ""
        elif not isinstance(attrib, str):
            msg = "Invalid data type ({}) for '{}'"\
                  .format(str(type(attrib)), key + ".attribute")
            raise ValueError(msg)
        else:
            attribstr = " [" + attrib + "]"
        if use_hsd_attribs:
            hsdattrib = obj.get(key + HSD_ATTRIB_SUFFIX)
        else:
            hsdattrib = None
        if isinstance(value, dict):
            key = hsdattrib.get("tag", key) if hsdattrib else key
            if value:
                fobj.write("{}{}{} {{\n".format(indentstr, key, attribstr))
                _dump_dict(
                    value, fobj, indentstr + _INDENT_STR, use_hsd_attribs)
                fobj.write("{}}}\n".format(indentstr))
            else:
                fobj.write("{}{}{} {{}}\n".format(indentstr, key, attribstr))
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            for ind, item in enumerate(value):
                key = hsdattrib[ind].get("tag", key) if hsdattrib else key
                fobj.write("{}{}{} {{\n".format(indentstr, key, attribstr))
                _dump_dict(
                    item, fobj, indentstr + _INDENT_STR, use_hsd_attribs)
                fobj.write("{}}}\n".format(indentstr))
        else:
            key = hsdattrib.get("tag", key) if hsdattrib else key
            valstr = _get_hsd_rhs(value, indentstr)
            fobj.write("{}{}{} {}\n"\
                     .format(indentstr, key, attribstr, valstr))


def _get_hsd_rhs(obj, indentstr):

    if isinstance(obj, list):
        objstr = _list_to_hsd(obj)
    elif np is not None and isinstance(obj, np.ndarray):
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

    if isinstance(item, bool):
        return "Yes" if item else "No"
    elif isinstance(item, (int, float)):
        return str(item)
    elif isinstance(item, str):
        return _str_to_hsd(item)
    else:
        msg = "Data type {} can not be converted to HSD string"\
              .format(type(item))
        raise TypeError(msg)


def _str_to_hsd(string):
    present = [qc in string for qc in _QUOTING_CHARS]
    nquotetypes = sum(present)
    delimiter = ""
    if not nquotetypes and True in [sc in string for sc in _SPECIAL_CHARS]:
        delimiter = _QUOTING_CHARS[0]
    elif nquotetypes == 1 and string[0] not in _QUOTING_CHARS:
        delimiter = _QUOTING_CHARS[1] if present[0] else _QUOTING_CHARS[0]
    elif nquotetypes > 1:
        msg = "String '{}' can not be quoted correctly".format(string)
        raise ValueError(msg)
    return delimiter + string + delimiter
