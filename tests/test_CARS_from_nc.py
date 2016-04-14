#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from datetime import datetime

import numpy as np
from numpy import ma

from oceansdb.cars import CARS

def test_import():
    # A shortcut
    from oceansdb import CARS
    db = CARS()


def test_available_vars():
    db = CARS()
    
    for v in ['TEMP', 'PSAL']:
        assert v in db.keys()


# ==== Request points coincidents to the CARS gridpoints
def test_coincident_gridpoint():
    db = CARS()

    t = db['TEMP'].extract(var='mn', doy=100,
            depth=0, lat=17.5, lon=322.5)
    assert np.allclose(t['mn'], [23.78240879])

    t = db['TEMP'].extract(var='mn', doy=[100, 150],
            depth=0, lat=17.5, lon=322.5)
    assert np.allclose(t['mn'], [23.78240879, 24.57544294])

    t = db['TEMP'].extract(var='mn', doy=100,
            depth=[0, 10], lat=17.5, lon=322.5)
    assert np.allclose(t['mn'], [23.78240879, 23.97279877])

    t = db['TEMP'].extract(var='mn', doy=100,
            depth=0, lat=[17.5, 12.5], lon=322.5)
    assert np.allclose(t['mn'], [24.61333538, 23.78240879])

    t = db['TEMP'].extract(var='mn', doy=100,
            depth=0, lat=17.5, lon=[322.5, 327.5])
    assert np.allclose(t['mn'], [23.78240879, 24.03691995])

    t = db['TEMP'].extract(var='mn', doy=100,
            depth=[0, 10], lat=[17.5, 12.5], lon=322.5)
    assert np.allclose(t['mn'],
            [[24.61333538, 23.78240879], [24.7047015, 23.97279877]])
