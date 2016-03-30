========
Usage
========

To use oceansdb in a project::

    $ from oceansdb import WOA

Now create a World Ocean Atlas database object by::

    $ db = WOA()

On the first time you run this, it might take sometime since it needs to download the actual database files. You don't need to do anything other than wait.

The propriety extract() of the database object is who takes care of subsample, and if necessary interpolate, to give you the variable(s) on the requested coordinates. The returnned output is always a dictionary, even if you requested only one variable from the database.

To get temperature at one point::

    $ t = db['TEMP'].extract(var='t_mn', doy=136.875, depth=0, \
    $ lat=17.5, lon=-37.5)

The climatologic temperature will be available as t['t_mn'].
If you prefer you can obtain all available variables by not defining var, like::

    $ t = db['PSAL'].extract(doy=136.875, depth=[0, 10, 15, 18], \
    $ lat=17.5, lon=-37.5)


To get one profile of salinity::

    $ t = db['PSAL'].extract(var='t_mn', doy=136.875, \
    $ depth=[0, 10, 15, 18], lat=17.5, lon=-37.5)

To get one section of temperature::

    $ t = db['TEMP'].extract(var='t_mn', doy=136.875, \
    $ lat=17.5, lon=[-39, -37.5, -35])
