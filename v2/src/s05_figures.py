"""Step 5 - Manuscript figures (300 dpi PNG) from Gold tables and step-4 outputs."""
import json

import duckdb
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Patch

from common import BRONZE, FIGURES, TABLES, V2, V2_GOLD, canon_district

matplotlib.use("Agg")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 300, "savefig.bbox": "tight"})
INK, MUTED, ACCENT, ACCENT2 = "#1f2937", "#6b7280", "#b45309", "#1d4ed8"
R = json.loads((V2 / "outputs" / "results.json").read_text(encoding="utf-8"))


def gold(sql):
    con = duckdb.connect(str(V2_GOLD), read_only=True)
    df = con.execute(sql).df()
    con.close()
    return df


def districts():
    g = gpd.read_file(BRONZE / "gadm_shapefiles" / "gadm41_BGD_2.shp")
    g["district"] = g.NAME_2.map(canon_district)
    return g


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    ax.set_xlim(0, 100); ax.set_ylim(0, 50); ax.axis("off")
    W, GAP = 22, 3.3
    cols = [("Sources", ["BBS Yearbooks 2012–2025", "MODIS MOD13Q1 v061", "ERA5-Land daily",
                         "JRC GSW v1.4 monthly", "Sentinel-1 GRD", "GADM, WorldCover, SRTM"]),
            ("Bronze", ["Unmodified PDFs", "camelot extraction", "Earth Engine extracts",
                        "Cached per variable-year"]),
            ("Silver", ["64-district gazetteer", "Arithmetic checks", "National-total checks",
                        "Edition comparison", "Range validation", "Harvest-year keys"]),
            ("Gold (DuckDB)", ["fact_boro_panel (960)", "fact_boro_national", "dim_district",
                               "stg_* source tables", "→ analysis, dashboard"])]
    for k, (title, items) in enumerate(cols):
        x = 1 + k * (W + GAP)
        h = 7 + 5 * len(items)
        ax.add_patch(FancyBboxPatch((x, 46 - h), W, h, boxstyle="round,pad=0.4",
                                    fc="#f3f4f6", ec=MUTED, lw=0.8))
        ax.text(x + W / 2, 43, title, ha="center", weight="bold", color=INK, fontsize=8.5)
        for i, it in enumerate(items):
            ax.text(x + 1.2, 37.5 - 5 * i, it, fontsize=6.6, color=INK, va="center")
        if k < 3:
            ax.annotate("", xy=(x + W + GAP - 0.4, 30), xytext=(x + W + 0.6, 30),
                        arrowprops=dict(arrowstyle="-|>", color=ACCENT, lw=1.4))
    fig.savefig(FIGURES / "fig1_pipeline.png"); plt.close(fig)


def fig_coverage():
    p = gold("SELECT * FROM fact_boro_panel")
    vars_ = {"yield_t_ha": "BBS yield", "ndvi_peak": "NDVI", "tmean_c": "ERA5-Land",
             "jrc_monsoon_flood": "Monsoon flood (JRC)", "jrc_flash_flood": "Flash flood (JRC)",
             "s1_monsoon_flood": "Monsoon flood (S1)", "s1_flash_flood": "Flash flood (S1)"}
    m = np.array([[p[p.harvest_year == y][v].notna().mean() for y in range(2011, 2026)] for v in vars_])
    fig, ax = plt.subplots(figsize=(7, 2.6))
    ax.imshow(m, cmap="Greys", vmin=0, vmax=1.4, aspect="auto")
    ax.set_yticks(range(len(vars_)), vars_.values())
    ax.set_xticks(range(15), range(2011, 2026), rotation=45)
    ax.set_xlabel("Boro harvest year")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            ax.text(j, i, f"{m[i, j] * 64:.0f}" if m[i, j] else "", ha="center", va="center",
                    fontsize=6, color="white" if m[i, j] > 0.5 else INK)
    ax.spines[:].set_visible(False)
    fig.savefig(FIGURES / "fig2_coverage.png"); plt.close(fig)


