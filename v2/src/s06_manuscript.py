"""Step 6 - Assemble the revised manuscript (Markdown -> .docx via pandoc).

Narrative parts live in v2/paper/parts/*.md.  Placeholders of the form
{{ expression }} are evaluated against results.json (as R) and the table
CSVs, so every number in the text comes from the analysis outputs.
Tables are generated here from the CSVs.
"""
import json
import re
import subprocess

import pandas as pd

from common import TABLES, V2, V2_BRONZE

PAPER = V2 / "paper"
PARTS = PAPER / "parts"
R = json.loads((V2 / "outputs" / "results.json").read_text(encoding="utf-8"))
REG = R["regressions"]


def fmt_p(p, d=3):
    return "< 0.001" if p < 0.001 else f"{p:.{d}f}"


def p_eq(p):
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def coef(m, v, d=3):
    c = REG[m]["coef"][v]
    return f"{c['b']:+.{d}f} t/ha (SE {c['se']:.{d}f}, {p_eq(c['p'])}; Driscoll–Kraay {p_eq(c['p_dk'])})"


AP = R["regressions_area_prod"]
EX = R["sensitivity_excl_2017"]


def bbs_stats():
    rows = pd.read_csv(V2_BRONZE / "bbs" / "bbs_boro_rows_all.csv")
    chk = pd.read_csv(V2_BRONZE / "bbs" / "bbs_edition_checks.csv")
    diffs = pd.read_csv(V2_BRONZE / "bbs" / "bbs_edition_diffs.csv")
    dist = rows[(rows.row_type == "district") & rows.crop_year.notna()]
    two = dist.groupby(["district", "crop_year"]).book_year.nunique()
    fails = dist[~dist.qc_pass]
    return dict(n_rows=len(dist), n_fail=int((~dist.qc_pass).sum()),
                fail_where=sorted({f"{b} edition, {c}" for b, c in zip(fails.book_year, fails.crop_year)}),
                n_edition_years=len(chk), n_nat=int(chk.national_prod.notna().sum()),
                n_complete=int((chk.n_districts == 64).sum()),
                incomplete=sorted({f"{int(b)} edition ({n} districts parsed)" for b, n in
                                   zip(chk.book_year, chk.n_districts) if n < 64}),
                n_nat_complete=int(((chk.n_districts == 64) & chk.national_prod.notna()).sum()),
                max_gap_pct=float(chk[chk.n_districts == 64].prod_gap_pct.abs().max()),
                n_two=int((two > 1).sum()), n_diff=len(diffs),
                max_area_diff=float((diffs.late_area - diffs.early_area).abs().max()) if len(diffs) else 0.0)


BBS = bbs_stats()
VI = pd.read_csv(TABLES / "table_vulnerability_index.csv").set_index("district")
TOP = VI[VI["rank"] <= 10]
EV = pd.read_csv(TABLES / "table_event_2017.csv").set_index("district").head(6)
DESC = pd.read_csv(TABLES / "table_descriptives.csv").set_index("variable")
_f = pd.read_csv(V2_BRONZE / "bbs" / "bbs_boro_district_year.csv")
NATSUM = _f.groupby("crop_year").production_t.sum().to_dict()


def pct(key, v, src=None):
    c = (src or AP)[key]["coef"][v]
    return (f"{100 * c['b']:+.1f} % (SE {100 * c['se']:.1f}, {p_eq(c['p'])}; "
            f"Driscoll–Kraay {p_eq(c['p_dk'])})")


def f(x, d=3):
    return f"{x:.{d}f}"


