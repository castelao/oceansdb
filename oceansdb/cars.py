# -*- coding: utf-8 -*-

""" Module to handle CARS climatology

Reference: http://www.marine.csiro.au/~dunn/cars2009/

Evaluate at day-of-year 45 (mid February)
t = 2pi x 45/366
feb = mean + an_cos*cos(t) + an_sin*sin(t) + sa_cos*cos(2*t) + sa_sin*sin(2*t)

download_file('http://www.marine.csiro.au/atlas/export/temperature_cars2009a.nc.gz', '755ec973e4d9bd05de202feb696704c2')
download_file('http://www.marine.csiro.au/atlas/export/salinity_cars2009a.nc.gz', '7f78173f4ef2c0a4ff9b5e52b62dc97d')
"""

import os
from os.path import expanduser
import re
from datetime import datetime

import numpy as np
from numpy import ma
import netCDF4
from scipy.interpolate import interp1d
# RectBivariateSpline
from scipy.interpolate import griddata

from .utils import dbsource
from .common import cropIndices


def extract(filename, doy, latitude, longitude, depth):
    """
        For now only the nearest value
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
        For now only the nearest value
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


class cars_data(object):
    """ Returns temperature/salinity from a CARS' file

        CARS climatology decompose temperature and salinity in annual
          and semi-annual harmonics. This class combines those harmonics
          on the fly, for the requested indices.

          data = cars_data('cars_file.nc')
          data[305, 0:10, :, :]
    """
    def __init__(self, carsfile):
        self.nc = carsfile

    def __getitem__(self, item):
        """ t, z, y, x
        """
        tn, zn, yn, xn = item

        #if type(zn) is not slice:
        #    zn = slice(zn, zn+1)
        #zn_an = slice(zn.start, min(64, zn.stop), zn.step)
        #zn_sa = slice(zn.start, min(55, zn.stop), zn.step)

        output = []
        d = 2 * np.pi * (np.arange(1, 367)[tn])/366
        for t in np.atleast_1d(d):
            tmp = self.nc['mean'][:, yn, xn]

            tmp[:64] += self.nc['an_cos'][:, yn, xn] * np.cos(t) + \
                    self.nc['an_sin'][:, yn, xn] * np.sin(t)
            tmp[:55] += self.nc['sa_cos'][:, yn, xn] * np.cos(2*t) + \
                    self.nc['sa_sin'][:, yn, xn] * np.sin(2*t)
            output.append(tmp[zn])

        return ma.asanyarray(output)


class CARS_var_nc(object):
    """
    Reads the CARS Climatology NetCDF file and
    returns the corresponding values of salinity or temperature mean and
    standard deviation for the given time, lat, lon, depth.
    """
    def __init__(self, source):
        self.ncs = source

        self.load_dims(dims=['lat', 'lon', 'depth'])
        self.set_keys()

    def __getitem__(self, item):
        """
            !!!ATENTION!!! Need to improve this.
            cars_data() should be modified to be used when loading ncs with source, thus avoiding the requirement on this getitem but running transparent.
        """
        if item == 'mn':
            return cars_data(self.ncs[0])
        else:
            return self.ncs[0].variables[item]

    def keys(self):
        return self.KEYS

    def load_dims(self, dims):
        self.dims = {}
        for d in dims:
            self.dims[d] = self.ncs[0][d][:]
            for nc in self.ncs[1:]:
                assert (self.dims[d] == nc[d][:]).all()

        #self.dims['time'] = []
        #mfrac = 365/12.
        #for nc in self.ncs:
        #    assert nc.variables['time'].size == 1
        #    self.dims['time'].append(mfrac * nc.variables['time'][0])
        self.dims['time'] = np.array([])

    def set_keys(self):
        """
        """
        self.KEYS = ['mn']
        for v in self.ncs[0].variables.keys():
            if self.ncs[0].variables[v].dimensions == \
                    (u'depth', u'lat', u'lon'):
                        S = self.ncs[0].variables[v].shape
                        for nc in self.ncs[1:]:
                            assert v in nc.variables
                            assert nc.variables[v].shape == S
                        self.KEYS.append(v)

    def __getitem__(self, item):
        if item in self.KEYS:
            return self.ncs[0].variables[item]
        elif re.match('(?:[s,t]_)?sd', item):
            return self.ncs[0].variables['std_dev']
        elif re.match('(?:[s,t]_)?dd', item):
            return self.ncs[0].variables['nq']

        return "yooo"

    def crop(self, doy, depth, lat, lon, var):
        """ Crop a subset of the dataset for each var

            Given doy, depth, lat and lon, it returns the smallest subset
              that still contains the requested coordinates inside it.

            It handels special cases like a region around greenwich and
            the international date line.

            Accepts 0 to 360 and -180 to 180 longitude reference.

            It extends time and longitude coordinates, so simplify the use
               of series. For example, a ship track can be requested with
               a longitude sequence like [352, 358, 364, 369, 380], and
               the equivalent for day of year above 365.
        """
        dims, idx = cropIndices(self.dims, lat, lon, depth)

        dims['time'] = np.atleast_1d(doy)
        idx['tn'] = np.arange(dims['time'].size)

        # Temporary solution. Create an object for CARS dataset
        xn = idx['xn']
        yn = idx['yn']
        zn = idx['zn']
        tn = idx['tn']

        subset = {}
        for v in var:
            if v == 'mn':
                mn = []
                for d in doy:
                    t = 2 * np.pi * d/366
                    # Naive solution
                    # FIXME: This is not an efficient solution.
                    value = self.ncs[0]['mean'][:, yn, xn]
                    value[:64] += self.ncs[0]['an_cos'][:, yn, xn] * np.cos(t) + \
                        self.ncs[0]['an_sin'][:, yn, xn] * np.sin(t)
                    value[:55] += self.ncs[0]['sa_cos'][:, yn, xn] * np.cos(2*t) + \
                        self.ncs[0]['sa_sin'][:, yn, xn] * np.sin(2*t)
                    mn.append(value[zn])

                subset['mn'] = ma.asanyarray(mn)
            else:
                subset[v] = ma.asanyarray(
                        doy.size * [self[v][zn, yn, xn]])
        return subset, dims

    def nearest(self, doy, depth, lat, lon, var):
        output = {}
        for v in var:
            output[v] = ma.masked_all((doy.size, depth.size, lat.size,
                lon.size), dtype='f')
            for tn_out, t in enumerate(doy):
                subset, dims = self.crop(np.array([t]), depth, lat, lon, [v])
                for yn_out, y in enumerate(lat):
                    yn_in = np.absolute(dims['lat']-y).argmin()
                    for xn_out, x in enumerate(lon):
                        xn_in = np.absolute(dims['lon']-x).argmin()
                        for zn_out, z in enumerate(depth):
                            zn_in = np.absolute(dims['depth']-z).argmin()
                            output[v][tn_out, zn_out, yn_out, xn_out] = \
                                    subset[v][0,zn_in, yn_in, xn_in]
        return output

    def interpolate(self, doy, depth, lat, lon, var):
        """ Interpolate each var on the coordinates requested

        """

        subset, dims = self.crop(doy, depth, lat, lon, var)

        if np.all([d in dims['time'] for d in doy]) & \
                np.all([z in dims['depth'] for z in depth]) & \
                np.all([y in dims['lat'] for y in lat]) & \
                np.all([x in dims['lon'] for x in lon]):
                    dn = np.nonzero([d in doy for d in dims['time']])[0]
                    zn = np.nonzero([z in depth for z in dims['depth']])[0]
                    yn = np.nonzero([y in lat for y in dims['lat']])[0]
                    xn = np.nonzero([x in lon for x in dims['lon']])[0]
                    output = {}
                    for v in subset:
                        # output[v] = subset[v][dn, zn, yn, xn]
                        # Seriously that this is the way to do it?!!??
                        output[v] = subset[v][:, :, :, xn][:, :, yn][:, zn][dn]
                    return output

        # The output coordinates shall be created only once.
        points_out = []
        for doyn in doy:
            for depthn in depth:
                for latn in lat:
                    for lonn in lon:
                        points_out.append([doyn, depthn, latn, lonn])
        points_out = np.array(points_out)

        output = {}
        for v in var:
            output[v] = ma.masked_all(
                    (doy.size, depth.size, lat.size, lon.size),
                    dtype=subset[v].dtype)

            # The valid data
            idx = np.nonzero(~ma.getmaskarray(subset[v]))

            if idx[0].size > 0:
                points = np.array([
                    dims['time'][idx[0]], dims['depth'][idx[1]],
                    dims['lat'][idx[2]], dims['lon'][idx[3]]]).T
                values = subset[v][idx]

                # Interpolate along the dimensions that have more than one
                #   position, otherwise it means that the output is exactly
                #   on that coordinate.
                ind = np.array(
                        [np.unique(points[:, i]).size > 1 for i in
                            range(points.shape[1])])
                assert ind.any()

                # These interpolators understand NaN, but not masks.
                values[ma.getmaskarray(values)] = np.nan

                values_out = griddata(
                        np.atleast_1d(np.squeeze(points[:, ind])),
                        values,
                        np.atleast_1d(np.squeeze(points_out[:, ind]))
                        )

                # Remap the interpolated value back into a 4D array
                idx = np.isfinite(values_out)
                for [t, z, y, x], out in zip(points_out[idx], values_out[idx]):
                    output[v][t==doy, z==depth, y==lat, x==lon] = out

            output[v] = ma.fix_invalid(output[v])

        return output

    def extract(self, mode=None, **kwargs):
        """

            Possible scenarios:
              - Point:   doy{1},   depth{1},     lat{1},lon{1}
              - Profile: doy{1},   depth{0,1,n}, lat{1},lon{1}
              - Section: doy{1},   depth{0, n}, [lat{1},lon{n} | lat{n},lon{1}]

              - Track:   doy{1,n}, depth{1,n2},  lat{n},lon{n}
        """
        for k in kwargs:
            assert k in ['var', 'doy', 'depth', 'lat', 'lon'], \
                    "Wrong dimension to extract, check the manual"

        if 'var' in kwargs:
            var = np.atleast_1d(kwargs['var'])
        else:
            var = np.asanyarray(self.KEYS)

        doy = np.atleast_1d(kwargs['doy'])
        # This would only work if doy is 1D
        if type(doy[0]) is datetime:
            doy = np.array([int(d.strftime('%j')) for d in doy])

        if 'depth' in kwargs:
            depth = np.atleast_1d(kwargs['depth'])
        else:
            depth = self.dims['depth'][:]

        assert np.all(depth >= 0), "Depth was supposed to be positive."

        lat = np.atleast_1d(kwargs['lat'])
        lon = np.atleast_1d(kwargs['lon'])

        if mode == 'nearest':
            output = self.nearest(doy, depth, lat, lon, var)
        else:
            output = self.interpolate(doy, depth, lat, lon, var)
            for v in output:
                output[v] = np.atleast_1d(np.squeeze(output[v]))

        return output

    def get_profile(var, doy, depth, lat, lon):
        print("get_profile is deprecated. You should migrate to extract()")
        return extract(var=var, doy=doy, depth=depth, lat=lat, lon=lon)


class CARS(object):
    """
    """
    def __init__(self, dbname='CARS'):
        self.dbname = dbname
        self.data = {'sea_water_temperature': None,
                'sea_water_salinity': None}

    def keys(self):
        return self.data.keys()

    def __getitem__(self, item):
        if item == 'TEMP':
            return self['sea_water_temperature']
        elif item == 'PSAL':
            return self['sea_water_salinity']

        if self.data[item] is None:
            self.data[item] = CARS_var_nc(source=dbsource(self.dbname, item))
        return self.data[item]
