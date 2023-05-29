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

The basics
----------

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



Accesing nested data structures via wrappers
--------------------------------------------

The hsd module contains lightweight wrappers (``HsdDict``, ``HsdList`` and
``HsdValue``), which offer convenient access to entries in nested data
structures.  With the help of these wrappers, nested nodes and values can be
directly accessed using paths. When accessing nested content via wrappers, the
resulting objects will be wrappers themself, wrapping the appropriate parts of
the data structure (and inheriting certain properties of the original wrapper).

For example, reading and wrapping the example above::

  import hsd
  hsdinp = hsd.wrap(hsd.load("test.hsd"))

creates an ``HsdDict`` wrapper instance (``hsdinp``), which can be used to query
encapsulated information in the structure::

  # Reading out the value directly (100)
  maxsteps = hsdinp["driver", "conjugate_gradients", "max_steps"].value

  # Storing wrapper (HsdValue) instance and reading out value and the attribute
  temp = hsdinp["hamiltonian / dftb / filling / fermi / temperature"]
  temp_value = temp.value
  temp_unit = temp.attrib

  # Getting a default value, if a given path does not exists:
  pot = hsdinp.get_item("hamiltonian / dftb / bias", default=hsd.HsdValue(100, attrib="V"))

  # Setting a value for given path by creating missing parents
  hsdinp.set_item("analysis / calculate_forces", True, parents=True)

As demonstrated above, paths can be specified as tuples or as slash (``/``) joined strings.

The wrappers also support case-insensitive access. Let's have a look at a
mixed-case example file ``test2.hsd``::

  Driver {
  ConjugateGradients {
    MovedAtoms = 1 2 "7:19"
    MaxSteps = 100
  }

We now make copy of the data structure before wrapping it, and make sure that
all keys are converted to lower case, but the original names are saved as
HSD-attributes::

  hsdinp = hsd.copy(hsd.load("test2.hsd"), lower_names=True, save_names=True)

This way, paths passed to the Hsd-wrapper are treated in a case-insensitive
way::

  maxsteps = hsdinp["driver", "CONJUGATEGRADIENTS", "MAXSTEPS"].value

When adding new items, the access is and remains case in-sensitive, but the
actual form of the name of the new node will be saved. The code snippet::

  hsdinp["driver", "conjugategradients", "MaxForce"] = hsd.HsdValue(1e-4, attrib="au")
  maxforceval = hsdinp["driver", "conjugategradients", "maxforce"]
  print(f"{maxforceval.value} {maxforceval.attrib}")
  print(hsd.dump_string(hsdinp.value, apply_hsd_attribs=True))

will result in ::

  0.0001 au
  Driver {
    ConjugateGradients {
      MovedAtoms = 1 2 "7:19"
      MaxSteps = 100
      MaxForce [au] = 0.0001
    }
  }

where the case-convention for ``MaxForce`` is identical to the one used when the
item was created.
