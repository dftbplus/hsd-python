#!/bin/env python3
#------------------------------------------------------------------------------#
#  hsd: package for manipulating HSD-formatted data                            #
#  Copyright (C) 2011 - 2020  DFTB+ developers group                           #
#                                                                              #
#  See the LICENSE file for terms of usage and distribution.                   #
#------------------------------------------------------------------------------#
#
import numpy as np
import hsd

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
    print(hsd.dumps(INPUT))
