========
Usage
========

To use oceansdb in a project:

.. code-block:: python

    import oceansdb

Now create a World Ocean Atlas database object by:

.. code-block:: python

    db = oceansdb.WOA()

On the first time you run this, it might take sometime since it needs to download the actual database files. You don't need to do anything other than wait.

The propriety extract() of the database object is who takes care of sub-sample, and if necessary interpolate, to give you the variable(s) on the requested coordinates. The returned output is always a dictionary, even if you requested only one variable from the database.

To get temperature at one point:

.. code-block:: python

    >>> t = db['TEMP'].extract(var='t_mn', doy=136.875, depth=0, lat=17.5, lon=-37.5)

The WOA climatologic temperature will be available as t['t_mn'].

.. code-block:: python

    >>> t.keys()
    ['t_mn']

    >>> t['t_mn'].shape
    (1,)

    >>> t['t_mn']
    masked_array(data = [ 24.60449791],
                 mask = False,
           fill_value = 1e+20)

If you prefer you can obtain all available variables by not defining var, like:

.. code-block:: python

    >>> t = db['PSAL'].extract(doy=136.875, depth=[0, 10, 15, 18], lat=17.5, lon=-37.5)

    >>> t.keys()
    ['s_dd', 's_sd', 's_se', 's_mn']

To get one profile of salinity:

.. code-block:: python

    >>> t = db['PSAL'].extract(var='t_mn', doy=136.875, depth=[0, 10, 15, 18], lat=17.5, lon=-37.5)

To get one section of temperature:

.. code-block:: python

    >>> t = db['TEMP'].extract(var='t_mn', doy=136.875, lat=17.5, lon=[-39, -37.5, -35])

To get a regular 3D grid:

.. code-block:: python

    >>> t = db['TEMP'].extract(var='t_mn', depth=[0, 10.23], doy=136.875, lat=[15, 17.5, 23], lon=[-39, -37.5, -35, -32.73])

    >>> t['t_mn'].shape
    (2, 3, 4)

To use bathymetry let's first load ETOPO

.. code-block:: python

    >>> db = oceansdb.ETOPO()

Let's check the variables available in ETOPO

.. code-block:: python 

    >>> db.keys()
    ['elevation']

To get topography for one point:

.. code-block:: python

    >>> db.extract(lat = 15, lon = 38 )
    {'elevation': masked_array(data = [ 1372.],
              mask = False,
        fill_value = 1e+20)}

To get topography along a latitude:

.. code-block:: python

    >>> db.extract(lat=15, lon=[25, 30, 38, 40, 45])
    {'elevation': masked_array(data = [1067.0 503.0500183105469 1372.0 152.0 1342.6754150390625],
              mask = [False False False False False],
        fill_value = 1e+20)}

To get topography along a longitude:

.. code-block:: python

   >>> db.extract(lat=[10, 15, 20, 25], lon=38)
   {'elevation': masked_array(data = [1904.0328369140625 1372.0 -733.8268432617188 914.0],
              mask = [False False False False],
        fill_value = 1e+20)}

To get topography along a area:

.. code-block:: python

   >>> db.extract(lat=[10, 15, 20, 25], lon=[30, 38, 40])
   {'elevation': masked_array(data =
   [[366.0 1904.0328369140625 1083.2891845703125]
   [503.0500183105469 1372.0 152.0]
   [305.0 -733.8268432617188 -254.84463500976562]
   [213.0 914.0 899.0667114257812]],
               mask =
   [[False False False]
   [False False False]
   [False False False]
   [False False False]],
         fill_value = 1e+20)}

