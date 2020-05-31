import math
from game_core import Point


def lonlat_to_cartesian(lon, lat):
    """ Convert longitude and latitude values to cartesian coordinates.

    The radius of the sphere is 1.0 but the results can be multiplied by
    a different radius

    NOTE: even though the values of lon and lat are in radians,
          this documentation uses degrees for human readability

    lat=90 is the north pole
    lat=0 is the equator
    lat=-90 is the south pole

    x-axis=(270, 0)
    y-axis=(0, 90)
    z-axis=(0, 0)

    Args:
        lon (float): longitude in radians going from 0 to 360 degrees
        lat (float): latitude in radians going from -90 to 90 degrees

    Returns:
        Point:
    """
    # TODO: probably just use astropy.UnitSphericalRepresentation to do this
    cos_lat = math.cos(lat)
    x = math.sin(lon) * cos_lat
    y = math.sin(lat)
    z = math.cos(lon) * cos_lat
    return Point(x, y, z)
