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


def test_ncs_size():
    """ Check if loaded the 4 seasonal climatology files

        The default for WOA is to load the seasonal climatology composed
          of four files, one for each season. This test checks if all four
          files were loaded.
    """
    db = WOA()
    assert len(db['sea_water_temperature'].ncs) == 4
    assert len(db['sea_water_salinity'].ncs) == 4


def test_available_vars():
    db = WOA()
    for v in ['sea_water_temperature', 'sea_water_salinity']:
        assert v in db.keys()


def test_oceansites_nomenclature():
    db = WOA()
    assert db['sea_water_temperature'] == db['TEMP']
    #assert db['sea_water_salinity'] == db['PSAL']


# ==== Request points coincidents to the WOA gridpoints
def test_coincident_gridpoint_13():
    db = WOA(dbname='WOA13')

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=-37.5)
    assert np.allclose(t['t_mn'], [24.60449791])

    t = db['sea_water_temperature'].extract(var='t_mn', doy=[136.875, 228.125],
            depth=0, lat=17.5, lon=-37.5)
    assert np.allclose(t['t_mn'], [24.60449791, 26.38446426])

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=[0, 10], lat=17.5, lon=-37.5)
    assert np.allclose(t['t_mn'], [24.60449791, 24.62145996])

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=0, lat=[17.5, 12.5], lon=-37.5)
    assert np.allclose(t['t_mn'], [25.17827606, 24.60449791])

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=[-37.5, -32.5])
    assert np.allclose(t['t_mn'], [24.60449791, 23.98172188])

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=[0, 10], lat=[17.5, 12.5], lon=-37.5)
    assert np.allclose(t['t_mn'],
            [[25.17827606, 24.60449791], [25.25433731, 24.62145996]])


def test_coincident_gridpoint():
    db = WOA()

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=-37.5)
    assert np.allclose(t['t_mn'], [24.641016])

    t = db['sea_water_temperature'].extract(var='t_mn', doy=[136.875, 228.125],
            depth=0, lat=17.5, lon=-37.5)
    assert np.allclose(t['t_mn'], [24.641016, 26.392792])

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=[0, 10], lat=17.5, lon=-37.5)
    assert np.allclose(t['t_mn'], [24.641016, 24.636028])

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=0, lat=[17.5, 12.5], lon=-37.5)
    assert np.allclose(t['t_mn'], [25.167528, 24.641016])

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=[-37.5, -32.5])
    assert np.allclose(t['t_mn'], [24.641016, 23.979605])

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=[0, 10], lat=[17.5, 12.5], lon=-37.5)
    assert np.allclose(t['t_mn'],
            [[25.167528, 24.641016], [25.190489, 24.636028]])


def test_only_one_coincident_gridpoint():
    """Makes difference if only lat, or only lon, is coincident

       Because lat/lon is interpolated together as a 2D space, if only
       one coordinate is coincident it should be instead a 1D interpolation.
    """
    db = WOA(dbname='WOA13')

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=0, lat=-14.03, lon=62.5)
    assert np.allclose(t['t_mn'], [27.41223907])

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=0, lat=-12.5, lon=62.03)
    assert np.allclose(t['t_mn'], [27.76179314])


def test_lon_cyclic():
    db = WOA()

    t1 = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=182.5)
    t2 = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=-177.5)
    assert np.allclose(t1['t_mn'], t2['t_mn'])

    t1 = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=[-37.5, -32.5])
    t2 = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=0, lat=17.5, lon=[322.5, 327.5])
    assert np.allclose(t1['t_mn'], t2['t_mn'])


def test_no_data_available():
    """ This is a position without valid data """

    db = WOA()
    out = db['sea_water_temperature'].extract(
            doy=155, lat=48.1953, lon=-69.5855,
            depth=[2.0, 5.0, 6.0, 21.0, 44.0, 79.0, 5000])
    varnames = [u't_dd', u't_mn', u't_sd', u't_se']
    for v in varnames:
        assert v in out.keys()
    for v in varnames:
        assert ma.getmaskarray(out[v]).all()


def test_extract_overlimit():
    """ Thest a request over the limits of the database """
    db = WOA(dbname='WOA13')

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=5502, lat=17.5, lon=-37.5)
    assert ma.is_masked(t['t_mn'])

    t = db['sea_water_temperature'].extract(var='t_mn', doy=136.875,
            depth=[10, 5502], lat=17.5, lon=-37.5)
    assert np.all(t['t_mn'].mask == [False, True])
    assert ma.allclose(t['t_mn'],
            ma.masked_array([24.62145996, 0], mask=[False, True]))


