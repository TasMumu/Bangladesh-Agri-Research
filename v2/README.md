# v2 — BBS-observed rebuild (revision, 2026)

This folder rebuilds the analysis using **only BBS-observed Boro yields**: no
NDVI-calibrated proxy, no interpolation, no imputed values. The original
notebooks, data and dashboard in the project root are left unchanged.

## What changed from v1

| Issue in v1 | v2 |
|---|---|
| 2001–2011 yields were an NDVI-calibrated proxy; 59 values interpolated | Removed. Panel = 64 districts × 15 BBS-observed seasons (960 rows) |
| BBS crop year "2012-13" was labelled 2012 while NDVI/climate used harvest year 2013 (one-year misalignment) | Every row is keyed on **harvest year** (crop year 2012-13 → 2013) |
| BBS 2010-11 and 2011-12 dropped; 57–61 districts in several years | All 14 yearbooks (2012–2025 editions) re-extracted: 64 districts every year, 2010-11 to 2024-25 |
| JRC annual flood file with undocumented season and river handling | Monsoon flood (Jun–Oct of t−1) and flash flood (Apr–May of t), net of same-year dry-season water, from JRC monthly (Landsat) and Sentinel-1 SAR; code included |
| Seasonal NDVI over all land | Peak-season (Jan–Apr) NDVI over cropland only (ESA WorldCover), QA-filtered |
| Cross-sectional spatial lag/error models presented as a robustness check | Removed. Spatial dependence tested on panel residuals; Driscoll–Kraay SEs reported |

## Data checks performed

* Each BBS row passes three arithmetic identities (acres↔hectares,
  maund/acre↔t/ha, area × yield = production); rows failing are excluded.
* District sums equal the printed national total in every edition where the
  national row is printed (`data/bronze/bbs/bbs_edition_checks.csv`).
* Years printed in two editions agree (differences ≤ 1 ha, rounding);
  the later edition is used (`bbs_edition_diffs.csv`).
* Range validation and duplicate checks on every Silver table (the
  pipeline stops on any failure; a log is written to `logs/` locally).

## Run

```bash
python v2/run_all.py
```

Requires an authenticated Earth Engine account (`earthengine authenticate`)
with access to project `bd-agri-climate` (set in `src/common.py`). Earth
Engine extracts are cached per variable and year in `data/bronze/gee/`.

| Step | Script | Output |
|---|---|---|
| 1 | `s01_bbs_extract.py` | `data/bronze/bbs/*.csv` |
| 2 | `s02_gee_extract.py` | `data/bronze/gee/*.csv` |
| 3 | `s03_build_panel.py` | `data/silver/*.parquet`, `data/gold/bangladesh_agri_v2.duckdb` |
| 4 | `s04_analysis.py` | `outputs/tables/*.csv`, `outputs/results.json` |
| 5 | `s05_figures.py` | `outputs/figures/*.png` |

Dashboard: `streamlit run v2/dashboard_v2.py`
