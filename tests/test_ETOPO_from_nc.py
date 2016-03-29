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
    
    for v in ['elevation']:
        assert v in db.keys()


# ==== Request points coincidents to the ETOPO gridpoints
def test_coincident_gridpoint():
    db = ETOPO()

    h = db.extract(lat=17.5, lon=0)
    assert np.allclose(h['elevation'], [305.])


    h = db.extract(lat=[17.5, 18.5], lon=0)
    assert np.allclose(h['elevation'], [305., 335.])

    h = db.extract(lat=17.5, lon=[359.92, 0])
    assert np.allclose(h['elevation'], [305., 305.])

    h = db.extract(lat=[17.5, 18.5], lon=[-0.08, 0])
    assert np.allclose(h['elevation'], [[305., 305.], [335., 335.]])


def test_lon_cyclic():
    db = ETOPO()

    h1 = db.extract(lat=17.5, lon=182.5)
    h2 = db.extract(lat=17.5, lon=-177.5)
    assert np.allclose(h1['elevation'], h2['elevation'])

    h1 = db.extract(lat=17.5, lon=[-37.5, -32.5])
    h2 = db.extract(lat=17.5, lon=[322.5, 327.5])
    assert np.allclose(h1['elevation'], h2['elevation'])

    lons = 360 * np.random.random(10)
    for lon1 in lons:
        h1 = db.extract(lat=17.5, lon=lon1)
        lon2 = lon1 - 360
        h2 = db.extract(lat=17.5, lon=lon2)
        assert np.allclose(h1['elevation'], h2['elevation']), \
                "Different elevation between: %s and %s" % (lon1, lon2)
