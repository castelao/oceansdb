#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Tests cars_data, a pseudo-dataset that extracts CARS values
"""

from numpy import ma

from oceansdb.cars import cars_data
from oceansdb.utils import dbsource


def test_single_points_temp():
    t = cars_data(dbsource("CARS", "sea_water_temperature")[0])

    assert ma.allclose(t[21, 10, 100, 100], 21.96829189)
    assert ma.allclose(t[21, 60, 100, 100], 2.90537812)
    assert ma.allclose(t[21, 70, 100, 100], 1.64459127)


def test_single_points_temp():
    s = cars_data(dbsource("CARS", "sea_water_salinity")[0])

    assert ma.allclose(s[21, 10, 100, 100], 35.40945547)
    assert ma.allclose(s[21, 60, 100, 100], 34.63498726)
    assert ma.allclose(s[21, 70, 100, 100], 34.73160469)


def test_single_point_temp_depth_range():
    t = cars_data(dbsource("CARS", "sea_water_temperature")[0])

    assert ma.allclose(
        t[21, 1:5, 100, 100], [[26.99971054, 26.94366615, 26.66702706, 25.99268163]]
    )


def test_temp_depth_transition():
    t = cars_data(dbsource("CARS", "sea_water_temperature")[0])

    assert ma.allclose(
        t[21, 50:70:3, 100, 100],
        [
            [
                8.53625959,
                6.30013341,
                4.38342194,
                3.15104323,
                2.67215991,
                2.44595852,
                1.98670899,
            ]
        ],
    )
