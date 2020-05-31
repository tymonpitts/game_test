import math
import mock

import pytest

from planet_test import utils


@pytest.mark.parametrize('lon_deg,lat_deg,expected_cartesian', [
    # axes
    (90, 0, [1, 0, 0]),
    (0, 90, [0, 1, 0]),
    (0, 0, [0, 0, 1]),

    (0, 45, [mock.ANY, math.sin(math.radians(45)), mock.ANY]),
    (90, 45, [mock.ANY, math.sin(math.radians(45)), mock.ANY]),
    (180, 45, [mock.ANY, math.sin(math.radians(45)), mock.ANY]),
    (270, 45, [mock.ANY, math.sin(math.radians(45)), mock.ANY]),
])
def test_lonlat_to_cartesian(lon_deg, lat_deg, expected_cartesian):
    lon = math.radians(lon_deg)
    lat = math.radians(lat_deg)
    result = utils.lonlat_to_cartesian(lon, lat)
    expected_cartesian = [pytest.approx(v) if v is not mock.ANY else mock.ANY for v in expected_cartesian]
    assert list(result) == expected_cartesian
