

from __future__ import absolute_import, print_function, unicode_literals

import datetime

import pytz
from astral import SUN_RISING, Astral

#KITCHEN WINDOW ->  2 gradi circa
#KITCHEN LIVING ->  6 gradi circa
#KITCHEN TV     -> 10 gradi circa

LAT = 41.850894
LON = 12.484656

TZ = pytz.timezone('Europe/Rome')

def sun_angle(dt = None):

    if not dt:
        dt = datetime.datetime.now()

    if not dt.tzinfo:
        dt = TZ.localize(dt)

    return Astral().solar_elevation(dt, latitude = LAT, longitude = LON)

def time_at_elevation(angle, date = None):
    return Astral().time_at_elevation_utc(
        angle, 
        direction = SUN_RISING, 
        date      = date or datetime.date.today(), 
        latitude  = LAT, 
        longitude = LON,
    ).astimezone(TZ)

for dt in [
    datetime.datetime(2018, 7, 19, 6, 00, 0),
    datetime.datetime.now()
    ]:

    print('-' * 20)
    print(dt)

    angle = sun_angle(dt)

    print(angle)

    t = time_at_elevation(angle, dt)

    print(t)

for angle in (2, 5, 8):
    print('-' * 20)
    print(angle)
    print(time_at_elevation(angle))
