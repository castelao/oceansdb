=====
pyWOA
=====

.. image:: https://zenodo.org/badge/4645/castelao/pyWOA.svg
   :target: https://zenodo.org/badge/latestdoi/4645/castelao/pyWOA

.. image:: https://readthedocs.org/projects/pyWOA/badge/?version=latest
   :target: https://readthedocs.org/projects/pyWOA/?badge=latest
         :alt: Documentation Status

.. image:: https://img.shields.io/travis/castelao/pyWOA.svg
        :target: https://travis-ci.org/castelao/pyWOA

.. image:: https://img.shields.io/pypi/v/pyWOA.svg
        :target: https://pypi.python.org/pypi/pyWOA


Package to subsample World Ocean Atlas climatology.

* Free software: 3-clause BSD style license - see LICENSE.rst  
* Documentation: https://pyWOA.readthedocs.org.

Features
--------

* If the WOA database files are not localy available, download it.
* Extract, or interpolate if necessary, climatologic data on requested coordinates;
* Can request a single point, a profile or a section;
* Ready to handle -180 to 180 or 0 to 360 coordinate system;

Quick howto use
---------------

Inside python:

    from pyWOA import WOA

    db = WOA()

To get temperature at one point:
    t = db['TEMP'].extract(var='t_mn', doy=136.875, depth=0, lat=17.5, lon=-37.5)

To get one profile of salinity:
    t = db['PSAL'].extract(var='t_mn', doy=136.875, depth=[0, 10, 15, 18], lat=17.5, lon=-37.5)

To get one section of temperature:
    t = db['TEMP'].extract(var='t_mn', doy=136.875, lat=17.5, lon=[-39, -37.5, -35])
