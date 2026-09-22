"""Headway + expected-wait analysis from scheduled trip starts.

For random passenger arrivals, expected wait follows E[w] = E[h]/2 +
Var(h)/(2E[h]) with h the headway (gap between consecutive departures).
All inputs are scheduled times: this measures timetable structure
(irregular scheduled headways already hurt riders), not observed delay.
"""

import numpy as np
import pandas as pd


def bucket(seconds):
    """Daypart bucket for a start-of-day second."""
    h = seconds // 3600
    if 7 <= h < 11:
        return "morning-peak"
    if 11 <= h < 16:
        return "midday"
    if 16 <= h < 20:
        return "evening-peak"
    return "off"


def trip_starts(cluster_rows):
    """First departure per trip: DataFrame[trip_id, start_s]."""
    firsts = (
        cluster_rows.sort_values(["trip_id", "stop_sequence"])
        .groupby("trip_id", as_index=False)
        .first()
    )
    return firsts[["trip_id", "dep_s"]].rename(columns={"dep_s": "start_s"})


def headway_stats(starts_s):
    """Dict with n, span, mean/std/CV headway (minutes) + expected wait."""
    s = np.sort(np.asarray(sorted(starts_s), dtype=float))
    if len(s) < 2:
        return {"n": len(s), "mean_min": 0.0, "std_min": 0.0, "cv": 0.0, "wait_min": 0.0}
    gaps = np.diff(s)
    # Gaps over 2h are service breaks (e.g. overnight halt), not headways:
    # excluded from the wait computation, counted separately. A random
    # arrival at 3am expects no bus; the formula must not pretend otherwise.
    breaks = int((gaps > 7200).sum())
    live = gaps[gaps <= 7200]
    if len(live) == 0:
        return {"n": len(s), "mean_min": 0.0, "std_min": 0.0, "cv": 0.0,
                "wait_min": 0.0, "breaks": breaks}
    mean, var = float(live.mean()), float(live.var())
    return {
        "n": len(s),
        "mean_min": round(mean / 60, 2),
        "std_min": round(float(live.std()) / 60, 2),
        "cv": round((var ** 0.5) / mean, 3) if mean else 0.0,
        "wait_min": round((mean / 2 + var / (2 * mean)) / 60, 2) if mean else 0.0,
        "breaks": breaks,
    }


def route_headways(cluster_rows, trips):
    """Per (route_id, bucket) headway stats. trips maps trip_id -> route_id."""
    starts = trip_starts(cluster_rows)
    route_of = dict(zip(trips["trip_id"].astype(str), trips["route_id"].astype(str)))
    starts["route_id"] = starts["trip_id"].astype(str).map(route_of)
    starts["bucket"] = starts["start_s"].map(bucket)
    rows = []
    for (route, buck), g in starts.groupby(["route_id", "bucket"]):
        st = headway_stats(g["start_s"].tolist())
        st.update({"route_id": route, "bucket": buck})
        rows.append(st)
    return pd.DataFrame(rows).sort_values(["route_id", "bucket"]).reset_index(drop=True)
