"""Post-hoc assignment of GPS-less photos to trips by timestamp.

Many phone photos lack GPS (screenshots are already filtered out, but some
camera shots, edits, or imported images have no location). Dropping them would
under-count the photos a blog post should mention. Instead, once trips are
built, any GPS-less photo whose timestamp falls inside a trip's date span is
counted toward that trip. Photos that match no trip are genuinely excluded.
"""

from __future__ import annotations

from .model import PhotoPoint, Trip


def assign_no_gps(trips: list[Trip], no_gps: list[PhotoPoint]) -> int:
    """Attach GPS-less photos to trips by time. Returns the number assigned."""
    if not trips or not no_gps:
        return 0

    spans = sorted(trips, key=lambda t: t.date_start)
    assigned = 0
    for photo in no_gps:
        for trip in spans:
            if trip.date_start <= photo.dt <= trip.date_end:
                trip.no_gps_points.append(photo)
                assigned += 1
                break
    return assigned
