# -*- coding: utf-8 -*-

"""
Test cropping a subset of a data array


"""

import numpy as np
from oceansdb.common import cropIndices

test_dims = {
        'time': np.array([45.625, 136.875, 228.125, 319.375]),
        'lat': np.array([-87.5, -50, -0.3, 0.1, 38, 87.5]),
        'lon': np.array([-2.5, 2.5, 7.5]),
        'depth': np.array([0, 10])
        }


def check_dims(dims_in, dims_out):
    """The output should contain all dimensions from the input

    Note that the trivial answer is a slice with all elements.
    """
    missing = [v for v in dims_in if v not in dims_out]
    assert len(missing) == 0, "Output missing dimensions: {}".format(missing)


def test_single_point():
    dims, idx = cropIndices(test_dims, lat=40, lon=0, depth=5, doy=60)

    check_dims(test_dims, dims)


def test_single_point_coincident():
    dims, idx = cropIndices(test_dims, lat=38, lon=2.5, depth=10, doy=45.625)

    check_dims(test_dims, dims)


def test_single_point_nodepth_nodoy():
    dims, idx = cropIndices(test_dims, lat=38, lon=2.5)

    check_dims(test_dims, dims)


def test_single_point_depth_extenting_beyond():
    depth = [0, 20]
    assert max(depth) > max(test_dims["depth"]), "Test requires a deeper depth"
    dims, idx = cropIndices(test_dims, lat=38, lon=2.5, depth=depth)

    check_dims(test_dims, dims)
