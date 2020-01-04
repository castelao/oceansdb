#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from datetime import datetime

import numpy as np
from numpy import ma

from oceansdb.etopo import ETOPO

def test_import():
    # A shortcut
    from oceansdb import ETOPO
    db = ETOPO()


def test_available_vars():
    db = ETOPO()
    
    for v in ['topography']:
        assert v in db.keys()


# ==== Request points coincidents to the ETOPO gridpoints
def test_coincident_gridpoint():
    db = ETOPO()

    h = db['topography'].extract(lat=17.5, lon=0)
    assert np.allclose(h['height'], [305.])

    h = db['topography'].extract(lat=[17.5, 18.5], lon=0)
    assert np.allclose(h['height'], [305., 335.])

    h = db['topography'].extract(lat=17.5, lon=[0, 0.25])
    assert np.allclose(h['height'], [305., 305.])

    h = db['topography'].extract(lat=[17.5, 18.5], lon=[0, 0.25])
    assert np.allclose(h['height'], [[305., 305.], [335., 335.]])


def test_lon_cyclic():
    db = ETOPO()

    h1 = db['topography'].extract(lat=17.5, lon=182.5)
    h2 = db['topography'].extract(lat=17.5, lon=-177.5)
    assert np.allclose(h1['height'], h2['height'])

    h1 = db['topography'].extract(lat=17.5, lon=[-37.5, -32.5])
    h2 = db['topography'].extract(lat=17.5, lon=[322.5, 327.5])
    assert np.allclose(h1['height'], h2['height'])

    lons = 360 * np.random.random(10)
    for lon1 in lons:
        h1 = db['topography'].extract(lat=17.5, lon=lon1)
        lon2 = lon1 - 360
        h2 = db['topography'].extract(lat=17.5, lon=lon2)
        assert np.allclose(h1['height'], h2['height']), \
                "Different height between: %s and %s" % (lon1, lon2)


def test_resolution():
    """Test different resolutions of ETOPO

       Test in places where the two resolutions give different values to
       validate the result
    """
    # 5 min arc resolution
    db = ETOPO(resolution='5min')
    h5min = db['topography'].extract(lat=-67, lon=103)
    assert np.allclose(h5min['height'], [1585.0])

    # 1 min arc resolution
    db = ETOPO(resolution='1min')
    h1min = db['topography'].extract(lat=-67, lon=103)
    assert np.allclose(h1min['height'], [-26])


def test_track():
    db = ETOPO()

    h = db['topography'].track(lat=[17.5, 18.5], lon=[0, 0.25])
    assert np.allclose(h['height'], [305., 335.])

    h = db['topography'].track(lat=[12, 15], lon=[-38, -35])
    assert np.allclose(h['height'], [-4895.982 , -5959.1216])
