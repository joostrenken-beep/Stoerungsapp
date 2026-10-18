"""Koordinatenumrechnung ohne externe Bibliotheken.

Unterstützt:
- ETRS89 / UTM (EPSG:25832, 25833) – Standard in Niedersachsen (Zone 32)
- DHDN / Gauß-Krüger (Bessel-Ellipsoid, Streifen 2–5) inkl. Datumsübergang nach WGS84

Die Genauigkeit liegt für Kanalkataster-Zwecke im Zentimeter- (UTM) bzw.
Meterbereich (Gauß-Krüger, 7-Parameter-Helmert).
"""
from math import atan2, cos, radians, degrees, sin, sqrt, tan, hypot

GRS80 = (6378137.0, 1 / 298.257222101)
BESSEL = (6377397.155, 1 / 299.1528128)
WGS84 = (6378137.0, 1 / 298.257223563)

# DHDN -> WGS84, Position-Vector-Konvention (wie PROJ +towgs84)
DHDN_TOWGS84 = (598.1, 73.7, 418.2, 0.202, 0.045, -2.455, 6.7)


def _tm_forward(lat_deg, lon_deg, a, f, k0, lon0_deg, fe, fn=0.0):
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    lat = radians(lat_deg)
    lon = radians(lon_deg)
    lon0 = radians(lon0_deg)
    n = a / sqrt(1 - e2 * sin(lat) ** 2)
    t = tan(lat) ** 2
    c = ep2 * cos(lat) ** 2
    aa = (lon - lon0) * cos(lat)
    m = a * (
        (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * lat
        - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * sin(2 * lat)
        + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * sin(4 * lat)
        - (35 * e2 ** 3 / 3072) * sin(6 * lat)
    )
    x = fe + k0 * n * (
        aa + (1 - t + c) * aa ** 3 / 6 + (5 - 18 * t + t ** 2 + 72 * c - 58 * ep2) * aa ** 5 / 120
    )
    y = fn + k0 * (
        m
        + n * tan(lat) * (
            aa ** 2 / 2
            + (5 - t + 9 * c + 4 * c ** 2) * aa ** 4 / 24
            + (61 - 58 * t + t ** 2 + 600 * c - 330 * ep2) * aa ** 6 / 720
        )
    )
    return x, y


def _tm_inverse(x, y, a, f, k0, lon0_deg, fe, fn=0.0):
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    m = (y - fn) / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - sqrt(1 - e2)) / (1 + sqrt(1 - e2))
    phi1 = (
        mu
        + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * sin(2 * mu)
        + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * sin(4 * mu)
        + (151 * e1 ** 3 / 96) * sin(6 * mu)
        + (1097 * e1 ** 4 / 512) * sin(8 * mu)
    )
    n1 = a / sqrt(1 - e2 * sin(phi1) ** 2)
    t1 = tan(phi1) ** 2
    c1 = ep2 * cos(phi1) ** 2
    r1 = a * (1 - e2) / (1 - e2 * sin(phi1) ** 2) ** 1.5
    d = (x - fe) / (n1 * k0)
    lat = phi1 - (n1 * tan(phi1) / r1) * (
        d ** 2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720
    )
    lon = radians(lon0_deg) + (
        d
        - (1 + 2 * t1 + c1) * d ** 3 / 6
        + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120
    ) / cos(phi1)
    return degrees(lat), degrees(lon)


def _geodetic_to_xyz(lat_deg, lon_deg, h, a, f):
    e2 = f * (2 - f)
    lat, lon = radians(lat_deg), radians(lon_deg)
    n = a / sqrt(1 - e2 * sin(lat) ** 2)
    return ((n + h) * cos(lat) * cos(lon), (n + h) * cos(lat) * sin(lon), (n * (1 - e2) + h) * sin(lat))


