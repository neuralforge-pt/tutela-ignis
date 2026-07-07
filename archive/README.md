# Archive - schema and layout

Append-only. Files are written once and never edited. A day is added when its data has
settled; late-arriving data (EFFIS publication lag, FIRMS/ICNF settling) means a day may
appear a few days after the fact, but once written it is immutable.

## Layout

```
archive/
├── predictions/ours/
│   ├── predictions-YYYY-MM-DD.parquet   per-cell record (authoritative benchmark input)
│   ├── country-YYYY-MM-DD.json.gz       our served risk map that day (nowcast)
│   └── forecast24h-YYYY-MM-DD.json.gz   our forecast issued that day for the next day
├── official/
│   ├── ipma-rcm/YYYY-MM-DD/
│   │   ├── rcm-d0.json                  IPMA RCM, day 0
│   │   └── rcm-d1.json                  IPMA RCM, day 1
│   └── effis-fwi/
│       └── effis-YYYY-MM-DD.parquet     EFFIS/GEFF-ERA5 FWI grid for that day
└── truth/
    └── fires/
        └── fires-YYYY-MM-DD.parquet     observed ignitions (FIRMS + ICNF) for that day
```

Dates are UTC calendar days unless noted.

## Streams

### `predictions/ours/` - our model
`predictions-*.parquet` is the authoritative per-cell record (cell id, coordinates, fire
probability, discrete risk level) as archived from the production database daily since
2026-05-19; this is the file the benchmark scores against. `country-*.json.gz` and
`forecast24h-*.json.gz` are the exact files served to the public at
https://data.tutela.land, gzipped verbatim (~88,527 continental cells, model
`seasonal-ensemble:be23+lst1`), captured going forward from 2026-07-07 (R2 keeps no
history, so the served-file form cannot be backfilled before that date; the parquet record
covers the full prospective window).
Each cell carries a relative risk score and a discrete level. The score is a **relative
ranking**, not a literal per-cell-day burn probability; see the calibration discussion in
the paper. JSON is gzipped because the raw grid is ~2.6 MB/day.

### `official/ipma-rcm/` - IPMA
Risco Conjuntural e Meteorologico, the operational Portuguese fire-danger index, one value
per concelho per day at levels 1-5. IPMA overwrites these files daily with **no public
history**, so this snapshot is the only surviving record of each day's forecast. Raw JSON,
preserved verbatim as returned by `api.ipma.pt`.

### `official/effis-fwi/` - EFFIS / Copernicus
Fire Weather Index from the GEFF-ERA5 reanalysis (Copernicus EWDS
`cems-fire-historical-v1`), native ~0.25 degree grid over Portugal. Published with a
~5 day lag; not-yet-published days are silently absent upstream and are therefore absent
here (never zero-filled). Longitudes normalized to -180..180.

### `truth/fires/` - observed ignitions
The union of FIRMS satellite detections (`record_type=firms`) and ICNF occurrence records
(`record_type=icnf`) for the day. A day with no fires is still written as an empty,
self-describing parquet ("nothing burned" is itself benchmark data). FIRMS near-real-time
products age out at ~60 days, and ICNF records can be revised, so each day is snapshotted
once it has settled and then frozen.

## Known gaps

- Prospective window starts **2026-05-19**. Nothing before that.
- Prediction days permanently missing (upstream bake gaps, no rows ever existed):
  **2026-05-21, 2026-06-25, 2026-06-26, 2026-06-27, 2026-06-28**.
- EFFIS days trail the current date by ~5 days by construction.
