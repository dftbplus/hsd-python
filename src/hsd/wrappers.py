# ------------------------------------------------------------------------------------------------ #
#   hsd-python: package for manipulating HSD-formatted data in Python                              #
#   Copyright (C) 2011 - 2023  DFTB+ developers group                                              #
#   Licensed under the BSD 2-clause license.                                                       #
# ------------------------------------------------------------------------------------------------ #
#
"""
Contains wrappers to make HSD handling comfortable.
"""
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
import re
from reprlib import repr
from hsd.dict import ATTRIB_KEY_SUFFIX, HSD_ATTRIB_KEY_SUFFIX


_HSD_PATH_SEP_PATTERN = re.compile(r"\s*/\s*")

_HSD_LIST_INDEX_PATTERN = re.compile(r"^-?\d+$")

_HSD_PATH_NAME_PATTERN = re.compile(r"^\s*([a-zA-Z]\w*)\s*$")

_HSD_PATH_SEP = "/"


class HsdNode:
    """Represents a HSD node with value, attribute and hsd attributes.

    Attributes:
        value: Value of the node (read-only).
        attrib: Attribute(s) of the node (read-only).
        hsdattrib: HSD-attribute(s) of the node (read-only).
    """

    def __init__(self, value, attrib=None, hsdattrib=None):
        """Initializes the instance.

        Args:
            value: Value to represent (mapping, sequence or leaf node value)
            attrib: Attribute(s) associated with the value.
            hsdattrib: HSD-attribute(s) associated with the value.
        """
        if isinstance(value, self.__class__):
            self._value = value._value
        else:
            self._value = value
        self._attrib = attrib
        self._hsdattrib = hsdattrib

    @property
    def value(self):
        return self._value

    @property
    def attrib(self):
        return self._attrib

    @property
    def hsdattrib(self):
        return self._hsdattrib

    def __repr__(self):
        clsname = self.__class__.__name__
        strrep = (
            f"{clsname}(value={repr(self._value)}, attrib={repr(self._attrib)}, "
            f"hsdattrib={repr(self._hsdattrib)})"
        )
        return strrep

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (
            self.attrib == other.attrib
            and self.hsdattrib == other.hsdattrib
            and self.value == other.value
        )


class HsdContainer(HsdNode):
    """Represents a container-like HSD-node (mapping or sequence).

    Args:
    """

    def __init__(
        self, value, attrib=None, hsdattrib=None, lower_names=False, save_names=False
    ):
        """Initializes the instance.

        Args:
            value: Value to represent (mapping, sequence or leaf node value)
            attrib: Attribute(s) associated with the value.
            hsdattrib: HSD-attribute(s) associated with the value.
            lower_names: Whether names in paths should be lowered when looked up (in order to
                support case insensitive searcher). Note, this option only effects queries invoked
                directly via this instance.
            save_names: If the lower_names setting is active, and an item is set, which name differs
                from its lowered form, the original name will be saved as an HSD-attribute, if this
                option is turned on. Note, this option only effects queries invoked directly via
                this instance.
        """
        super().__init__(value, attrib=attrib, hsdattrib=hsdattrib)
        self._lower_names = lower_names
        self._save_names = save_names

    def __getitem__(self, key):
        path = _path_from_key(key)
        normpath = _normalized_path(path, self._lower_names)
        nodes = _find_path(self._value, normpath)
        attrib, hsdattrib = _get_last_attributes(nodes, normpath)
        return _hsd_from_node(nodes[-1], attrib, hsdattrib)

    def __setitem__(self, key, value):
        self.set_item(key, value, parents=False)

    def __delitem__(self, key):
        path = _path_from_key(key)
        normpath = _normalized_path(path, self._lower_names)
        nodes = _find_path(self._value, normpath[:-1])
        _del_value(nodes, normpath)

    def __len__(self):
        return len(self._value)

    def __iter__(self):
        return iter(self._value)

    def set_item(self, key, value, parents=False):
        """Sets an item at a given key/path.

        Args:
            key: Path/key where the item should be stored.
            value: Item to store.
            parents: Whether missing parents should be created. Creating missing parents is only
                possible if the missing path does not contain list indices.
        """
        path = _path_from_key(key)
        normpath = _normalized_path(path, self._lower_names)
        nodes = _find_path(self._value, normpath[:-1], return_partial=parents)
        # Note: _find_path() returns root + all nodes in the passed path
        if len(nodes) != len(normpath):
            for ind in range(len(nodes), len(normpath)):
                if isinstance(path[ind - 1], int):
                    raise KeyError(
                        "Missing path components must not contain list indices"
                    )
                newvalue = {}
                _set_value(
                    nodes,
                    path[:ind],
                    normpath[:ind],
                    newvalue,
                    None,
                    None,
                    self._save_names,
                )
                nodes.append(newvalue)
        value, attrib, hsdattrib = _value_and_attribs(value)
        _set_value(nodes, path, normpath, value, attrib, hsdattrib, self._save_names)

    def get_item(self, key, default=None):
        """Returns a key or a default value if not found.

        Args:
            key: Key / path to look for.
            default: Default value to return if no item was found.

        Returns:
            Item at given key/path or the default value.
        """
        return self.get(key, default=default)

    def set_default(self, key, default=None, parents=False):
        """Returns value for an existing key, or create the key with default value and returns that.

        Args:
            key: Key to look for
            default: Default value to return (and set for newly created key), if key does not exist.
            parents: Whether missing parents should be created when new key is created. Creating
                missing parents is only possible if the missing subpath does not contain list
                indices.

        Returns:
            Value for the given key, if key existed, default value otherwise.
        """
        try:
            return self[key]
        except KeyError:
            self.set_item(key, default, parents=parents)
            return default

    @classmethod
    def copy(cls, source, lower_names=False, save_names=False):
        """Creates a new object instance by copying the entries of a suitable object.

        Note: This is a 'semi-deep' copy as all keys are created new, but values are shallow-copied.

        Args:
            lower_names: Whether all keys should be converted to lower case during the copy (to
                support case insensitive searches). The resulting instance will also be created with
                identical lower_names option.
            save_names: Whether the original of the converted keys should be stored as
                HSD-attributes. The resulting instance will also be created with identical
                save_names option.
        """
        srcdict, srcattrib, srchsdattrib = _value_and_attribs(source)
        value = _hsd_copy(srcdict, lower_names, save_names)
        return cls(
            value,
            attrib=srcattrib,
            hsdattrib=srchsdattrib,
            lower_names=lower_names,
            save_names=save_names,
        )


