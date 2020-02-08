#!/bin/env python3
#------------------------------------------------------------------------------#
#  hsd: package for manipulating HSD-formatted data                            #
#  Copyright (C) 2011 - 2020  DFTB+ developers group                           #
#                                                                              #
#  See the LICENSE file for terms of usage and distribution.                   #
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
