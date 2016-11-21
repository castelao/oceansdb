# -*- coding: utf-8 -*-

"""

"""

import os
import sys
import pkg_resources
import json

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


def dbsource(dbname, var, resolution=None, tscale=None):
    """

        Temporary solution, just to move on with CoTeDe.
    """

    db_cfg = {}
    cfg_dir = 'datasource'
    for src_cfg in pkg_resources.resource_listdir('oceansdb', cfg_dir):
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

    for cfg in cfg['vars'][var][resolution][tscale]:
        # download_file(cfg['url'], cfg['md5'], dbpath)
        download_file(outputdir=dbpath, url=cfg['url'])

        if 'filename' in cfg:
            datafiles.append(os.path.join(dbpath, cfg['filename']))
        else:
            datafiles.append(os.path.join(dbpath,
                os.path.basename(urlparse(cfg['url']).path)))

    return datafiles