class HsdDict(HsdContainer, MutableMapping):
    """HSD wrapper around dictionaries."""

    @classmethod
    def copy(cls, source, lower_names=False, save_names=False):
        """Creates a new object instance by copying the entries of a suitable object.

        Note: This is a 'semi-deep' copy as all keys are created new, but values are shallow-copied.

        Args:
            lower_names: Whether all keys should be converted to lower case during the copy (to
                support case insensitive searches). The resulting instance will also be created with
                identical lower_names option.
            save_names: Whether the original of the converted keys should be stored as
                HSD-attributes. The resulting instance will also be created with identical
                save_names option.
        """
        if not _is_hsd_dict_compatible(source):
            raise TypeError("Source must be of HsdDict compatible type")
        return super(cls, cls).copy(source, lower_names=lower_names, save_names=save_names)


class HsdList(HsdContainer, MutableSequence):
    """HSD wrapper around lists"""

    @classmethod
    def copy(cls, source, lower_names=False, save_names=False):
        """Creates a new object instance by copying the entries of a suitable object.

        Note: This is a 'semi-deep' copy as all keys are created new, but values are shallow-copied.

        Args:
            lower_names: Whether all keys should be converted to lower case during the copy (to
                support case insensitive searches). The resulting instance will also be created with
                identical lower_names option.
            save_names: Whether the original of the converted keys should be stored as
                HSD-attributes. The resulting instance will also be created with identical
                save_names option.
        """
        if not _is_hsd_list_compatible(source):
            raise TypeError("Source must be of HsdList compatible type")
        return super(cls, cls).copy(source, lower_names=lower_names, save_names=save_names)

    def __setitem__(self, ind, value):
        if not _is_hsd_dict_compatible(value):
            raise TypeError("HsdList might only contain HsdDict compatible elements")
        super().__setitem__(ind, value)

    def insert(self, ind, value):
        if not _is_hsd_dict_compatible(value):
            raise TypeError("Only HsdDict compatible items can be inserted into HsdLists")
        value, attrib, hsdattrib = _value_and_attribs(value)
        if self._attrib is None and attrib is not None:
            raise ValueError(
                "HsdList without attribute can not be extended with a value with attribute"
            )
        elif self._attrib is not None:
            self._attrib.insert(ind, attrib)
        if self._hsdattrib is None and hsdattrib is not None:
            raise ValueError(
                "HsdList without HSD-attribute can not be extended with a value with HSD-attribute"
            )
        elif self._hsdattrib is not None:
            self._hsdattrib.insert(ind, hsdattrib)
        self._value.insert(ind, value)


class HsdValue(HsdNode):
    """HSD wrapper around values (leaf nodes)"""


