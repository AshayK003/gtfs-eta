"""Headway math + lookup on hand-computed cases (hermetic)."""

import pandas as pd

from headways import bucket, headway_stats
from lookup import next_departures


def test_expected_wait_math():
    # gaps 600,600,1200: E=800, Var=80000 -> E[w]=400+80000/1600=450s=7.5min
    st = headway_stats([0, 600, 1200, 2400])
    assert st["n"] == 4
    assert st["mean_min"] == round(800 / 60, 2)
    assert st["wait_min"] == 7.5


def test_buckets():
    assert bucket(8 * 3600) == "morning-peak"
    assert bucket(13 * 3600) == "midday"
    assert bucket(18 * 3600) == "evening-peak"
    assert bucket(23 * 3600) == "off"


def test_lookup_next():
    rows = pd.DataFrame(
        {
            "route_id": ["r1"] * 4,
            "trip_id": ["t1", "t1", "t2", "t2"],
            "stop_id": ["s1", "s2", "s1", "s2"],
            "dep_s": [6 * 3600, 6 * 3600 + 600, 7 * 3600, 7 * 3600 + 720],
            "stop_sequence": [0, 1, 0, 1],
        }
    )
    got = next_departures(rows, "r1", "s2", 6 * 3600 + 300)
    assert [d for d, _ in got] == [6 * 3600 + 600, 7 * 3600 + 720]
    assert next_departures(rows, "r1", "s9", 0) == []
