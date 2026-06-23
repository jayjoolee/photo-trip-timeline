"""Geographic helpers. Pure functions, no dependencies beyond the stdlib."""

from __future__ import annotations

import math

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters between two lat/lon points."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return haversine_m(lat1, lon1, lat2, lon2) / 1000.0


def distance_from_home_km(lat: float, lon: float, home: tuple[float, float] | None) -> float:
    """Distance to the nearest home point, or 0.0 if home is unknown.

    ``home`` may be a single (lat, lon); callers that track multiple homes over
    time should pass the home active for the photo's date.
    """
    if home is None:
        return 0.0
    return haversine_km(lat, lon, home[0], home[1])


def dbscan(coords: list[tuple[float, float]], eps_m: float, min_samples: int) -> list[int]:
    """Minimal DBSCAN over (lat, lon) points using haversine distance.

    Returns a label per point; ``-1`` marks noise. Pure-python and O(n^2),
    which is fine for the few hundred photos in a single trip and keeps the
    algorithm core free of a scikit-learn dependency (so it runs in CI without
    native wheels). Behavior matches the standard DBSCAN definition.
    """
    n = len(coords)
    labels = [-1] * n
    if n == 0:
        return labels

    # Precompute neighbors within eps for each point.
    neighbors: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if haversine_m(coords[i][0], coords[i][1], coords[j][0], coords[j][1]) <= eps_m:
                neighbors[i].append(j)
                neighbors[j].append(i)

    cluster = -1
    visited = [False] * n
    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True
        # +1 to include the point itself (core-point definition).
        if len(neighbors[i]) + 1 < min_samples:
            continue  # leave as noise for now; may be claimed as a border point
        cluster += 1
        labels[i] = cluster
        seeds = list(neighbors[i])
        k = 0
        while k < len(seeds):
            q = seeds[k]
            k += 1
            if labels[q] == -1:
                labels[q] = cluster  # border point reachable from a core point
            if not visited[q]:
                visited[q] = True
                if len(neighbors[q]) + 1 >= min_samples:
                    for nb in neighbors[q]:
                        if nb not in seeds:
                            seeds.append(nb)
    return labels
