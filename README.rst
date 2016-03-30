========
OceansDB
========

.. image:: https://zenodo.org/badge/4645/castelao/pyWOA.svg
   :target: https://zenodo.org/badge/latestdoi/4645/castelao/pyWOA

.. image:: https://readthedocs.org/projects/pywoa/badge/?version=latest
    :target: http://pywoa.readthedocs.org/en/latest/?badge=latest
         :alt: Documentation Status

.. image:: https://img.shields.io/travis/castelao/oceansdb.svg
        :target: https://travis-ci.org/castelao/oceansdb

.. image:: https://img.shields.io/pypi/v/oceansdb.svg
        :target: https://pypi.python.org/pypi/oceansdb


Package to subsample, or interpolate, World Ocean Atlas climatology to any coordinates.

This package started with functions to obtain climatological values to compare with measured data, allowing a quality control check by comparison. It hence needed to work for any coordinates requested. I recently split these functionalities from CoTeDe into this standalone package to allow more people to use it for other purposes.

* Free software: 3-clause BSD style license - see LICENSE.rst  
* Documentation: https://oceansdb.readthedocs.org.

Features
--------

* If the WOA database files are not localy available, download it.
* Extract, or interpolate if necessary, climatologic data on requested coordinates;
* Can request a single point, a profile or a section;
* Ready to handle -180 to 180 or 0 to 360 coordinate system;

Quick howto use
---------------

Inside python:

    from oceansdb import WOA

    db = WOA()

To get temperature at one point:
    t = db['TEMP'].extract(var='t_mn', doy=136.875, depth=0, lat=17.5, lon=-37.5)

To get one profile of salinity:
    t = db['PSAL'].extract(var='t_mn', doy=136.875, depth=[0, 10, 15, 18], lat=17.5, lon=-37.5)

To get a full depth section of temperature:
    t = db['TEMP'].extract(var='t_mn', doy=136.875, lat=17.5, lon=[-39, -37.5, -35])
