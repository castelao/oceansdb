# -*- coding: utf-8 -*-

"""

Reference: http://www.marine.csiro.au/~dunn/cars2009/

Evaluate at day-of-year 45 (mid February)
t = 2pi x 45/366
feb = mean + an_cos*cos(t) + an_sin*sin(t) + sa_cos*cos(2*t) + sa_sin*sin(2*t)

download_file('http://www.marine.csiro.au/atlas/export/temperature_cars2009a.nc.gz', '755ec973e4d9bd05de202feb696704c2')
download_file('http://www.marine.csiro.au/atlas/export/salinity_cars2009a.nc.gz', '7f78173f4ef2c0a4ff9b5e52b62dc97d')
"""

import numpy as np
import netCDF4

def extract(filename, doy, latitude, longitude, depth):
    """
        For now only the closest value
        For now only for one position, not an array of positions
        longitude 0-360
    """
    assert np.size(doy) == 1
    assert np.size(latitude) == 1
    assert np.size(longitude) == 1
    assert np.size(depth) == 1

    assert (longitude >= 0) & (longitude <= 360)
    assert depth >= 0

    nc = netCDF4.Dataset(filename)

    t = 2 * np.pi * doy/366

    Z = np.absolute(nc['depth'][:] - depth).argmin()
    I = np.absolute(nc['lat'][:] - latitude).argmin()
    J = np.absolute(nc['lon'][:] - longitude).argmin()

    # Naive solution
    value = nc['mean'][:, I, J]
    value[:64] += nc['an_cos'][Z, I, J] * np.cos(t) + \
            nc['an_sin'][:, I, J] * np.sin(t)
    value[:55] += nc['sa_cos'][Z, I, J] * np.cos(2*t) + \
            nc['sa_sin'][:, I, J] * np.sin(2*t)
    value = value[Z]

    std = nc['std_dev'][Z, I, J]

    return value, std


def cars_profile(filename, doy, latitude, longitude, depth):
    """
        For now only the closest value
        For now only for one position, not an array of positions
        longitude 0-360
    """
    assert np.size(doy) == 1
    assert np.size(latitude) == 1
    assert np.size(longitude) == 1
    #assert np.size(depth) == 1

    assert (longitude >= 0) & (longitude <= 360)
    assert depth >= 0

    nc = netCDF4.Dataset(filename)

    t = 2 * np.pi * doy/366

    # Improve this. Optimize to get only necessary Z
    Z = slice(0, nc['depth'].size)
    I = np.absolute(nc['lat'][:] - latitude).argmin()
    J = np.absolute(nc['lon'][:] - longitude).argmin()

    # Not efficient, but it works
    assert (nc['depth'][:64] == nc['depth_ann'][:]).all()
    assert (nc['depth'][:55] == nc['depth_semiann'][:]).all()
    value = nc['mean'][:, I, J]
    value[:64] += nc['an_cos'][Z, I, J] * np.cos(t) + \
            nc['an_sin'][:, I, J] * np.sin(t)
    value[:55] += nc['sa_cos'][Z, I, J] * np.cos(2*t) + \
            nc['sa_sin'][:, I, J] * np.sin(2*t)
    value = value

    output = {'depth': np.asanyarray(depth)}
    from scipy.interpolate import griddata
    output['value'] = griddata(nc['depth'][Z], value[Z], depth)

    for v in ['std_dev']:
        output[v] = griddata(nc['depth'][Z], nc[v][Z, I, J], depth)

    return output
