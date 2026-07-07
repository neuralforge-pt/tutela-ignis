# Tutela Ignis - public benchmark archive

An append-only, publicly timestamped record of daily wildfire-risk predictions for
continental Portugal, published alongside the official baselines and the observed
fire outcomes, so that anyone can verify how well each product actually performed.

This repository is three things:

1. **`archive/`** - the daily ledger. Our forecast, the official products (IPMA RCM,
   EFFIS FWI), and the fire truth, one immutable file per day. This is the evidence
   base for the prospective benchmark.
2. **`benchmark/`** - the analysis code that reads `archive/` and produces the
   scorecards (coverage, flagged area, calibration, matched-operating-point ratios).
3. **`paper/`** - the preprint that reports the findings.

## Why this exists

Tutela Ignis (live at https://tutela.land) is a 1 km wildfire-risk model for Portugal.
It is positioned honestly as a **complement** to the operational products from IPMA and
EFFIS, not a replacement and not a state-of-the-art claim. Its measured skill is in the
published literature band.

A model that grades its own homework is not credible. So every prediction is committed
here **before** its outcome can be known, next to the same-day official forecasts and
the fire record that arrives days later. The commit history is the proof of ordering.
See [`docs/provenance.md`](docs/provenance.md).

## What is in the archive

| Path | Stream | Source | Cadence |
|---|---|---|---|
| `archive/predictions/ours/country-*.json.gz` | Our served risk map (nowcast) | tutela.land | daily |
| `archive/predictions/ours/forecast24h-*.json.gz` | Our next-day forecast | tutela.land | daily |
| `archive/official/ipma-rcm/{date}/rcm-d*.json` | IPMA Risco Conjuntural e Meteorologico | api.ipma.pt | daily |
| `archive/official/effis-fwi/effis-*.parquet` | EFFIS / GEFF-ERA5 Fire Weather Index | Copernicus EWDS | daily (~5 day lag) |
| `archive/truth/fires/fires-*.parquet` | Observed ignitions | FIRMS + ICNF | daily (settled) |

Schema and provenance details: [`archive/README.md`](archive/README.md).

## Coverage window

Prospective from **2026-05-19**. Five prediction days are permanently absent
(bake gaps: 2026-05-21 and 2026-06-25..28); the benchmark tolerates them explicitly.

## Licensing

- Archive data (`archive/`): **CC BY 4.0** (see `LICENSE-DATA`). Upstream sources retain
  their own terms; this repository redistributes for verification and research.
- Code (`benchmark/`, workflows, scripts): **MIT** (see `LICENSE-CODE`).

## Citing

See `CITATION.cff`.
