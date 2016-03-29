#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from datetime import datetime

import numpy as np
from numpy import ma

from oceansdb.woa import WOA

def test_import():
    # A shortcut
    from oceansdb import WOA
    db = WOA()


def test_available_vars():
    db = WOA()
    
    for v in ['TEMP', 'PSAL']:
        assert v in db.keys()


# ==== Request points coincidents to the WOA gridpoints
def test_coincident_gridpoint():
    db = WOA()

    t = db['TEMP'].extract(var='mn', doy=136.875,
            depth=0, lat=17.5, lon=-37.5)
    assert np.allclose(t['mn'], [24.60449791])

    t = db['TEMP'].extract(var='t_mn', doy=[136.875, 228.125],
            depth=0, lat=17.5, lon=-37.5)
    assert np.allclose(t['t_mn'], [24.60449791,  26.38446426])

    t = db['TEMP'].extract(var='t_mn', doy=136.875,
            depth=[0, 10], lat=17.5, lon=-37.5)
    assert np.allclose(t['t_mn'], [24.60449791,  24.62145996])

    t = db['TEMP'].extract(var='t_mn', doy=136.875,
            depth=0, lat=[17.5, 12.5], lon=-37.5)
    assert np.allclose(t['t_mn'], [25.17827606,  24.60449791])

    t = db['TEMP'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=[-37.5, -32.5])
    assert np.allclose(t['t_mn'], [24.60449791,  23.98172188])

    t = db['TEMP'].extract(var='t_mn', doy=136.875,
            depth=[0, 10], lat=[17.5, 12.5], lon=-37.5)
    assert np.allclose(t['t_mn'],
            [[ 25.17827606,  24.60449791], [ 25.25433731,  24.62145996]])


def test_lon_cyclic():
    db = WOA()

    t1 = db['TEMP'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=182.5)
    t2 = db['TEMP'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=-177.5)
    assert np.allclose(t1['t_mn'], t2['t_mn'])

    t1 = db['TEMP'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=[-37.5, -32.5])
    t2 = db['TEMP'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=[322.5, 327.5])
    assert np.allclose(t1['t_mn'], t2['t_mn'])

def test_no_data_available():
    """ This is a position without valid data """

    db = WOA()
    out = db['TEMP'].extract(doy=155, lat=48.1953, lon=-69.5855,
            depth=[2.0, 5.0, 6.0, 21.0, 44.0, 79.0, 5000])
    assert sorted(out.keys()) == [u't_dd', u't_mn', u't_sd', u't_se']
    for v in out:
        ma.getmaskarray(out[v]).all()

def test_extract_overlimit():
    """ Thest a request over the limits of the database """
    db = WOA()

    t = db['TEMP'].extract(var='t_mn', doy=136.875,
            depth=5502, lat=17.5, lon=-37.5)
    assert ma.is_masked(t['t_mn'])

    t = db['TEMP'].extract(var='t_mn', doy=136.875,
            depth=[10, 5502], lat=17.5, lon=-37.5)
    assert np.all(t['t_mn'].mask == [False, True])
    assert ma.allclose(t['t_mn'],
            ma.masked_array([24.62145996, 0], mask=[False, True]))

# ======


def notest_get_point():
    db = WOA()

    t = db['TEMP'].extract(var='t_mn', doy=90,
            depth=0, lat=17.5, lon=-37.5)
            #depth=0, lat=10, lon=330)
    assert np.allclose(t['mn'], [24.60449791])


def notest_get_profile():
    db = WOA()


    t = db['TEMP'].extract(var='mn', doy=10,
            depth=[0,10], lat=10, lon=330)
    assert np.allclose(t['mn'], [ 28.09378815,  28.09343529])

    t = db['TEMP'].extract(doy=10,
            depth=[0,10], lat=10, lon=330)
    assert np.allclose(t['t_se'], [ 0.01893404,  0.0176903 ])
    assert np.allclose(t['t_sd'], [ 0.5348658,  0.4927946])
    assert np.allclose(t['t_mn'], [ 28.09378815,  28.09343529])
    assert np.allclose(t['t_dd'], [ 798, 776])


def notest_get_track():
    db = WOA()
    db['TEMP'].get_track(doy=[datetime.now()], depth=0, lat=[10], lon=[330])
    db['TEMP'].get_track(doy=2*[datetime.now()], depth=0, lat=[10, 12], lon=[330, -35])


def test_dev():
    db = WOA()
    t = db['TEMP'].extract(doy=228.125, lat=12.5, lon=-37.5)
