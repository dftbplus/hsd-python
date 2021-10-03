#  hsd-python: package for manipulating HSD-formatted data in Python           #
#  Copyright (C) 2011 - 2021  DFTB+ developers group                                  #
#  Licensed under the BSD 2-clause license.                                    #
#------------------------------------------------------------------------------#
#
"""
Provides functionality to dump Python structures to HSD
"""
import io
from typing import Union, TextIO
from hsd.dict import HsdDictWalker, HsdDictBuilder
from hsd.formatter import HsdFormatter
from hsd.parser import HsdParser


_INDENT_STR = "  "



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
            be stored. Use it, if you wish to keep the formatting of the data
            close to the original on writing (e.g. lowered tag names
            converted back to their original form, equals signs between parent
            and only child kept, instead of converted to curly braces).
        flatten_data: Whether multiline data in the HSD input should be
            flattened into a single list. Othewise a list of lists is created,
            with one list for every line (default).

    Returns:
        Dictionary representing the HSD data.

    Examples:
        See :func:`hsd.load_string` for examples of usage.
    """
    dictbuilder = HsdDictBuilder(lower_tag_names=lower_tag_names, flatten_data=flatten_data,
                                 include_hsd_attribs=include_hsd_attribs)
    parser = HsdParser(eventhandler=dictbuilder)
    if isinstance(hsdfile, str):
        with open(hsdfile, "r") as hsddescr:
            parser.parse(hsddescr)
    else:
        parser.parse(hsdfile)
    return dictbuilder.hsddict


def load_string(
        hsdstr: str, lower_tag_names: bool = False,
        include_hsd_attribs: bool = False, flatten_data: bool = False
    ) -> dict:
    """Loads a string with HSD-formatted data into a Python dictionary.

    Args:
        hsdstr: String with HSD-formatted data.
        lower_tag_names: When set, all tag names will be converted to lower-case
            (practical, when input should be treated case insensitive.) If
            ``include_hsd_attribs`` is set, the original tag name will be
            stored among the HSD attributes.
        include_hsd_attribs: Whether the HSD-attributes (processing related
            attributes, like original tag name, line information, etc.) should
            be stored. Use it, if you wish to keep the formatting of the data
            close to the original one on writing (e.g. lowered tag names
            converted back to their original form, equals signs between parent
            and only child kept, instead of converted to curly braces).
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
        {'Dftb': {'Scc': True, 'Filling': {'Fermi': {'Temperature': 100,
        'Temperature.attrib': 'Kelvin'}}}}

        In order to ease the case-insensitive handling of the input, the tag
        names can be converted to lower case during reading using the
        ``lower_tag_names`` option.

        >>> hsd.load_string(hsdstr, lower_tag_names=True)
        {'dftb': {'scc': True, 'filling': {'fermi': {'temperature': 100,
        'temperature.attrib': 'Kelvin'}}}}

        The original tag names (together with additional information like the
        line number of a tag) can be recorded, if the ``include_hsd_attribs``
        option is set:

        >>> data = hsd.load_string(hsdstr, lower_tag_names=True,
        ... include_hsd_attribs=True)

        Each tag in the dictionary will have a corresponding ".hsdattrib" entry
        with the recorded data:

        >>> data["dftb.hsdattrib"]
        {'equal': False, 'line': 1, 'name': 'Dftb'}

        This additional data can be then also used to format the tags in the
        original style, when writing the data in HSD-format again. Compare:

        >>> hsd.dump_string(data)
        'dftb {\\n  scc = Yes\\n  filling {\\n    fermi {\\n
        temperature [Kelvin] = 100\\n    }\\n  }\\n}\\n'

        versus

        >>> hsd.dump_string(data, use_hsd_attribs=True)
        'Dftb {\\n  Scc = Yes\\n  Filling {\\n    Fermi {\\n
        Temperature [Kelvin] = 100\\n    }\\n  }\\n}\\n'

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
            ``include_hsd_attribs`` options set or keep the equal signs
            between parent and contained only child.

    Raises:
        TypeError: if object is not a dictionary instance.

    Examples:

        See :func:`hsd.load_string` for an example.
    """
    if not isinstance(data, dict):
        msg = "Invalid object type"
        raise TypeError(msg)
    if isinstance(hsdfile, str):
        with open(hsdfile, "w") as hsddescr:
            _dump_dict(data, hsddescr, use_hsd_attribs)
    else:
        _dump_dict(data, hsdfile, use_hsd_attribs)


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
        'Dftb {\\n  Scc = Yes\\n  Filling {\\n    Fermi {\\n
        Temperature [Kelvin] = 100\\n    }\\n  }\\n}\\n'

        See also :func:`hsd.load_string` for an example.

    """
    result = io.StringIO()
    dump(data, result, use_hsd_attribs=use_hsd_attribs)
    return result.getvalue()


def _dump_dict(obj: dict, fobj: TextIO, use_hsd_attribs: bool):

    formatter = HsdFormatter(fobj, use_hsd_attribs=use_hsd_attribs)
    walker = HsdDictWalker(formatter)
    walker.walk(obj)
