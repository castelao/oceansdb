# -*- coding: utf-8 -*-

""" Module to handle ETOPO bathymetry
"""

import numpy as np
from numpy import ma
import netCDF4

from .utils import dbsource
from .common import cropIndices

from scipy.interpolate import griddata


def get_depth(lat, lon, cfg):
    """

    ATTENTION, conceptual error on the data near by Greenwich.
    url='http://opendap.ccst.inpe.br/Climatologies/ETOPO/etopo5.cdf'

    If I ever need to get depth from multiple points, check the history
      of this file. One day it was like that.
    """
    # This assert fails if it is a np.float64. Re-think this assert anyways.
    #assert type(lat) in [int, float]
    #assert type(lon) in [int, float]

    # if lat.shape != lon.shape:
    #            print "lat and lon must have the same size"

    try:
        try:
            etopo = netCDF4.Dataset(expanduser(cfg['file']))
        except:
            # FIXME, It must have a time limit defined here, otherwise it can
            #   get stuck trying to open the file.
            etopo = netCDF4.Dataset(expanduser(cfg['url']))
        x = etopo.variables['ETOPO05_X'][:]
        y = etopo.variables['ETOPO05_Y'][:]
    except:
        etopo = open_url(cfg['url']).ROSE
        x = etopo.ETOPO05_X[:]
        y = etopo.ETOPO05_Y[:]

    if lon < 0:
        lon += 360

    iini = (abs(lon - x)).argmin() - 2
    ifin = (abs(lon - x)).argmin() + 2
    jini = (abs(lat - y)).argmin() - 2
    jfin = (abs(lat - y)).argmin() + 2

    assert (iini >= 0) or (iini <= len(x)) or \
        (jini >= 0) or (jini <= len(y)), \
        "Sorry not ready to handle too close to boundaries"

    try:
        z = etopo.variables['ROSE'][jini:jfin, iini:ifin]
    except:
        z = etopo.ROSE[jini:jfin, iini:ifin]

    interpolator = RectBivariateSpline(x[iini:ifin], y[jini:jfin], z.T)
    return interpolator(lon, lat)[0][0]


class ETOPO_var_nc(object):
    """
    ETOPO global topography
    """
    def __init__(self, source):
        self.ncs = source

        self.load_dims(dims=['lat', 'lon'])
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

    def set_keys(self):
        self.KEYS = ['height']

    def crop(self, lat, lon, var):
        """ Crop a subset of the dataset for each var

            Given doy, depth, lat and lon, it returns the smallest subset
              that still contains the requested coordinates inside it.

            It handels special cases like a region around greenwich and
            the international date line.

            Accepts 0 to 360 and -180 to 180 longitude reference.

            It extends time and longitude coordinates, so simplify the use
               of series. For example, a ship track can be requested with
               a longitude sequence like [352, 358, 364, 369, 380].
        """
        dims, idx = cropIndices(self.dims, lat, lon)
        subset = {}
        for v in var:
            subset = {v: self.ncs[0][v][idx['yn'], idx['xn']]}
        return subset, dims

    def nearest(self, lat, lon, var):
        output = {}
        dims, idx = cropIndices(self.dims, lat, lon)
        for v in var:
            if v == 'height':
                v = 'z'
            subset = self.ncs[0].variables[v][idx['yn'], idx['xn']]
            output[v] = ma.masked_all((lat.size, lon.size), dtype='f')
            for yn_out, y in enumerate(lat):
                yn_in = np.absolute(dims['lat']-y).argmin()
                for xn_out, x in enumerate(lon):
                    xn_in = np.absolute(dims['lon']-x).argmin()
                    output[v][yn_out, xn_out] = subset[yn_in, xn_in]
        return output

    def interpolate(self, lat, lon, var):
        """ Interpolate each var on the coordinates requested

        """

        subset, dims = self.crop(lat, lon, var)

        if np.all([y in dims['lat'] for y in lat]) & \
                np.all([x in dims['lon'] for x in lon]):
                    yn = np.nonzero([y in lat for y in dims['lat']])[0]
                    xn = np.nonzero([x in lon for x in dims['lon']])[0]
                    output = {}
                    for v in subset:
                        # output[v] = subset[v][dn, zn, yn, xn]
                        # Seriously that this is the way to do it?!!??
                        output[v] = subset[v][:, xn][yn]
                    return output

        # The output coordinates shall be created only once.
        points_out = []
        for latn in lat:
            for lonn in lon:
                points_out.append([latn, lonn])
        points_out = np.array(points_out)

        output = {}
        for v in var:
            output[v] = ma.masked_all(
                    (lat.size, lon.size),
                    dtype=subset[v].dtype)

            # The valid data
            idx = np.nonzero(~ma.getmaskarray(subset[v]))

            if idx[0].size > 0:
                points = np.array([
                    dims['lat'][idx[0]], dims['lon'][idx[1]]]).T
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
                for [y, x], out in zip(points_out[idx], values_out[idx]):
                    output[v][y==lat, x==lon] = out

        return output

    def extract(self, mode=None, **kwargs):
        """

            Possible scenarios:
              - Point:   lat{1},lon{1}
              - Section: [lat{1},lon{n} | lat{n},lon{1}]

              - Track:   lat{n},lon{n}
        """
        for k in kwargs:
            assert k in ['var', 'lat', 'lon'], \
                    "Wrong dimension to extract, check the manual"

        if 'var' in kwargs:
            var = np.atleast_1d(kwargs['var'])
        else:
            var = np.asanyarray(self.keys())

        lat = np.atleast_1d(kwargs['lat'])
        lon = np.atleast_1d(kwargs['lon'])

        if mode == 'nearest':
            output = self.nearest(lat, lon, var)
        else:
            output = self.interpolate(lat, lon, var)
            for v in output:
                output[v] = np.atleast_1d(np.squeeze(output[v]))

        return output


class ETOPO(ETOPO_var_nc):
    """
    """
    def __init__(self, dbname='ETOPO'):
        self.dbname = dbname
        self.data = {'topography': None}

    def keys(self):
        return self.data.keys()

    def __getitem__(self, item):
        if item == 'elevation':
            print("elevation is deprecated. Use topography instead")
            import time
            time.sleep(3)
            return self['topography']

        if self.data[item] is None:
            self.data[item] = ETOPO_var_nc(source=dbsource(self.dbname, item))
        return self.data[item]

    def extract(self, *args, **kwargs):
        print("Deprecated syntax, better use: db['topography'].extract(...)")
        import time
        time.sleep(3)
        return self['topography'].extract(*args, **kwargs)['height']
