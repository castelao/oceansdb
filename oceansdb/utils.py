# -*- coding: utf-8 -*-

"""

"""

import os
import sys
import pkg_resources
import json

from netCDF4 import Dataset

from supportdata import download_file

if sys.version_info >= (3, 0):
    from urllib.parse import urlparse
else:
    from urlparse import urlparse


def oceansdb_dir():
    return os.path.expanduser(os.getenv('OCEANSDB_DIR', '~/.config/oceansdb'))

"""

        http://data.nodc.noaa.gov/thredds/dodsC/woa/WOA13/DATAv2/temperature/netcdf/decav/0.25/woa13_decav_t00_04v2.nc.html
        http://data.nodc.noaa.gov/thredds/dodsC/woa/WOA13/DATAv2/salinity/netcdf/decav/0.25/woa13_decav_s00_04v2.nc.html
        http://data.nodc.noaa.gov/thredds/dodsC/woa/WOA13/DATA/oxygen/netcdf/all/1.00/woa13_all_o00_01.nc.html
        http://data.nodc.noaa.gov/thredds/dodsC/woa/WOA13/DATA/nitrate/netcdf/all/1.00/woa13_all_n00_01.nc.html


http://data.nodc.noaa.gov/thredds/fileServer/woa/WOA13/DATAv2/temperature/netcdf/decav/1.00/woa13_decav_t00_01v2.nc
http://data.nodc.noaa.gov/thredds/fileServer/woa/WOA13/DATAv2/temperature/netcdf/decav/1.00/woa13_decav_t13_01v2.nc
http://data.nodc.noaa.gov/thredds/fileServer/woa/WOA13/DATAv2/temperature/netcdf/decav/1.00/woa13_decav_t01_01v2.nc

http://data.nodc.noaa.gov/thredds/fileServer/woa/WOA13/DATAv2/temperature/netcdf/decav/0.25/woa13_decav_t00_04v2.nc
http://data.nodc.noaa.gov/thredds/fileServer/woa/WOA13/DATAv2/temperature/netcdf/decav/0.25/woa13_decav_t13_04v2.nc
http://data.nodc.noaa.gov/thredds/fileServer/woa/WOA13/DATAv2/temperature/netcdf/decav/0.25/woa13_decav_t01_04v2.nc

"""


class Dataset_flex(object):
    def __init__(self, filename, **kwargs):
        self.ds = Dataset(filename, mode='r')
        if 'aliases' in kwargs:
            self.aliases = kwargs['aliases']
        else:
            self.aliases = {}
    def __getitem__(self, item):
        try:
            return self.ds.variables[self.aliases[item]]
        except:
            return self.ds.variables[item]
    @property
    def variables(self):
        return self.ds.variables


def dbsource(dbname, var, resolution=None, tscale=None):
    """Return which file(s) to use according to dbname, var, etc
    """
    db_cfg = {}
    cfg_dir = 'datasource'
    cfg_files = pkg_resources.resource_listdir('oceansdb', cfg_dir)
    cfg_files = [f for f in cfg_files if f[-5:] == '.json']
    for src_cfg in cfg_files:
        text = pkg_resources.resource_string(
                'oceansdb', os.path.join(cfg_dir, src_cfg))
        text = text.decode('UTF-8', 'replace')
        cfg = json.loads(text)
        for c in cfg:
            assert c not in db_cfg, "Trying to overwrite %s"
            db_cfg[c] = cfg[c]

    dbpath = oceansdb_dir()
    datafiles = []
    cfg = db_cfg[dbname]

    if (resolution is None):
        resolution = cfg['vars'][var]['default_resolution']

    if (tscale is None):
        tscale = cfg['vars'][var][resolution]["default_tscale"]

    for c in cfg['vars'][var][resolution][tscale]:
        download_file(outputdir=dbpath, **c)

        if 'filename' in c:
            filename = os.path.join(dbpath, c['filename'])
        else:
            filename = os.path.join(dbpath,
                    os.path.basename(urlparse(c['url']).path))

        if 'varnames' in cfg['vars'][var][resolution]:
            datafiles.append(Dataset_flex(filename,
                aliases=cfg['vars'][var][resolution]['varnames']))
        else:
            datafiles.append(Dataset_flex(filename))

    return datafiles
