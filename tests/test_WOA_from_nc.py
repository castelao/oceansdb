#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
"""

from datetime import datetime

from WOA.woa import WOA

def test_import():
    # A shortcut
    from WOA import WOA
    db = WOA()


def test_available_vars():
    db = WOA()
    
    for v in ['TEMP', 'PSAL']:
        assert v in db.keys()

      
def test_get_profile():
    db = WOA()

    db['TEMP'].get_profile(var='mn', doy=datetime.now(),
            depth=0, lat=10, lon=330)
    db['TEMP'].get_profile(var='mn', doy=datetime.now(),
            depth=[0,10], lat=10, lon=330)
    db['TEMP'].get_profile(doy=datetime.now(),
            depth=[0,10], lat=10, lon=330)


def test_get_track():
    db = WOA()
    db['TEMP'].get_track(doy=[datetime.now()], depth=0, lat=[10], lon=[330])
    db['TEMP'].get_track(doy=2*[datetime.now()], depth=0, lat=[10, 12], lon=[330, -35])
