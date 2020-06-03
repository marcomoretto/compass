How To
======

This section contains several examples of GraphQL queries in order to perform main operations on a COMPASS GraphQL endpoint. For each query there might be additional parameters. **An easy way to have the list of all available parameters is to use the GraphiQL client** and use the autocompletion (ALT + SPACEBAR).

GET available compendia
-----------------------

.. code-block:: javascript

	{
	  compendia {
		name,
		fullName,
		description,
		defaultVersion
		versions {
		  versionNumber,
		  versionAlias,
		  defaultDatabase,
		  databases {
			name,
			normalizations
		  }
		}
	  }
	}


GET compendium data sources
---------------------------

.. code-block:: javascript

    {
      dataSources(compendium: "vespucci") {
        edges {
          node {
            id,
            sourceName
          }
        }
      }
    }


GET platform information
------------------------

.. code-block:: javascript

    {
      platforms(compendium:"vespucci") {
        edges {
          node {
            platformAccessId,
            platformName,
            description,
            dataSource {
              sourceName
            },
            platformType {
              name
            }
          }
        }
      }
    }


GET platform types
------------------

.. code-block:: javascript

    {
      platformTypes(compendium:"vespucci") {
        edges {
          node {
            id,
            name,
            description
          }
        }
      }
    }


GET experiments information
---------------------------

.. code-block:: javascript

    {
      experiments(compendium:"vespucci") {
        edges {
          node {
            organism,
            experimentAccessId,
            experimentName
          }
        }
      }
    }


GET sample annotation
---------------------

.. code-block:: javascript

    {
      sampleAnnotations(compendium: "vespucci", first: 10) {
        edges {
          node {
            sample {
              id,
              sampleName
            },
            annotation
          }
        }
      }
    }

.. note::

    The returned annotation is the JSON-LD format of RDF annotation.


GET biological feature annotations
----------------------------------

.. code-block:: javascript

	{
	  biofeatureAnnotations(compendium: "vespucci", bioFeature_Name: "VIT_00s0332g00060") {
		edges {
		  node {
			annotation
		  }
		}
	  }
	}

.. note::

    The returned annotation is the JSON-LD format of RDF annotation.


GET ontology structure
----------------------

.. code-block:: javascript

    {
     ontology(compendium:"vespucci", name:"Gene ontology") {
      edges {
        node {
          structure
        }
      }
     }
    }

.. note::

    The returned structure is a JSON created using the `networkx Python package <https://networkx.github.io/documentation/latest/reference/readwrite/generated/networkx.readwrite.json_graph.node_link_data.html>`_


GET samples by annotation terms
-------------------------------

.. code-block:: javascript

    <TODO>


GET samples by experiment access id
-----------------------------------

.. code-block:: javascript

    {
     samples(compendium:"vespucci", experiment_ExperimentAccessId:"GSE54347") {
      edges {
        node {
          sampleName,
          description
        }
      }
     }
    }


GET sample by access id
-----------------------

.. code-block:: javascript

    {
     samples(compendium:"vespucci", sampleName_Icontains:"GSM1313535") {
      edges {
        node {
          sampleName,
          description
        }
      }
     }
    }


GET sample set by name
----------------------

.. code-block:: javascript


    {
     sampleSets(compendium:"vespucci", name:"GSE27180_48hours-1-vs-GSE27180_0h-2") {
      edges {
        node {
          id,
          name
        }
      }
     }
    }


GET sample set by sample id
---------------------------

.. code-block:: javascript

    {
     sampleSets(compendium:"vespucci", samples:["U2FtcGxlVHlwZTox"]) {
      edges {
        node {
          id,
          name
        }
      }
     }
    }


GET biological feature by name
------------------------------

.. code-block:: javascript

    {
      biofeatures(compendium:"vespucci", name:"VIT_00s0332g00060") {
        edges {
          node {
            name,
            biofeaturevaluesSet(bioFeatureField_Name:"sequence") {
              edges {
                node {
                  value
                }
              }
            }
          }
        }
      }
    }


GET biological feature by annotation terms
------------------------------------------

.. code-block:: javascript

    <TODO>


CREATE MODULE with biological features and sample sets
------------------------------------------------------

.. code-block:: javascript

	{
	  modules(compendium: "vespucci", version:"legacy", biofeaturesIds: ["QmlvRmVhdHVyZVR5cGU6MQ==","QmlvRmVhdHVyZVR5cGU6Mg=="], samplesetIds: ["U2FtcGxlU2V0VHlwZToxMjYw", "U2FtcGxlU2V0VHlwZToxMjYx", "U2FtcGxlU2V0VHlwZToxMjYy"]) {
		normalizedValues
		sampleSets {
		  edges {
			node {
			  id
			  name
			  normalizationdesignsampleSet {
				edges {
				  node {
					sample {
					  sampleName
					}
				  }
				}
			  }
			}
		  }
		}
		biofeatures {
		  edges {
			node {
			  id
			  name
			}
		  }
		}
	  }
	}