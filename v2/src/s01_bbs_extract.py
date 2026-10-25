"""Step 1 - Extract district-level Total Boro (Local+HYV+Hybrid) estimates
from every BBS Yearbook of Agricultural Statistics (2012-2025 editions).

Every value is read from the printed table; nothing is imputed.  Each row is
checked three ways (acres<->hectares, maund/acre<->t/ha, area x yield =
production), each yearbook's district sum is checked against its printed
national total, and years printed in two editions are compared.

Outputs (v2/data/bronze/bbs):
  bbs_boro_rows_all.csv      every parsed row, all editions, with QC flags
  bbs_boro_national.csv      printed national totals per edition/year
  bbs_boro_district_year.csv one row per district x crop year (later edition)
  bbs_edition_diffs.csv      district-years whose values differ between editions
"""
import re
import warnings

import camelot
import numpy as np
import pandas as pd

from common import BRONZE, V2_BRONZE, canon_district

warnings.filterwarnings("ignore")

PDF_DIR = BRONZE / "bbs" / "pdfs"
OUT = V2_BRONZE / "bbs"
OUT.mkdir(parents=True, exist_ok=True)

# Pages (1-based) holding the "Total Boro (Local+HYV+Hybrid)" district table,
# located by searching each yearbook's table titles.
PAGES = {
    2012: "90,91", 2013: "92,93", 2014: "90,91", 2015: "94,95",
    2016: "96,97", 2017: "95,96", 2018: "96,97", 2019: "96,97",
    2020: "92,93", 2021: "98,99", 2022: "98,99", 2023: "99,100",
    2024: "96,97", 2025: "97,98",
}

ACRE_HA = 0.404686           # hectares per acre
MAUND_T = 0.0373242          # tonnes per maund
YEAR_RE = re.compile(r"(20\d\d)\s*-\s*(?:20)?(\d\d)(?!\d)")


def to_num(s):
    s = str(s).replace(",", "").replace("\n", "").strip()
    if re.fullmatch(r"-?\d+(\.\d+)?", s):
        return float(s)
    return None


def parse_table(df, book, page):
    header = " ".join(df.iloc[:3].astype(str).values.ravel())
    years = []
    for a, b in YEAR_RE.findall(header):
        cy = f"{a}-{b}"
        if cy not in years:
            years.append(cy)
    rows = []
    for _, r in df.iterrows():
        cells = [str(c).replace("\n", " ").strip() for c in r.tolist()]
        nums, name_parts = [], []
        for c in cells:
            v = to_num(c)
            if v is None:
                if c:
                    name_parts.append(c)
            elif name_parts or nums:            # skip leading serial numbers
                nums.append(v)
        name = re.sub(r"^\d+\s*", "", " ".join(name_parts)).strip()
        if not name or len(nums) not in (5, 10):
            continue
        blocks = [nums[i:i + 5] for i in range(0, len(nums), 5)]
        if len(blocks) != len(years):
            # a single-year table, or a header we failed to read
            ys = years[-len(blocks):] if len(years) >= len(blocks) else [None] * len(blocks)
        else:
            ys = years
        for cy, (acre, ha, maund, tha, prod) in zip(ys, blocks):
            rows.append(dict(book_year=book, page=page, raw_name=name, crop_year=cy,
                             area_acres=acre, area_ha=ha, yield_maund_acre=maund,
                             yield_t_ha=tha, production_t=prod))
    return rows