def fig_maps():
    g = districts().merge(pd.read_csv(TABLES / "table_vulnerability_index.csv"), on="district")
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 4.4))
    g.plot("vi", ax=axs[0], cmap="YlOrRd", edgecolor="white", linewidth=0.3, legend=True,
           legend_kwds=dict(shrink=0.6, label="Vulnerability index"))
    for _, r in g[g["rank"] <= 5].iterrows():         # rank numbers; names in caption
        c = r.geometry.representative_point()
        axs[0].annotate(str(r["rank"]), (c.x, c.y), fontsize=7, ha="center", va="center",
                        color="white", weight="bold")
    colors = {"HH": "#b91c1c", "LL": "#15803d", "HL": "#f59e0b", "LH": "#60a5fa", "ns": "#e5e7eb"}
    g.plot(color=g.cluster_005.map(colors), ax=axs[1], edgecolor="white", linewidth=0.3)
    sig_fdr = g[g.cluster_fdr != "ns"]
    if len(sig_fdr):
        sig_fdr.boundary.plot(ax=axs[1], color=INK, linewidth=0.9)
    axs[1].legend(handles=[Patch(color=colors[k], label=k) for k in ["HH", "LL", "HL", "LH", "ns"]]
                  + [Patch(fc="none", ec=INK, label="FDR < 0.05")], loc="lower left", fontsize=6, frameon=False)
    for a, t in zip(axs, ["(a) Vulnerability index (top five numbered)", "(b) LISA clusters (p < 0.05)"]):
        a.set_title(t, fontsize=9, loc="left", y=1.0); a.axis("off")
    fig.savefig(FIGURES / "fig3_vulnerability_lisa.png"); plt.close(fig)


