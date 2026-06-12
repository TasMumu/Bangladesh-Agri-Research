# ═══════════════════════════════════════════════════════════════════
# Bangladesh Agricultural Vulnerability Dashboard
# Climate-Driven Vulnerability of Boro Rice · 64 Districts · 2001–2022
# Author: Tasnim Ahmad Mumu
# Run: streamlit run dashboard.py
# ═══════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import duckdb
from pathlib import Path

# ── Page config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bangladesh Agricultural Vulnerability",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global dark theme CSS ────────────────────────────────────────────
# Forces dark background on the main content area regardless of the
# user's Streamlit theme setting. This ensures legends and tooltips
# always look correct against a known dark background.
st.markdown("""
<style>
/* ── Force dark background on main area ── */
.stApp {
    background-color: #0f1117 !important;
    color: #e2e8f0 !important;
}
.main .block-container {
    background-color: #0f1117 !important;
}

/* ── Sidebar: dark slate ── */
[data-testid="stSidebar"] {
    background: #0a0d13 !important;
    border-right: 1px solid #1e2530;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] hr { border-color: #1e2530 !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    font-size: 0.875rem !important;
    padding: 7px 12px !important;
    border-radius: 6px !important;
    transition: background 0.15s;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #1a2030 !important;
}
[data-testid="stSidebar"] .stCaption {
    color: #475569 !important;
    font-size: 0.7rem !important;
}

/* ── Sidebar logo ── */
.sidebar-logo {
    display:flex; align-items:center; gap:12px;
    padding:4px 0 14px 0;
    border-bottom:1px solid #1e2530;
    margin-bottom:16px;
}
.sidebar-logo .logo-icon {
    font-size:2rem; line-height:1;
    background: linear-gradient(135deg,#22c55e,#16a34a);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}
.sidebar-logo .logo-text h3 {
    margin:0; font-size:0.95rem; font-weight:700;
    color:#f1f5f9 !important; letter-spacing:-0.02em;
}
.sidebar-logo .logo-text p {
    margin:2px 0 0; font-size:0.72rem;
    color:#64748b !important; line-height:1.3;
}
.nav-label {
    font-size:0.65rem; font-weight:700; letter-spacing:0.12em;
    text-transform:uppercase; color:#475569 !important;
    margin:8px 0 4px 2px;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    border:1px solid rgba(100,116,139,0.3);
    border-radius:10px; padding:14px 18px;
    background:rgba(34,197,94,0.06);
}
[data-testid="stMetricLabel"] {
    font-size:0.72rem !important; font-weight:700 !important;
    text-transform:uppercase !important; letter-spacing:0.07em !important;
    color:#22c55e !important;
}
[data-testid="stMetricValue"] {
    font-size:1.55rem !important; font-weight:700 !important;
    color:#f1f5f9 !important;
}

/* ── All regular text ── */
h1,h2,h3,h4,h5,p,label,span,div {
    color:#e2e8f0;
}
h1 { border-left:4px solid #22c55e; padding-left:14px; }

/* ── Tables ── */
[data-testid="stDataFrame"] {
    border:1px solid #1e2530 !important;
    border-radius:8px !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background:#141820 !important;
    border:1px solid #1e2530 !important;
    border-radius:8px !important;
}

/* ── Tabs ── */
[data-testid="stTab"] { font-weight:600; }
button[data-baseweb="tab"] {
    color:#94a3b8 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color:#22c55e !important;
    border-bottom-color:#22c55e !important;
}

/* ── Info/warning boxes ── */
[data-testid="stAlert"] { border-radius:8px !important; }

/* ── Selectbox / multiselect ── */
[data-testid="stSelectbox"] > div,
[data-testid="stMultiSelect"] > div {
    background:#141820 !important;
    border-color:#2a3040 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Paths ────────────────────────────────────────────────────────────
ROOT   = Path(__file__).parent
SILVER = ROOT / "data/silver"
GOLD   = ROOT / "data/gold"

# ── Shared Plotly style constants ────────────────────────────────────
# Dark bg, light text — always readable on the forced dark main area
LEGEND = dict(
    bgcolor="rgba(20,24,32,0.92)",
    font=dict(color="#e2e8f0", size=12),
    bordercolor="rgba(255,255,255,0.10)",
    borderwidth=1,
)
GRID     = "rgba(255,255,255,0.06)"
PLOT_BG  = dict(plot_bgcolor="#141820", paper_bgcolor="rgba(0,0,0,0)")
FONT_CLR = "#e2e8f0"
AXIS_CLR = "#64748b"

# ── Tooltip config shared across all Plotly figures ───────────────────
# Dark bg, white text, rounded corners — clean and readable
TOOLTIP_STYLE = dict(
    bgcolor="#1e2533",
    font=dict(color="#f1f5f9", size=13),
    bordercolor="#334155",
    borderwidth=1,
)

def apply_dark_tooltip(fig):
    """Apply consistent dark tooltip style to any Plotly figure."""
    fig.update_layout(hoverlabel=TOOLTIP_STYLE)
    return fig

# ── Data loading ─────────────────────────────────────────────────────
@st.cache_data
def load_vulnerability():
    con = duckdb.connect(str(GOLD / "bangladesh_agri.duckdb"), read_only=True)
    df  = con.execute("SELECT * FROM mart_vulnerability_index").df()
    con.close()
    return df

@st.cache_data
def load_panel():
    con = duckdb.connect(str(GOLD / "bangladesh_agri.duckdb"), read_only=True)
    df  = con.execute("""
        SELECT district_name, division_name, year, season,
               boro_yield_mt_ha AS yield_mt_ha,
               ndvi, ndvi_anomaly,
               precip_total_mm, precip_anomaly_mm,
               temp_mean_c, temp_anomaly_c,
               flood_fraction, is_major_flood_year,
               flood_risk_tier, yield_data_source
        FROM fact_district_season_v2
        WHERE season = 'boro' AND boro_yield_mt_ha IS NOT NULL
        ORDER BY district_name, year
    """).df()
    con.close()
    return df

@st.cache_data
def load_geodata():
    # Try Silver parquet first — available on Streamlit Cloud
    silver_geo = SILVER / "silver_districts_geo.parquet"
    if silver_geo.exists():
        gdf = gpd.read_parquet(silver_geo)
        if "district_name" not in gdf.columns:
            if "district_n" in gdf.columns:
                gdf = gdf.rename(columns={"district_n": "district_name"})
            elif "NAME_2" in gdf.columns:
                gdf = gdf.rename(columns={"NAME_2": "district_name"})
        if "division_name" not in gdf.columns:
            if "division_n" in gdf.columns:
                gdf = gdf.rename(columns={"division_n": "division_name"})
            elif "NAME_1" in gdf.columns:
                gdf = gdf.rename(columns={"NAME_1": "division_name"})
        if gdf.crs is None:
            gdf = gdf.set_crs("EPSG:4326")
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs("EPSG:4326")
        cols = [c for c in ["district_name", "division_name", "geometry"] if c in gdf.columns]
        return gdf[cols]
    # Fallback: Bronze shapefile (local only)
    for p in [ROOT / "data/bronze/gadm_shapefiles/bangladesh_districts_clean.shp",
              ROOT / "data/bronze/gadm_shapefiles/gadm41_BGD_2.shp"]:
        if p.exists():
            gdf = gpd.read_file(p)
            if "district_name" not in gdf.columns:
                gdf = gdf.rename(columns={"district_n":"district_name","NAME_2":"district_name"})
            if "division_name" not in gdf.columns:
                gdf = gdf.rename(columns={"division_n":"division_name","NAME_1":"division_name"})
            gdf = gdf.to_crs("EPSG:4326")
            return gdf[[c for c in ["district_name","division_name","geometry"] if c in gdf.columns]]
    return None

@st.cache_data
def load_spatial_analysis():
    p = SILVER / "silver_spatial_analysis.parquet"
    return gpd.read_parquet(p) if p.exists() else None

@st.cache_data
def load_slm_results():
    p = ROOT / "outputs/analysis/spatial_lag_model_results.csv"
    return pd.read_csv(p) if p.exists() else None

df_vuln  = load_vulnerability()
df_panel = load_panel()
gdf      = load_geodata()
gdf_lisa = load_spatial_analysis()
df_slm   = load_slm_results()

# ── Pre-compute geo objects once at startup ───────────────────────────
@st.cache_data
def build_vuln_map(_gdf, _df_vuln):
    if _gdf is None:
        return None, None
    gdf_clean = _gdf.drop(columns=["division_name"], errors="ignore")
    merged    = gdf_clean.merge(_df_vuln, on="district_name", how="left")
    merged["lon"] = merged.geometry.centroid.x
    merged["lat"] = merged.geometry.centroid.y
    return merged.drop(columns="geometry"), merged.__geo_interface__

@st.cache_data
def build_lisa_map(_gdf_lisa):
    if _gdf_lisa is None:
        return None, None
    g = _gdf_lisa.copy()
    if g.crs is None:
        g = g.set_crs("EPSG:3106")
    g = g.to_crs("EPSG:4326")
    g["cluster"] = g.apply(
        lambda r: r["lisa_label"] if r["lisa_sig"] == 1 else "Not significant", axis=1)
    return g.drop(columns="geometry"), g.__geo_interface__

vuln_df_map, vuln_geojson = build_vuln_map(gdf, df_vuln)
lisa_df_map, lisa_geojson = build_lisa_map(gdf_lisa)

ALL_DIVISIONS = sorted(df_panel["division_name"].dropna().unique().tolist())
ALL_TIERS     = ["High", "Medium", "Low"]
YEAR_MIN, YEAR_MAX = int(df_panel["year"].min()), int(df_panel["year"].max())
TIER_COLORS  = {"High":"#e05c3a","Medium":"#d4923a","Low":"#4ade80"}
TIER_EMOJI   = {"High":"🔴","Medium":"🟡","Low":"🟢"}

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div class="sidebar-logo">
  <div class="logo-icon">🌾</div>
  <div class="logo-text">
    <h3>BD Agri Vulnerability</h3>
    <p>Boro Rice · 64 Districts · 2001–2022</p>
  </div>
</div>
""", unsafe_allow_html=True)
    st.markdown('<p class="nav-label">Navigation</p>', unsafe_allow_html=True)
    page = st.radio(
        "nav",
        ["Overview","District Explorer","Vulnerability Map",
         "Flood & Climate","Regression Findings","About"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Sources: BBS · FAO · MODIS · ERA5 · BARC · JRC · GADM")
    st.caption("Moran's I = 0.804*** · Two-way FE + Spatial Lag Model")


# ══════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.title("Bangladesh Boro Rice — Vulnerability Dashboard")
    st.markdown(
        "Multi-source spatial research project analysing climate-driven vulnerability "
        "of Boro rice across **64 districts** · **2001–2022** · "
        "Bronze → Silver → Gold pipeline · Moran's I spatial clustering · Two-way FE regression"
    )

    with st.expander("🔽  Filters", expanded=False):
        oc1, oc2 = st.columns(2)
        with oc1:
            sel_div_ov  = st.multiselect("Division", ALL_DIVISIONS, default=[], key="ov_div",
                                         placeholder="All divisions")
        with oc2:
            sel_tier_ov = st.multiselect("Tier", ALL_TIERS, default=[], key="ov_tier",
                                         placeholder="All tiers")

    dvf = df_vuln.copy()
    dpf = df_panel.copy()
    if sel_div_ov:
        dvf = dvf[dvf["division_name"].isin(sel_div_ov)]
        dpf = dpf[dpf["division_name"].isin(sel_div_ov)]
    if sel_tier_ov:
        dvf = dvf[dvf["vulnerability_tier"].isin(sel_tier_ov)]
        dpf = dpf[dpf["district_name"].isin(dvf["district_name"])]

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Districts", len(dvf))
    c2.metric("Study period", "2001–2022")
    c3.metric("High vulnerability", f"{len(dvf[dvf['vulnerability_tier']=='High'])} districts")
    c4.metric("Mean Boro yield", f"{dpf['yield_mt_ha'].mean():.2f} MT/ha" if len(dpf) else "—")
    c5.metric("Moran's I", "0.804***")

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Vulnerability tier distribution")
        tc = dvf["vulnerability_tier"].value_counts().reindex(ALL_TIERS, fill_value=0).reset_index()
        tc.columns = ["Tier","Count"]
        fig = px.bar(tc, x="Tier", y="Count", color="Tier",
                     color_discrete_map=TIER_COLORS, text="Count",
                     custom_data=["Tier","Count"])
        fig.update_traces(
            textposition="outside",
            marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>Districts: %{y}<extra></extra>",
        )
        fig.update_layout(
            showlegend=False, height=300,
            margin=dict(t=10,b=10,l=10,r=10),
            **PLOT_BG,
            font=dict(color=FONT_CLR),
            yaxis=dict(showgrid=True, gridcolor=GRID, tickfont=dict(color=AXIS_CLR)),
            xaxis=dict(tickfont=dict(color=AXIS_CLR)),
        )
        apply_dark_tooltip(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("National mean Boro yield (2001–2022)")
        yr = dpf.groupby("year")["yield_mt_ha"].mean().reset_index()
        fig = px.area(yr, x="year", y="yield_mt_ha", markers=True,
                      labels={"yield_mt_ha":"Yield (MT/ha)","year":"Year"},
                      color_discrete_sequence=["#4ade80"])
        fig.update_traces(
            fill="tozeroy",
            fillcolor="rgba(74,222,128,0.08)",
            hovertemplate="<b>%{x}</b><br>Yield: %{y:.3f} MT/ha<extra></extra>",
        )
        for yr_flood in [2004,2007,2017]:
            fig.add_vline(x=yr_flood, line_dash="dash", line_color="#e05c3a", opacity=0.7,
                          annotation_text=f"🌊 {yr_flood}", annotation_position="top",
                          annotation_font_size=10, annotation_font_color="#e05c3a")
        fig.update_layout(
            height=300, margin=dict(t=10,b=10,l=10,r=10),
            **PLOT_BG, font=dict(color=FONT_CLR),
            yaxis=dict(showgrid=True, gridcolor=GRID, tickfont=dict(color=AXIS_CLR)),
            xaxis=dict(tickfont=dict(color=AXIS_CLR)),
        )
        apply_dark_tooltip(fig)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Most vulnerable districts")
    n_show = st.slider("Show top N", 5, 30, 10, key="ov_topn")
    top_n  = dvf.nlargest(n_show,"vulnerability_index")[
        ["district_name","division_name","vulnerability_index",
         "vulnerability_tier","n_poor_ndvi_years","mean_ndvi_boro"]
    ].reset_index(drop=True)
    top_n.index += 1
    top_n.columns = ["District","Division","Vuln. Index","Tier","Poor NDVI yrs","Mean NDVI"]
    st.dataframe(
        top_n.style
        .background_gradient(subset=["Vuln. Index"], cmap="RdYlGn_r", vmin=0, vmax=1)
        .format({"Vuln. Index":"{:.3f}","Mean NDVI":"{:.3f}"}),
        use_container_width=True,
        height=min(40*n_show+60, 600),
    )


# ══════════════════════════════════════════════════════════════════════
# PAGE 2 — DISTRICT EXPLORER
# ══════════════════════════════════════════════════════════════════════
elif page == "District Explorer":
    st.title("District Explorer")
    st.markdown("Drill into any district's 22-year record across yield, NDVI, climate, and flood exposure.")

    dc1,dc2,dc3 = st.columns([1,2,2])
    with dc1:
        sel_div = st.selectbox("Division", ["All"]+list(ALL_DIVISIONS), key="de_div")
    with dc2:
        opts = (sorted(df_panel[df_panel["division_name"]==sel_div]["district_name"].unique())
                if sel_div != "All" else sorted(df_panel["district_name"].unique()))
        sel_dist = st.selectbox("District", opts, key="de_dist")
    with dc3:
        yr_rng = st.slider("Year range", YEAR_MIN, YEAR_MAX, (YEAR_MIN, YEAR_MAX), key="de_yr")

    st.divider()
    left, right = st.columns([1,3])

    with left:
        vrow = df_vuln[df_vuln["district_name"]==sel_dist]
        if len(vrow):
            r     = vrow.iloc[0]
            tier  = r["vulnerability_tier"]
            color = TIER_COLORS.get(tier,"#888")
            emoji = TIER_EMOJI.get(tier,"⚪")
            st.markdown(f"""
<div style="background:{color}18;border:2px solid {color};border-radius:12px;padding:18px;">
  <h4 style="color:{color};margin:0 0 12px 0;font-size:1.05rem">{emoji} {sel_dist}</h4>
  <table style="width:100%;border-collapse:collapse;font-size:0.82rem;color:#cbd5e1">
    <tr><td style="padding:3px 0;opacity:0.7">Division</td>
        <td style="padding:3px 0;text-align:right;font-weight:600">{r['division_name']}</td></tr>
    <tr><td style="padding:3px 0;opacity:0.7">Vuln. index</td>
        <td style="padding:3px 0;text-align:right;font-weight:700;color:{color};font-size:1.1rem">{r['vulnerability_index']:.3f}</td></tr>
    <tr><td style="padding:3px 0;opacity:0.7">Tier</td>
        <td style="padding:3px 0;text-align:right;font-weight:600">{tier}</td></tr>
    <tr><td style="padding:3px 0;opacity:0.7">Poor NDVI yrs</td>
        <td style="padding:3px 0;text-align:right;font-weight:600">{int(r['n_poor_ndvi_years'])}</td></tr>
    <tr><td style="padding:3px 0;opacity:0.7">Mean NDVI</td>
        <td style="padding:3px 0;text-align:right;font-weight:600">{r['mean_ndvi_boro']:.3f}</td></tr>
    <tr><td style="padding:3px 0;opacity:0.7">Flood risk</td>
        <td style="padding:3px 0;text-align:right;font-weight:600">{r.get('flood_risk_tier','—')}</td></tr>
  </table>
</div>""", unsafe_allow_html=True)

    with right:
        d = (df_panel[(df_panel["district_name"]==sel_dist) &
                      (df_panel["year"]>=yr_rng[0]) &
                      (df_panel["year"]<=yr_rng[1])]
             .sort_values("year"))

        tab1, tab2, tab3 = st.tabs(["📈  Yield & NDVI","🌡️  Climate","🌊  Flood"])

        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=d["year"], y=d["yield_mt_ha"],
                name="Boro yield (MT/ha)",
                line=dict(color="#4ade80", width=2.5),
                mode="lines+markers", marker=dict(size=7),
                hovertemplate="<b>%{x}</b><br>Yield: %{y:.3f} MT/ha<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=d["year"], y=d["ndvi"],
                name="NDVI",
                line=dict(color="#60a5fa", width=2, dash="dot"),
                mode="lines+markers", marker=dict(size=6),
                yaxis="y2",
                hovertemplate="<b>%{x}</b><br>NDVI: %{y:.4f}<extra></extra>",
            ))
            for _, row in d[d["is_major_flood_year"]==1].iterrows():
                fig.add_vrect(
                    x0=row["year"]-0.4, x1=row["year"]+0.4,
                    fillcolor="#e05c3a", opacity=0.12, line_width=0,
                    annotation_text="🌊 flood", annotation_position="top left",
                    annotation_font_size=9, annotation_font_color="#e05c3a",
                )
            fig.update_layout(
                title=dict(text=f"{sel_dist} — Yield & NDVI ({yr_rng[0]}–{yr_rng[1]})",
                           font=dict(color=FONT_CLR, size=14)),
                yaxis=dict(title=dict(text="Yield (MT/ha)", font=dict(color="#4ade80")),
                           tickfont=dict(color="#4ade80"),
                           showgrid=True, gridcolor=GRID),
                yaxis2=dict(title=dict(text="NDVI", font=dict(color="#60a5fa")),
                            tickfont=dict(color="#60a5fa"),
                            overlaying="y", side="right"),
                legend=LEGEND,
                height=380, margin=dict(t=50,b=20,l=20,r=20),
                **PLOT_BG,
                xaxis=dict(showgrid=True, gridcolor=GRID, tickfont=dict(color=AXIS_CLR)),
            )
            apply_dark_tooltip(fig)
            st.plotly_chart(fig, use_container_width=True)
            if "yield_data_source" in d.columns:
                src = d["yield_data_source"].value_counts().to_dict()
                st.caption(f"Yield data sources: {src}")

        with tab2:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=d["year"], y=d["precip_total_mm"],
                name="Precipitation (mm)",
                marker_color="#60a5fa", opacity=0.75,
                hovertemplate="<b>%{x}</b><br>Precipitation: %{y:.0f} mm<extra></extra>",
            ))
            fig.add_trace(go.Scatter(
                x=d["year"], y=d["temp_mean_c"],
                name="Mean temp (°C)",
                line=dict(color="#f87171", width=2.5),
                mode="lines+markers", marker=dict(size=6),
                yaxis="y2",
                hovertemplate="<b>%{x}</b><br>Temperature: %{y:.1f} °C<extra></extra>",
            ))
            fig.update_layout(
                title=dict(text=f"{sel_dist} — Climate ({yr_rng[0]}–{yr_rng[1]})",
                           font=dict(color=FONT_CLR, size=14)),
                yaxis=dict(title=dict(text="Precipitation (mm)", font=dict(color="#60a5fa")),
                           tickfont=dict(color="#60a5fa")),
                yaxis2=dict(title=dict(text="Temperature (°C)", font=dict(color="#f87171")),
                            tickfont=dict(color="#f87171"),
                            overlaying="y", side="right"),
                legend=LEGEND,
                height=380, margin=dict(t=50,b=20,l=20,r=20),
                **PLOT_BG,
                xaxis=dict(showgrid=True, gridcolor=GRID, tickfont=dict(color=AXIS_CLR)),
            )
            apply_dark_tooltip(fig)
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            if "flood_fraction" in d.columns:
                flood_label = d["is_major_flood_year"].map({0:"Normal year",1:"Major flood year"})
                fig = px.bar(
                    d, x="year", y="flood_fraction",
                    color=flood_label,
                    color_discrete_map={"Normal year":"#3b82f6","Major flood year":"#e05c3a"},
                    labels={"flood_fraction":"Flood fraction","color":""},
                    title=f"{sel_dist} — Flood fraction ({yr_rng[0]}–{yr_rng[1]})",
                    custom_data=[d["flood_fraction"]],
                )
                fig.update_traces(
                    hovertemplate="<b>%{x}</b><br>Flood fraction: %{y:.4f}<extra></extra>",
                )
                fig.update_layout(
                    height=380, margin=dict(t=50,b=20,l=20,r=20),
                    legend=LEGEND, **PLOT_BG,
                    title=dict(font=dict(color=FONT_CLR, size=14)),
                    xaxis=dict(showgrid=True, gridcolor=GRID, tickfont=dict(color=AXIS_CLR)),
                    yaxis=dict(showgrid=True, gridcolor=GRID, tickfont=dict(color=AXIS_CLR)),
                )
                apply_dark_tooltip(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Flood data not available.")


# ══════════════════════════════════════════════════════════════════════
# PAGE 3 — VULNERABILITY MAP
# ══════════════════════════════════════════════════════════════════════
elif page == "Vulnerability Map":
    st.title("Vulnerability & Spatial Clusters")

    tab1, tab2 = st.tabs(["🗺️  Vulnerability Index","🔴  LISA Clusters"])

    with tab1:
        if vuln_df_map is not None:
            mc1,mc2 = st.columns([2,1])
            with mc1:
                sel_tier_map = st.multiselect("Highlight tiers", ALL_TIERS, default=[],
                                              key="map_tier", placeholder="All tiers shown")
            with mc2:
                map_style = st.selectbox("Map style",
                    ["carto-darkmatter","carto-positron","open-street-map"], key="map_style")

            plot_df = vuln_df_map.copy()
            if sel_tier_map:
                plot_df = plot_df[plot_df["vulnerability_tier"].isin(sel_tier_map)]

            fig = px.choropleth_mapbox(
                plot_df, geojson=vuln_geojson, locations=plot_df.index,
                color="vulnerability_index",
                color_continuous_scale="RdYlGn_r", range_color=(0,1),
                hover_name="district_name",
                hover_data={
                    "division_name":       True,
                    "vulnerability_index": ":.3f",
                    "vulnerability_tier":  True,
                    "n_poor_ndvi_years":   True,
                    "mean_ndvi_boro":      ":.3f",
                },
                mapbox_style=map_style, zoom=6,
                center={"lat":23.7,"lon":90.4}, opacity=0.78,
                labels={"vulnerability_index":"Vulnerability Index"},
                custom_data=["division_name","vulnerability_tier",
                             "n_poor_ndvi_years","mean_ndvi_boro","vulnerability_index"],
            )
            # Custom tooltip template — rich, readable, dark background
            fig.update_traces(
                hovertemplate=(
                    "<b style='font-size:14px'>%{hovertext}</b><br>"
                    "<span style='color:#94a3b8'>Division: </span>%{customdata[0]}<br>"
                    "<span style='color:#94a3b8'>Tier: </span>%{customdata[1]}<br>"
                    "<span style='color:#94a3b8'>Vulnerability index: </span>"
                    "<b>%{customdata[4]:.3f}</b><br>"
                    "<span style='color:#94a3b8'>Poor NDVI years: </span>%{customdata[2]}<br>"
                    "<span style='color:#94a3b8'>Mean Boro NDVI: </span>%{customdata[3]:.3f}"
                    "<extra></extra>"
                )
            )
            fig.update_layout(
                height=620, margin=dict(t=0,b=0,l=0,r=0),
                coloraxis_colorbar=dict(
                    title=dict(text="Vulnerability<br>Index", font=dict(color="#e2e8f0",size=12)),
                    tickvals=[0,0.25,0.5,0.75,1],
                    ticktext=["0.00 (Low)","0.25","0.50","0.75","1.00 (High)"],
                    tickfont=dict(color="#e2e8f0", size=11),
                    bgcolor="rgba(20,24,32,0.90)",
                    bordercolor="rgba(255,255,255,0.12)",
                    borderwidth=1,
                    len=0.6,
                ),
            )
            apply_dark_tooltip(fig)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Moran's I = 0.804 (z = 8.31, p < 0.001) — strong positive spatial autocorrelation. "
                "Southwest cluster (Khulna + Barisal) = highest vulnerability. "
                "Hover over any district for full details."
            )

            with st.expander("📊  Full district table"):
                tbl = vuln_df_map[
                    ["district_name","division_name","vulnerability_index",
                     "vulnerability_tier","n_poor_ndvi_years","mean_ndvi_boro"]
                ].sort_values("vulnerability_index", ascending=False).reset_index(drop=True)
                tbl.index += 1
                if sel_tier_map:
                    tbl = tbl[tbl["vulnerability_tier"].isin(sel_tier_map)]
                st.dataframe(
                    tbl.style
                    .background_gradient(subset=["vulnerability_index"],
                                         cmap="RdYlGn_r", vmin=0, vmax=1)
                    .format({"vulnerability_index":"{:.3f}","mean_ndvi_boro":"{:.3f}"}),
                    use_container_width=True,
                )
        else:
            st.error("Geodata not found — push silver_districts_geo.parquet to GitHub.")

    with tab2:
        if lisa_df_map is not None:
            map_style2 = st.selectbox("Map style",
                ["carto-darkmatter","carto-positron","open-street-map"], key="lisa_style")

            LISA_COLORS = {
                "HH (hotspot)":   "#e05c3a",
                "LL (coldspot)":  "#22c55e",
                "HL (outlier)":   "#f59e0b",
                "LH (outlier)":   "#60a5fa",
                "Not significant":"#334155",
            }
            hov = {c:True for c in ["division_name","vulnerability_index","lisa_p"]
                   if c in lisa_df_map.columns}
            if "vulnerability_index" in hov: hov["vulnerability_index"]=":.3f"
            if "lisa_p" in hov:             hov["lisa_p"]=":.4f"

            # Build custom data for rich tooltip
            cdata_cols = [c for c in
                ["division_name","vulnerability_index","lisa_p","lisa_label","lisa_sig"]
                if c in lisa_df_map.columns]

            fig = px.choropleth_mapbox(
                lisa_df_map, geojson=lisa_geojson, locations=lisa_df_map.index,
                color="cluster", color_discrete_map=LISA_COLORS,
                hover_name="district_name",
                hover_data=hov,
                mapbox_style=map_style2, zoom=6,
                center={"lat":23.7,"lon":90.4}, opacity=0.85,
                labels={"cluster":"LISA Cluster"},
                category_orders={"cluster":list(LISA_COLORS.keys())},
                custom_data=cdata_cols,
            )
            fig.update_traces(
                hovertemplate=(
                    "<b style='font-size:14px'>%{hovertext}</b><br>"
                    "<span style='color:#94a3b8'>Division: </span>%{customdata[0]}<br>"
                    "<span style='color:#94a3b8'>Cluster: </span><b>%{customdata[3]}</b><br>"
                    "<span style='color:#94a3b8'>Vulnerability index: </span>"
                    "<b>%{customdata[1]:.3f}</b><br>"
                    "<span style='color:#94a3b8'>LISA p-value: </span>%{customdata[2]:.4f}"
                    "<extra></extra>"
                )
            )
            fig.update_layout(
                height=620, margin=dict(t=0,b=0,l=0,r=0),
                legend=dict(
                    title=dict(text="LISA Cluster", font=dict(color="#e2e8f0",size=12)),
                    font=dict(color="#e2e8f0", size=12),
                    bgcolor="rgba(20,24,32,0.92)",
                    bordercolor="rgba(255,255,255,0.12)",
                    borderwidth=1,
                    itemsizing="constant",
                ),
            )
            apply_dark_tooltip(fig)
            st.plotly_chart(fig, use_container_width=True)

            lc1,lc2,lc3,lc4 = st.columns(4)
            cc = lisa_df_map["cluster"].value_counts()
            for col,lbl in zip([lc1,lc2,lc3,lc4],
                               ["HH (hotspot)","LL (coldspot)","HL (outlier)","LH (outlier)"]):
                col.metric(lbl, cc.get(lbl,0))
            st.caption(
                "HH hotspots (🔴 14 districts): Khulna + Barisal — river flood + coastal tidal convergence.  "
                "LL coldspots (🟢 10 districts): Mymensingh, Sylhet haor, Chattogram hill tracts."
            )
        else:
            st.warning("LISA results not found — push silver_spatial_analysis.parquet to GitHub.")


