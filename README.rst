========
OceansDB
========

.. image:: https://zenodo.org/badge/52222122.svg
   :target: https://zenodo.org/badge/latestdoi/52222122

.. image:: https://readthedocs.org/projects/oceansdb/badge/?version=latest
    :target: http://oceansdb.readthedocs.org/en/latest/?badge=latest
         :alt: Documentation Status

.. image:: https://img.shields.io/travis/castelao/oceansdb.svg
        :target: https://travis-ci.org/castelao/oceansdb

.. image:: https://img.shields.io/pypi/v/oceansdb.svg
        :target: https://pypi.python.org/pypi/oceansdb


Package to subsample, or interpolate, climatologies like WOA to any coordinates.

This package started with functions to obtain climatological values to compare with measured data, allowing a quality control check by comparison. It hence needed to work for any coordinates requested. I split these functionalities from `CoTeDe <http://cotede.castelao.net>`_ into this standalone package to allow more people to use it for other purposes.

* Free software: 3-clause BSD style license - see LICENSE.rst  
* Documentation: https://oceansdb.readthedocs.io.

Features
--------

- If the database files are not localy available, automatically download it.

- Extract, or interpolate if necessary, climatologic data on requested coordinates;

  - Can request a single point, a profile or a section;

  - Ready to handle -180 to 180 or 0 to 360 coordinate system;

- Ready to use with:

  - World Ocean Atlas (WOA)

  - CSIRO Atlas Regional Seas (CARS)

  - ETOPO (topography)

Quick howto use
---------------

Inside python:

.. code-block:: python

    >>> import oceansdb
    >>> db = oceansdb.WOA()

Find out what is available:

.. code-block:: python

    >>> db.keys()

Average temperature at one point:

.. code-block:: python

    >>> t = db['sea_water_temperature'].extract(var='mean', doy=136.875, depth=0, lat=17.5, lon=-37.5)

A profile of salinity:

.. code-block:: python

    >>> t = db['sea_water_salinity'].extract(var='mean', doy=136.875, depth=[0, 10, 15, 18], lat=17.5, lon=-37.5)

A full depth section of temperature:

.. code-block:: python

    >>> t = db['sea_water_temperature'].extract(var='mean', doy=136.875, lat=17.48, lon=[-39, -37.5, -35.2])

Using CARS instead of WOA:

.. code-block:: python

    >>> db = oceansdb.CARS()
    >>> t = db['sea_water_temperature'].extract(var='mean', doy=136.875, lat=17.48, lon=[-39, -37.5, -35.2], depth=[0,10,120,280])

Or to get topography for one point:

.. code-block:: python

    >>> db = oceansdb.ETOPO()
    >>> h = db['topography'].extract(lat=17.5, lon=0)
