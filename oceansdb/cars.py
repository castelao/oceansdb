# -*- coding: utf-8 -*-

"""

Reference: http://www.marine.csiro.au/~dunn/cars2009/

Evaluate at day-of-year 45 (mid February)
t = 2pi x 45/366
feb = mean + an_cos*cos(t) + an_sin*sin(t) + sa_cos*cos(2*t) + sa_sin*sin(2*t)

download_file('http://www.marine.csiro.au/atlas/export/temperature_cars2009a.nc.gz', '755ec973e4d9bd05de202feb696704c2')
download_file('http://www.marine.csiro.au/atlas/export/salinity_cars2009a.nc.gz', '7f78173f4ef2c0a4ff9b5e52b62dc97d')
"""

from os.path import expanduser
import re
from datetime import datetime

import numpy as np
from numpy import ma

import os

from oceansdb.utils import dbsource

try:
    import netCDF4
except:
    print("netCDF4 is not available")

# try:
#    from pydap.client import open_url
#    import pydap.lib
#    pydap.lib.CACHE = expanduser('~/.cotederc/pydap_cache')
# except:
#    print("PyDAP is not available")

from scipy.interpolate import interp1d
# RectBivariateSpline
from scipy.interpolate import griddata


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


class CARS_var_nc(object):
    """
    Reads the CARS Climatology NetCDF file and
    returns the corresponding values of salinity or temperature mean and
    standard deviation for the given time, lat, lon, depth.
    """
    def __init__(self, source):
        self.ncs = []
        for s in source:
            self.ncs.append(netCDF4.Dataset(s, 'r'))

        self.load_dims(dims=['lat', 'lon', 'depth'])
        self.set_keys()

    def keys(self):
        return self.KEYS

    def load_dims(self, dims):
        self.dims = {}
        for d in dims:
            self.dims[d] = self.ncs[0].variables[d][:]
            for nc in self.ncs[1:]:
                assert (self.dims[d] == nc.variables[d][:]).all()

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

    def closest(self, doy, depth, lat, lon, var):
        tn = (np.abs(doy - self.dims['time'][:])).argmin()
        zn = [(np.abs(z - self.dims['depth'][:])).argmin() for z in depth]
        yn = (np.abs(lat - self.dims['lat'][:])).argmin()
        # FIXME
        xn = (np.abs(lon - self.dims['lon'][:])).argmin()

        subset = {}
        for v in var:
            if v in self.KEYS:
                subset[v] = self.ncs[tn][v][0, zn, yn, xn]
            else:
                # FIXME: Ugly temporary solution
                tmp = [vv for vv in self.KEYS if vv[2:] == v]
                assert len(tmp) == 1
                subset[v] = self.ncs[tn][tmp[0]][0, zn, yn, xn]

        return subset

    def subset(self, doy, depth, lat, lon, var):
        """ Subset the necessary data to interpolate in the right position

            Special cases that should be handled here:
                0 to 360 versus -180 to 180
                position near grenwich, or international date line

        """
        dims = {}

        zn = slice(
                np.nonzero(self.dims['depth'] <= depth.min())[0].max(),
                np.nonzero(
                    self.dims['depth'] >=
                            min(self.dims['depth'].max(), depth.max())
                            )[0].min() + 1
                )
        # If a higher degree interpolation system uses more than one data
        #   point in the edge, I should extend this selection one point on
        #   each side, without go beyond 0
        # if zn.start < 0:
        #    zn = slice(0, zn.stop, zn.step)
        dims['depth'] = np.atleast_1d(self.dims['depth'][zn])

        yn = slice(
                np.nonzero(self.dims['lat'] <= lat.min())[0].max(),
                np.nonzero(self.dims['lat'] >= lat.max())[0].min() + 1)
        dims['lat'] = np.atleast_1d(self.dims['lat'][yn])

        lon_ext = np.array(
                (self.dims['lon'] - 360).tolist() +
                        self.dims['lon'].tolist() +
                        (self.dims['lon']+360).tolist())
        xn_ext = np.array(3 * list(range(self.dims['lon'].shape[0])))
        xn_start = np.nonzero(lon_ext <= lon.min())[0].max()
        xn_end = np.nonzero(lon_ext >= lon.max())[0].min()
        xn = xn_ext[xn_start:xn_end+1]
        dims['lon'] = np.atleast_1d(lon_ext[xn_start:xn_end+1])

        #if self.dims['time'].shape == (1,):
        #    tn = 0
        #    dims['time'] = self.dims['time']
        #else:
        #    time_ext = np.array(
        #            [self.dims['time'][-1] - 365.25] +
        #                    self.dims['time'].tolist() +
        #                    [self.dims['time'][0] + 365.25])
        #    tn_ext = list(range(self.dims['time'].size))
        #    tn_ext = [tn_ext[-1]] + tn_ext + [tn_ext[0]]
        #    tn_start = np.nonzero(time_ext <= doy.min())[0].max()
        #    tn_end = np.nonzero(time_ext >= doy.max())[0].min()
        #    tn = tn_ext[tn_start:tn_end+1]
        #    dims['time'] = np.atleast_1d(time_ext[tn_start:tn_end+1])
        dims['time'] = np.atleast_1d(doy)

        # messy way to accept t_mn or mn
        varin = []
        #for v in var:
        #    if v in self.KEYS:
        #        varin.append(v)
        #    elif self.KEYS[0][:2] + v in self.KEYS:
        #        varin.append(self.KEYS[0][:2] + v)
        import re
        #for v in var:
        #    if re.search('(?:[t,s]_)?mn', v):
        #        varin.append('mn')
        #    elif re.search('(?:[t,s]_)?sd', v):
        #        varin.append('sd')
        #    elif re.search('(?:[t,s]_)?dd', v):
        #        varin.append('sd')

        subset = {}
        #for v, vin in zip(var, varin):
        #    subset[v] = ma.asanyarray(
        #            [self.ncs[tnn][vin][0, zn, yn, xn] for tnn in tn])

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

    def interpolate(self, doy, depth, lat, lon, var):
        """ Interpolate each var on the coordinates requested

        """

        subset, dims = self.subset(doy, depth, lat, lon, var)

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

                values_out = griddata(
                        np.atleast_1d(np.squeeze(points[:, ind])),
                        values,
                        np.atleast_1d(np.squeeze(points_out[:, ind]))
                        )

                # Remap the interpolated value back into a 4D array
                idx = np.isfinite(values_out)
                for [t, z, y, x], out in zip(points_out[idx], values_out[idx]):
                    output[v][t==doy, z==depth, y==lat, x==lon] = out

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

        try:
            if mode == 'nearest':
                output = self.closest(doy, depth, lat, lon, var)
            else:
                output = self.interpolate(doy, depth, lat, lon, var)
                for v in output:
                    output[v] = np.atleast_1d(np.squeeze(output[v]))
        except:
            print("Sorry, I was not able to extract the climatology.")
            return

        return output

    def get_profile(var, doy, depth, lat, lon):
        print("get_profile is deprecated. You should migrate to extract()")
        return extract(var=var, doy=doy, depth=depth, lat=lat, lon=lon)


class CARS(object):
    """
    """
    def __init__(self, dbname='CARS'):
        self.dbname = dbname
        self.data = {'TEMP': None, 'PSAL': None}

    def keys(self):
        return self.data.keys()

    def __getitem__(self, item):
        if self.data[item] is None:
            self.data[item] = CARS_var_nc(source=dbsource(self.dbname, item))

        return self.data[item]