# ══════════════════════════════════════════════════════════════════════
# PAGE 4 — FLOOD & CLIMATE
# ══════════════════════════════════════════════════════════════════════
elif page == "Flood & Climate":
    st.title("Flood Exposure and Climate Trends")

    with st.expander("🔽  Filters", expanded=True):
        ff1,ff2 = st.columns(2)
        with ff1:
            sel_div_fc = st.multiselect("Division", ALL_DIVISIONS, default=[], key="fc_div",
                                        placeholder="All divisions")
        with ff2:
            yr_fc = st.slider("Year range", YEAR_MIN, YEAR_MAX, (YEAR_MIN, YEAR_MAX), key="fc_yr")

    dfc = df_panel.copy()
    if sel_div_fc:
        dfc = dfc[dfc["division_name"].isin(sel_div_fc)]
    dfc = dfc[(dfc["year"]>=yr_fc[0]) & (dfc["year"]<=yr_fc[1])]

    col1,col2 = st.columns(2)

    with col1:
        st.subheader("Mean flood fraction by division")
        if "flood_fraction" in dfc.columns:
            df_div = (dfc.dropna(subset=["flood_fraction"])
                      .groupby("division_name")["flood_fraction"].mean()
                      .sort_values().reset_index())
            df_div.columns = ["Division","Mean flood fraction"]
            fig = px.bar(df_div, x="Mean flood fraction", y="Division",
                         orientation="h", color="Mean flood fraction",
                         color_continuous_scale="Blues",
                         text=df_div["Mean flood fraction"].map("{:.3f}".format))
            fig.update_traces(
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Mean flood fraction: %{x:.4f}<extra></extra>",
            )
            fig.update_layout(height=360, margin=dict(t=10,b=10,l=10,r=10),
                               showlegend=False, coloraxis_showscale=False,
                               **PLOT_BG, font=dict(color=FONT_CLR),
                               xaxis=dict(gridcolor=GRID, tickfont=dict(color=AXIS_CLR)),
                               yaxis=dict(tickfont=dict(color=AXIS_CLR)))
            apply_dark_tooltip(fig)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Districts with major floods per year")
        if "is_major_flood_year" in dfc.columns:
            fy = dfc.groupby("year")["is_major_flood_year"].sum().reset_index()
            fy.columns = ["Year","Districts"]
            fig = px.bar(fy, x="Year", y="Districts",
                         color="Districts", color_continuous_scale="YlOrRd",
                         text="Districts")
            fig.update_traces(
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Districts with major flood: %{y}<extra></extra>",
            )
            fig.update_layout(height=360, margin=dict(t=10,b=10,l=10,r=10),
                               showlegend=False, coloraxis_showscale=False,
                               **PLOT_BG, font=dict(color=FONT_CLR),
                               yaxis=dict(gridcolor=GRID, tickfont=dict(color=AXIS_CLR)),
                               xaxis=dict(tickfont=dict(color=AXIS_CLR)))
            apply_dark_tooltip(fig)
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("NDVI anomaly heatmap — all districts × years")
    st.caption("Red = below-average crop health · Green = above-average · "
               "Major flood years (2004, 2007, 2017) visible as horizontal red bands.")
    pivot = dfc.pivot_table(index="district_name", columns="year",
                             values="ndvi_anomaly", aggfunc="mean")
    if not pivot.empty:
        fig = px.imshow(pivot, color_continuous_scale="RdYlGn",
                        color_continuous_midpoint=0, aspect="auto",
                        labels={"color":"NDVI anomaly","x":"Year","y":"District"})
        fig.update_coloraxes(
            colorbar_title=dict(text="NDVI<br>anomaly", font=dict(color="#e2e8f0",size=12)),
            colorbar_tickfont=dict(color="#e2e8f0", size=11),
            colorbar_bgcolor="rgba(20,24,32,0.90)",
            colorbar_bordercolor="rgba(255,255,255,0.12)",
            colorbar_borderwidth=1,
        )
        fig.update_traces(
            hovertemplate="<b>%{y}</b> · %{x}<br>NDVI anomaly: %{z:.4f}<extra></extra>",
        )
        fig.update_layout(
            height=max(400, min(80*len(pivot),800)),
            margin=dict(t=10,b=20,l=20,r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=FONT_CLR),
            xaxis=dict(tickfont=dict(color=AXIS_CLR)),
            yaxis=dict(tickfont=dict(color=AXIS_CLR)),
        )
        apply_dark_tooltip(fig)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No NDVI data for selected filters.")


