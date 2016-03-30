# -*- coding: utf-8 -*-

import numpy as np
from numpy import ma
from scipy.interpolate import griddata

from oceansdb.utils import dbsource

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
    """
    def __init__(self, source):
        import netCDF4

        self.ncs = []
        for s in source:
            self.ncs.append(netCDF4.Dataset(s, 'r'))

        self.load_dims()

    def keys(self):
        return ['elevation']

    def __getitem__(self, item):
        # elevation
        return self.data[item]

    def load_dims(self):
        self.dims = {
                'lat': self.ncs[0].variables['ETOPO05_Y'][:],
                'lon': self.ncs[0].variables['ETOPO05_X'][:],
                }

    def subset(self, lat, lon, var):    
        dims = {}

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

        #varin = []
        #for v in var:
        #    if v in self.keys():
        #        varin.append(v)

        subset = {}
        #for v, vin in zip(var, varin):
        #    subset[v] = ma.asanyarray(
        #            [self.ncs[0][vin][yn, xn]])
        subset = {'elevation': self.ncs[0].variables['ROSE'][yn, xn]}

        return subset, dims

    def interpolate(self, lat, lon, var):
        """ Interpolate each var on the coordinates requested

        """

        subset, dims = self.subset(lat, lon, var)

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

        try:
            if mode == 'nearest':
                output = self.closest(lat, lon, var)
            else:
                output = self.interpolate(lat, lon, var)
                for v in output:
                    output[v] = np.atleast_1d(np.squeeze(output[v]))
        except:
            print("Sorry, I was not able to extract the climatology.")
            return

        return output


class ETOPO(ETOPO_var_nc):
    """
    """
    def __init__(self, dbname='ETOPO'):
        super(ETOPO, self).__init__(source=dbsource(dbname, 'DEPTH'))
        #self.data = {}
        #self.data['DEPTH'] = ETOPO_var_nc(source=dbsource(dbname, 'DEPTH'))
        #self.data = ETOPO_var_nc(source=dbsource(dbname, 'DEPTH'))
        #self.data['DEPTH'] = ETOPO_var_nc(source='/Users/castelao/.oceansdbrc/etopo/etopo5.nc')

#    def keys(self):
#        return self.data.keys()
#
#    def __getitem__(self, item):
#        return self.data[item]
