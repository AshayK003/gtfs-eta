"""The one runnable check (SPEC): synthetic 2-route micro-feed parses to
hand-computed tables; integrity flags fire; cluster slice is exact."""

import io

import pandas as pd

from gtfs_parse import cluster_trips, hms_to_seconds, validate

STOPS = """stop_id,stop_name,stop_lat,stop_lon
s1,A,28.6,77.2
s2,B,28.61,77.21
s3,C,28.62,77.22
"""
ROUTES = """route_id,agency_id,route_long_name,route_type
r1,DTC,159UP,3
r2,DTC,159DOWN,3
"""
TRIPS = """route_id,service_id,trip_id,shape_id
r1,1,t1,
r1,1,t2,
r2,1,t3,
"""
STOP_TIMES = """trip_id,arrival_time,departure_time,stop_id,stop_sequence
t1,06:00:00,06:00:00,s1,0
t1,06:10:00,06:10:00,s2,1
t1,06:25:00,06:25:00,s3,2
t2,07:00:00,07:00:00,s1,0
t2,07:12:00,07:12:00,s2,1
t3,06:05:00,06:05:00,s9,0
"""


def micro_feed():
    read = lambda s: pd.read_csv(io.StringIO(s), dtype=str)
    return {
        "stops": read(STOPS),
        "routes": read(ROUTES),
        "trips": read(TRIPS),
        "stop_times": read(STOP_TIMES),
    }


def test_tables_and_times():
    feed = micro_feed()
    assert (len(feed["stops"]), len(feed["routes"]), len(feed["trips"])) == (3, 2, 3)
    assert hms_to_seconds("25:15:00") == 25 * 3600 + 15 * 60
    assert hms_to_seconds("06:01:13") == 6 * 3600 + 60 + 13


def test_integrity_flags_orphan_stop():
    rep = validate(micro_feed())
    assert rep["orphan_stop_ids"]["bad_count"] == 1  # s9
    assert rep["trips_without_stop_times"]["bad_count"] == 0


def test_cluster_slice_exact():
    tids, rows = cluster_trips(micro_feed(), ["r1"])
    assert sorted(tids) == ["t1", "t2"]
    assert len(rows) == 5
    seg = rows.loc[(rows["trip_id"] == "t1") & (rows["stop_sequence"] == 1), "arr_s"].iloc[0]
    assert seg == 6 * 3600 + 10 * 60
