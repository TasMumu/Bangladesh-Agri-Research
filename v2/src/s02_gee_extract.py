"""Step 2 - District x harvest-year remote-sensing and climate variables from
Google Earth Engine.  Harvest year t = the Boro crop sown Nov(t-1), harvested
Apr-May(t) = BBS crop year "(t-1)-t".

Variables (all observed; no gap filling):
  NDVI      MODIS MOD13Q1 v061, 250 m, SummaryQA <= 1, cropland pixels only
            (ESA WorldCover v200 class 40 covering > 50 % of the MODIS cell).
            ndvi_peak = mean of Jan-Apr(t) composites (Boro vegetative to grain
            filling); ndvi_max = maximum Jan-Apr composite.
  Climate   ERA5-Land daily aggregates (0.1 deg), season Nov(t-1)-May(t):
            tmean_c, tmax_c (mean daily maximum), precip_mm (season total),
            hot_days (days with Tmax > 35 C in Mar-May(t), flowering window).
  Flood     Share of district area newly under water relative to the same
            year's dry season (Jan-Mar), so permanent rivers are excluded.
            monsoon_flood : water in any month Jun-Oct(t-1)   (antecedent)
            flash_flood   : water in Apr or May(t)            (pre-harvest)
            JRC GSW v1.4 MonthlyHistory (Landsat, 30 m)   1984-2021
            Sentinel-1 GRD VV, monthly median, < -18 dB    Oct 2014 onward
            The two sources are kept as separate variables (never spliced).

Results are cached per variable and year in v2/data/bronze/gee/.
"""
import json
import sys
import time

import ee
import geopandas as gpd
import pandas as pd

from common import BRONZE, GEE_PROJECT, V2_BRONZE, canon_district

OUT = V2_BRONZE / "gee"
OUT.mkdir(parents=True, exist_ok=True)
HARVEST_YEARS = range(2011, 2026)

ee.Initialize(project=GEE_PROJECT)


def districts_fc():
    g = gpd.read_file(BRONZE / "gadm_shapefiles" / "gadm41_BGD_2.shp")
    g["district"] = g.NAME_2.map(canon_district)
    g["geometry"] = g.geometry.simplify(0.001, preserve_topology=True)
    gj = json.loads(g[["district", "geometry"]].to_json())
    feats = [ee.Feature(ee.Geometry(f["geometry"]), {"district": f["properties"]["district"]})
             for f in gj["features"]]
    return ee.FeatureCollection(feats)


FC = districts_fc()
BD = FC.geometry().bounds()


def reduce(img, scale, reducer=None, tile=8):
    reducer = reducer or ee.Reducer.mean()
    res = img.reduceRegions(collection=FC, reducer=reducer, scale=scale, tileScale=tile)
    rows = res.select(["district"] + img.bandNames().getInfo(), retainGeometry=False).getInfo()
    return pd.DataFrame([f["properties"] for f in rows["features"]])


def cached(name, year, fn):
    f = OUT / f"{name}_{year}.csv"
    if f.exists():
        return pd.read_csv(f)
    for attempt in range(3):
        try:
            t0 = time.time()
            df = fn(year)
            df["harvest_year"] = year
            df.to_csv(f, index=False)
            print(f"  {name} {year}: {len(df)} rows in {time.time() - t0:.0f}s", flush=True)
            return df
        except Exception as e:                       # transient EE errors
            print(f"  {name} {year}: attempt {attempt + 1} failed: {e}", flush=True)
            time.sleep(10)
    raise RuntimeError(f"{name} {year} failed")


# ── NDVI ─────────────────────────────────────────────────────────────────
MODIS = ee.ImageCollection("MODIS/061/MOD13Q1")
_modis_proj = MODIS.first().projection()
CROPLAND = (ee.Image("ESA/WorldCover/v200/2021").eq(40).unmask(0)
            .reduceResolution(ee.Reducer.mean(), maxPixels=1024)
            .reproject(_modis_proj).gt(0.5))


def ndvi(year):
    col = (MODIS.filterDate(f"{year}-01-01", f"{year}-05-01")
           .map(lambda i: i.select("NDVI").multiply(0.0001)
                .updateMask(i.select("SummaryQA").lte(1))))
    img = ee.Image.cat(col.mean().rename("ndvi_peak"), col.max().rename("ndvi_max"))
    return reduce(img.updateMask(CROPLAND), 250)


# ── Climate ──────────────────────────────────────────────────────────────
ERA = ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")