# ══════════════════════════════════════════════════════════════════════
# PAGE 5 — REGRESSION FINDINGS
# ══════════════════════════════════════════════════════════════════════
elif page == "Regression Findings":
    st.title("Statistical Modelling Findings")
    st.markdown(
        "**Model:** Two-way fixed-effects panel regression (district + year FE) · "
        "SE clustered by district · "
        "**Extension:** Spatial Lag Model (GM-Lag) · Moran's I = 0.804"
    )

    reg_path  = ROOT / "outputs/analysis/regression_results_table.csv"
    coef_path = ROOT / "outputs/analysis/fig3_regression_coefficients.png"

    if reg_path.exists():
        df_reg = pd.read_csv(reg_path)
        st.subheader("Fixed-Effects Panel Regression — three-model comparison")
        st.dataframe(df_reg, use_container_width=True)
        st.caption(
            "\\*\\*\\* p<0.01  \\*\\* p<0.05  \\* p<0.1 · "
            "Within-R² = 0.025: district + year FE absorb most variance; "
            "F-stat = 6.76 (p < 0.001) confirms joint significance."
        )
    else:
        st.warning("regression_results_table.csv not found in outputs/analysis/")

    if coef_path.exists():
        st.divider()
        st.subheader("Model 2 — Coefficient plot with 95% CI")
        st.image(str(coef_path), use_container_width=True)

    # Spatial lag model results
    st.divider()
    st.subheader("Spatial Lag Model — geographic spillovers")
    if df_slm is not None:
        rho_row   = df_slm[df_slm["variable"].str.contains("W_yield", na=False)]
        coef_rows = df_slm[~df_slm["variable"].str.contains("W_yield|CONSTANT", na=False)]
        if not rho_row.empty:
            rv,rp = rho_row["coefficient"].values[0], rho_row["p_value"].values[0]
            sig   = "***" if rp<0.01 else "**" if rp<0.05 else "*" if rp<0.10 else ""
            sm1,sm2,sm3 = st.columns(3)
            sm1.metric("ρ (spatial autoregressive)", f"{rv:.4f}{sig}")
            sm2.metric("p-value", f"{rp:.4f}")
            sm3.metric("Result", "Significant clustering" if rp<0.05 else "Weak dependence")
        if not coef_rows.empty:
            coefs  = coef_rows["coefficient"].tolist()
            ses    = coef_rows["std_error"].tolist()
            labels = coef_rows["variable"].tolist()
            colors = ["#4ade80" if c>0 else "#e05c3a" for c in coefs]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=coefs, y=labels, mode="markers",
                marker=dict(color=colors, size=11, symbol="circle"),
                error_x=dict(type="data", array=[1.96*s for s in ses],
                             color="rgba(148,163,184,0.5)", thickness=1.5, width=6),
                hovertemplate="<b>%{y}</b><br>Coefficient: %{x:.4f}<extra></extra>",
            ))
            fig.add_vline(x=0, line_dash="dash", line_color="rgba(148,163,184,0.4)")
            fig.update_layout(
                title=dict(text="SLM — coefficient plot (95% CI)",
                           font=dict(color=FONT_CLR,size=13)),
                xaxis_title="Effect on Boro yield (MT/ha)",
                height=260, margin=dict(t=40,b=20,l=20,r=20),
                **PLOT_BG, showlegend=False,
                font=dict(color=FONT_CLR),
                xaxis=dict(showgrid=True, gridcolor=GRID, tickfont=dict(color=AXIS_CLR)),
                yaxis=dict(showgrid=False, tickfont=dict(color="#e2e8f0")),
            )
            apply_dark_tooltip(fig)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("spatial_lag_model_results.csv not found — run Section 4 of 03_Econometric_Modelling.ipynb")

    st.divider()
    st.subheader("Variable interpretation")
    st.dataframe(pd.DataFrame({
        "Variable":  ["NDVI anomaly","Precipitation anomaly","Temperature anomaly",
                      "Flood fraction (contemp.)","Flood fraction (lagged)"],
        "Direction": ["⬆ +1.83*** ","⬆ −0.0005 (ns)","⬆ +0.097**",
                      "⬇ −0.049 (ns)","⬇ test Model 3"],
        "Mechanism": [
            "Higher crop health → higher yield — dominant predictor",
            "Boro is irrigated; rainfall anomaly has limited direct effect",
            "Cold-stress relief in cool Boro window (Jan–May, below sterility threshold)",
            "Aman flooding → soil waterlogging → reduced Boro yield; lag tested",
            "One-season lag captures Aman→Boro temporal damage pathway",
        ],
    }), use_container_width=True, hide_index=True)

    with st.expander("📌  Note on BBS-only robustness check"):
        st.markdown("""
NDVI coefficient diverges between full sample (+1.83) and BBS-actual subsample (2012–2022).
Two mechanisms:
1. **Circularity** — NDVI constructs the pre-2012 yield proxy AND appears as regressor
2. **Trend-FE multicollinearity** — strong NDVI upward trend (τ=+0.697, p<0.001) is
   largely absorbed by year fixed effects in the short 2012–2022 window

The BBS-only coefficient is **not** a genuine negative NDVI-yield effect.
Both estimates motivate careful interpretation; the causal estimate lies between them.
        """)


