"""Offline next-departure lookup + expected wait (the shippable package).

No connectivity, no model weights: given the frozen timetable and the
precomputed headway table, answer "when are the next buses, and how long
will I probably wait."
"""


def next_departures(cluster_rows, route_id, stop_id, after_s, k=3):
    """Next k scheduled departures as [(dep_s, trip_id)]. Pure timetable."""
    sub = cluster_rows[
        (cluster_rows["route_id"] == str(route_id))
        & (cluster_rows["stop_id"] == str(stop_id))
        & (cluster_rows["dep_s"] >= after_s)
    ].sort_values("dep_s")
    return list(zip(sub["dep_s"].tolist()[:k], sub["trip_id"].tolist()[:k]))


def expected_wait(headway_table, route_id, at_s):
    """Expected wait (minutes) from the headway table. Needs headways.bucket."""
    from headways import bucket

    buck = bucket(at_s)
    hit = headway_table[
        (headway_table["route_id"] == str(route_id)) & (headway_table["bucket"] == buck)
    ]
    if len(hit) == 0:
        return None
    return float(hit.iloc[0]["wait_min"])


def eta(route_rows, headway_table, route_id, stop_id, after_s, k=3):
    """Combined answer: next departures + expected wait. All offline."""
    return {
        "next": next_departures(route_rows, route_id, stop_id, after_s, k),
        "expected_wait_min": expected_wait(headway_table, route_id, after_s),
    }
