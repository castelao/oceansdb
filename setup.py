#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst


from setuptools import setup
from codecs import open

with open('README.rst', encoding='utf-8') as f:
    readme = f.read()

with open('HISTORY.rst', encoding='utf-8') as f:
    history = f.read().replace('.. :changelog:', '')

with open('requirements.txt', encoding='utf-8') as f:
    requirements = f.read()

setup(
    name='oceansdb',
    version='0.8.4',
    description="Package to subsample ocean climatologies and reference data.",
    long_description=readme + '\n\n' + history,
    author="Guilherme Castelao",
    author_email='guilherme@castelao.net',
    url='https://github.com/castelao/oceansdb',
    packages=['oceansdb'],
    package_dir={'oceansdb': 'oceansdb'},
    include_package_data=True,
    install_requires=requirements,
    license='3-clause BSD',
    zip_safe=False,
    keywords='WOA World Ocean Atlas climatology oceanographic data' +
             ' oceanography ETOPO temperature salinity bathymetry',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering',
    ]
)
