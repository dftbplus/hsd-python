#!/bin/env python3
#------------------------------------------------------------------------------#
#  hsd-python: package for manipulating HSD-formatted data in Python           #
#  Copyright (C) 2011 - 2021  DFTB+ developers group                           #
#  Licensed under the BSD 2-clause license.                                    #
#------------------------------------------------------------------------------#
#
import hsd
import os.path as op


def test_parser():
    parser = hsd.HsdParser()
    with open(op.join(op.dirname(__file__), "test.hsd"), "r") as fobj:
        parser.feed(fobj)


if __name__ == '__main__':
    test_parser()
