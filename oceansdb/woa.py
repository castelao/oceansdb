# -*- coding: utf-8 -*-

""" Module to handle World Ocean Atlas (WOA) climatology
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


# ============================================================================
def woa_profile(var, d, lat, lon, depth, cfg):
    # Must improve here. This try make sense if fail because there isn't an
    #   etopo file, but if fail for another reason, like there is no lat,
    #   it will loose time trying from_dap.
    try:
        woa = woa_profile_from_file(var, d, lat, lon, depth, cfg)
    except:
        try:
            woa = woa_profile_from_dap(var, d, lat, lon, depth, cfg)
        except:
            print("Couldn't make woa_comparison of %s" % var)
            return

    return woa


def woa_profile_from_dap(var, d, lat, lon, depth, cfg):
    """
    Monthly Climatologic Mean and Standard Deviation from WOA,
    used either for temperature or salinity.

    INPUTS
        time: [day of the year]
        lat: [-90<lat<90]
        lon: [-180<lon<180]
        depth: [meters]

    Reads the WOA Monthly Climatology NetCDF file and
    returns the corresponding WOA values of salinity or temperature mean and
    standard deviation for the given time, lat, lon, depth.
    """
    if lon < 0:
        lon = lon+360

    url = cfg['url']

    doy = int(d.strftime('%j'))
    dataset = open_url(url)

    dn = (np.abs(doy-dataset['time'][:])).argmin()
    xn = (np.abs(lon-dataset['lon'][:])).argmin()
    yn = (np.abs(lat-dataset['lat'][:])).argmin()

    if re.match("temperature\d?$", var):
        mn = ma.masked_values(dataset.t_mn.t_mn[dn, :, yn, xn].reshape(
            dataset['depth'].shape[0]), dataset.t_mn.attributes['_FillValue'])
        sd = ma.masked_values(dataset.t_sd.t_sd[dn, :, yn, xn].reshape(
            dataset['depth'].shape[0]), dataset.t_sd.attributes['_FillValue'])
        # se = ma.masked_values(dataset.t_se.t_se[dn, :, yn, xn].reshape(
        #    dataset['depth'].shape[0]), dataset.t_se.attributes['_FillValue'])
        # Use this in the future. A minimum # of samples
        # dd = ma.masked_values(dataset.t_dd.t_dd[dn, :, yn, xn].reshape(
        #    dataset['depth'].shape[0]), dataset.t_dd.attributes['_FillValue'])
    elif re.match("salinity\d?$", var):
        mn = ma.masked_values(dataset.s_mn.s_mn[dn, :, yn, xn].reshape(
            dataset['depth'].shape[0]), dataset.s_mn.attributes['_FillValue'])
        sd = ma.masked_values(dataset.s_sd.s_sd[dn, :, yn, xn].reshape(
            dataset['depth'].shape[0]), dataset.s_sd.attributes['_FillValue'])
        # dd = ma.masked_values(dataset.s_dd.s_dd[dn, :, yn, xn].reshape(
        #    dataset['depth'].shape[0]), dataset.s_dd.attributes['_FillValue'])
    zwoa = ma.array(dataset.depth[:])

    ind = (depth <= zwoa.max()) & (depth >= zwoa.min())
    # Mean value profile
    f = interp1d(zwoa[~ma.getmaskarray(mn)].compressed(), mn.compressed())
    mn_interp = ma.masked_all(depth.shape)
    mn_interp[ind] = f(depth[ind])
    # The stdev profile
    f = interp1d(zwoa[~ma.getmaskarray(sd)].compressed(), sd.compressed())
    sd_interp = ma.masked_all(depth.shape)
    sd_interp[ind] = f(depth[ind])

    output = {'woa_an': mn_interp, 'woa_sd': sd_interp}

    return output


def woa_track_from_file(d, lat, lon, filename, varnames=None):
    """ Temporary solution: WOA for surface track
    """
    d = np.asanyarray(d)
    lat = np.asanyarray(lat)
    lon = np.asanyarray(lon)

    lon[lon < 0] += 360

    doy = np.array([int(dd.strftime('%j')) for dd in d])

    nc = netCDF4.Dataset(expanduser(filename), 'r')

    if varnames is None:
        varnames = {}
        for v in nc.variables.keys():
            if nc.variables[v].dimensions == \
                    (u'time', u'depth', u'lat', u'lon'):
                        varnames[v] = v

    output = {}
    for v in varnames:
        output[v] = []

    for d_n, lat_n, lon_n in zip(doy, lat, lon):
        # Get the nearest point. In the future interpolate.
        n_d = (np.abs(d_n - nc.variables['time'][:])).argmin()
        n_x = (np.abs(lon_n - nc.variables['lon'][:])).argmin()
        n_y = (np.abs(lat_n - nc.variables['lat'][:])).argmin()

        for v in varnames:
            output[v].append(nc.variables[varnames[v]][n_d, 0, n_y, n_x])

    for v in varnames:
        output[v] = ma.fix_invalid(output[v])

    return output


class WOA_URL(object):
    def __init__(self):
        pass


class WOA_var_nc(object):
    """
    Reads the WOA Monthly Climatology NetCDF file and
    returns the corresponding WOA values of salinity or temperature mean and
    standard deviation for the given time, lat, lon, depth.
    """
    def __init__(self, source):
        self.ncs = source

        self.load_dims(dims=['lat', 'lon', 'depth'])
        self.set_keys()

    def __getitem__(self, item):
        return self.data[item]

    def keys(self):
        return self.KEYS

    def load_dims(self, dims):
        self.dims = {}
        for d in dims:
            self.dims[d] = self.ncs[0][d][:]
            for nc in self.ncs[1:]:
                assert (self.dims[d] == nc[d][:]).all()

        self.dims['time'] = []
        mfrac = 365/12.
        for nc in self.ncs:
            assert nc.variables['time'].size == 1
            self.dims['time'].append(mfrac * nc['time'][0])
        self.dims['time'] = np.array(self.dims['time'])

    def set_keys(self):
        """
        """
        self.KEYS = []
        for v in self.ncs[0].variables.keys():
            if self.ncs[0].variables[v].dimensions == \
                    (u'time', u'depth', u'lat', u'lon'):
                        S = self.ncs[0].variables[v].shape
                        for nc in self.ncs[1:]:
                            assert v in nc.variables
                            assert nc.variables[v].shape == S
                        self.KEYS.append(v)

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
        dims, idx = cropIndices(self.dims, lat, lon, depth, doy)
        subset = {}
        for v in var:
            subset[v] = ma.asanyarray([
                self.ncs[tnn][v][0, idx['zn'], idx['yn'], idx['xn']] \
                        for tnn in idx['tn']])
        return subset, dims

    def nearest(self, doy, depth, lat, lon, var):
        output = {}
        dims, idx = cropIndices(self.dims, lat, lon, depth, doy)
        for v in var:
            output[v] = ma.masked_all((doy.size, depth.size, lat.size,
                lon.size), dtype='f')
            for tn_out, t in enumerate(doy):
                tn_in = np.absolute(dims['time']-t).argmin()
                subset = self.ncs[tn_in][v][0, idx['zn'], idx['yn'], idx['xn']]
                for yn_out, y in enumerate(lat):
                    yn_in = np.absolute(dims['lat']-y).argmin()
                    for xn_out, x in enumerate(lon):
                        xn_in = np.absolute(dims['lon']-x).argmin()
                        for zn_out, z in enumerate(depth):
                            zn_in = np.absolute(dims['depth']-z).argmin()
                            output[v][tn_out, zn_out, yn_out, xn_out] = \
                                    subset[zn_in, yn_in, xn_in]
        return output

    def interpolate(self, doy, depth, lat, lon, var):
        """ Interpolate each var on the coordinates requested

        """
        subset, dims = self.crop(doy, depth, lat, lon, var)

        # Subset contains everything requested. No need to interpolate.
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

        output = {}
        for v in var:
            output[v] = ma.masked_all(
                    (doy.size, depth.size, lat.size, lon.size),
                    dtype=subset[v].dtype)

            # These interpolators don't understand Masked Arrays, but do NaN
            if subset[v].dtype in ['int32']:
                subset[v] = subset[v].astype('f')
            subset[v][ma.getmaskarray(subset[v])] = np.nan
            subset[v] = subset[v].data

        # First linear interpolate on time.
        if not (doy == dims['time']).all():
            for v in subset.keys():
                f = interp1d(dims['time'], subset[v], axis=0)
                subset[v] = f(doy)
            dims['time'] = np.atleast_1d(doy)

        if not (np.all(lat == dims['lat']) and np.all(lon == dims['lon'])):
            # Lat x Lon target coordinates are the same for all time and depth.
            points_out = []
            for latn in lat:
                for lonn in lon:
                    points_out.append([latn, lonn])
            points_out = np.array(points_out)

            # Interpolate on X/Y plane
            for v in subset:
                tmp = np.nan * np.ones(
                        (doy.size, dims['depth'].size, lat.size, lon.size),
                        dtype=subset[v].dtype)
                for nt in range(doy.size):
                    for nz in range(dims['depth'].size):
                        data = subset[v][nt, nz]
                        # The valid data
                        idx = np.nonzero(~np.isnan(data))
                        if idx[0].size > 0:
                            points = np.array([
                                dims['lat'][idx[0]], dims['lon'][idx[1]]]).T
                            values = data[idx]
                            # Interpolate along the dimensions that have more than
                            #   one position, otherwise it means that the output
                            #   is exactly on that coordinate.
                            #ind = np.array([np.unique(points[:, i]).size > 1
                            #    for i in range(points.shape[1])])
                            #assert ind.any()

                            try:
                                values_out = griddata(
                                    #np.atleast_1d(np.squeeze(points[:, ind])),
                                    np.atleast_1d(np.squeeze(points)),
                                    values,
                                    #np.atleast_1d(np.squeeze(points_out[:, ind])))
                                    np.atleast_1d(np.squeeze(points_out)))
                            except:
                                values_out = []
                                for p in points_out:
                                    try:
                                        values_out.append(griddata(
                                            np.atleast_1d(np.squeeze(points)),
                                            values,
                                            np.atleast_1d(np.squeeze(
                                                p))))
                                    except:
                                        values_out.append(np.nan)
                                values_out = np.array(values_out)

                            # Remap the interpolated value back into a 4D array
                            idx = np.isfinite(values_out)
                            for [y, x], out in zip(
                                    points_out[idx], values_out[idx]):
                                tmp[nt, nz, y==lat, x==lon] = out
                subset[v] = tmp

        # Interpolate on z
        same_depth = (np.shape(depth) == dims['depth'].shape) and \
                np.allclose(depth, dims['depth'])
        if not same_depth:
            for v in list(subset.keys()):
                try:
                    f = interp1d(dims['depth'], subset[v], axis=1, bounds_error=False)
                    # interp1d does not handle Masked Arrays
                    subset[v] = f(np.array(depth))
                except:
                    print("Fail to interpolate '%s' in depth" % v)
                    del(subset[v])

        for v in subset:
            if output[v].dtype in ['int32']:
                subset[v] = np.round(subset[v])
            output[v][:] = ma.fix_invalid(subset[v][:])

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

    def extract_track(self, mode=None, **kwargs):
        """

            Possible scenarios:
              - Track:   doy{1,n}, depth{1,n2}, lat{n}, lon{n}
        """
        for k in kwargs:
            assert k in ['var', 'doy', 'depth', 'lat', 'lon'], \
                    "Wrong dimension to extract, check the manual"

        if 'var' in kwargs:
            var = np.atleast_1d(kwargs['var'])
        else:
            var = np.asanyarray(self.KEYS)

        doy = np.atleast_1d(kwargs['doy'])
        if type(doy[0]) is datetime:
            doy = np.array([int(d.strftime('%j')) for d in doy])

        if 'depth' in kwargs:
            depth = np.atleast_1d(kwargs['depth'])
        else:
            depth = self.dims['depth'][:]

        assert np.all(depth >= 0), "Depth was supposed to be positive."

        lat = np.atleast_1d(kwargs['lat'])
        lon = np.atleast_1d(kwargs['lon'])

        assert lat.shape == lon.shape

        output = {}
        for v in var:
            output[v] = []

        for y, x in zip(lat, lon):
            if mode == 'nearest':
                tmp = self.nearest(
                        doy, depth, np.array([y]), np.array([x]), var)
            else:
                tmp = self.interpolate(
                        doy, depth, np.array([y]), np.array([x]), var)

            for v in tmp:
                output[v].append(tmp[v])

        for v in output:
            output[v] = np.atleast_1d(np.squeeze(output[v]))

        return output

    def get_profile(var, doy, depth, lat, lon):
        print("get_profile is deprecated. You should migrate to extract()")
        return extract(var=var, doy=doy, depth=depth, lat=lat, lon=lon)


class WOA(object):
    """
    """
    def __init__(self, dbname='WOA13'):
        self.dbname = dbname
        self.data = {'sea_water_temperature': None,
                'sea_water_salinity': None}

    def keys(self):
        return self.data.keys()

    def __getitem__(self, item):
        if item in ['TEMP', 'temperature']:
            return self['sea_water_temperature']
        elif item in ['PSAL', 'salinity']:
            return self['sea_water_salinity']

        if self.data[item] is None:
            self.data[item] = WOA_var_nc(source=dbsource(self.dbname, item))
        return self.data[item]
