#!/usr/bin/env python3
"""Fetch the EFFIS / GEFF-ERA5 Fire Weather Index tail -> Azure blob (per day).

Standalone port of the private pipeline's scripts/fetch_effis_fwi.py, with the
modules.ignis dependency inlined (PT bbox + month iteration) so it runs on a bare
GitHub Actions runner. Writes ONE parquet per day:

    {container}/{prefix}/effis-YYYY-MM-DD.parquet   columns: date, latitude, longitude, fwi

Days already present in blob are skipped (idempotent). Source: Copernicus EWDS
(ewds.climate.copernicus.eu) dataset ``cems-fire-historical-v1`` (GEFF-ERA5
reanalysis, native ~0.25 deg). Publication lag ~5 days; not-yet-published days are
SILENTLY dropped from the response, so absent days are treated as absent, never zero.

Auth: EWDS key from env CDSAPI_KEY (falls back to ~/.cdsapirc). Blob write: an account
SAS token passed via --sas (needs write + list).

Traps handled (from the private PLAYBOOK): grid "0.25/0.25" not original_grid+area (400);
zip-in-nc downloads; valid_time vs time coord; 0..360 longitudes normalized to -180..180.
"""
from __future__ import annotations

import argparse
import logging
import sys
import tempfile
import zipfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("fetch_effis")

EWDS_URL_DEFAULT = "https://ewds.climate.copernicus.eu/api"
EFFIS_DATASET = "cems-fire-historical-v1"
PUBLICATION_LAG_DAYS = 5

# Portugal bounding box (EPSG:4326) — inlined from modules/ignis/config.py
PORTUGAL_BBOX = {"west": -9.5, "south": 36.96, "east": -6.19, "north": 42.15}


def months_in_range(start: date, end: date) -> list[tuple[int, int]]:
    """Distinct (year, month) pairs covering [start, end], in order."""
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def month_days(year: int, month: int, start: date, end: date) -> list[int]:
    """Days of (year, month) that fall inside [start, end]."""
    first = date(year, month, 1)
    nxt = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    last = nxt - timedelta(days=1)
    lo, hi = max(first, start), min(last, end)
    return list(range(lo.day, hi.day + 1)) if lo <= hi else []


def build_effis_request(year: int, month: int, days: list[int]) -> tuple[str, dict]:
    """EWDS request for one month of daily FWI over the Portugal bbox."""
    request = {
        "product_type": "reanalysis",
        "variable": ["fire_weather_index"],
        "dataset_type": "intermediate_dataset",
        "system_version": ["4_1"],
        "year": str(year),
        "month": f"{month:02d}",
        "day": [f"{d:02d}" for d in days],
        "grid": "0.25/0.25",  # original_grid + area is a 400 on EWDS; this is the native res
        "area": [
            PORTUGAL_BBOX["north"], PORTUGAL_BBOX["west"],
            PORTUGAL_BBOX["south"], PORTUGAL_BBOX["east"],
        ],
        "data_format": "netcdf",
    }
    return EFFIS_DATASET, request


def flatten_fwi(ds) -> pd.DataFrame:
    """Flatten an FWI xarray Dataset to date/latitude/longitude/fwi rows."""
    var = next((v for v in ("fwinx", "fwi") if v in ds.data_vars), None)
    if var is None:
        raise RuntimeError(f"no FWI variable in dataset: {list(ds.data_vars)}")
    tdim = "valid_time" if "valid_time" in ds.coords else "time"
    df = ds[var].to_dataframe().reset_index()
    df["date"] = pd.to_datetime(df[tdim]).dt.date
    df = df.rename(columns={var: "fwi"})[["date", "latitude", "longitude", "fwi"]]
    # GEFF delivers 0-360 longitudes (PT ~ 350-354) — normalize to -180..180
    df["longitude"] = df["longitude"].where(df["longitude"] <= 180, df["longitude"] - 360)
    return df.dropna(subset=["fwi"]).reset_index(drop=True)


