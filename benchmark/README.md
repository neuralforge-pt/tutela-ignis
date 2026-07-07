# Benchmark

Analysis code that reads `archive/` and reproduces the scorecards reported in the paper
and at https://tutela.land/ignis/validacao:

- coverage of observed ignitions, always paired with the flagged-area fraction
- matched-operating-point area ratios vs IPMA RCM and EFFIS FWI
- dangerous-miss accounting (fires in low-risk cells)
- per-bucket calibration
- skill scores that assign zero to an always-red forecast (TSS, ETS)

Dual cut: all ignitions, and the subset that reached >= 1 ha.

Code lands here once the reference implementation is extracted from the private pipeline.
Until then this directory is a placeholder describing the intended contents.