def copy(source, lower_names=False, save_names=False):
    """Makes a copy of the source and wraps it with an appropriate HSD-container.

    Note: This is a 'semi-deep' copy as all keys are created new, but values are shallow-copied.

    Args:
        lower_names: Whether all keys should be converted to lower case during the copy (to
            support case insensitive searches). The resulting instance will also be created with
            identical lower_names option.
        save_names: Whether the original of the converted keys should be stored as
            HSD-attributes. The resulting instance will also be created with identical
            save_names option.
    """
    if _is_hsd_dict_compatible(source):
        return HsdDict.copy(source, lower_names=lower_names, save_names=save_names)
    elif _is_hsd_list_compatible(source):
        return HsdList.copy(source, lower_names=lower_names, save_names=save_names)
    raise TypeError("Only HsdDict and HsdList compatible types can be copied")


def wrap(source, lower_names=False, save_names=False):
    """Wraps an object with an appropriate HSD-container.

    Note: This is a 'semi-deep' copy as all keys are created new, but values are shallow-copied.

    Args:
        lower_names: Whether names in paths should be lowered when looked up (in order to
            support case insensitive searcher). Note, this option only effects queries invoked
            directly via this instance.
        save_names: If the lower_names setting is active, and an item is set, which name differs
            from its lowered form, the original name will be saved as an HSD-attribute, if this
            option is turned on. Note, this option only effects queries invoked directly via
            this instance.
    """
    if _is_hsd_dict_compatible(source):
        return HsdDict(source, lower_names=lower_names, save_names=save_names)
    elif _is_hsd_list_compatible(source):
        return HsdList(source, lower_names=lower_names, save_names=save_names)
    raise TypeError("Only HsdDict and HsdList compatible types can be wrapped")


def _path_from_key(key):
    """Returns an iterable path from the provided key."""
    if isinstance(key, str):
        pathcomps = _HSD_PATH_SEP_PATTERN.split(key)
        pathcomps = [
            int(pc) if _HSD_LIST_INDEX_PATTERN.match(pc) else pc for pc in pathcomps
        ]
    elif isinstance(key, Sequence):
        pathcomps = key
        if len(pathcomps) == 0:
            raise ValueError(f"Key sequence has zero length")
    else:
        raise TypeError(f"Key '{key}' has invalid type")

    path = []
    for pc in pathcomps:
        if isinstance(pc, int):
            path.append(pc)
        elif match := _HSD_PATH_NAME_PATTERN.match(pc):
            path.append(match.group(1))
        else:
            raise ValueError(f"Invalid path component {pc!r} in path {key!r}")
    return path


def _find_path(root, path, return_partial=False):
    """Returns list of nodes corresponding to a path relative to (and starting from) root."""
    nodes = [root]
    node = root
    found = True
    key = None
    for key in path:
        parent = node
        try:
            node = parent[key]
        except (KeyError, IndexError):
            found = False
            break
        nodes.append(node)
    if found or return_partial:
        return nodes
    failedpath = _HSD_PATH_SEP.join([str(p) for p in path[: len(nodes)]])
    # Raise key error, so that the "in" operator can be used with HsdDicts.
    raise KeyError(f"Could not find item '{key}' at '{failedpath}'")


def _get_last_attributes(nodes, path):
    """Returns attribute and hsdattributes associated with the last node in a path."""
    if isinstance(nodes[-2], Sequence):
        parent = nodes[-3]
        key, ind = path[-2], path[-1]
        attrib = parent.get(key + ATTRIB_KEY_SUFFIX)
        hsdattrib = parent.get(key + HSD_ATTRIB_KEY_SUFFIX)
        attrib = attrib[ind] if attrib is not None else None
        hsdattrib = hsdattrib[ind] if hsdattrib is not None else None
    else:
        parent = nodes[-2]
        key = path[-1]
        attrib = parent.get(key + ATTRIB_KEY_SUFFIX)
        hsdattrib = parent.get(key + HSD_ATTRIB_KEY_SUFFIX)
    return attrib, hsdattrib


def _hsd_from_node(node, attrib, hsdattrib):
    """Returns a HsdNode subclass wrapper depending on the node type."""
    if _is_hsd_dict_compatible(node):
        return HsdDict(node, attrib, hsdattrib)
    elif _is_hsd_list_compatible(node):
        return HsdList(node, attrib, hsdattrib)
    else:
        return HsdValue(node, attrib, hsdattrib)


def _value_and_attribs(obj):
    """Returns value, attribute and hsdattributes corresponding to an object."""
    if isinstance(obj, HsdNode):
        attrib = obj._attrib
        hsdattrib = obj._hsdattrib
        value = obj._value
    else:
        value = obj
        attrib = hsdattrib = None
    return value, attrib, hsdattrib


