************
Introduction
************

This package contains utilities to read and write files in the Human-friendly
Structured Data (HSD) format.

The HSD-format is very similar to XML, JSON and YAML, but tries to minimize the
effort for **humans** to read and write it. It ommits special characters as much
as possible (in contrast to XML and JSON) and is not indentation dependent (in
contrast to YAML). It was developed originally as the input format for the
scientific simulation tool (`DFTB+ <https://github.com/dftbplus/dftbplus>`_),
but is of general purpose. Data stored in HSD can be easily mapped to a subset
of JSON, YAML or XML and *vice versa*.

This document describes hsd-python version 0.1.


Installation
============

The package can be installed via conda-forge::

  conda install hsd-python

Alternatively, the package can be downloaded and installed via pip into the
active Python interpreter (preferably using a virtual python environment) by ::

  pip install hsd

or into the user space issueing ::

  pip install --user hsd


Quick tutorial
==============

A typical, self-explaining input written in HSD looks like ::

  driver {
    conjugate_gradients {
      moved_atoms = 1 2 "7:19"
      max_steps = 100
    }
  }

  hamiltonian {
    dftb {
      scc = yes
      scc_tolerance = 1e-10
      mixer {
        broyden {}
      }
      filling {
        fermi {
          # This is comment which will be ignored
          # Note the attribute (unit) of the field below
          temperature [kelvin] = 100
        }
      }
      k_points_and_weights {
        supercell_folding {
          2   0   0
          0   2   0
          0   0   2
          0.5 0.5 0.5
        }
      }
    }
  }

The above input can be parsed into a Python dictionary with::

  import hsd
  hsdinput = hsd.load("test.hsd")

The dictionary ``hsdinput`` will then look as::

  {
      "driver": {
          "conjugate_gradients" {
              "moved_atoms": [1, 2, "7:19"],
              "max_steps": 100
          }
      },
      "hamiltonian": {
          "dftb": {
              "scc": True,
              "scc_tolerance": 1e-10,
              "mixer": {
                  "broyden": {}
              },
              "filling": {
                  "fermi": {
                      "temperature": 100,
                      "temperature.attrib": "kelvin"
                  }
              }
              "k_points_and_weights": {
                  "supercell_folding": [
                      [2, 0, 0],
                      [0, 2, 0],
                      [0, 0, 2],
                      [0.5, 0.5, 0.5]
                  ]
              }
          }
      }
  }

Being a simple Python dictionary, it can be easily queried and manipulated in
Python ::

  hsdinput["driver"]["conjugate_gradients"]["max_steps"] = 200

and then stored again in HSD format ::

    hsd.dump(hsdinput, "test2.hsd")
