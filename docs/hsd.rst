**************
The HSD format
**************

General description
===================

You can think about the Human-readable Structured Data format as a pleasant
representation of a tree structure. It can represent a subset of what you
can do for example with XML. The following constraints compared
to XML apply:

* Every node of a tree, which is not empty, either contains further nodes
  or data, but never both.

* Every node may have a single (string) attribute only.

These constraints allow a very natural looking formatting of the data.

As an example, let's have a look at a data tree, which represents input
for scientific software. In the XML representation, it could be written as ::

  <Hamiltonian>
    <Dftb>
      <Scc>Yes</Scc>
      <Filling>
        <Fermi>
          <Temperature attrib="Kelvin">77</Temperature>
        </Fermi>
      <Filling>
    </Dftb>
  </Hamiltonian>

The same information can be encoded in a much more natural and compact form in HSD
format as ::

  Hamiltonian {
    Dftb {
      Scc = Yes
      Filling {
        Fermi {
          Temperature [Kelvin] = 77
        }
      }
    }
  }

The content of a node are passed either between an opening and a closing
curly brace or after an equals sign. In the latter case the end of the line will
be the closing delimiter. The attribute (typically the unit of the data
which the node contains) is specified between square brackets after
the node name.

The equals sign can be used to assign data as a node content (provided
the data fits into one line), or to assign a single child node as content
for a given node. This leads to a compact and expressive notation for those
cases, where (by the semantics of the input) a given node is only allowed to
have a single child node as content. The tree above is a piece of a typical
DFTB+ input, where only one child node is allowed for the nodes ``Hamiltonian``
and ``Filling``, respectively (They specify the type of the Hamiltonian
and the filling function). By making use of equals signs, the
simplified HSD representation can be as compact as ::

  Hamiltonian = Dftb {
    Scc = Yes
    Filling = Fermi {
      Temperature [Kelvin] = 77
    }
  }

and still represent the same tree.


Mapping to dictionaries
=======================

Being basically a subset of XML, HSD data is best represented as an XML
DOM-tree. However, very often a dictionary representation is more desirable,
especially when the language used to query and manipulate the tree offers
dictionaries as primary data type (e.g. Python). The data in an HSD input
can be easily represented with the help of nested dictionaries and lists. The
input from the previous section would have the following representation as
Python dictionary (or as a JSON formatted input file)::

  {
      "Hamiltonian": {
          "Dftb": {
              "Scc": Yes,
              "Filling": {
                  "Fermi": {
                      "Temperature": 77,
                      "Temperature.attrib": "Kelvin"
                  }
              }
          }
      }
  }

The attribute of a node is stored under a special key containting the name of
the node and the ``.attrib`` suffix.

One slight complication of the dictionary representation arises in the case
of node which has multiple child nodes with the same name ::

  <ExternalField>
    <PointCharges>
      <GaussianBlurWidth>3</GaussianBlurWidth>
      <CoordsAndCharges>
       3.3 -1.2 0.9   9.2
       1.2 -3.4 5.6  -3.3
      </CoordsAndCharges>
    </PointCharges>
    <PointCharges>
      <GaussianBlurWidth>10</GaussianBlurWidth>
      <CoordsAndCharges>
       1.0   2.0  3.0  4.0
       -1.0 -2.0 -3.0 -4.0
      </CoordsAndCharges>
    </PointCharges>
  </ExternalField>

While the HSD representation has no problem to cope with the situation ::

  ExternalField {
    PointCharges {
      GaussianBlurWidth = 3
      CoordsAndCharges {
       3.3 -1.2 0.9   9.2
       1.2 -3.4 5.6  -3.3
      }
    }
    PointCharges {
      GaussianBlurWidth = 10
      CoordsAndCharges {
       1.0   2.0  3.0  4.0
       -1.0 -2.0 -3.0 -4.0
      }
    }
  }