def md_table(df):
    cols = list(df.columns)
    # Pandoc sizes pipe-table columns by the relative length of the dashes, so
    # make each proportional to its widest cell (or longest header word).
    def width(c):
        cells = [len(str(v)) for v in df[c] if not pd.isna(v)]
        head = max(len(w) for w in str(c).split())
        return min(max([head] + cells + [9]), 26)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("-" * width(c) for c in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join("" if pd.isna(r[c]) else str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def table_alignment():
    rows = [("Boro yield", "BBS crop year (t−1)–t", "Harvest Apr–May t"),
            ("Peak-season NDVI", "MODIS composites", "Jan–Apr t"),
            ("Mean temperature, mean daily maximum, season precipitation", "ERA5-Land daily", "Nov t−1 – May t"),
            ("Hot days (Tmax > 35 °C)", "ERA5-Land daily", "Mar–May t"),
            ("Monsoon flood fraction", "JRC monthly / Sentinel-1", "Jun–Oct t−1, net of Jan–Mar t−1 water"),
            ("Flash flood fraction", "JRC monthly / Sentinel-1", "Apr–May t, net of Jan–Mar t water")]
    return md_table(pd.DataFrame(rows, columns=["Variable", "Source", "Window for harvest year t"]))


def table_bbs_checks():
    c = pd.read_csv(V2_BRONZE / "bbs" / "bbs_edition_checks.csv")
    f = pd.read_csv(V2_BRONZE / "bbs" / "bbs_boro_district_year.csv")
    rows = []
    for cy, g in c.groupby("crop_year"):
        fin = f[f.crop_year == cy]
        complete = g[g.n_districts == 64]
        gap = complete.prod_gap_pct.dropna()
        if len(gap):
            chk = "< 0.001 %" if gap.abs().max() < 0.001 else f"{gap.abs().max():.3f} %"
        else:
            chk = "matches text total"
        rows.append({"Crop year": cy, "Harvest year": int(cy[:4]) + 1,
                     "Editions": ", ".join(str(int(b)) for b in g.book_year),
                     "Districts": fin.district.nunique(),
                     "Rows failing checks": int(g.n_qc_fail.sum()),
                     "Gap to national total": chk,
                     "Edition used": int(fin.book_year.max())})
    return md_table(pd.DataFrame(rows))


def table_descriptives():
    d = pd.read_csv(TABLES / "table_descriptives.csv")
    for c in ["mean", "sd", "min", "max"]:
        d[c] = d[c].map(lambda x: f"{x:,.0f}" if abs(x) >= 1000 else f"{x:.3f}")
    return md_table(d.rename(columns={"variable": "Variable", "years": "Harvest years", "n": "N",
                                      "mean": "Mean", "sd": "SD", "min": "Min", "max": "Max"}))


def table_fe():
    d = pd.read_csv(TABLES / "table_panel_fe.csv").fillna("")
    hdr = {m: f"{m} {REG[m]['title']}" for m in REG}
    return md_table(d.rename(columns=hdr))


def table_vi_top():
    v = pd.read_csv(TABLES / "table_vulnerability_index.csv").head(10)
    v = v.assign(vi=v.vi.map("{:.3f}".format),
                 p_top10_random_weights=(100 * v.p_top10_random_weights).round(0).astype(int),
                 mean_yield=v.mean_yield.map("{:.2f}".format),
                 monsoon_flood_mean=(100 * v.monsoon_flood_mean).map("{:.1f}".format),
                 flash_flood_mean=(100 * v.flash_flood_mean).map("{:.1f}".format),
                 hot_days_mean=v.hot_days_mean.map("{:.1f}".format))
    return md_table(v[["rank", "district", "vi", "mean_yield", "monsoon_flood_mean",
                       "flash_flood_mean", "hot_days_mean", "p_top10_random_weights", "cluster_005"]].rename(columns={
        "rank": "Rank", "district": "District", "vi": "Index",
        "mean_yield": "Yield (t/ha)", "monsoon_flood_mean": "Monsoon flood (%)",
        "flash_flood_mean": "Flash flood (%)", "hot_days_mean": "Hot days",
        "p_top10_random_weights": "Top-10 share (%)", "cluster_005": "LISA"}))


def table_mk():
    t = pd.read_csv(TABLES / "table_mann_kendall.csv")
    t = t.assign(tau=t.tau.round(3), sen_slope=t.sen_slope.map(lambda x: f"{x:+.4f}"),
                 p=t.p.map(fmt_p))
    return md_table(t.rename(columns={"variable": "Series", "years": "Harvest years", "n": "n",
                                      "trend": "Trend", "tau": "Kendall's tau", "sen_slope": "Sen's slope (per year)",
                                      "p": "p (Hamed–Rao)"}))


def table_fe_ap():
    d = pd.read_csv(TABLES / "table_panel_fe_area_production.csv").fillna("")
    return md_table(d.rename(columns={k: k.replace("Production", "Prod.") for k in d.columns if k != "Variable"}))


def table_event():
    d = pd.read_csv(TABLES / "table_event_2017.csv").head(8)
    d = d.assign(**{c: d[c].map(lambda x: f"{x:+.1f}" if "change" in c else f"{x:.1f}")
                    for c in d.columns if c != "district"})
    return md_table(d.rename(columns={"district": "District", "s1_flash_flood_pct": "Flash flood, S1 (%)",
                                      "jrc_flash_flood_pct": "Flash flood, JRC (%)",
                                      "area_change_pct": "Harvested area (%)", "yield_change_pct": "Yield (%)",
                                      "production_change_pct": "Production (%)"}))


def table_moran():
    d = pd.read_csv(TABLES / "table_residual_moran.csv")
    d = d.assign(moran_i=d.moran_i.round(3), p_sim=d.p_sim.map(lambda x: f"{x:.4f}"),
                 p_fdr=d.p_fdr.map(lambda x: f"{x:.4f}"))
    return md_table(d.rename(columns={"harvest_year": "Harvest year", "moran_i": "Moran's I",
                                      "p_sim": "Pseudo p", "p_fdr": "FDR-adjusted p"}))


def table_software():
    from importlib.metadata import version
    import platform
    pk = [("Python", platform.python_version(), "Language"),
          ("duckdb", version("duckdb"), "Analytical warehouse (Gold layer)"),
          ("pandas", version("pandas"), "Data manipulation"), ("numpy", version("numpy"), "Numerics"),
          ("pyarrow", version("pyarrow"), "Parquet (Silver layer)"),
          ("camelot-py", version("camelot-py"), "BBS PDF table extraction"),
          ("earthengine-api", version("earthengine-api"), "MODIS, ERA5-Land, JRC, Sentinel-1 extraction"),
          ("geopandas", version("geopandas"), "Boundaries and maps"),
          ("libpysal", version("libpysal"), "Spatial weights"), ("esda", version("esda"), "Moran's I, LISA"),
          ("linearmodels", version("linearmodels"), "Fixed-effects panel models"),
          ("statsmodels", version("statsmodels"), "FDR correction"),
          ("pymannkendall", version("pymannkendall"), "Mann–Kendall tests"),
          ("scipy", version("scipy"), "Rank correlations"), ("matplotlib", version("matplotlib"), "Figures"),
          ("streamlit", version("streamlit"), "Dashboard"), ("plotly", version("plotly"), "Dashboard charts")]
    return md_table(pd.DataFrame(pk, columns=["Package", "Version", "Role"]))


TABLE_FUNCS = {"table_alignment": table_alignment, "table_bbs_checks": table_bbs_checks,
               "table_descriptives": table_descriptives, "table_fe": table_fe,
               "table_fe_ap": table_fe_ap, "table_event": table_event, "table_moran": table_moran,
               "table_software": table_software, "table_vi_top": table_vi_top, "table_mk": table_mk}


def render(text):
    def ev(m):
        expr = m.group(1).strip()
        if expr in TABLE_FUNCS:
            return TABLE_FUNCS[expr]()
        return str(eval(expr, {"R": R, "REG": REG, "AP": AP, "EX": EX, "BBS": BBS, "VI": VI, "TOP": TOP, "EV": EV, "DESC": DESC, "NATSUM": NATSUM, "int": int, "sum": sum, "coef": coef, "pct": pct,
                               "fmt_p": fmt_p, "p_eq": p_eq, "f": f, "len": len, "round": round, "abs": abs,
                               "max": max, "min": min}))
    return re.sub(r"\{\{(.+?)\}\}", ev, text, flags=re.S)


def renumber_citations(md):
    """Number references in order of first citation and check coverage."""
    body, rest = md.split("# References", 1)
    refs, tail = rest.split("# Appendix", 1)
    order = []
    for grp in re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", body):
        for n in (int(x) for x in grp.split(",")):
            if n not in order:
                order.append(n)
    entries = dict(re.findall(r"^\[(\d+)\] (.+)$", refs, flags=re.M))
    entries = {int(k): v for k, v in entries.items()}
    missing = set(order) - set(entries)
    uncited = set(entries) - set(order)
    assert not missing and not uncited, f"citations missing {missing}, uncited {uncited}"
    new = {old: i + 1 for i, old in enumerate(order)}
    body = re.sub(r"\[(\d+(?:\s*,\s*\d+)*)\]",
                  lambda m: "[" + ",".join(str(new[int(x)]) for x in m.group(1).split(",")) + "]", body)
    refs = "\n\n" + "\n\n".join(f"[{new[o]}] {entries[o]}" for o in order) + "\n\n"
    return body + "# References" + refs + "# Appendix" + tail


def main():
    parts = sorted(PARTS.glob("*.md"))
    md = "\n\n".join(render(p.read_text(encoding="utf-8")) for p in parts)
    md = renumber_citations(md)
    out_md = PAPER / "Manuscript_v2.md"
    out_md.write_text(md, encoding="utf-8")
    ref = PAPER / "reference.docx"
    cmd = ["pandoc", str(out_md), "-o", str(PAPER / "Manuscript_v2.docx"),
           "--resource-path", str(V2 / "outputs"), "--from", "markdown+pipe_tables"]
    if ref.exists():
        cmd += ["--reference-doc", str(ref)]
    subprocess.run(cmd, check=True)
    print("wrote", PAPER / "Manuscript_v2.docx")


if __name__ == "__main__":
    main()
