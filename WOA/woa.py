# -*- coding: utf-8 -*-

from os.path import expanduser
import re
from datetime import datetime

import numpy as np
from numpy import ma

import os

from WOA.utils import dbsource

try:
    import netCDF4
except:
    print("netCDF4 is not available")

try:
    from pydap.client import open_url
    import pydap.lib
    pydap.lib.CACHE = expanduser('~/.cotederc/pydap_cache')
except:
    print("PyDAP is not available")

from scipy.interpolate import interp1d
# RectBivariateSpline
from scipy.interpolate import griddata


# ============================================================================
def woa_profile(var, d, lat, lon, depth, cfg):
    # Must improve here. This try make sense if fail because there isn't an
    #   etopo file, but if fail for another reason, like there is no lat,
    #   it will loose time trying from_dap.
    try:
        woa = woa_profile_from_file(var,
                d, lat, lon, depth, cfg)
    except:
        try:
            woa = woa_profile_from_dap(var,
                d, lat, lon, depth, cfg)
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


def woa_profile_from_file(var, d, lat, lon, depth, cfg):
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
        lon = lon + 360

    doy = int(d.strftime('%j'))
    nc = netCDF4.Dataset(expanduser(cfg['file']), 'r')

    # Get the nearest point. In the future interpolate.
    dn = (np.abs(doy - nc.variables['time'][:])).argmin()
    xn = (np.abs(lon - nc.variables['lon'][:])).argmin()
    yn = (np.abs(lat - nc.variables['lat'][:])).argmin()

    vars = cfg['vars']

    climdata = {}
    for v in vars:
        climdata[v] = ma.masked_values(
                nc.variables[vars[v]][dn, :, yn, xn],
                nc.variables[vars[v]]._FillValue)

    zwoa = ma.array(nc.variables['depth'][:])

    ind_z = (depth <= zwoa.max()) & (depth >= zwoa.min())
    output = {}
    # Mean value profile
    for v in vars:
        # interp1d can't handle masked values
        ind_valid = ~ma.getmaskarray(climdata[v])
        f = interp1d(zwoa[ind_valid], climdata[v][ind_valid])
        output[v] = ma.masked_all(depth.shape)
        output[v][ind_z] = f(depth[ind_z])
    # # The stdev profile
    # f = interp1d(zwoa[~ma.getmaskarray(sd)].compressed(), sd.compressed())
    # sd_interp = ma.masked_all(depth.shape)
    # sd_interp[ind] = f(depth[ind])

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
            if nc.variables[v].dimensions == (u'time', u'depth', u'lat', u'lon'):
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


# ---- unifinished, under development ----
def build_input(doy, depth, lat, lon, filename, varnames):
    """ Subsample WOA from nc file

        To improve efficiency of interpolation
    """
    nc = netCDF4.Dataset(expanduser(filename), 'r')

    output = {}
    for v in (u'time', u'depth', u'lat', u'lon'):
        output[v] = nc.variables[v][:]
    for v in varnames:
        output[v] = nc.variables[v][:]

    return output
    # Get the nearest point. In the future interpolate.
    dn = slice(
            (np.abs(np.min(doy) - nc.variables['time'][:])).argmin() - 1,
            (np.abs(np.max(doy) - nc.variables['time'][:])).argmin() + 1
            )
    zn = slice(
            (np.abs(np.min(depth) - nc.variables['depth'][:])).argmin() - 1,
            (np.abs(np.max(depth) - nc.variables['depth'][:])).argmin() + 1
            )
    xn = slice(
            (np.abs(np.min(lon) - nc.variables['lon'][:])).argmin() - 1,
            (np.abs(np.max(lon) - nc.variables['lon'][:])).argmin() + 1
            )
    yn = slice(
            (np.abs(np.min(lat) - nc.variables['lat'][:])).argmin() - 1,
            (np.abs(np.max(lat) - nc.variables['lat'][:])).argmin() + 1
            )

    # Temporary solution. Improve in the future
    if dn.start < 0:
        dn = slice(0, dn.stop, dn.step)
    if zn.start < 0:
        zn = slice(0, zn.stop, zn.step)
    if xn.start < 0:
        xn = slice(0, xn.stop, xn.step)
    if yn.start < 0:
        yn = slice(0, yn.stop, yn.step)


