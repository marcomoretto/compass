Deploy COMPASS
==============

COMPASS is a complex application and relies on several other software components to work. In order to ease up the deployment process a ``docker-compose.yml`` file is provided, so assuming you have a working `Docker Compose <https://docs.docker.com/compose/>`_ environment, the deployment process will be a matter of running a few commands.

In case you want to manually deploy COMPASS in your environment there will be more steps you will need to take care of such as installing the web-server, the DBMS, etc.

Requirements
------------
Have a look at the ``requirements.txt`` file for details. COMMAND>_ main dependencies are:

 - `Python 3 <https://www.python.org/>`_
 - `Django <https://www.djangoproject.com/>`_
 - `PostgreSQL <https://www.postgresql.org/>`_
 - `Numpy <http://www.numpy.org/>`_
 - `Pandas <https://pandas.pydata.org/>`_
 
Docker Compose
--------------
Assuming that you have `Docker Compose correctly installed <https://docs.docker.com/compose/install/>`_, you should be able to perform the following steps:

.. code-block:: bash

   # 1. clone the repository
   git clone https://github.com/marcomoretto/compass.git

   # 2. build
   docker-compose build

   # 3. start docker
   docker-compose up -d

   # 4. create database schema
   docker-compose exec web python manage.py migrate

That's it! You should be able to point your browser to http://localhost/graphql and see the GraphiQL interface.


Manual Deploy
-------------

One easy way to understand what you need to do to manually deploy COMPASS is to have a look at 2 files:

 - the `Dockerfile <https://github.com/marcomoretto/compass/blob/master/Dockerfile>`_
 - the `docker-compose.yml file <https://github.com/marcomoretto/compass/blob/master/docker-compose.yml>`_

In a nutshell, after having installed and configured `Nginx <https://www.nginx.com/>`_ (or another web-server to run Django applications), `PostgreSQL <https://www.postgresql.org/>`_

.. code-block:: bash

    pip3 install --upgrade pip
    pip3 install -r requirements.txt

Now you should be ready configure Django (check the `documentation for details <https://docs.djangoproject.com/en/1.11>`_), create the database schema and run the application.

.. code-block:: bash

   python manage.py migrate

.. Note::

    COMPASS id a Django application so refer to the Django docs for database configuration https://docs.djangoproject.com/en/1.11/ref/settings/