def _ewds_client():
    """cdsapi client pointed at EWDS. Key from env CDSAPI_KEY, else ~/.cdsapirc."""
    import os

    import cdsapi

    url = os.environ.get("CDSAPI_URL", EWDS_URL_DEFAULT)
    key = os.environ.get("CDSAPI_KEY")
    if not key:
        rc = Path.home() / ".cdsapirc"
        if rc.exists():
            for line in rc.read_text().splitlines():
                if line.strip().startswith("key:"):
                    key = line.split(":", 1)[1].strip()
    if not key:
        raise RuntimeError("no EWDS key — set CDSAPI_KEY or provide ~/.cdsapirc")
    return cdsapi.Client(url=url, key=key)


def _read_netcdf(nc_path: Path):
    """Open a (possibly zip-wrapped) NetCDF download — zip-in-nc trap."""
    import xarray as xr

    if zipfile.is_zipfile(nc_path):
        members = []
        with zipfile.ZipFile(nc_path) as zf:
            for name in zf.namelist():
                if name.endswith(".nc"):
                    out = nc_path.parent / f"{nc_path.stem}_{Path(name).name}"
                    out.write_bytes(zf.read(name))
                    members.append(out)
        if not members:
            raise RuntimeError(f"EFFIS zip has no .nc member: {nc_path}")
        return xr.open_dataset(members[0]) if len(members) == 1 else xr.merge(
            [xr.open_dataset(m) for m in members]
        )
    return xr.open_dataset(nc_path)


def fetch_window_df(start: date, end: date, workdir: Path) -> pd.DataFrame:
    """Fetch [start, end] from EWDS and return flattened date/lat/lon/fwi rows."""
    client = _ewds_client()
    frames = []
    for year, month in months_in_range(start, end):
        days = month_days(year, month, start, end)
        if not days:
            continue
        dataset, request = build_effis_request(year, month, days)
        target = workdir / f"effis_{year}_{month:02d}.nc"
        logger.info("EFFIS %d-%02d: requesting %d day(s)", year, month, len(days))
        client.retrieve(dataset, request, str(target))
        df = flatten_fwi(_read_netcdf(target))
        logger.info("EFFIS %d-%02d: %d rows, FWI %.1f-%.1f",
                    year, month, len(df), df["fwi"].min(), df["fwi"].max())
        frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
        columns=["date", "latitude", "longitude", "fwi"]
    )


def _container_client(account: str, container: str, sas: str):
    from azure.storage.blob import ContainerClient

    return ContainerClient(
        f"https://{account}.blob.core.windows.net", container, credential=sas
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--window-days", type=int, default=10,
                    help="trailing days (ending today-5 lag) to attempt")
    ap.add_argument("--account", required=True)
    ap.add_argument("--container", required=True)
    ap.add_argument("--prefix", default="raw/effis")
    ap.add_argument("--sas", required=True, help="account SAS token (write + list)")
    ap.add_argument("--start", type=date.fromisoformat, default=None)
    ap.add_argument("--end", type=date.fromisoformat, default=None)
    args = ap.parse_args()

    today = datetime.now(UTC).date()
    end = args.end or (today - timedelta(days=PUBLICATION_LAG_DAYS))
    start = args.start or (end - timedelta(days=args.window_days - 1))
    logger.info("EFFIS window %s -> %s", start, end)

    cc = _container_client(args.account, args.container, args.sas)
    existing = {b.name for b in cc.list_blobs(name_starts_with=f"{args.prefix}/effis-")}

    with tempfile.TemporaryDirectory(prefix="effis-") as tmp:
        df = fetch_window_df(start, end, Path(tmp))
        if df.empty:
            logger.warning("EFFIS returned no rows for %s..%s (publication lag?)", start, end)
            return 0
        uploaded = skipped = 0
        for day, day_df in df.groupby("date"):
            blob = f"{args.prefix}/effis-{day.isoformat()}.parquet"
            if blob in existing:
                skipped += 1
                continue
            local = Path(tmp) / f"effis-{day.isoformat()}.parquet"
            day_df.reset_index(drop=True).to_parquet(local, index=False)
            with open(local, "rb") as fh:
                cc.upload_blob(name=blob, data=fh, overwrite=False)
            logger.info("uploaded %s (%d rows)", blob, len(day_df))
            uploaded += 1
    logger.info("EFFIS_FETCH_DONE uploaded=%d skipped=%d", uploaded, skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
