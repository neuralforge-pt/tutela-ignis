#!/usr/bin/env python3
"""Standalone EFFIS / GEFF-ERA5 FWI tail fetch -> Azure blob (for the fetch-effis workflow).

STATUS: STUB. This must be ported from the private pipeline before the fetch-effis
workflow is put on a schedule. The faithful source is scripts/fetch_effis_fwi.py in the
Tutela working tree; port it here WITHOUT the modules.ignis dependency (inline the PT bbox
and the era5 month-chunking) so it runs on a bare GitHub runner.

Port checklist (traps already learned, see the private PLAYBOOK):
  1. cdsapi.Client(url=EWDS_URL, key=...) pointed at https://ewds.climate.copernicus.eu/api,
     dataset "cems-fire-historical-v1", GEFF-ERA5 reanalysis, native 0.25 deg grid.
  2. Request grid: "0.25/0.25"  (NOT original_grid + area, that returns a 400).
  3. Response is a zip-in-nc; unzip, read the .nc, NOT a bare netcdf.
  4. valid_time vs time coordinate trap (handle both).
  5. Normalize longitudes to -180..180 (GEFF ships 0..360; PT would map to the Atlantic).
  6. Publication lag ~5 days; not-yet-published days are silently dropped from the response.
     Treat absent dates as absent, never zero-fill.
  7. Output one parquet per day: columns at least [lat, lon, fwi, date]; upload to
     {container}/{prefix}/effis-YYYY-MM-DD.parquet, skipping days already present.

Until ported, this exits non-zero so a scheduled run cannot silently publish nothing.
"""
import sys

if __name__ == "__main__":
    sys.stderr.write(
        "fetch_effis.py is a stub. Port from scripts/fetch_effis_fwi.py before enabling "
        "the fetch-effis schedule. See the port checklist in this file.\n"
    )
    sys.exit(2)
