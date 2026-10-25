"""Step 3 - Silver and Gold layers.

Silver: one tidy parquet per source keyed on (district, harvest_year), with
range validation.  Gold: DuckDB tables used by every analysis and the
dashboard.  The panel contains BBS-observed yields only; no value is
imputed, interpolated or modelled.  Missing inputs stay NULL.
"""
import duckdb
import geopandas as gpd
import pandas as pd

from common import BRONZE, CANONICAL, LOGS, V2_BRONZE, V2_GOLD, V2_SILVER, canon_district

GEE = V2_BRONZE / "gee"

RANGES = {                       # plausible ranges for validation
    "yield_t_ha": (1.0, 7.0), "area_ha": (0, 300000), "ndvi_peak": (0.0, 1.0),
    "ndvi_max": (0.0, 1.0), "tmean_c": (10, 35), "tmax_c": (15, 40),
    "precip_mm": (0, 3000), "hot_days": (0, 92),
    "jrc_monsoon_flood": (0, 1), "jrc_flash_flood": (0, 1),
    "s1_monsoon_flood": (0, 1), "s1_flash_flood": (0, 1),
}


def validate(df, name, log):
    for c, (lo, hi) in RANGES.items():
        if c in df:
            bad = df[c].notna() & ~df[c].between(lo, hi)
            log.append(f"{name}: {c} out of [{lo},{hi}]: {int(bad.sum())}")
            assert bad.sum() == 0, f"{name}.{c} has {bad.sum()} out-of-range values"
    dup = df.duplicated(["district", "harvest_year"]).sum()
    log.append(f"{name}: duplicate district-years: {dup}")
    assert dup == 0


def main():
    log = []
    # ── Silver ──────────────────────────────────────────────────────────
    bbs = pd.read_csv(V2_BRONZE / "bbs" / "bbs_boro_district_year.csv")
    bbs["district"] = bbs.district.map(canon_district)
    bbs = bbs[["district", "harvest_year", "crop_year", "area_ha", "yield_t_ha",
               "production_t", "book_year", "page"]].rename(
        columns={"book_year": "bbs_edition", "page": "bbs_page"})
    nat = pd.read_csv(V2_BRONZE / "bbs" / "bbs_boro_national.csv")
    nat = (nat.sort_values("book_year").drop_duplicates("crop_year", keep="last")
           .assign(harvest_year=lambda x: x.crop_year.str[:4].astype(int) + 1))

    silver = {"bbs_boro": bbs}
    for name in ["ndvi", "climate", "jrc", "s1"]:
        df = pd.read_csv(GEE / f"{name}_all.csv")
        df["district"] = df.district.map(canon_district)
        silver[name] = df
    for name, df in silver.items():
        validate(df, name, log)
        df.to_parquet(V2_SILVER / f"silver_{name}.parquet", index=False)

    g = gpd.read_file(BRONZE / "gadm_shapefiles" / "gadm41_BGD_2.shp")
    g["district"] = g.NAME_2.map(canon_district)
    g["division"] = g.NAME_1.replace({"Barisal": "Barishal", "Chittagong": "Chattogram"})
    g["area_km2"] = g.to_crs(32646).area / 1e6
    assert sorted(g.district) == sorted(CANONICAL)
    dim = pd.DataFrame(g[["district", "division", "area_km2"]])

    # ── Gold ────────────────────────────────────────────────────────────
    con = duckdb.connect(str(V2_GOLD))
    for name, df in silver.items():
        con.register("tmp", df)
        con.execute(f"CREATE OR REPLACE TABLE stg_{name} AS SELECT * FROM tmp")
        con.unregister("tmp")
    con.register("tmp", dim)
    con.execute("CREATE OR REPLACE TABLE dim_district AS SELECT * FROM tmp")
    con.unregister("tmp")
    # National series from district sums (all 15 years), with the printed
    # national row alongside wherever an edition prints one.
    con.register("tmp", nat[["harvest_year", "area_ha", "yield_t_ha", "production_t"]])
    con.execute("""
        CREATE OR REPLACE TABLE fact_boro_national AS
        SELECT b.harvest_year, any_value(b.crop_year) AS crop_year,
               sum(b.area_ha) AS area_ha, sum(b.production_t) AS production_t,
               sum(b.production_t) / sum(b.area_ha) AS yield_t_ha,
               any_value(t.production_t) AS printed_national_production_t,
               any_value(t.yield_t_ha) AS printed_national_yield_t_ha
        FROM stg_bbs_boro b LEFT JOIN tmp t USING (harvest_year)
        GROUP BY b.harvest_year ORDER BY b.harvest_year
    """)
    con.unregister("tmp")

    con.execute("""
        CREATE OR REPLACE TABLE fact_boro_panel AS
        SELECT b.district, d.division, d.area_km2, b.harvest_year, b.crop_year,
               b.yield_t_ha, b.area_ha, b.production_t, b.bbs_edition, b.bbs_page,
               n.ndvi_peak, n.ndvi_max,
               c.tmean_c, c.tmax_c, c.precip_mm, c.hot_days,
               j.jrc_monsoon_flood, j.jrc_flash_flood, j.jrc_monsoon_obs, j.jrc_flash_obs,
               s.s1_monsoon_flood, s.s1_flash_flood
        FROM stg_bbs_boro b
        JOIN dim_district d USING (district)
        LEFT JOIN stg_ndvi n USING (district, harvest_year)
        LEFT JOIN stg_climate c USING (district, harvest_year)
        LEFT JOIN stg_jrc j USING (district, harvest_year)
        LEFT JOIN stg_s1 s USING (district, harvest_year)
        ORDER BY district, harvest_year
    """)
    panel = con.execute("SELECT * FROM fact_boro_panel").df()
    con.close()

    assert len(panel) == 64 * 15 and not panel.duplicated(["district", "harvest_year"]).any()
    log.append(f"fact_boro_panel: {len(panel)} rows, {panel.district.nunique()} districts, "
               f"{panel.harvest_year.min()}-{panel.harvest_year.max()}")
    log.append("Non-missing counts:\n" + panel.notna().sum().to_string())
    (LOGS / "s03_build_panel.log").write_text("\n".join(log), encoding="utf-8")
    print("\n".join(log))


if __name__ == "__main__":
    main()
