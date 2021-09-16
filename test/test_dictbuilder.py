#!/bin/env python3
#------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python           #
#  Copyright (C) 2011 - 2021  DFTB+ developers group                           #
#  Licensed under the BSD 2-clause license.                                    #
#------------------------------------------------------------------------------#
#
import os.path as op
import hsd

def test_dictbuilder():
    dictbuilder = hsd.HsdDictBuilder()
    parser = hsd.HsdParser(eventhandler=dictbuilder)
    with open(op.join(op.dirname(__file__), "test.hsd"), "r") as fobj:
        parser.feed(fobj)
    pyrep = dictbuilder.hsddict
    print("** Python structure without data flattening:\n")
    print(pyrep)
    print("\n** Turning back to HSD:\n")
    print(hsd.dump_string(pyrep))


def test_dictbuilder_flat():
    dictbuilder = hsd.HsdDictBuilder(flatten_data=True, include_hsd_attribs=True)
    parser = hsd.HsdParser(eventhandler=dictbuilder, lower_tag_names=True)
    with open(op.join(op.dirname(__file__), "test.hsd"), "r") as fobj:
        parser.feed(fobj)
    pyrep = dictbuilder.hsddict
    print("** Python structure with data flattening:\n")
    print(pyrep)
    print("\n** Turning back to HSD:\n")
    print(hsd.dump_string(pyrep, use_hsd_attribs=True))


if __name__ == '__main__':
    test_dictbuilder()
    test_dictbuilder_flat()
