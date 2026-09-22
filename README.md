# Static-GTFS Bus ETA (Delhi)

**Author:** [Ashay Kushwaha](https://github.com/AshayK003) ([CypherLabs](https://github.com/AshayK003))

> **Status: feed inspection in progress — no numbers yet.** Nothing below
> is claimed until one command reproduces it. Article follows numbers,
> never precedes them.

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