def fig_coefficients():
    labels = {"tmean_c": "Mean temperature (1 °C)", "precip_100": "Season precipitation (100 mm)",
              "hot_days": "Hot days (1 day)", "ndvi_01": "Peak NDVI (0.1)",
              "jrc_monsoon_10": "Monsoon flood, JRC (10 pp)", "jrc_flash_10": "Flash flood, JRC (10 pp)",
              "s1_monsoon_10": "Monsoon flood, S1 (10 pp)", "s1_flash_10": "Flash flood, S1 (10 pp)"}
    rows = []
    for m, r in R["regressions"].items():
        for v, c in r["coef"].items():
            rows.append(dict(model=m, var=v, b=c["b"], se=c["se"]))
    d = pd.DataFrame(rows)
    order = [v for v in labels if v in set(d["var"])]
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 4), gridspec_kw=dict(width_ratios=[1.15, 1]))
    ax = axs[0]
    offs = {"M1": -0.27, "M2": -0.09, "M3": 0.09, "M4": 0.27}
    cols = {"M1": MUTED, "M2": INK, "M3": ACCENT, "M4": ACCENT2}
    for m, dm in d.groupby("model"):
        y = [order.index(v) + offs[m] for v in dm["var"]]
        ax.errorbar(dm.b, y, xerr=1.96 * dm.se, fmt="o", ms=3.5, color=cols[m], capsize=2,
                    lw=1, label=f"{m}: {R['regressions'][m]['title']} ({R['regressions'][m]['years']})")
    ax.axvline(0, color=MUTED, lw=0.8, ls="--")
    ax.set_yticks(range(len(order)), [labels[v] for v in order]); ax.invert_yaxis()
    ax.set_xlabel("Effect on yield (t/ha), 95% CI")
    ax.set_title("(a) Yield", fontsize=9, loc="left")
    ax.legend(fontsize=5.8, frameon=False, loc="lower left", bbox_to_anchor=(0, -0.42))

    # (b) Flood effects on harvested area and production (% per 10 pp)
    ax = axs[1]
    fl = ["jrc_monsoon_10", "jrc_flash_10", "s1_monsoon_10", "s1_flash_10"]
    ap = R["regressions_area_prod"]
    for k, (tag, col, off) in enumerate([("Area", ACCENT, -0.12), ("Production", INK, 0.12)]):
        for i, v in enumerate(fl):
            m = "M3" if v.startswith("jrc") else "M4"
            c = ap[f"{tag} {m}"]["coef"][v]
            ax.errorbar(100 * c["b"], i + off, xerr=196 * c["se"], fmt="o", ms=3.5, color=col,
                        capsize=2, lw=1, label=f"log {tag.lower()}" if i == 0 else None)
    ax.axvline(0, color=MUTED, lw=0.8, ls="--")
    ax.set_yticks(range(len(fl)), [labels[v] for v in fl]); ax.invert_yaxis()
    ax.set_xlabel("Effect (%), 95% CI")
    ax.set_title("(b) Harvested area and production", fontsize=9, loc="left")
    ax.legend(fontsize=6.5, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig4_coefficients.png"); plt.close(fig)


def fig_trends():
    s = pd.read_csv(TABLES / "national_annual_series.csv", index_col=0)
    t = pd.read_csv(TABLES / "table_mann_kendall.csv").set_index("variable")
    panels = [("national_yield", "National Boro yield (t/ha)", "National Boro yield (t/ha, BBS)"),
              ("ndvi_peak", "Peak-season NDVI", "Peak-season NDVI (area-weighted)"),
              ("tmean_c", "Mean temperature (°C)", "Mean temperature (°C, area-weighted)"),
              ("hot_days", "Hot days, Tmax > 35 °C", "Hot days (area-weighted)")]
    fig, axs = plt.subplots(2, 2, figsize=(7, 4.6))
    for a, (c, lab, key) in zip(axs.ravel(), panels):
        a.plot(s.index, s[c], "o-", color=INK, ms=3, lw=1)
        r = t.loc[key]
        x = s.index.values
        a.plot(x, np.median(s[c] - r.sen_slope * x) + r.sen_slope * x, color=ACCENT, lw=1.2)
        ptxt = "p < 0.001" if r.p < 0.001 else f"p = {r.p:.3f}"
        a.set_title(f"{lab}\nSen slope {r.sen_slope:+.4f}/yr, {ptxt}", fontsize=8, loc="left")
        a.set_xticks(range(2011, 2026, 2))
    fig.tight_layout(); fig.savefig(FIGURES / "fig5_trends.png"); plt.close(fig)


def fig_flood_agreement():
    p = gold("SELECT * FROM fact_boro_panel")
    fig, axs = plt.subplots(1, 2, figsize=(7, 3.2))
    for a, (j, s, lab, key) in zip(axs, [("jrc_monsoon_flood", "s1_monsoon_flood", "Monsoon flood", "flood_overlap_monsoon"),
                                         ("jrc_flash_flood", "s1_flash_flood", "Flash flood", "flood_overlap_flash")]):
        d = p.dropna(subset=[j, s])
        a.scatter(d[j], d[s], s=6, alpha=0.5, color=INK)
        lim = max(d[j].max(), d[s].max()) * 1.05
        a.plot([0, lim], [0, lim], color=MUTED, ls="--", lw=0.8)
        o = R[key]
        a.set_title(f"{lab}, {o['years']} (n = {o['n']})\nPearson r = {o['pearson_r']:.2f}", fontsize=8, loc="left")
        a.set_xlabel("JRC (Landsat) fraction"); a.set_ylabel("Sentinel-1 fraction")
    fig.tight_layout(); fig.savefig(FIGURES / "fig6_flood_agreement.png"); plt.close(fig)


if __name__ == "__main__":
    fig_pipeline(); fig_coverage(); fig_maps(); fig_coefficients(); fig_trends(); fig_flood_agreement()
    print("figures written to", FIGURES)
