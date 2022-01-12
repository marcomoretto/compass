.. COMPASS documentation master file, created by
   sphinx-quickstart on Mon Feb 11 14:08:53 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. |email| image:: _static/email.png

Welcome to COMPASS's documentation!
===================================

COMPASS (**COM**\pendia **P**\rogrammatic **A**\ccess **S**\upport **S**\oftware) is a software layer that provides a `GraphQL <https://graphql.org/>`_ endpoint to query compendia built using `COMMAND>_ <https://command.readthedocs.io>`_ technology.
COMPASS is meant to be the barebone interface on top of a `compendium database <https://command.readthedocs.io/en/latest/database_schema.html>`_ and it is usually preferable to query the database using the Python package `pyCOMPASS <https://pycompass.readthedocs.io>`_ or the R package rCOMPASS for data analysis purposes.

.. note::

   `VESPUCCI <https://vespucci.readthedocs.io>`_, the *Vitis vinifera*  cross-platform expression compendium, is accessible using its COMPASS frontend. Check out the `use cases! <https://vespucci.readthedocs.io/en/latest/use_cases.html>`_

.. note::

   `DashCOMPASS <https://github.com/marcomoretto/dashcompass>`_ is a `Dash <https://dash.plotly.com/introduction>`_ applications built on top of COMPASS using `pyCOMPASS <https://pycompass.readthedocs.io>`_ meant to showcase how to build higher level tools.
   A running instance can be found on `http://compass.fmach.it/dashcompass <http://compass.fmach.it/dashcompass>`_, while complete documentation on the interface can be found in :any:`my-section` section.

.. toctree::
   :maxdepth: 2
   :caption: Table of Contents

   quickstart
   dashcompass
   howto
   deploy

Contribute & Support
====================

Use the `GitHub Push Request and/or Issue Tracker <https://github.com/marcomoretto/compass>`_.

Author
======

To send me an e-mail about anything else related to COMPASS write to |email|

License
=======

The project is licensed under the `GPLv3 license <https://www.gnu.org/licenses/gpl-3.0.html>`_.