def woa_from_file(doy, depth, lat, lon, filename, varnames=None):
    """
    Monthly Climatologic Mean and Standard Deviation from WOA,
    used either for temperature or salinity.

    INPUTS
        doy: [day of year]
        lat: [-90<lat<90]
        lon: [-180<lon<180]
        depth: [meters]

    Reads the WOA Monthly Climatology NetCDF file and
    returns the corresponding WOA values of salinity or temperature mean and
    standard deviation for the given time, lat, lon, depth.
    """

    doy = np.asanyarray(doy)
    depth = np.asanyarray(depth)
    lat = np.asanyarray(lat)
    lon = np.asanyarray(lon)

    assert np.all(depth >= 0)

    if lon < 0:
        lon = lon + 360

    nc = netCDF4.Dataset(expanduser(filename), 'r')

    if varnames is None:
        varnames = []
        for v in nc.variables.keys():
            if nc.variables[v].dimensions == (u'time', u'depth', u'lat', u'lon'):
                varnames.append(v)

    woa = build_input(doy, depth, lat, lon, filename, varnames)

    points_out = []
    for tn in doy:
        for zn in depth:
            for yn in lat:
                for xn in lon:
                    points_out.append([tn, zn, yn, xn])

    output = []
    for v in varnames:
        values = []
        points = []
        ind = np.nonzero(~ma.getmaskarray(woa[v]))
        points = np.array([
            woa['time'][ind[0]],
            woa['depth'][ind[0]],
            woa['lat'][ind[0]],
            woa['lon'][ind[0]]
            ]).T
        values = woa[v][ind]

        for nt, tn in enumerate(woa['time']):
            for nz, zn in enumerate(woa['depth']):
                for ny, yn in enumerate(woa['lat']):
                    for nx, xn in enumerate(woa['lon']):
                        points.append([tn, zn, yn, xn])
                        values.append(woa[v][nt, nz, ny, nx])
        points = np.array(points)
        values = np.array(points)
        output[v] = griddata(points, values, points_out)

    return output


class WOA_URL(object):
    def __init__(self):
        pass


