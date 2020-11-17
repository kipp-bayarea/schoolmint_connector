Getting Started
****************

Prerequisites
===============

.. toctree::

    schoolmint_setup

Dependencies
=============

* Python3.7
* `Pipenv <https://pipenv.readthedocs.io/en/latest/>`_
* `Docker <https://www.docker.com/>`_
    * Install for `Mac <https://docs.docker.com/docker-for-mac/install/>`_
    * Install for `Linux <https://docs.docker.com/install/linux/docker-ce/debian/>`_
    * Install for `Windows <https://docs.docker.com/docker-for-windows/install/>`_


Environment
=============

.. toctree::

    environment_setup
    schema_setup

Running the job
================

Build the Docker image
-----------------------
.. code-block:: bash

    docker build -t schoolmint .

Run
----
.. code-block:: bash

    docker run --rm -it schoolmint


Run with volume mapping
------------------------
.. code-block:: bash

    docker run --rm -it -v ${PWD}:/code/ schoolmint


Run with enrollment targets sync (optional)
--------------------------------------------
.. code-block:: bash

    docker run --rm -it schoolmint --targets
