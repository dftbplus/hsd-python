#!/bin/env python3
#------------------------------------------------------------------------------#
#  hsd: package for manipulating HSD-formatted data                            #
#  Copyright (C) 2011 - 2020  DFTB+ developers group                           #
#                                                                              #
#  See the LICENSE file for terms of usage and distribution.                   #
#------------------------------------------------------------------------------#
#
import hsd

def test_dictbuilder():
    dictbuilder = hsd.HsdDictBuilder()
    parser = hsd.HsdParser(eventhandler=dictbuilder)
    with open("test.hsd", "r") as fobj:
        parser.feed(fobj)
    pyrep = dictbuilder.hsddict
    print("** Python structure without data flattening:\n")
    print(pyrep)
    print("\n** Turning back to HSD:\n")
    print(hsd.dumps(pyrep))


def test_dictbuilder_flat():
    dictbuilder = hsd.HsdDictBuilder(flatten_data=True)
    parser = hsd.HsdParser(eventhandler=dictbuilder)
    with open("test.hsd", "r") as fobj:
        parser.feed(fobj)
    pyrep = dictbuilder.hsddict
    print("** Python structure with data flattening:\n")
    print(pyrep)
    print("\n** Turning back to HSD:\n")
    print(hsd.dumps(pyrep))


if __name__ == '__main__':
    test_dictbuilder()
    test_dictbuilder_flat()
