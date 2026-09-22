"""GTFS static parser: tidy tables + referential-integrity report (pandas).

Only the five core files are read (stops, routes, trips, stop_times,
calendar). Shapes/fare extras are out of scope v1.
"""

import pandas as pd

CORE_FILES = ["stops.txt", "routes.txt", "trips.txt", "stop_times.txt", "calendar.txt"]


def hms_to_seconds(s):
    """GTFS times may exceed 24h (e.g. 25:15:00). Returns int seconds."""
    h, m, sec = s.split(":")
    return int(h) * 3600 + int(m) * 60 + int(sec)


def load_feed_from_zip(zip_path):
    """{table-name: DataFrame}, all columns as str (ids keep leading zeros)."""
    import zipfile

    feed = {}
    with zipfile.ZipFile(zip_path) as z:
        names = set(z.namelist())
        for fname in CORE_FILES:
            key = fname[:-4]
            if fname in names:
                with z.open(fname) as fh:
                    feed[key] = pd.read_csv(fh, dtype=str)
    return feed


def load_feed_from_dir(directory):
    import os

    feed = {}
    for fname in CORE_FILES:
        key = fname[:-4]
        path = os.path.join(directory, fname)
        if os.path.exists(path):
            feed[key] = pd.read_csv(path, dtype=str)
    return feed


def validate(feed):
    """Referential-integrity report. Returns {check: {bad_count, example}}."""
    out = {}
    st, trips, stops, routes = (
        feed.get("stop_times"),
        feed.get("trips"),
        feed.get("stops"),
        feed.get("routes"),
    )
    if st is not None and stops is not None:
        orphan = set(st["stop_id"].unique()) - set(stops["stop_id"].unique())
        out["orphan_stop_ids"] = {"bad_count": len(orphan), "example": sorted(orphan)[:3]}
    if st is not None and trips is not None:
        orphan = set(st["trip_id"].unique()) - set(trips["trip_id"].unique())
        out["orphan_trip_ids"] = {"bad_count": len(orphan), "example": sorted(orphan)[:3]}
        empty = set(trips["trip_id"].unique()) - set(st["trip_id"].unique())
        out["trips_without_stop_times"] = {"bad_count": len(empty), "example": sorted(empty)[:3]}
    if trips is not None and routes is not None:
        orphan = set(trips["route_id"].unique()) - set(routes["route_id"].unique())
        out["orphan_route_ids"] = {"bad_count": len(orphan), "example": sorted(orphan)[:3]}
    return out


def cluster_trips(feed, route_ids):
    """Trip ids for the frozen cluster + their stop-time rows, time-sorted."""
    wanted = set(map(str, route_ids))
    trips = feed["trips"]
    tids = trips.loc[trips["route_id"].isin(wanted), "trip_id"].unique().tolist()
    st = feed["stop_times"]
    rows = st[st["trip_id"].isin(set(tids))].copy()
    rows["arr_s"] = rows["arrival_time"].map(hms_to_seconds)
    rows["dep_s"] = rows["departure_time"].map(hms_to_seconds)
    rows["stop_sequence"] = rows["stop_sequence"].astype(int)
    return tids, rows.sort_values(["trip_id", "stop_sequence"]).reset_index(drop=True)
