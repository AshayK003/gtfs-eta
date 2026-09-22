"""One-command v1 evaluation (revised scope, 2026-09-22).

Prints: (1) zero-variance proof on the frozen cluster, (2) headway +
expected-wait table, (3) lookup demo. Feed zip via argv[1] or
data/delhi.zip. Realtime scoring plugs in here later (evaluation seam).

Usage: python evaluate.py [feed.zip]
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gtfs_parse import cluster_trips, load_feed_from_dir, load_feed_from_zip, validate  # noqa: E402
from headways import route_headways  # noqa: E402
from lookup import eta  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def fmt(s):
    return f"{int(s // 3600):02d}:{int((s % 3600) // 60):02d}"


def main():
    corpus = json.load(open(os.path.join(HERE, "corpus.json")))
    route_ids = corpus["cluster"]["route_ids"]
    if len(sys.argv) > 1:
        feed = load_feed_from_zip(sys.argv[1])
    elif os.path.exists(os.path.join(HERE, "data", "delhi.zip")):
        feed = load_feed_from_zip(os.path.join(HERE, "data", "delhi.zip"))
    elif os.path.isdir(os.path.join(HERE, "data", "cluster")):
        print("(using committed cluster slice data/cluster/)")
        feed = load_feed_from_dir(os.path.join(HERE, "data", "cluster"))
    else:
        sys.exit("no feed: pass a GTFS zip, or provide data/delhi.zip (see CONTRIBUTING)")
    print("== integrity ==")
    for check, rep in validate(feed).items():
        print(f"  {check}: bad={rep['bad_count']} ex={rep['example']}")

    tids, rows = cluster_trips(feed, route_ids)
    rows = rows.merge(feed["trips"][["trip_id", "route_id"]], on="trip_id")
    print(f"== cluster {corpus['cluster']['id']}: {len(tids)} trips, {len(rows)} stop-times ==")

    # (1) zero-variance proof: per-segment travel-time std across trips
    rows = rows.sort_values(["trip_id", "stop_sequence"])
    rows["next_arr"] = rows.groupby("trip_id")["arr_s"].shift(-1)
    seg = rows.dropna(subset=["next_arr"]).copy()
    seg["dur"] = seg["next_arr"] - seg["arr_s"]
    by_seg = seg.groupby(["route_id", "stop_id"])["dur"].agg(["mean", "std", "count"])
    worst = by_seg["std"].fillna(0)
    print(f"segments: {len(by_seg)}, max std: {worst.max():.1f}s, "
          f"segments with std>1s: {(worst > 1.0).sum()}")

    # (2) headway table
    hw = route_headways(rows, feed["trips"])
    print("== headways (route x bucket: n, mean±std min, CV, E[wait] min) ==")
    for _, r in hw.iterrows():
        brk = f" breaks={int(r['breaks'])}" if r.get("breaks", 0) else ""
        print(f"  {r['route_id']} {r['bucket']:<13} n={r['n']:<4} "
              f"{r['mean_min']}±{r['std_min']} cv={r['cv']} wait={r['wait_min']}{brk}")

    # (3) lookup demo: first stop of 159UP at 08:00 + mid stop at 18:00
    r0 = rows[rows["route_id"] == route_ids[0]].sort_values("stop_sequence")
    first_stop = r0.iloc[0]["stop_id"]
    mid_stop = r0.iloc[len(r0) // 2]["stop_id"]
    for stop, at in [(first_stop, 8 * 3600), (mid_stop, 18 * 3600)]:
        ans = eta(rows, hw, route_ids[0], stop, at)
        nxt = [(fmt(d), t) for d, t in ans["next"]]
        print(f"  route {route_ids[0]} stop {stop} after {fmt(at)}: next={nxt} "
              f"E[wait]={ans['expected_wait_min']}min")


if __name__ == "__main__":
    main()