def extract():
    rows = []
    for book, pages in PAGES.items():
        pdf = PDF_DIR / f"bbs_agri_yearbook_{book}.pdf"
        tables = camelot.read_pdf(str(pdf), pages=pages, flavor="lattice")
        for t in tables:
            rows += parse_table(t.df, book, t.page)
        print(f"{book}: {len(tables)} tables")
    d = pd.DataFrame(rows)
    # The 2012 and 2013 editions group districts under former "greater
    # district" regions.  Five regions contain exactly one present-day
    # district and print no district row beneath them, so the region row
    # *is* that district's printed estimate.
    single = {"bandarbanregion": "Bandarban", "khagrachariregion": "Khagrachhari",
              "rangamatiregion": "Rangamati", "mymenshingregion": "Mymensingh",
              "tangailregion": "Tangail"}
    key = d.raw_name.str.lower().str.replace(r"[^a-z]", "", regex=True)
    is_single = d.book_year.isin([2012, 2013]) & key.isin(single)
    d["district"] = d.raw_name.map(canon_district)
    d.loc[is_single, "district"] = key[is_single].map(single)
    d.loc[is_single, "raw_name"] = d.loc[is_single, "raw_name"] + " [single-district region]"
    name_l = d.raw_name.str.lower()
    d["row_type"] = np.where(name_l.str.contains("bangladesh|national"), "national",
                     np.where(name_l.str.contains("division|divison|region") & ~is_single, "division",
                     np.where(d.district.notna(), "district", "unknown")))
    # Arithmetic QC (relative error)
    d["qc_ha"] = (d.area_acres * ACRE_HA / d.area_ha - 1).abs()
    d["qc_yield"] = (d.yield_maund_acre * MAUND_T / ACRE_HA / d.yield_t_ha - 1).abs()
    d["qc_prod"] = (d.area_ha * d.yield_t_ha / d.production_t - 1).abs()
    d["qc_pass"] = (d.qc_ha < 0.01) & (d.qc_yield < 0.02) & (d.qc_prod < 0.02)
    return d


def main():
    d = extract()
    d.to_csv(OUT / "bbs_boro_rows_all.csv", index=False)
    unknown = d[d.row_type == "unknown"].raw_name.unique()
    if len(unknown):
        print("Unrecognised row names:", list(unknown))

    nat = d[d.row_type == "national"][["book_year", "crop_year", "area_ha", "yield_t_ha", "production_t"]]
    nat.to_csv(OUT / "bbs_boro_national.csv", index=False)

    dist = d[(d.row_type == "district") & d.crop_year.notna()].copy()
    dist = dist.drop_duplicates(["book_year", "crop_year", "district"])

    # District sum vs printed national total, per edition and year
    s = dist.groupby(["book_year", "crop_year"]).agg(
        n_districts=("district", "nunique"), sum_prod=("production_t", "sum"),
        sum_area=("area_ha", "sum"), n_qc_fail=("qc_pass", lambda x: int((~x).sum())))
    s = s.join(nat.set_index(["book_year", "crop_year"])[["production_t", "area_ha"]]
               .rename(columns={"production_t": "national_prod", "area_ha": "national_area"}))
    s["prod_gap_pct"] = 100 * (s.sum_prod / s.national_prod - 1)
    s.to_csv(OUT / "bbs_edition_checks.csv")
    print(s.to_string())

    # Compare editions where a crop year is printed twice
    keys = ["district", "crop_year"]
    multi = dist[dist.duplicated(keys, keep=False)].sort_values(keys + ["book_year"])
    diffs = []
    for (dn, cy), g in multi.groupby(keys):
        a, b = g.iloc[0], g.iloc[-1]
        if abs(a.yield_t_ha - b.yield_t_ha) > 0.0005 or abs(a.area_ha - b.area_ha) > 0.5:
            diffs.append(dict(district=dn, crop_year=cy, early_book=a.book_year,
                              late_book=b.book_year, early_yield=a.yield_t_ha,
                              late_yield=b.yield_t_ha, early_area=a.area_ha, late_area=b.area_ha))
    pd.DataFrame(diffs).to_csv(OUT / "bbs_edition_diffs.csv", index=False)
    print(f"District-years printed in two editions: {multi[keys].drop_duplicates().shape[0]}, "
          f"differing: {len(diffs)}")

    # Final: one row per district-year, taking the later (revised) edition
    # among rows that pass the arithmetic QC.
    good = dist[dist.qc_pass].sort_values("book_year")
    final = good.drop_duplicates(keys, keep="last").copy()
    final["harvest_year"] = final.crop_year.str[:4].astype(int) + 1
    final = final.sort_values(["harvest_year", "district"])
    final.to_csv(OUT / "bbs_boro_district_year.csv", index=False)
    cov = final.groupby("crop_year").district.nunique()
    print("Districts per crop year (final):\n", cov.to_string())
    print("QC failures (excluded):", int((~dist.qc_pass).sum()))


if __name__ == "__main__":
    main()
