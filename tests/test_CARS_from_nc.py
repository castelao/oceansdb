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
    
    for v in ['sea_water_temperature', 'sea_water_salinity']:
        assert v in db.keys()


def test_oceansites_nomenclature():
    db = CARS()
    assert db['sea_water_temperature'] == db['TEMP']
    #assert db['sea_water_salinity'] == db['PSAL']


def test_access_coordinates():
    """Direct access to coordinates and some checking values
    """
    cars = CARS()

    for dataset in ("sea_water_temperature", "sea_water_salinity"):
        assert cars[dataset]["lon"][644] == 322.0
        assert cars[dataset]["lat"][180] == 15.
        assert cars[dataset]["depth"][78] == 5500.
        assert cars[dataset]["depth_ann"][63] == 1800.
        assert cars[dataset]["depth_semiann"][54] == 1000.

def test_access_variables():
    cars = CARS()

    dataset = "sea_water_temperature"
    assert ma.allclose(cars[dataset]["mean"][2, 180, 644], 25.803320464498803)
    assert ma.allclose(cars[dataset]["nq"][2, 180, 644], 1003)
    assert ma.allclose(cars[dataset]["std_dev"][2, 180, 644], 1.23336334365892)

    dataset = "sea_water_salinity"
    assert ma.allclose(cars[dataset]["mean"][2, 180, 644], 36.459932400469995)
    assert ma.allclose(cars[dataset]["nq"][2, 180, 644], 837)
    assert ma.allclose(cars[dataset]["std_dev"][2, 180, 644], 0.23606427296171395)

# ==== Request points coincidents to the CARS gridpoints
def test_coincident_gridpoint():
    db = CARS()

    t = db['sea_water_temperature'].extract(var='mn', doy=100,
            depth=0, lat=17.5, lon=322.5)
    assert np.allclose(t['mn'], [23.78240879])

    t = db['sea_water_temperature'].extract(var='mn', doy=[100, 150],
            depth=0, lat=17.5, lon=322.5)
    assert np.allclose(t['mn'], [23.78240879, 24.57544294])

    t = db['sea_water_temperature'].extract(var='mn', doy=100,
            depth=[0, 10], lat=17.5, lon=322.5)
    assert np.allclose(t['mn'], [23.78240879, 23.97279877])

    t = db['sea_water_temperature'].extract(var='mn', doy=100,
            depth=0, lat=[17.5, 12.5], lon=322.5)
    assert np.allclose(t['mn'], [24.61333538, 23.78240879])

    t = db['sea_water_temperature'].extract(var='mn', doy=100,
            depth=0, lat=17.5, lon=[322.5, 327.5])
    assert np.allclose(t['mn'], [23.78240879, 24.03691995])

    t = db['sea_water_temperature'].extract(var='mn', doy=100,
            depth=[0, 10], lat=[17.5, 12.5], lon=322.5)
    assert np.allclose(t['mn'],
            [[24.61333538, 23.78240879], [24.7047015, 23.97279877]])


def valid_mean_masked_std():
    """Position with valid mean but masked standard deviation

       This was a special case for CoTeDe's quality control where there is a
       reference mean value but can't scale the variability since there is no
       standard deviation.

       I checked this values manually, directly from the original CARS'
       netCDF.
    """
    t = db['sea_water_temperature'].extract(var='mn', doy=156,
            lat=-30, lon=15, depth=1000)
    assert np.allclose(t['mn'], [3.365484633192386])

    t = db['sea_water_temperature'].extract(var='std_dev', doy=156,
            lat=-30, lon=15, depth=1000)
    assert ma.is_masked(t['std_dev'])

    t = db['sea_water_temperature'].extract(var='mn', doy=156,
            lat=-30, lon=15, depth=[475, 500])
    assert np.allclose(t['mn'], [6.576306195708654, 6.205499360879657])

    t = db['sea_water_temperature'].extract(var='std_dev', doy=156,
            lat=-30, lon=15, depth=1000)
    assert np.allclose(t['std_dev'][0], [0.7555582683533487])
    assert ma.is_masked(t['std_dev'][1])


def test_special_cases_near_land():
    """Specific cases from WOD

    Simon pointed 3 profiles from WOD that would fail
    """
    db = CARS()

    coords = [[-67.4683, 109.91, -1.55866820], [-4.32, 114.65, 28.42269382], [-66.95, 111.7, -1.47608867]]
    for (lat, lon, ans) in coords:
        t = db["sea_water_temperature"].extract(var="mn", doy=90, depth=0, lat=lat, lon=lon)
        assert np.allclose(t["mn"], ans)
