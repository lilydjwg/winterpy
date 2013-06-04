# vim:fileencoding=utf-8

from __future__ import division

from math import radians, sin, cos, acos, sqrt

# units: metres
EARTH_RADIUS = 6372797
EARTH_E_RADIUS = 6378137
EARTH_FLATTENING = 0.0033528

def d_from_origin(phi, a, b):
    r'''distance from origin to a point on an ellipse

    The ellipse is $\frac{x^2}{a^2} + \frac{y^2}{b^2} = 1$,
    and ``phi`` is the latitude in radians (angle from x-axis).

    The calculation:

    \frac{x^2}{a^2} + \frac{y^2}{b^2} = 1 \\
    x = d \cos \phi \\
    y = d \sin \phi \\
    b^2x^2 + a^2y^2 = a^2b^2\\
    b^2d^2\cos^2\phi + a^2d^2\sin^2\phi = a^2b^2 \\
    d = \frac{ab}{ \sqrt{b^2 + (a^2-b^2)\sin^2\phi} }
    '''
    b2 = b * b
    sinphi = sin(phi)
    return a * b / sqrt(b2 + (a*a - b2) * sinphi * sinphi)

def geoloc2xyz(longtitude, latitude, altitude=0, e_radius=EARTH_E_RADIUS, flattening=EARTH_FLATTENING):
    a, b = radians(longtitude), radians(latitude)
    p_radius = e_radius * (1 - flattening)

    d = d_from_origin(b, p_radius, e_radius) + altitude
    # x = d \cos a \cos b
    # y = d \sin a \cos b
    # z = d \sin b
    x = d * cos(a) * cos(b)
    y = d * sin(a) * cos(b)
    z = d * sin(b)
    return x, y, z

def distance_on_unit_sphere(p1, p2):
    # http://janmatuschek.de/LatitudeLongitudeBoundingCoordinates
    # dist = arccos(sin(lat1) · sin(lat2) + cos(lat1) · cos(lat2) · cos(lng1 - lng2)) · R
    #
    # Real distance is too hard to calculate:
    # http://mathworld.wolfram.com/Geodesic.html
    # And only <100m difference on Earth:
    # http://www.johndcook.com/blog/2009/03/02/what-is-the-shape-of-the-earth/
    # But Wolram|Alpha and Google Maps show bigger differences
    # should be less than 1%.
    lng1, lat1 = p1
    lng2, lat2 = p2
    return acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lng1 - lng2))

def distance_on_earth(loc1, loc2):
    p1 = [radians(x) for x in loc1]
    p2 = [radians(x) for x in loc2]
    return distance_on_unit_sphere(p1, p2) * EARTH_RADIUS
