# Static-GTFS Bus ETA (Delhi)

**Author:** [Ashay Kushwaha](https://github.com/AshayK003) ([CypherLabs](https://github.com/AshayK003))

> **Status: measured on the frozen cluster, `python evaluate.py`
> regenerates every number.** Article follows numbers, never precedes them.

---

## Gap

Most Indian city buses have no live display, and real-time AVL feeds
barely exist. The default deployment is a static timetable or nothing —
and the static feed itself models no delay (constant intervening times,
arrival = departure everywhere). Heavy GNN/LSTM papers assume the dense
AVL data that is missing here; commercial dashboards assume fleet
hardware. **No small offline package predicts stop-level ETA from the
static timetable alone with an honest error table.** This repo is that
package.

## What it will do

Parse one Delhi route cluster from the static GTFS feed, build segment
travel-time tables by time-of-day, smooth with a Kalman filter, and
report MAE in minutes plus percent-within-±2-min against the schedule
baseline — then beat it rung by rung (schedule → segment means →
Kalman → LightGBM stretch). Realtime evaluation plugs in later through
an evaluation-only seam; the model never requires connectivity.

## Results (`python evaluate.py`, feed snapshot 2026-09-22)

Cluster DTC-159-bidirectional (routes 5064/5530, 316 trips, 9006
stop-times). Integrity: 0 orphan stops/trips/routes, 0 tripless trips.

**Zero-variance proof:** 55 segments, max travel-time std **0.0s**, 0
segments above 1s. The static feed carries no variance to learn — any
static-only ETA collapses to timetable lookup. (Feed-wide check: 3.27M
rows, 115,752 segments, 0 above 1s.)

**Headways + expected wait** (E[w] = E[h]/2 + Var(h)/2E[h]):

| Route | Bucket | Trips | Headway (min) | CV | E[wait] (min) |
|---|---|---|---|---|---|
| 5064 | morning-peak | 43 | 5.43±2.78 | 0.512 | 3.43 |
| 5064 | midday | 44 | 6.93±4.37 | 0.630 | 4.84 |
| 5064 | evening-peak | 38 | 6.27±3.82 | 0.609 | 4.30 |
| 5064 | off | 33 | 6.48±3.33 | 0.514 | 4.10 (+1 overnight break) |
| 5530 | morning-peak | 42 | 5.61±2.75 | 0.490 | 3.48 |
| 5530 | midday | 44 | 6.77±4.08 | 0.603 | 4.61 |
| 5530 | evening-peak | 41 | 5.80±3.22 | 0.555 | 3.79 |
| 5530 | off | 31 | 6.83±3.81 | 0.557 | 4.47 (+1 overnight break) |

Gaps over 2h count as service breaks (the overnight halt), excluded
from wait math and reported — a 313-minute ``expected wait'' at 3am
was caught and fixed during development.

**Lookup demo:** route 5064 stop 3075 after 08:00 → next 08:02, 08:06,
08:10, E[wait] 3.43min. Fully offline: timetable + headway table only.

## References

- Delhi Open Transit static GTFS: https://otd.delhi.gov.in/data/static/
- BMTC GTFS mirror (transfer check): https://github.com/Vonter/bmtc-gtfs
- Wessel & Farber 2019 (schedule overstates reality 5–15%): https://doi.org/10.5198/jtlu.2019.1502
- Newmark 2024 (GTFS accuracy assessment): https://doi.org/10.31979/mti.2024.2017

## Limitations (honest, updated as numbers land)

- Static-only ceiling is real: without observed arrivals the model learns
  schedule structure, and MAE is reported against holdouts plus (later)
  realtime samples — never oversold.
- One cluster first; city-wide claims wait.
