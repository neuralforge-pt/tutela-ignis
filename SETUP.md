# Setup / operations

What a human has to do once. The workflows themselves are self-driving after this.

## 1. GitHub repository settings

- **Secrets** (Settings -> Secrets and variables -> Actions):
  - `AZURE_BLOB_SAS` - a read (+list) SAS for the `sttutela001` account, covering
    containers `tutela-bronze` and `tutela-backups`. The `fetch-effis` workflow also
    needs **write** to `tutela-bronze/raw/effis`, so grant `racwl` if you use one SAS for
    both, or split into `AZURE_BLOB_SAS_RO` (publish) and a write SAS (effis).
  - `CDSAPI_URL` = `https://ewds.climate.copernicus.eu/api`  (for fetch-effis)
  - `CDSAPI_KEY` = the ECMWF/EWDS API key  (for fetch-effis)
- **Branch protection** on `main`: block force-push and history rewrite. This is what
  makes the commit ledger tamper-evident (see docs/provenance.md).
- The publish workflow pushes to this same repo using the built-in `GITHUB_TOKEN`
  (`permissions: contents: write`). No personal access token is needed at runtime.

Generate the SAS (run against the tutela subscription, e.g. as the `tutela-deploy` SP):

```bash
end=$(date -u -d "+2 years" +%Y-%m-%dT%H:%MZ)
# read-only for publish:
az storage account generate-sas --account-name sttutela001 \
  --services b --resource-types co --permissions rl \
  --expiry "$end" --https-only -o tsv
# read+write+list for effis+publish combined (broader):
az storage account generate-sas --account-name sttutela001 \
  --services b --resource-types co --permissions racwl \
  --expiry "$end" --https-only -o tsv
```

## 2. First backfill

The blob already holds RCM (since 2026-06-04) and fires (since 2026-05-19). Backfill them
into git once:

- Actions -> publish-archive -> Run workflow -> set `window_days` to e.g. `420`.

Subsequent scheduled runs use the default 14-day trailing window.

## 3. Going public

The repo is private today. Flip to public only after the first backfill looks right and
the READMEs read well. Once public it may be forked, cached, and indexed, so it is a
one-way door in practice.

## 4. EFFIS (still to finish)

`scripts/fetch_effis.py` is a stub. Port it from the private `scripts/fetch_effis_fwi.py`
(checklist in the stub), verify a manual `fetch-effis` run writes a sane parquet to blob,
then uncomment the `schedule:` block in `.github/workflows/fetch-effis.yml`.

## 5. Azure fires archiver

Separate from this repo: the fires truth is produced by a new timer function added to the
`func-tutela-archiver` app in the private pipeline (`functions/fires_archiver/`). It writes
`tutela-backups/fires/fires-YYYY-MM-DD.parquet`, which publish-archive then mirrors here.
Deploy + cron details live with that code.