def _xyz_to_geodetic(x, y, z, a, f):
    e2 = f * (2 - f)
    lon = atan2(y, x)
    p = hypot(x, y)
    lat = atan2(z, p * (1 - e2))
    for _ in range(10):
        n = a / sqrt(1 - e2 * sin(lat) ** 2)
        lat = atan2(z + e2 * n * sin(lat), p)
    return degrees(lat), degrees(lon)


def _helmert(x, y, z, params):
    tx, ty, tz, rx, ry, rz, s = params
    arc = radians(1 / 3600)
    rx, ry, rz = rx * arc, ry * arc, rz * arc
    m = 1 + s * 1e-6
    return (
        tx + m * (x - rz * y + ry * z),
        ty + m * (rz * x + y - rx * z),
        tz + m * (-ry * x + rx * y + z),
    )


def utm_nach_wgs84(ostwert, nordwert, zone=32):
    return _tm_inverse(ostwert, nordwert, *GRS80, 0.9996, zone * 6 - 183, 500000.0)


def wgs84_nach_utm(lat, lon, zone=32):
    return _tm_forward(lat, lon, *GRS80, 0.9996, zone * 6 - 183, 500000.0)


def gk_nach_wgs84(rechtswert, hochwert):
    streifen = int(rechtswert // 1_000_000)
    lat, lon = _tm_inverse(rechtswert, hochwert, *BESSEL, 1.0, streifen * 3, streifen * 1_000_000 + 500000.0)
    x, y, z = _geodetic_to_xyz(lat, lon, 0.0, *BESSEL)
    return _xyz_to_geodetic(*_helmert(x, y, z, DHDN_TOWGS84), *WGS84)


def nach_wgs84(rechtswert, hochwert, standard_zone=32):
    """Erkennt das Koordinatensystem am Wertebereich des Rechtswerts.

    - 8-stellig mit Zonenpräfix (z. B. 32490000): UTM, Zone aus dem Präfix
    - 6-stellig (100000–999999): UTM in `standard_zone`
    - 7-stellig (2000000–5999999): Gauß-Krüger, Streifen = erste Ziffer
    Gibt (lat, lon) oder None zurück.
    """
    if rechtswert is None or hochwert is None:
        return None
    rw, hw = float(rechtswert), float(hochwert)
    if 10_000_000 <= rw < 100_000_000:
        zone = int(rw // 1_000_000)
        return utm_nach_wgs84(rw - zone * 1_000_000, hw, zone)
    if 100_000 <= rw < 1_000_000:
        return utm_nach_wgs84(rw, hw, standard_zone)
    if 1_000_000 <= rw < 6_000_000:
        return gk_nach_wgs84(rw, hw)
    return None


def abstand_m(p1, p2):
    """Näherungsweiser Abstand zweier (lat, lon)-Punkte in Metern."""
    lat_m = 111_320.0
    lon_m = 111_320.0 * cos(radians((p1[0] + p2[0]) / 2))
    return hypot((p2[0] - p1[0]) * lat_m, (p2[1] - p1[1]) * lon_m)


def punkt_auf_linie(koordinaten, anteil):
    """Interpoliert einen Punkt bei `anteil` (0..1) der Gesamtlänge einer Polylinie."""
    if not koordinaten:
        return None
    if len(koordinaten) == 1:
        return tuple(koordinaten[0])
    anteil = min(max(anteil, 0.0), 1.0)
    laengen = [abstand_m(koordinaten[i], koordinaten[i + 1]) for i in range(len(koordinaten) - 1)]
    gesamt = sum(laengen)
    if gesamt == 0:
        return tuple(koordinaten[0])
    ziel = gesamt * anteil
    for i, seg in enumerate(laengen):
        if ziel <= seg or i == len(laengen) - 1:
            t = 0 if seg == 0 else min(ziel / seg, 1.0)
            a, b = koordinaten[i], koordinaten[i + 1]
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        ziel -= seg
    return tuple(koordinaten[-1])
