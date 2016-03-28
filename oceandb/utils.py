# -*- coding: utf-8 -*-

"""

"""

import os
import sys
import shutil
import hashlib
from tempfile import NamedTemporaryFile
import pkg_resources
import json

#from filelock import FileLock

if sys.version_info >= (3, 0):
    from urllib.request import urlopen
    from urllib.parse import urlparse
else:
    from urllib2 import urlopen
    from urlparse import urlparse

import filelock

def oceandb_dir():
        return os.path.expanduser(os.getenv('OCEANDB_DIR', '~/.config/oceandb'))

def download_file(url, md5hash, dbpath):
    """ Download data file from web

        Copied from CoTeDe.

        IMPROVE it to automatically extract gz files
    """
    download_block_size = 2 ** 16

    assert type(md5hash) is str

    if not os.path.exists(dbpath):
        os.makedirs(dbpath)

    hash = hashlib.md5()

    fname = os.path.join(dbpath, os.path.basename(urlparse(url).path))
    if os.path.isfile(fname):
        return
        # FIXME: This is not efficient. As it is, a checksum is estimated
        #   for every access. That's way too much.
        #h = hashlib.md5(open(fname, 'rb').read()).hexdigest()
        #if h == md5hash:
        #    #print("Was previously downloaded: %s" % fname)
        #    return
        #else:
        #    assert False, "%s already exist but doesn't match the hash: %s" % \
        #            (fname, md5hash)

    #try:
    #    with lock.acquire(timeout = 10):
    #        pass
    #except filelock.Timeout:
    #    pass

    flock = "%s.lock" % fname
    lock = filelock.FileLock(flock)
    with lock.acquire(timeout = 1000):
        if os.path.isfile(fname):
            return
        print("Will download %s" % url)
        remote = urlopen(url)

        with NamedTemporaryFile(delete=False) as f:
            try:
                bytes_read = 0
                block = remote.read(download_block_size)
                while block:
                    f.write(block)
                    hash.update(block)
                    bytes_read += len(block)
                    block = remote.read(download_block_size)
            except:
                if os.path.exists(f.name):
                    os.remove(f.name)
                    raise

        h = hash.hexdigest()
        #if h != md5hash:
        if False:
            os.remove(f.name)
            print("Downloaded file doesn't match. %s" % h)
            assert False, "Downloaded file (%s) doesn't match with expected hash (%s)" % \
                    (fname, md5hash)

        shutil.move(f.name, fname)
        print("Downloaded: %s" % fname)


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

def dbsource(var, resolution='5', tscale='seasonal'):
    dbpath = oceandb_dir()
    datafiles = []
    src_dir = 'datasource'
    src_cfg = 'woa.json'
    text = pkg_resources.resource_string(
            'oceandb', os.path.join(src_dir, src_cfg))
    files_db = json.loads(text)
    for cfg in files_db[var][resolution][tscale]:
        #with FileLock(fname):
        #download_file(cfg['url'], cfg['md5'], dbpath)
        download_file(cfg, 'null', dbpath)

        datafiles.append(os.path.join(dbpath,
            os.path.basename(urlparse(cfg).path)))
            #os.path.basename(urlparse(cfg['url']).path)))

    return datafiles
