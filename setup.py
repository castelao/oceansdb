#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('VERSION') as version_file:
    version = version_file.read().rstrip('\n')

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'numpy',
    'netCDF4',
    'scipy',
]

with open('test-requirements.txt') as test_requirements_file:
    test_requirements = test_requirements_file.read()


# == Temporary solution
def download_data():
    """ Temporary solution to download WOA database.

        Copied from CoTeDe. Update it after CoTeDe is completely migrated to use it here.
    """
    try:
        # Python 3
        import urllib.request as urllib
    except:
        import urllib2 as urllib
    import os
    woa_dir = os.path.expanduser(os.getenv('WOA_DIR', '~/.woarc'))
    urls = ['http://data.nodc.noaa.gov/thredds/fileServer/woa/WOA09/NetCDFdata/temperature_seasonal_5deg.nc',
    'http://data.nodc.noaa.gov/thredds/fileServer/woa/WOA09/NetCDFdata/salinity_seasonal_5deg.nc']

    if not os.path.exists(woa_dir):
        os.makedirs(woa_dir)

    for url in urls:
        print("Downloading: %s" % url)
        remote = urllib.urlopen(url)
        f = open(os.path.join(woa_dir, os.path.basename(url)), 'wb')
        f.write(remote.read())
        f.close()

download_data()


setup(
    name='pyWOA',
    version=version,
    description="Package to subsample World Ocean Atlas climatology.",
    long_description=readme + '\n\n' + history,
    author="Guilherme Castelao",
    author_email='guilherme@castelao.net',
    url='https://github.com/castelao/pyWOA',
    packages=[
        'WOA',
    ],
    package_dir={'WOA':
                 'WOA'},
    include_package_data=True,
    install_requires=requirements,
    license='3-clause BSD',
    zip_safe=False,
    keywords='WOA World Ocean Atlas climatology oceanographic data oceanography temperature salinity',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering',
    ]
)
