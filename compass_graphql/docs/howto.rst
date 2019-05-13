How To
======

This section contains several examples of GraphQL queries in order to perform main operations on a COMPASS GraphQL endpoint. For each query there might be additional parameters. A good way to have the list of all available parameters is to use a good GraphQL client like `Insomnia <https://insomnia.rest/>`_ and use the autocompletion.

GET available compendia
-----------------------

.. code-block:: javascript

   {
    compendia {
        name,
        fullName,
        description,
        normalization
    }
   }


GET compendium data sources
---------------------------

.. code-block:: javascript

    {
      dataSources(compendium: "vitis_vinifera") {
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
      platforms(compendium:"vitis_vinifera") {
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
      platformTypes(compendium:"vitis_vinifera") {
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
      experiments(compendium:"vitis_vinifera") {
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
      sampleAnnotations(compendium: "vitis_vinifera", first: 10) {
        edges {
          node {
            sample {
              id,
              sampleName
            },
            annotation {
              ontologyNode {
                originalId,
                ontology {
                  name
                }
              }
              value
            }
          }
        }
      }
    }


GET biological feature annotations
----------------------------------

.. code-block:: javascript

    {
     biofeatureAnnotations(compendium:"vitis_vinifera",
        bioFeature_Name:"VIT_00s0332g00060",
      annotationValue_OntologyNode_Ontology_Name:"Gene ontology") {
        edges {
          node {
            annotationValue {
              ontologyNode {
                originalId,
                ontology {
                    name
                }
              }
            }
          }
        }
      }
    }


GET ontology structure
----------------------

.. code-block:: javascript

    {
     ontology(compendium:"vitis_vinifera", name:"Gene ontology") {
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

    {
      sampleAnnotations(compendium:"vitis_vinifera", annotationValue_OntologyNode_OriginalId:"GROWTH.GREENHOUSE") {
        edges {
          node {
            sample {
              sampleName,
              experiment {
                experimentAccessId
              }
            }
          }
        }
      }
    }


GET samples by experiment access id
-----------------------------------

.. code-block:: javascript

    {
     samples(compendium:"vitis_vinifera", experiment_ExperimentAccessId:"GSE1620") {
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
     samples(compendium:"vitis_vinifera", sampleName_Icontains:"GSM786264") {
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
     sampleSets(compendium:"vitis_vinifera", name:"GSM786264.ch1-vs-GSM786258.ch1") {
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
     sampleSets(compendium:"vitis_vinifera", samples:["U2FtcGxlVHlwZTo0MDg2Ng=="]) {
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
      biofeatures(compendium:"vitis_vinifera", name:"VIT_00s0332g00060") {
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

    {
     biofeatureAnnotations(compendium:"vitis_vinifera",annotationValue_OntologyNode_OriginalId:"GO:0006260") {
      edges {
        node {
            bioFeature {
            name
          }
        }
      }
     }
    }


CREATE MODULE with biological features and sample sets
------------------------------------------------------

.. code-block:: javascript

    {
      modules(compendium:"vitis_vinifera",
        biofeaturesIds:["QmlvRmVhdHVyZVR5cGU6NTIzMjU=","QmlvRmVhdHVyZVR5cGU6NTIzMjY="],
        samplesetIds:["U2FtcGxlU2V0VHlwZToxMjYw","U2FtcGxlU2V0VHlwZToxMjYx","U2FtcGxlU2V0VHlwZToxMjYy"]) {
        normalizedValues,
        sampleSets {
          edges {
            node {
              id,
              name,
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
              id,
              name
            }
          }
        }
      }
    }


GET list of saved modules (login required)
------------------------------------------

.. code-block:: javascript

    {
      searchModules(compendium:"vitis_vinifera") {
        edges {
          node {
            id,
            name
          }
        }
      }
    }


SAVE module (login required)
----------------------------

.. code-block:: javascript

    mutation {
      saveModule(compendium:"vitis_vinifera", name:"test", biofeaturesIds:["QmlvRmVhdHVyZVR5cGU6NTIzMjU=","QmlvRmVhdHVyZVR5cGU6NTIzMjY="],
        samplesetIds:["U2FtcGxlU2V0VHlwZToxMjYw","U2FtcGxlU2V0VHlwZToxMjYx","U2FtcGxlU2V0VHlwZToxMjYy"]) {
        ok
      }
    }


UPDATE module name (login required)
-----------------------------------

.. code-block:: javascript

    mutation {
      updateModuleName(compendium:"vitis_vinifera", oldName:"test", newName:"test1") {
        ok
      }
    }


DELETE saved module (login required)
------------------------------------

.. code-block:: javascript

    mutation {
      deleteModule(compendium:"vitis_vinifera", name:"test1") {
        ok
      }
    }


GET saved module values (login required)
----------------------------------------

.. code-block:: javascript

    {
      modules(compendium:"vitis_vinifera",
        name:"test") {
        normalizedValues,
      }
    }


GET saved module's biological features (login required)
-------------------------------------------------------

.. code-block:: javascript

     {
      modules(compendium:"vitis_vinifera",
        name:"test") {
        biofeatures {
          edges {
            node {
              id,
              name
            }
          }
        }
      }
    }


GET saved module's sample sets (login required)
-----------------------------------------------

.. code-block:: javascript

    {
      modules(compendium:"vitis_vinifera",
        name:"test") {
        sampleSets {
          edges {
            node {
              id,
              name,
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
      }
    }


