# -*- coding: utf-8 -*-

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

        if self.dims['time'].shape == (1,):
            tn = 0
            dims['time'] = self.dims['time']
        else:
            time_ext = np.array(
                    [self.dims['time'][-1] - 365.25] +
                            self.dims['time'].tolist() +
                            [self.dims['time'][0] + 365.25])
            tn_ext = list(range(self.dims['time'].size))
            tn_ext = [tn_ext[-1]] + tn_ext + [tn_ext[0]]
            tn_start = np.nonzero(time_ext <= doy.min())[0].max()
            tn_end = np.nonzero(time_ext >= doy.max())[0].min()
            tn = tn_ext[tn_start:tn_end+1]
            dims['time'] = np.atleast_1d(time_ext[tn_start:tn_end+1])

        # messy way to accept t_mn or mn
        varin = []
        for v in var:
            if v in self.KEYS:
                varin.append(v)
            elif self.KEYS[0][:2] + v in self.KEYS:
                varin.append(self.KEYS[0][:2] + v)

        subset = {}
        for v, vin in zip(var, varin):
            subset[v] = ma.asanyarray(
                    [self.ncs[tnn][vin][0, zn, yn, xn] for tnn in tn])

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


class WOA(object):
    """
    """
    def __init__(self, dbname='WOA13'):
        self.data = {}
        self.data['TEMP'] = WOA_var_nc(source=dbsource(dbname, 'TEMP'))
        self.data['PSAL'] = WOA_var_nc(source=dbsource(dbname, 'PSAL'))

    def keys(self):
        return self.data.keys()

    def __getitem__(self, item):
        return self.data[item]