def _set_value(nodes, path, normpath, value, attrib, hsdattrib, save_names):
    """Sets the value of the last node in a path."""
    node = nodes[-1]
    node[normpath[-1]] = value
    if isinstance(node, Sequence):
        ind, normkey = normpath[-1], normpath[-2]
        key = path[-2]
        parent = nodes[-2]
        if attrib is not None:
            parent[normkey + ATTRIB_KEY_SUFFIX][ind] = attrib
        if save_names:
            if normkey != key:
                hsdattrib = {} if hsdattrib is None else hsdattrib.copy()
                hsdattrib["name"] = key
            elif hsdattrib is not None and "name" in hsdattrib:
                del hsdattrib["name"]
        if hsdattrib is not None:
            parent[normkey + HSD_ATTRIB_KEY_SUFFIX][ind] = hsdattrib
        elif parent[normkey + HSD_ATTRIB_KEY_SUFFIX] is not None:
            parent[normkey + HSD_ATTRIB_KEY_SUFFIX][ind] = None
    else:
        key = path[-1]
        normkey = normpath[-1]
        if attrib is not None:
            node[normkey + ATTRIB_KEY_SUFFIX] = attrib
        if save_names:
            if isinstance(value, Sequence):
                if normkey != key:
                    # The container hsdattrib may be None, or it may be a list, which may have None
                    # elements itself. We handle both cases and return a list of dicts.
                    tmphsdattrib = [None] * len(value) if hsdattrib is None else hsdattrib
                    hsdattrib = [
                        {} if hsddict is None else hsddict.copy() for hsddict in tmphsdattrib
                    ]
                    for hsddict in hsdattrib:
                        hsddict["name"] = key
                elif hsdattrib is not None:
                    hsdattrib = [
                        None if hsddict is None else hsddict.copy()
                        for hsddict in hsdattrib
                    ]
                    for hsddict in hsdattrib:
                        if hsddict is not None and "name" in hsddict:
                            del hsddict["name"]
            else:
                if normkey != key:
                    hsdattrib = {} if hsdattrib is None else hsdattrib.copy()
                    hsdattrib["name"] = key
                elif hsdattrib is not None and "name" in hsdattrib:
                    del hsdattrib["name"]

        if hsdattrib is not None:
            node[normkey + HSD_ATTRIB_KEY_SUFFIX] = hsdattrib
        elif normkey + HSD_ATTRIB_KEY_SUFFIX in node:
            del node[normkey + HSD_ATTRIB_KEY_SUFFIX]


def _del_value(nodes, path):
    """Deletes the last node in a path."""
    node = nodes[-1]
    del node[path[-1]]
    if isinstance(node, Sequence):
        ind, key = path[-1], path[-2]
        parent = nodes[-2]
        if key + ATTRIB_KEY_SUFFIX in parent:
            del parent[key + ATTRIB_KEY_SUFFIX][ind]
        if key + HSD_ATTRIB_KEY_SUFFIX in parent:
            del parent[key + HSD_ATTRIB_KEY_SUFFIX][ind]
    else:
        key = path[-1]
        if key + ATTRIB_KEY_SUFFIX in node:
            del node[key + ATTRIB_KEY_SUFFIX]
        if key + HSD_ATTRIB_KEY_SUFFIX in node:
            del node[key + HSD_ATTRIB_KEY_SUFFIX]


def _hsd_copy(source, lower_names, save_names):
    """Copies a HSD-tree recursively (by creating new containers and keys)."""
    if _is_hsd_dict_compatible(source):
        result = {}
        for key, value in source.items():
            if key.endswith(ATTRIB_KEY_SUFFIX) or key.endswith(HSD_ATTRIB_KEY_SUFFIX):
                continue
            attrib = source.get(key + ATTRIB_KEY_SUFFIX)
            hsdattrib = source.get(key + HSD_ATTRIB_KEY_SUFFIX)
            newkey = key.lower() if lower_names else key
            if save_names and newkey != key:
                if _is_hsd_list_compatible(value):
                    if hsdattrib is None:
                        hsdattrib = [{} for _ in range(len(value))]
                    for dd in hsdattrib:
                        dd["name"] = key
                else:
                    hsdattrib = hsdattrib if hsdattrib is not None else {}
                    hsdattrib["name"] = key
            if attrib is not None:
                result[newkey + ATTRIB_KEY_SUFFIX] = attrib
            if hsdattrib is not None:
                result[newkey + HSD_ATTRIB_KEY_SUFFIX] = hsdattrib
            result[newkey] = _hsd_copy(
                value, lower_names=lower_names, save_names=save_names
            )
    elif _is_hsd_list_compatible(source):
        result = [_hsd_copy(item, lower_names, save_names) for item in source]
    else:
        result = source
    return result


def _normalized_path(path, lower_names):
    """Returns a normalized path."""
    return [
        name.lower() if lower_names and isinstance(name, str) else name for name in path
    ]


def _is_hsd_dict_compatible(obj):
    """Whether an object can be wrapped as HsdDict."""
    return isinstance(obj, Mapping)


def _is_hsd_list_compatible(obj):
    """Whether an object can be wrapped as HsdList."""
    return isinstance(obj, Sequence) and all([isinstance(item, Mapping) for item in obj])
