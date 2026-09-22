# Contributing

## One command reproduces everything

```bash
python -m pytest tests -q   # suite green, hermetic (synthetic micro-feed)
python evaluate.py          # committed cluster slice, no download needed
python evaluate.py [feed.zip]  # full-feed re-run (e.g. fresh MobilityDB pull)
```

The full feed snapshot (MobilityDB mdb-3139, 2026-09-22) is not committed;
`corpus.json` records its fingerprint. Any feed swap re-runs everything.

## Corpus policy (frozen v1)

Cluster DTC-159-bidirectional (routes 5064/5530) is **frozen**. Additions
bump the version and re-run everything.

## Headway rules

Gaps over 2h are service breaks: excluded from wait math, counted in the
table. The `E[w] = E[h]/2 + Var(h)/2E[h]` formula assumes random
arrivals during service hours — do not apply it across overnight halts.

## Open issues (stretch, in order)

1. **City-wide modeling** — beyond the frozen cluster.
2. Realtime scoring when keyed (evaluation-only seam already in `evaluate.py`).
3. BMTC sampled transfer check.
4. Map-matching (OSMnx) if stop coordinates prove unreliable.