a trick is needed for the dictionary / JSON representation, as multiple keys
with the same name are not allowed in a dictionary. Therefore, the repetitive
nodes will be mapped to one key, which will contain a list of dictionaries
(instead of a single dictionary as in the usual case)::

  {
      "ExternalField": {
          // Note the list of dictionaries here!
          "PointCharges": [
              {
                  "GaussianBlurWidth": 3,
                  "CoordsAndCharges": [
                      [3.3, -1.2, 0.9, 9.2],
                      [1.2, -3.4, 5.6, -3.3]
                  ]
              },
              {
                  "GaussianBlurWidth": 10,
                  "CoordsAndCharges": [
                      [1.0,  2.0, 3.0, 4.0 ],
                      [-1.0, -2.0, -3.0, -4.0 ]
                  ]
              },
          ]
          # Also attributes becomes a list. Due to technialc reasons the
          # dictbuilder always creates an attribute list for mulitple nodes,
          # even if none of the nodes carries an actual attribute.
          "PointCharges.attrib": [None, None]
      }
  }

The mapping works in both directions, so that this dictionary (or the JSON file
created from it) can be easily converted back to the HSD form again.


Processing related information
==============================

Additional to the data stored in an HSD-file, further processing related
information can be recorded on demand. The current Python implementation is able
to record following additional data for each HSD node:

* the line, where the node was defined in the input (helpful for printing out
  informative error messages),

* the name of the HSD node, as found in the input (useful if the tag names are
  converted to lower case to ease case-insensitive handling of the input) and

* whether an equals sign was used to open the block.

If this information is being recorded, a special key with the
``.hsdattrib`` suffix will be generated for each node in the dictionary/JSON
presentation. The corresponding value will be a dictionary with those
information.

As an example, let's store the input from the previous section ::

  Hamiltonian = Dftb {
    Scc = Yes
    Filling = Fermi {
      Temperature [Kelvin] = 77
    }
  }

in the file `test.hsd`, parse it and convert the node names to lower case
(to make enable case-insensitive input processing). Using the Python command ::

  inpdict = hsd.load("test.hsd", lower_tag_names=True, include_hsd_attribs=True)

will yield the following dictionary representation of the input::

  {
      'hamiltonian.hsdattrib': {'equal': True, 'line': 0, 'tag': 'Hamiltonian'},
      'hamiltonian': {
          'dftb.hsdattrib': {'line': 0, equal: False, 'tag': 'Dftb'},
          'dftb': {
              'scc.hsdattrib': {'equal': True, 'line': 1, 'tag': 'Scc'},
              'scc': True,
              'filling.hsdattrib': {'equal': True, 'line': 2, 'tag': 'Filling'},
              'filling': {
                  'fermi.hsdattrib': {'line': 2, 'equal': False, 'tag': 'Fermi'},
                  'fermi': {
                      'temperature.attrib': 'Kelvin',
                      'temperature.hsdattrib': {'equal': True, 'line': 3,
                                                'tag': 'Temperature'},
                      'temperature': 77
                  }
              }
          }
      }
  }

The recorded line numbers can be used to issue helpful error messages with
information about where the user should search for the problem.
The node names and formatting information about the equal sign ensures
that the formatting is similar to the original HSD, if the data is dumped
into the HSD format again. Dumping the dictionary with ::

  hsd.dump(inpdict, "test2-formatted.hsd", use_hsd_attribs=True)

would indeed yield ::

  Hamiltonian = Dftb {
    Scc = Yes
    Filling = Fermi {
      Temperature [Kelvin] = 77
    }
  }

which is basically identical with the original input. If the additional
processing information is not recorded when the data is loaded, or
it is not considered when the data is dumped as HSD again ::

  inpdict = hsd.load("test.hsd", lower_tag_names=True)
  hsd.dump(inpdict, "test2-unformatted.hsd")

the resulting formatting will more strongly differ from the original HSD ::

  hamiltonian {
    dftb {
      scc = Yes
      filling {
        fermi {
          temperature [Kelvin] = 77
        }
      }
    }
  }

Still nice and readable, but less compact and with different casing.
