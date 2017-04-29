# -*- coding: utf-8 -*-


import numpy as np


def cropIndices(dims, lat, lon, depth=None, doy=None):
    """ Return the indices to crop dataset

        Assuming that the dataset have the dimensions given by
          dims, this function return the indices to conform with
          the given coordinates (lat, lon, ...)
    """
    dims_out = {}
    idx = {}
    
    yn = slice(
            np.nonzero(dims['lat'] <= lat.min())[0].max(),
            np.nonzero(dims['lat'] >= lat.max())[0].min() + 1)
    dims_out['lat'] = np.atleast_1d(dims['lat'][yn])
    idx['yn'] = yn

    lon_ext = np.array(
            (dims['lon'] - 2*360).tolist() +
            (dims['lon'] - 360).tolist() +
            dims['lon'].tolist() +
            (dims['lon'] + 360).tolist())
    xn_ext = list(4 * list(range(dims['lon'].shape[0])))
    xn_start = np.nonzero(lon_ext <= lon.min())[0].max()
    xn_end = np.nonzero(lon_ext >= lon.max())[0].min()
    xn = xn_ext[xn_start:xn_end+1]
    dims_out['lon'] = np.atleast_1d(lon_ext[xn_start:xn_end+1])
    idx['xn'] = xn

    if depth is not None:
        zn = slice(
                np.nonzero(dims['depth'] <= depth.min())[0].max(),
                np.nonzero(dims['depth'] >= min(dims['depth'].max(), depth.max())
                    )[0].min() + 1
                                                        )
        # If a higher degree interpolation system uses more than one data
        #   point in the edge, I should extend this selection one point on
        #   each side, without go beyond 0
        # if zn.start < 0:
        #    zn = slice(0, zn.stop, zn.step)
        dims_out['depth'] = np.atleast_1d(dims['depth'][zn])
        idx['zn'] = zn

    if doy is not None:
        # Source has only one time, like total mean field, or annual mean.
        if dims['time'].shape == (1,):
            dims_out['time'] = dims['time']
            idx['tn'] = [0]
        else:
            time_ext = np.array(
                    [dims['time'][-1] - 365.25] +
                            dims['time'].tolist() +
                            [dims['time'][0] + 365.25])
            tn_ext = list(range(dims['time'].size))
            tn_ext = [tn_ext[-1]] + tn_ext + [tn_ext[0]]
            tn_start = np.nonzero(time_ext <= doy.min())[0].max()
            tn_end = np.nonzero(time_ext >= doy.max())[0].min()
            dims_out['time'] = np.atleast_1d(time_ext[tn_start:tn_end+1])
            idx['tn'] = tn_ext[tn_start:tn_end+1]

    return dims_out, idx
