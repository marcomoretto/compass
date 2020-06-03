Quick start
===========

About GraphQL
-------------

*GraphQL is an open-source data query and manipulation language for APIs, and a runtime for fulfilling queries with existing data [...] It provides an efficient, powerful and flexible approach to developing web APIs, and has been compared and contrasted with REST and other web service architectures. It allows clients to define the structure of the data required, and exactly the same structure of the data is returned from the server* [#f1]_

Simple query using the GraphiQL client
--------------------------------------

`GraphiQL <https://www.electronjs.org/apps/graphiql>`_ is a powerful GraphQL web client we are going to use in this documentation to show how to query a COMPASS GraphQL endpoint. The GraphiQL interface is the default way to query COMPASS and it is accessible at 'http://compass.fmach.it/graphql'.

.. _query_1:
.. figure::  _static/graphi.png
   :align:   center

.. note::

   A simple Python script using the `requests <https://pypi.org/project/requests/>`_ package would work just fine, but maybe in that case you might want to have a look at the `pyCOMPASS <https://pycompass.readthedocs.io>`_ package.

   .. code-block:: python
      
      import requests

      url = 'http://compass.fmach.it/graphql'
      query = '''
        {
            compendia {
                name,
                fullName,
                description,
                normalization
            }
        }
      '''
      request = requests.post('http://compass.fmach.it/graphql', json={'query': query})
      print(request.json())

      


.. [#f1] Wikipedia `GraphQL <https://en.wikipedia.org/wiki/GraphQL>`_