class WOA_var_nc(object):
    def __init__(self, source):
        import netCDF4

        self.ncs = []
        for s in source:
            self.ncs.append(netCDF4.Dataset(s, 'r'))

        self.load_dims()
        self.set_keys()

    def keys(self):
        return self.KEYS

    def load_dims(self):
        self.dims = {}
        for d in ['lat', 'lon', 'depth']:
            self.dims[d] = self.ncs[0].variables[d][:]
            for nc in self.ncs[1:]:
                assert (self.dims[d] == nc.variables[d][:]).all()

        self.dims['time'] = []
        mfrac = 365/12.
        for nc in self.ncs:
            assert nc.variables['time'].size == 1
            self.dims['time'].append(mfrac * nc.variables['time'][0])
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

    def closest(self, doy, depth, lat, lon, var):
        tn = (np.abs(doy - self.dims['time'][:])).argmin()
        zn = [(np.abs(z - self.dims['depth'][:])).argmin() for z in depth]
        yn = (np.abs(lat - self.dims['lat'][:])).argmin()
        # FIXME
        xn = (np.abs(lon - self.dims['lon'][:])).argmin()

        subset = {}
        for v in var:
            if v in self.KEYS:
                subset[v] = self.ncs[tn][v][0,zn,yn,xn]
            else:
                # FIXME: Ugly temporary solution
                tmp = [vv for vv in self.KEYS if vv[2:] == v]
                assert len(tmp) == 1
                subset[v] = self.ncs[tn][tmp[0]][0,zn,yn,xn]

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
                np.nonzero(self.dims['depth'] >= depth.max())[0].min()+1)
        dims['depth'] = np.atleast_1d(self.dims['depth'][zn])

        yn = slice(
                np.nonzero(self.dims['lat'] <= lat.min())[0].max(),
                np.nonzero(self.dims['lat'] >= lat.max())[0].min() + 1)
        dims['lat'] = np.atleast_1d(self.dims['lat'][yn])

        lon_ext = np.array(
                (self.dims['lon'] - 360).tolist() + \
                        self.dims['lon'].tolist() + \
                        (self.dims['lon']+360).tolist())
        xn_ext = np.array(3 * range(self.dims['lon'].shape[0]))
        xn_start = np.nonzero(lon_ext <= lon.min())[0].max()
        xn_end = np.nonzero(lon_ext >= lon.max())[0].min()
        xn = xn_ext[xn_start:xn_end+1]
        dims['lon'] = np.atleast_1d(lon_ext[xn_start:xn_end+1])

        #tn_last = self.dims['time'].shape[0]
        #if doy.min() < self.dims['time'].min():
        #    dims['time'] = np.append(
        #            [self.dims['time'][-1] - 365.25], self.dims['time'])
        #    tn_start = [tn_last, 0]
        #else:
        #    dims['time'] = self.dims['time'][0]
        #    tn_start = [0]
        #if doy.max() > self.dims['time'].max():
        #    tn_end = [tn_last, 0]
        #else:
        #    tn_end = [tn_last]
        #tn = tn_start + range(tn_start[-1] + 1, tn_end[0]) + tn_end

        #if doy.min() < self.dims['time'][:].min():
        tn = (np.abs(doy - self.dims['time'][:])).argmin()
        dims['time'] = np.array([self.dims['time'][tn]])

        subset = {}
        for v in var:
            if v in self.KEYS:
                subset[v] = self.ncs[tn][v][0:1,zn,yn,xn]
            else:
                # FIXME: Ugly temporary solution
                tmp = [vv for vv in self.KEYS if vv[2:] == v]
                assert len(tmp) == 1
                subset[v] = self.ncs[tn][tmp[0]][0:1,zn,yn,xn]

        return subset, dims

    def extract(self, **kwargs):
        for k in kwargs:
            assert k in ['var', 'doy', 'depth', 'lat', 'lon'], \
                    "Wrong dimension to extract, check the manual"

        if 'var' in kwargs:
            var = kwargs['var']
            if type(var) == str:
                var = [var]
        else:
            var = self.KEYS

        doy = kwargs['doy']
        if np.size(doy) == 1:
            if type(doy) is datetime:
                doy = int(doy.strftime('%j'))
        else:
            import pdb; pdb.set_trace()

        if 'depth' in kwargs:
            depth = np.asanyarray(kwargs['depth'])
            if np.ndim(depth) == 0:
                depth = np.array([depth])
        else:
            depth = self.dims['depth'][:]

        lat = np.asanyarray(kwargs['lat'])
        lon = np.asanyarray(kwargs['lon'])


        #yn = slice(
        #        max(0,
        #            (np.abs(
        #                np.min(lat) - self.dims['lat'][:])).argmin() - 1),
        #        min(self.dims['lat'].size,
        #            (np.abs(
        #                np.max(lat) - self.dims['lat'][:])).argmin() + 1)
        #        )

        #FIXME
        #xn = slice(
        #        max(0,
        #            (np.abs(
        #                np.min(lon) - self.dims['lon'][:])).argmin() - 1),
        #        min(self.dims['lon'].size-1,
        #            (np.abs(
        #                np.max(lon) - self.dims['lon'][:])).argmin() + 1)
        #        )

            #zn = slice(None, None, None)
            #zn = slice(
            #    max(0,
            #        (np.abs(
            #            np.min(depth) - self.dims['depth'][:])).argmin() - 1),
            #    min(self.dims['depth'].size-1,
            #        (np.abs(
            #            np.max(depth) - self.dims['depth'][:])).argmin() + 1)
            #    )

        #if len(self.ncs) == 1:
        #    tn = [0]
        #else:

        #tn = [max(0,
        #    (np.abs(
        #        np.min(doy) - self.dims['time'][:])).argmin() - 1),
        #    min(self.dims['time'].size-1,
        #        (np.abs(
        #            np.max(doy) - self.dims['time'][:])).argmin() + 1)
        #    ]
        #if doy < min(self.dims['time']):
        #    tn = [-1] + tn
        #if doy > max(self.dims['time']):
        #    tn = tn + [0]

        subset = self.closest(doy, depth, lat, lon, var)

        return subset

        import pdb; pdb.set_trace()
        subset = []
        for n in tn:
            subset.append(self.ncs[n]['t_mn'][0,zn,yn,xn])

        subset = np.asanyarray(subset)
        output = self.ncs[0]['t_mn']

#x = [1, 2, 1, 2]
#y = [10, 20, 20, 10]
#ssh = [4, 8, 4, 8]

#xout = [1.5]
#yout = [12]

#griddata((x,y),ssh,(xout,yout))