# ══════════════════════════════════════════════════════════════════════
# PAGE 6 — ABOUT
# ══════════════════════════════════════════════════════════════════════
elif page == "About":
    st.title("About this project")
    st.markdown("""
### Climate-Driven Vulnerability of Boro Rice Yield
### Across Bangladesh's 64 Districts (2001–2022)

**Research question:**  
To what extent do satellite-derived flood inundation extent and NDVI-based crop health,
combined with rainfall variability, explain district-level Boro rice yield disparities
across Bangladesh from 2001 to 2022 — and which districts are most vulnerable to
compounding climate stress?
""")
    st.divider()
    col1,col2 = st.columns(2)

    with col1:
        st.markdown("#### Data sources")
        st.dataframe(pd.DataFrame({
            "Source":   ["BBS Agricultural Yearbooks","MODIS MOD13Q1 v061 (GEE)",
                         "ERA5 Monthly Means (CDS)","JRC Global Surface Water (GEE)",
                         "BARC Flood Hazard / HDX","GADM v4.1","FAO FAOSTAT"],
            "Variable": ["District Boro yield","NDVI crop health",
                         "Temperature & precipitation","Annual flood fraction",
                         "Static flood risk zones","District boundaries",
                         "National rice production"],
            "Period":   ["2012–2022","2001–2023","2001–2023","2001–2021",
                         "Static","Static","2001–2023"],
        }), use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### Key findings")
        st.markdown("""
- **Moran's I = 0.804** (z = 8.31, p < 0.001) — strong geographic clustering
- **14 HH hotspot districts** — southwest delta (Khulna + Barisal)
- **10 LL coldspot districts** — Mymensingh, Sylhet haor, Chattogram hill tracts
- **NDVI anomaly** dominant predictor (β = +1.83 MT/ha, p < 0.01)
- **Temperature anomaly** significant positive (β = +0.097, p < 0.05) — cold-stress relief
- **Yield trend:** +0.015 MT/ha/year (Mann-Kendall, p < 0.001) — technology-driven
        """)
        st.markdown("#### Methodology")
        st.markdown("""
- Data: Bronze → Silver → Gold medallion pipeline · DuckDB
- Spatial: Queen contiguity · Global & Local Moran's I (PySAL/esda)
- Econometric: Two-way FE panel regression (linearmodels) + Spatial Lag Model (spreg)
- Trend: Mann-Kendall + Sen's slope (pymannkendall)
- Scenarios: IPCC AR6 illustrative (SSP2-4.5 / SSP5-8.5)
        """)

    st.divider()
    st.markdown(
        "**GitHub:** [github.com/TasMumu](https://github.com/TasMumu?tab=repositories)  "
        "| **Contact:** tasnimmumu414@gmail.com"
    )