def test_interpolate_partially_insuficient_data():
    """ Special case with unsificient data for some points

        At 4700m depth the limited available data isin a plane that does not
          contain the desired output. It should not fail, but return non
          masked valid values where it is possible.
    """
    db = WOA()
    t = db['sea_water_temperature'].extract(var='mean', doy=108, lat=4, lon=-38)
    assert not t['mean'].mask.all()


def test_get_point():
    db = WOA(dbname='WOA13')

    t = db['sea_water_temperature'].extract(var='t_mn', doy=90,
            depth=0, lat=17.5, lon=-37.5)
            #depth=0, lat=10, lon=330)
    assert np.allclose(t['t_mn'], [24.306862])


def test_get_point_inland():
    db = WOA()

    t = db['sea_water_temperature'].extract(var='t_mn', doy=90,
            depth=0, lat=-19.9, lon=-43.9)
    assert t['t_mn'].mask.all()


def test_get_profile():
    db = WOA(dbname='WOA13')

    t = db['sea_water_temperature'].extract(var='mean', doy=10,
            depth=[0,10], lat=10, lon=330)
    assert np.allclose(t['mean'], [ 26.07524300,  26.12986183])

    t = db['sea_water_temperature'].extract(doy=10,
            depth=[0,10], lat=10, lon=330)
    assert np.allclose(t['t_se'], [ 0.02941939,  0.0287159 ])
    assert np.allclose(t['t_sd'], [ 0.8398821,  0.8142529])
    assert np.allclose(t['t_mn'], [ 26.07524300,  26.12986183])
    assert np.allclose(t['t_dd'], [ 813, 806])


def test_profile_maskedDepth():
    """Test BUG#10
    """
    db = WOA()
    depth = ma.masked_array([10, 100])
    db['sea_water_temperature'].extract(var='mean', doy=10,
            depth=depth, lat=10, lon=330)


def test_get_section():
    db = WOA()
    t = db['sea_water_temperature'].extract(var='t_mn', doy=10,
            depth=[0,10], lat=28, lon=[-117, -114, -112, -105, -99, -93])


def test_get_surface():
    db = WOA()
    t = db['sea_water_temperature'].extract(var='t_mn', doy=10,
            depth=[0,10], lat=[21, 24, 28, 32],
            lon=[-117, -114, -112, -105, -99, -93])


def test_track():
    db = WOA(dbname='WOA18')
    params = [
            [{"doy": 34, "depth": 0, "lat": 10, "lon": 330},
                [25.51016]],
            [{"doy": 120, "depth": 0, "lat": 10, "lon": 330},
                [25.795078]],
            [{"doy": 34, "depth": 300, "lat": 10, "lon": 330},
                [10.52824]],
            [{"doy": 34, "depth": 0, "lat": 12, "lon": -25},
                [24.412867]],
            [{"doy": [34, 120], "depth": 0, "lat": 10, "lon": 330},
                [25.51016, 25.795078]],
            [{"doy": 34, "depth": [0, 300], "lat": 10, "lon": 330},
                [25.51016, 10.52824]],
            [{"doy": 34, "depth": 0, "lat": [10, 12], "lon": [330, -25]},
                [25.51016, 24.412867]],
            [{"doy": [34, 120], "depth": 0, "lat": [10, 12], "lon": [330, -25]},
                [25.51016, 24.953312]],
            ]

    for p in params:
        t = db['sea_water_temperature'].track(var='t_mn', **p[0])
        assert np.allclose(t['t_mn'], p[1])

def test_dev():
    db = WOA()
    t = db['sea_water_temperature'].extract(doy=228.125, lat=12.5, lon=-37.5)


def test_horizontalSurface_coincidentLatLon():
    """ Creates an horizontal surface with coincident Lat/Lon
    """
    db = WOA()
    t = db['sea_water_temperature'].extract(var='mean', doy=136.875, depth=43,
                                            lon = np.arange(-180, -170, 1),
                                            lat = np.arange(-50, -40, 1),
                                            mode = 'nearest')
    t = db['sea_water_temperature'].extract(var='mean', doy=136.875, depth=43,
                                            lon = np.arange(-180, -170, 1),
                                            lat = np.arange(-50, -40, 1))
