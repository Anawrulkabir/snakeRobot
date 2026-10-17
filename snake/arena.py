"""Post lattice geometry (config/arena.yaml). Pure numpy: returns post centres."""

import math

import numpy as np


def spacing(arena, density, body_length):
    """Centre-to-centre spacing d = L / (L/d); None for open ground."""
    ratio = arena["lattice"]["L_over_d"][density]
    return None if ratio == 0 else body_length / ratio


def post_centres(arena, density, body_length):
    """(N, 2) array of post centres for the density, in the region
    x in [0, length], |y| <= width/2. Hexagonal: rows d*sqrt(3)/2 apart in x,
    alternate rows shifted by d/2 in y. The first row's posts touch x = 0."""
    lat = arena["lattice"]
    d = spacing(arena, density, body_length)
    if d is None:
        return np.zeros((0, 2))
    if lat["pattern"] != "hexagonal":
        raise ValueError(f"pattern {lat['pattern']!r} not implemented")
    r = lat["post_diameter_m"] / 2
    if d <= lat["post_diameter_m"]:
        raise ValueError("spacing must exceed the post diameter")
    row_dx = d * math.sqrt(3) / 2
    pts = []
    x, row = r, 0
    while x <= lat["length_m"] - r + 1e-12:
        y0 = (d / 2) if row % 2 else 0.0
        ys = np.arange(y0 - math.floor((lat["width_m"] / 2 + y0) / d) * d, lat["width_m"] / 2 + 1e-12, d)
        pts += [(x, y) for y in ys if abs(y) <= lat["width_m"] / 2]
        x += row_dx
        row += 1
    return np.array(pts)
