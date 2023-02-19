#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst


from setuptools import setup
from codecs import open

setup(
    author="Guilherme Castelao",
    author_email='guilherme@castelao.net',
    url='https://github.com/castelao/oceansdb',
    packages=['oceansdb'],
    package_dir={'oceansdb': 'oceansdb'},
    include_package_data=True,
    license='3-clause BSD',
    zip_safe=False,
)