class WOA_var_nc_old(object):
    """

        http://data.nodc.noaa.gov/thredds/dodsC/woa/WOA13/DATAv2/temperature/netcdf/decav/0.25/woa13_decav_t00_04v2.nc.html
        http://data.nodc.noaa.gov/thredds/dodsC/woa/WOA13/DATAv2/salinity/netcdf/decav/0.25/woa13_decav_s00_04v2.nc.html
        http://data.nodc.noaa.gov/thredds/dodsC/woa/WOA13/DATA/oxygen/netcdf/all/1.00/woa13_all_o00_01.nc.html
        http://data.nodc.noaa.gov/thredds/dodsC/woa/WOA13/DATA/nitrate/netcdf/all/1.00/woa13_all_n00_01.nc.html


        First case, returns one profile of one variable from a local netCDF file.
        woa_profile(v,
                        data.attributes['datetime'],
                        data.attributes['LATITUDE'],
                        data.attributes['LONGITUDE'],
                        data['PRES'],
                        cfg)
    """
    def __init__(self, source):
        self.source = source

        import netCDF4
        self.nc = netCDF4.Dataset(self.source, 'r')
        # self.KEYS = [u't_mn', u't_dd', u't_sd', u't_se', u'crs']
        self.data = {}
        for v in self.nc.variables.keys():
            if v[2:] in ['mn', 'dd', 'sd', 'se']:
                vout = v[2:]
            else:
                vout = v
            self.data[vout] = self.nc.variables[v]

    def keys(self):
        # return self.KEYS
        return self.data.keys()

    def __getitem__(self, item=None):

        return self.data[item]

    def get_profile(self, var=None, doy=None, depth=None, lat=None, lon=None):

        assert (lat is not None) and (lon is not None)

        if type(var) is str:
            var = (var,)
        elif var is None:
            var = [v for v in self.keys()
                    if self[v].dimensions ==
                    (u'time', u'depth', u'lat', u'lon')]

        for v in var:
            assert v in self.keys()

        if type(doy) is datetime:
            doy = int(doy.strftime('%j'))

        assert type(doy) is int

        dn = (np.abs(doy - self['time'][:])).argmin()
        xn = (np.abs(lon - self['lon'][:])).argmin()
        yn = (np.abs(lat - self['lat'][:])).argmin()

        if depth is None:
            zn = slice(None, None, None)

        elif np.size(depth) == 1:
            zn = (np.abs(depth - self['depth'][:])).argmin()
        else:
            zn = [(np.abs(z - self['depth'][:])).argmin() for z in depth]

        climdata = {}
        for v in var:
            climdata[v] = ma.masked_values(
                    self[v][dn, zn, yn, xn],
                    self[v]._FillValue)

        climdata['depth'] = self['depth'][zn]

        return climdata

    def get_track(self, var=None, doy=None, depth=None, lat=None, lon=None):
        """

            Temporary solution for CoTeDe
        """

        doy = np.asanyarray(doy)
        lat = np.asanyarray(lat)
        lon = np.asanyarray(lon)

        lon[lon < 0] += 360

        assert np.shape(lat) == np.shape(lon)

        # (np.size(depth) == 1), \
        assert (np.shape(doy) == np.shape(lat)), \
                "Sorry, I'm not ready for that yet."

        if type(var) is str:
            var = (var,)
        elif var is None:
            var = [v for v in self.keys()
                    if self[v].dimensions ==
                    (u'time', u'depth', u'lat', u'lon')]

        for v in var:
            assert v in self.keys()


        if type(doy[0]) is datetime:
            doy = np.array([int(dd.strftime('%j')) for dd in doy])

        #assert type(doy) is int

        climdata = {}
        for v in var:
            climdata[v] = []

        #dn = (np.abs(doy - self['time'][:])).argmin()
        #xn = (np.abs(lon - self['lon'][:])).argmin()
        #yn = (np.abs(lat - self['lat'][:])).argmin()
        for d_n, lat_n, lon_n in zip(doy, lat, lon):
            # Get the nearest point. In the future interpolate.
            n_d = (np.abs(d_n - self['time'][:])).argmin()
            n_x = (np.abs(lon_n - self['lon'][:])).argmin()
            n_y = (np.abs(lat_n - self['lat'][:])).argmin()

            n_z = 0

            for v in var:
                climdata[v].append(self[v][n_d, n_z, n_y, n_x])

        for v in var:
            climdata[v] = ma.fix_invalid(climdata[v])

        #for v in var:
        #    climdata[v] = ma.masked_values(
        #            self[v][dn, zn, yn, xn],
        #            self[v]._FillValue)

        return climdata


class WOA(object):
    """
    """
    def __init__(self):
        self.data = {}
        self.data['TEMP'] = WOA_var_nc(source=datafile('TEMP'))
        self.data['PSAL'] = WOA_var_nc(source=datafile('PSAL'))

    def keys(self):
        return self.data.keys()

    def __getitem__(self, item):
        return self.data[item]