def climate(year):
    season = ERA.filterDate(f"{year - 1}-11-01", f"{year}-06-01")
    tmean = season.select("temperature_2m").mean().subtract(273.15).rename("tmean_c")
    tmax = season.select("temperature_2m_max").mean().subtract(273.15).rename("tmax_c")
    prec = season.select("total_precipitation_sum").sum().multiply(1000).rename("precip_mm")
    hot = (ERA.filterDate(f"{year}-03-01", f"{year}-06-01").select("temperature_2m_max")
           .map(lambda i: i.subtract(273.15).gt(35)).sum().rename("hot_days"))
    return reduce(ee.Image.cat(tmean, tmax, prec, hot), 1000)


# ── Flood: JRC monthly ───────────────────────────────────────────────────
JRC = ee.ImageCollection("JRC/GSW1_4/MonthlyHistory")


def _jrc_months(y, m0, m1):
    return JRC.filter(ee.Filter.calendarRange(y, y, "year")).filter(
        ee.Filter.calendarRange(m0, m1, "month"))


def _jrc_water(y, m0, m1):
    c = _jrc_months(y, m0, m1)
    water = c.map(lambda i: i.eq(2)).max().unmask(0)
    seen = c.map(lambda i: i.gt(0)).max().unmask(0)
    return water, seen


def jrc_flood(year):
    mon_w, mon_seen = _jrc_water(year - 1, 6, 10)
    dry_prev, _ = _jrc_water(year - 1, 1, 3)
    bands = [mon_w.And(dry_prev.Not()).rename("jrc_monsoon_flood"),
             mon_seen.rename("jrc_monsoon_obs")]
    if year <= 2021:                          # JRC monthly ends Dec 2021
        fl_w, fl_seen = _jrc_water(year, 4, 5)
        dry_cur, _ = _jrc_water(year, 1, 3)
        bands += [fl_w.And(dry_cur.Not()).rename("jrc_flash_flood"),
                  fl_seen.rename("jrc_flash_obs")]
    return reduce(ee.Image.cat(bands).clip(BD), 30)


# ── Flood: Sentinel-1 ────────────────────────────────────────────────────
S1 = (ee.ImageCollection("COPERNICUS/S1_GRD")
      .filter(ee.Filter.eq("instrumentMode", "IW"))
      .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
      .filterBounds(BD).select("VV"))
SLOPE_OK = ee.Terrain.slope(ee.Image("USGS/SRTMGL1_003")).lt(5)
S1_THRESH = -18


def _s1_water(start, end):
    c = S1.filterDate(start, end)
    vv = c.median().focal_median(50, "circle", "meters")
    return vv.lt(S1_THRESH).And(SLOPE_OK).unmask(0), c.size()


def _s1_monthly_any(y, m0, m1):
    imgs = []
    for m in range(m0, m1 + 1):
        end = f"{y}-{m + 1:02d}-01" if m < 12 else f"{y + 1}-01-01"
        w, _ = _s1_water(f"{y}-{m:02d}-01", end)
        imgs.append(w)
    return ee.ImageCollection(imgs).max()


def s1_flood(year):
    mon = _s1_monthly_any(year - 1, 6, 10)
    dry_prev, _ = _s1_water(f"{year - 1}-01-01", f"{year - 1}-04-01")
    fl = _s1_monthly_any(year, 4, 5)
    dry_cur, _ = _s1_water(f"{year}-01-01", f"{year}-04-01")
    bands = [fl.And(dry_cur.Not()).rename("s1_flash_flood")]
    if year - 1 >= 2015:                      # full Jun-Oct and Jan-Mar coverage
        bands.insert(0, mon.And(dry_prev.Not()).rename("s1_monsoon_flood"))
    return reduce(ee.Image.cat(bands).clip(BD), 60)


def main(which):
    jobs = {
        "ndvi": (ndvi, HARVEST_YEARS),
        "climate": (climate, HARVEST_YEARS),
        "jrc": (jrc_flood, range(2011, 2023)),      # monsoon 2010-2021 / flash to 2021
        "s1": (s1_flood, range(2015, 2026)),        # flash 2015+, monsoon 2015+ (t>=2016)
    }
    for name in which:
        fn, years = jobs[name]
        print(f"[{name}]", flush=True)
        frames = [cached(name, y, fn) for y in years]
        pd.concat(frames).to_csv(OUT / f"{name}_all.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1:] or ["ndvi", "climate", "jrc", "s1"])
