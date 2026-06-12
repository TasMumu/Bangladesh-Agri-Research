# ═══════════════════════════════════════════════════════════════════
# Bangladesh Agricultural Vulnerability Dashboard
# Climate-Driven Vulnerability of Boro Rice Yield · 64 Districts · 2001–2022
# Author: Tasnim Ahmad Mumu
# Run: streamlit run dashboard.py
# ═══════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════
# Bangladesh Agricultural Vulnerability Dashboard
# Run with: streamlit run dashboard.py
# ═══════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import duckdb
from pathlib import Path

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bangladesh Agriculture Vulnerability",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Sidebar: clean dark slate, works in both light & dark mode ── */
[data-testid="stSidebar"] {
    background: #0f1117 !important;
    border-right: 1px solid #2a2d35;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] hr { border-color: #2a2d35 !important; }

/* Nav logo block */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 4px 0 12px 0;
    border-bottom: 1px solid #2a2d35;
    margin-bottom: 16px;
}
.sidebar-logo .logo-icon {
    font-size: 2rem;
    line-height: 1;
    background: linear-gradient(135deg, #22c55e, #16a34a);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.sidebar-logo .logo-text h3 {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 700;
    color: #f1f5f9 !important;
    letter-spacing: -0.02em;
}
.sidebar-logo .logo-text p {
    margin: 2px 0 0 0;
    font-size: 0.72rem;
    color: #64748b !important;
    line-height: 1.3;
}

/* Nav section label */
.nav-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #475569 !important;
    margin: 8px 0 4px 2px;
}

/* Radio nav items */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    font-size: 0.875rem !important;
    padding: 6px 10px !important;
    border-radius: 6px !important;
    transition: background 0.15s;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #1e293b !important;
}

/* Footer caption in sidebar */
[data-testid="stSidebar"] .stCaption {
    color: #475569 !important;
    font-size: 0.7rem !important;
}

/* ── Metric cards: border-only, mode-agnostic ── */
[data-testid="stMetric"] {
    border: 1px solid rgba(100,116,139,0.25);
    border-radius: 10px;
    padding: 14px 18px;
    background: rgba(34,197,94,0.04);
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    color: #22c55e !important;
}
[data-testid="stMetricValue"] { font-size: 1.55rem !important; font-weight: 700 !important; }

/* ── Page title accent ── */
h1 { border-left: 4px solid #22c55e; padding-left: 14px; }

/* ── Plotly legend: always readable ── */
.js-plotly-plot .legend text { fill: currentColor !important; }

/* ── Tabs ── */
[data-testid="stTab"] { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Paths ──────────────────────────────────────────────────────────
ROOT   = Path(__file__).parent
SILVER = ROOT / "data/silver"
GOLD   = ROOT / "data/gold"

# ── Data loading ───────────────────────────────────────────────────
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
    # Try Silver parquet first (available on Streamlit Cloud)
    silver_geo = SILVER / "silver_districts_geo.parquet"
    if silver_geo.exists():
        gdf = gpd.read_parquet(silver_geo)

        # Rename only columns that actually exist — avoid creating duplicates
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

        cols = [c for c in ["district_name", "division_name", "geometry"]
                if c in gdf.columns]
        return gdf[cols]

    # Fallback: Bronze shapefile (local machine only)
    candidates = [
        ROOT / "data/bronze/gadm_shapefiles/bangladesh_districts_clean.shp",
        ROOT / "data/bronze/gadm_shapefiles/gadm41_BGD_2.shp",
    ]
    shp = next((p for p in candidates if p.exists()), None)
    if shp is None:
        return None
    gdf = gpd.read_file(shp)
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
    gdf = gdf.to_crs("EPSG:4326")
    cols = [c for c in ["district_name", "division_name", "geometry"]
            if c in gdf.columns]
    return gdf[cols]
    

@st.cache_data
def load_spatial_analysis():
    p = SILVER / "silver_spatial_analysis.parquet"
    if not p.exists():
        return None
    return gpd.read_parquet(p)

df_vuln  = load_vulnerability()
df_panel = load_panel()
gdf      = load_geodata()
gdf_lisa = load_spatial_analysis()

# ── Pre-compute expensive geo objects once at startup ──────────────
@st.cache_data
def build_vuln_map(_gdf, _df_vuln):
    """Merge shapefile + vulnerability table and convert to GeoJSON once."""
    if _gdf is None:
        return None, None
    gdf_no_div = _gdf.drop(columns=["division_name"], errors="ignore")
    merged = gdf_no_div.merge(_df_vuln, on="district_name", how="left")
    merged["lon"] = merged.geometry.centroid.x
    merged["lat"] = merged.geometry.centroid.y
    geojson = merged.__geo_interface__          # slow step — done once
    return merged.drop(columns="geometry"), geojson

@st.cache_data
def build_lisa_map(_gdf_lisa):
    """Reproject LISA GDF and convert to GeoJSON once."""
    if _gdf_lisa is None:
        return None, None
    gdf_wgs = _gdf_lisa.copy()
    if gdf_wgs.crs is None:
        gdf_wgs = gdf_wgs.set_crs("EPSG:3106")
    gdf_wgs = gdf_wgs.to_crs("EPSG:4326")
    gdf_wgs["cluster"] = gdf_wgs.apply(
        lambda r: r["lisa_label"] if r["lisa_sig"] == 1 else "Not significant",
        axis=1,
    )
    geojson = gdf_wgs.__geo_interface__
    return gdf_wgs.drop(columns="geometry"), geojson

vuln_df_map, vuln_geojson   = build_vuln_map(gdf, df_vuln)
lisa_df_map, lisa_geojson   = build_lisa_map(gdf_lisa)

ALL_DIVISIONS = sorted(df_panel["division_name"].dropna().unique().tolist())
ALL_TIERS     = ["High", "Medium", "Low"]
YEAR_MIN, YEAR_MAX = int(df_panel["year"].min()), int(df_panel["year"].max())

TIER_COLORS  = {"High": "#993C1D", "Medium": "#C47B2B", "Low": "#3B6D11"}
TIER_EMOJI   = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}

# ── Sidebar ────────────────────────────────────────────────────────
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
        "Navigate",
        ["Overview", "District Explorer", "Vulnerability Map",
         "Flood & Climate", "Regression Findings", "About"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("Sources: BBS · FAO · MODIS · ERA5 · BARC · JRC · GADM")
    st.caption("Spatial autocorrelation: Moran's I = 0.804***")


# ══════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════
if page == "Overview":
    st.title("Bangladesh Boro Rice — Vulnerability Dashboard")
    st.markdown(
        "Multi-source spatial research project analysing climate-driven vulnerability "
        "of Boro rice yield across **64 districts** from **2001 to 2022**."
    )

    # ── Filters ──────────────────────────────────────────────────
    with st.expander("🔽  Filters", expanded=False):
        fc1, fc2 = st.columns(2)
        with fc1:
            sel_div_ov = st.multiselect(
                "Filter by division", ALL_DIVISIONS, default=[], key="ov_div",
                placeholder="All divisions",
            )
        with fc2:
            sel_tier_ov = st.multiselect(
                "Filter by vulnerability tier", ALL_TIERS, default=[], key="ov_tier",
                placeholder="All tiers",
            )

    df_vuln_f  = df_vuln.copy()
    df_panel_f = df_panel.copy()
    if sel_div_ov:
        df_vuln_f  = df_vuln_f[df_vuln_f["division_name"].isin(sel_div_ov)]
        df_panel_f = df_panel_f[df_panel_f["division_name"].isin(sel_div_ov)]
    if sel_tier_ov:
        df_vuln_f  = df_vuln_f[df_vuln_f["vulnerability_tier"].isin(sel_tier_ov)]
        df_panel_f = df_panel_f[df_panel_f["district_name"].isin(df_vuln_f["district_name"])]

    # ── KPI cards ────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Districts shown", len(df_vuln_f))
    with c2:
        st.metric("Study period", "2001–2022")
    with c3:
        high_n = len(df_vuln_f[df_vuln_f["vulnerability_tier"] == "High"])
        st.metric("High vulnerability", f"{high_n} districts")
    with c4:
        avg_y = df_panel_f["yield_mt_ha"].mean() if len(df_panel_f) else float("nan")
        st.metric("Mean Boro yield", f"{avg_y:.2f} MT/ha")
    with c5:
        st.metric("Moran's I (global)", "0.804***")

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Vulnerability tier distribution")
        tier_counts = df_vuln_f["vulnerability_tier"].value_counts().reindex(
            ALL_TIERS, fill_value=0
        ).reset_index()
        tier_counts.columns = ["Tier", "Count"]
        fig = px.bar(
            tier_counts, x="Tier", y="Count",
            color="Tier", color_discrete_map=TIER_COLORS,
            text="Count",
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(
            showlegend=False, height=300,
            margin=dict(t=10, b=10, l=10, r=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(showgrid=True, gridcolor="#e8f5e9"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("National mean Boro yield over time")
        yearly = df_panel_f.groupby("year")["yield_mt_ha"].mean().reset_index()
        fig = px.area(
            yearly, x="year", y="yield_mt_ha",
            markers=True,
            labels={"yield_mt_ha": "Mean yield (MT/ha)", "year": "Year"},
            color_discrete_sequence=["#2e7d32"],
        )
        fig.update_traces(fill="tozeroy", fillcolor="rgba(46,125,50,0.12)")
        for yr in [2004, 2007, 2017]:
            fig.add_vline(
                x=yr, line_dash="dash", line_color="#993C1D", opacity=0.6,
                annotation_text=f"{yr}", annotation_position="top",
                annotation_font_size=11, annotation_font_color="#993C1D",
            )
        fig.update_layout(
            height=300, margin=dict(t=10, b=10, l=10, r=10),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(showgrid=True, gridcolor="#e8f5e9"),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Most vulnerable districts")
    n_show = st.slider("Show top N districts", 5, 30, 10, key="ov_topn")
    top_n = df_vuln_f.nlargest(n_show, "vulnerability_index")[
        ["district_name", "division_name", "vulnerability_index",
         "vulnerability_tier", "n_poor_ndvi_years", "mean_ndvi_boro"]
    ].reset_index(drop=True)
    top_n.index += 1
    top_n.columns = ["District", "Division", "Vuln. Index",
                     "Tier", "Poor NDVI years", "Mean NDVI (Boro)"]
    st.dataframe(
        top_n.style
        .background_gradient(subset=["Vuln. Index"], cmap="RdYlGn_r", vmin=0, vmax=1)
        .format({"Vuln. Index": "{:.3f}", "Mean NDVI (Boro)": "{:.3f}"}),
        use_container_width=True,
        height=min(40 * n_show + 60, 600),
    )


# ══════════════════════════════════════════════════════════════════
# PAGE 2 — DISTRICT EXPLORER
# ══════════════════════════════════════════════════════════════════
elif page == "District Explorer":
    st.title("District Explorer")
    st.markdown("Drill into any district's 22-year yield, NDVI, and climate record.")

    # ── Filters ──────────────────────────────────────────────────
    fcol1, fcol2, fcol3 = st.columns([1, 2, 2])
    with fcol1:
        selected_division = st.selectbox(
            "Division", ["All"] + ALL_DIVISIONS, key="de_div"
        )
    with fcol2:
        opts = (
            sorted(df_panel[df_panel["division_name"] == selected_division]["district_name"].unique())
            if selected_division != "All"
            else sorted(df_panel["district_name"].unique())
        )
        selected_district = st.selectbox("District", opts, key="de_dist")
    with fcol3:
        yr_range = st.slider(
            "Year range", YEAR_MIN, YEAR_MAX, (YEAR_MIN, YEAR_MAX), key="de_yr"
        )

    st.divider()

    # ── Vulnerability card + charts ───────────────────────────────
    left, right = st.columns([1, 3])

    with left:
        vuln_row = df_vuln[df_vuln["district_name"] == selected_district]
        if len(vuln_row):
            r    = vuln_row.iloc[0]
            tier = r["vulnerability_tier"]
            emoji = TIER_EMOJI.get(tier, "⚪")
            color = TIER_COLORS.get(tier, "#888")
            vuln_pct = int(r["vulnerability_index"] * 100)
            st.markdown(f"""
<div style="background:{color}18;border:2px solid {color};border-radius:12px;padding:16px;">
<h4 style="color:{color};margin:0 0 8px 0">{emoji} {selected_district}</h4>
<p style="margin:4px 0"><b>Division:</b> {r['division_name']}</p>
<p style="margin:4px 0"><b>Vulnerability index:</b> <span style="color:{color};font-size:1.3rem;font-weight:700">{r['vulnerability_index']:.3f}</span></p>
<p style="margin:4px 0"><b>Tier:</b> {tier}</p>
<p style="margin:4px 0"><b>Poor NDVI years:</b> {int(r['n_poor_ndvi_years'])}</p>
<p style="margin:4px 0"><b>Mean Boro NDVI:</b> {r['mean_ndvi_boro']:.3f}</p>
</div>
""", unsafe_allow_html=True)

    with right:
        d = (
            df_panel[
                (df_panel["district_name"] == selected_district) &
                (df_panel["year"] >= yr_range[0]) &
                (df_panel["year"] <= yr_range[1])
            ]
            .sort_values("year")
        )

        tab1, tab2, tab3 = st.tabs(["📈  Yield & NDVI", "🌡️  Climate", "🌊  Flood"])

        with tab1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=d["year"], y=d["yield_mt_ha"],
                name="Boro yield (MT/ha)",
                line=dict(color="#2e7d32", width=2.5),
                mode="lines+markers",
                marker=dict(size=7),
            ))
            fig.add_trace(go.Scatter(
                x=d["year"], y=d["ndvi"],
                name="NDVI",
                line=dict(color="#1565c0", width=2, dash="dot"),
                mode="lines+markers",
                marker=dict(size=6),
                yaxis="y2",
            ))
            for _, row in d[d["is_major_flood_year"] == 1].iterrows():
                fig.add_vrect(
                    x0=row["year"] - 0.4, x1=row["year"] + 0.4,
                    fillcolor="#993C1D", opacity=0.12, line_width=0,
                    annotation_text="flood", annotation_position="top left",
                    annotation_font_size=9,
                )
            fig.update_layout(
                title=f"{selected_district} — Yield & NDVI ({yr_range[0]}–{yr_range[1]})",
                yaxis=dict(
                    title=dict(text="Yield (MT/ha)", font=dict(color="#2e7d32")),
                    tickfont=dict(color="#2e7d32"),
                ),
                yaxis2=dict(
                    title=dict(text="NDVI", font=dict(color="#1565c0")),
                    tickfont=dict(color="#1565c0"),
                    overlaying="y", side="right",
                ),
                legend=dict(x=0.01, y=0.99, bgcolor="rgba(15,17,23,0.75)", font=dict(color="#e2e8f0"), bordercolor="rgba(255,255,255,0.1)", borderwidth=1),
                height=380, margin=dict(t=40, b=20, l=20, r=20),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="#e8f5e9"),
                yaxis_gridcolor="#e8f5e9",
            )
            st.plotly_chart(fig, use_container_width=True)
            if "yield_data_source" in d.columns:
                st.caption(f"Yield data sources: {d['yield_data_source'].value_counts().to_dict()}")

        with tab2:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=d["year"], y=d["precip_total_mm"],
                name="Precipitation (mm)",
                marker_color="#42a5f5", opacity=0.75,
            ))
            fig.add_trace(go.Scatter(
                x=d["year"], y=d["temp_mean_c"],
                name="Mean temp (°C)",
                line=dict(color="#e53935", width=2.5),
                mode="lines+markers",
                marker=dict(size=6),
                yaxis="y2",
            ))
            fig.update_layout(
                title=f"{selected_district} — Climate ({yr_range[0]}–{yr_range[1]})",
                yaxis=dict(
                    title=dict(text="Precipitation (mm)", font=dict(color="#1565c0")),
                    tickfont=dict(color="#1565c0"),
                ),
                yaxis2=dict(
                    title=dict(text="Temperature (°C)", font=dict(color="#c62828")),
                    tickfont=dict(color="#c62828"),
                    overlaying="y", side="right",
                ),
                height=380, margin=dict(t=40, b=20, l=20, r=20),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0")),
                xaxis_gridcolor="#e8f5e9",
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            if "flood_fraction" in d.columns:
                fig = px.bar(
                    d, x="year", y="flood_fraction",
                    color=d["is_major_flood_year"].map({0: "Normal year", 1: "Major flood year"}),
                    color_discrete_map={"Normal year": "#90caf9", "Major flood year": "#993C1D"},
                    labels={"flood_fraction": "Flood fraction", "color": ""},
                    title=f"{selected_district} — Flood fraction ({yr_range[0]}–{yr_range[1]})",
                )
                fig.update_layout(
                    height=380, margin=dict(t=40, b=20, l=20, r=20),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0")),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Flood data not available.")


# ══════════════════════════════════════════════════════════════════
# PAGE 3 — VULNERABILITY MAP
# ══════════════════════════════════════════════════════════════════
elif page == "Vulnerability Map":
    st.title("Vulnerability & Spatial Clusters")

    tab1, tab2 = st.tabs(["🗺️  Vulnerability Index", "🔴  LISA Clusters"])

    with tab1:
        if vuln_df_map is not None:
            # ── Filters (only pandas ops — no geo work) ───────────
            mc1, mc2 = st.columns([2, 1])
            with mc1:
                sel_tier_map = st.multiselect(
                    "Highlight tiers", ALL_TIERS, default=[], key="map_tier",
                    placeholder="All tiers shown",
                )
            with mc2:
                map_style = st.selectbox(
                    "Map style",
                    ["carto-positron", "carto-darkmatter", "open-street-map"],
                    key="map_style",
                )

            plot_df = vuln_df_map.copy()
            if sel_tier_map:
                # grey out non-selected — we pass custom opacity per row via a
                # colour column trick: filter the df shown on the map
                plot_df = plot_df[plot_df["vulnerability_tier"].isin(sel_tier_map)]

            fig = px.choropleth_mapbox(
                plot_df,
                geojson=vuln_geojson,          # pre-built, no recompute
                locations=plot_df.index,
                color="vulnerability_index",
                color_continuous_scale="RdYlGn_r",
                range_color=(0, 1),
                hover_name="district_name",
                hover_data={
                    "division_name":       True,
                    "vulnerability_index": ":.3f",
                    "vulnerability_tier":  True,
                    "n_poor_ndvi_years":   True,
                    "mean_ndvi_boro":      ":.3f",
                },
                mapbox_style=map_style,
                zoom=6,
                center={"lat": 23.7, "lon": 90.4},
                opacity=0.75,
                labels={"vulnerability_index": "Vulnerability Index"},
            )
            fig.update_layout(
                height=620,
                margin=dict(t=0, b=0, l=0, r=0),
                coloraxis_colorbar=dict(
                    title="Vulnerability<br>Index",
                    tickvals=[0, 0.25, 0.5, 0.75, 1],
                    ticktext=["0 (Low)", "0.25", "0.50", "0.75", "1 (High)"],
                    len=0.6,
                ),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Moran's I = 0.804 (p < 0.001) — strong positive spatial autocorrelation. "
                "Southwest cluster (Khulna + Barisal divisions) = highest vulnerability."
            )

            with st.expander("📊  District vulnerability table"):
                tbl = vuln_df_map[
                    ["district_name", "division_name", "vulnerability_index",
                     "vulnerability_tier", "n_poor_ndvi_years", "mean_ndvi_boro"]
                ].sort_values("vulnerability_index", ascending=False).reset_index(drop=True)
                tbl.index += 1
                if sel_tier_map:
                    tbl = tbl[tbl["vulnerability_tier"].isin(sel_tier_map)]
                st.dataframe(
                    tbl.style
                    .background_gradient(subset=["vulnerability_index"], cmap="RdYlGn_r", vmin=0, vmax=1)
                    .format({"vulnerability_index": "{:.3f}", "mean_ndvi_boro": "{:.3f}"}),
                    use_container_width=True,
                )
        else:
            st.error("Shapefile not found. Run Phase 3 cell 1e first.")

    with tab2:
        if lisa_df_map is not None:
            map_style2 = st.selectbox(
                "Map style",
                ["carto-positron", "carto-darkmatter", "open-street-map"],
                key="lisa_style",
            )
            color_map = {
                "HH (hotspot)":    "#993C1D",
                "LL (coldspot)":   "#0F6E56",
                "HL (outlier)":    "#EF9F27",
                "LH (outlier)":    "#85B7EB",
                "Not significant": "#D4D0C8",
            }
            hover_cols = {c: True for c in ["division_name", "vulnerability_index", "lisa_p"]
                          if c in lisa_df_map.columns}
            if "vulnerability_index" in hover_cols:
                hover_cols["vulnerability_index"] = ":.3f"
            if "lisa_p" in hover_cols:
                hover_cols["lisa_p"] = ":.3f"

            fig = px.choropleth_mapbox(
                lisa_df_map,
                geojson=lisa_geojson,          # pre-built, no recompute
                locations=lisa_df_map.index,
                color="cluster",
                color_discrete_map=color_map,
                hover_name="district_name",
                hover_data=hover_cols,
                mapbox_style=map_style2,
                zoom=6,
                center={"lat": 23.7, "lon": 90.4},
                opacity=0.82,
                labels={"cluster": "LISA Cluster"},
                category_orders={"cluster": list(color_map.keys())},
            )
            fig.update_layout(height=620, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

            lc1, lc2, lc3, lc4 = st.columns(4)
            cluster_counts = lisa_df_map["cluster"].value_counts()
            for col, label in zip([lc1, lc2, lc3, lc4],
                                  ["HH (hotspot)", "LL (coldspot)", "HL (outlier)", "LH (outlier)"]):
                col.metric(label, cluster_counts.get(label, 0))
            st.caption(
                "HH hotspots: 14 districts in southwest Bangladesh (Khulna + Barisal). "
                "LL coldspots: 10 districts in northeast and Chattogram hill tracts."
            )
        else:
            st.warning("LISA results not found. Run Phase 4 Moran's I cell first.")


# ══════════════════════════════════════════════════════════════════
# PAGE 4 — FLOOD & CLIMATE
# ══════════════════════════════════════════════════════════════════
elif page == "Flood & Climate":
    st.title("Flood Exposure and Climate Trends")

    # ── Filters ──────────────────────────────────────────────────
    with st.expander("🔽  Filters", expanded=True):
        ff1, ff2 = st.columns(2)
        with ff1:
            sel_div_fc = st.multiselect(
                "Filter by division", ALL_DIVISIONS, default=[], key="fc_div",
                placeholder="All divisions",
            )
        with ff2:
            yr_range_fc = st.slider(
                "Year range", YEAR_MIN, YEAR_MAX, (YEAR_MIN, YEAR_MAX), key="fc_yr"
            )

    df_fc = df_panel.copy()
    if sel_div_fc:
        df_fc = df_fc[df_fc["division_name"].isin(sel_div_fc)]
    df_fc = df_fc[(df_fc["year"] >= yr_range_fc[0]) & (df_fc["year"] <= yr_range_fc[1])]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Mean flood fraction by division")
        if "flood_fraction" in df_fc.columns:
            div_flood = (
                df_fc.dropna(subset=["flood_fraction"])
                .groupby("division_name")["flood_fraction"]
                .mean()
                .sort_values()
                .reset_index()
            )
            div_flood.columns = ["Division", "Mean flood fraction"]
            fig = px.bar(
                div_flood, x="Mean flood fraction", y="Division",
                orientation="h",
                color="Mean flood fraction",
                color_continuous_scale="Blues",
                text=div_flood["Mean flood fraction"].map("{:.3f}".format),
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                height=360, margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False, coloraxis_showscale=False,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis_gridcolor="#e8f5e9",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Districts experiencing major floods by year")
        if "is_major_flood_year" in df_fc.columns:
            flood_yr = (
                df_fc.groupby("year")["is_major_flood_year"]
                .sum().reset_index()
            )
            flood_yr.columns = ["Year", "Districts"]
            fig = px.bar(
                flood_yr, x="Year", y="Districts",
                color="Districts",
                color_continuous_scale="YlOrRd",
                text="Districts",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                height=360, margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False, coloraxis_showscale=False,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                yaxis_gridcolor="#e8f5e9",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("NDVI anomaly heatmap")
    st.caption("Red = below-average crop health (proxy for yield stress). Filter divisions above to zoom in.")

    ndvi_pivot = df_fc.pivot_table(
        index="district_name", columns="year", values="ndvi_anomaly", aggfunc="mean"
    )
    if not ndvi_pivot.empty:
        fig = px.imshow(
            ndvi_pivot,
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0,
            aspect="auto",
            labels={"color": "NDVI anomaly", "x": "Year", "y": "District"},
        )
        fig.update_coloraxes(colorbar_title="NDVI<br>anomaly")
        h = max(400, min(80 * len(ndvi_pivot), 800))
        fig.update_layout(height=h, margin=dict(t=10, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No NDVI data for selected filters.")


# ══════════════════════════════════════════════════════════════════
# PAGE 5 — REGRESSION FINDINGS
# ══════════════════════════════════════════════════════════════════
elif page == "Regression Findings":
    st.title("Statistical Modelling Findings")
    st.markdown(
        "Two-way fixed-effects panel regression (district + year FE). "
        "Standard errors clustered by district."
    )

    reg_path  = ROOT / "outputs/analysis/regression_results_table.csv"
    coef_path = ROOT / "outputs/analysis/fig3_regression_coefficients.png"

    if reg_path.exists():
        df_reg = pd.read_csv(reg_path)
        st.subheader("Regression results — model comparison")
        st.dataframe(df_reg, use_container_width=True)
        st.caption("\\*\\*\\* p<0.01  \\*\\* p<0.05  \\* p<0.1")
    else:
        st.warning("Regression results CSV not found — run Phase 5 first.")

    st.divider()

    if coef_path.exists():
        st.subheader("Model 2 — Coefficient plot (95% CI)")
        st.image(str(coef_path), use_container_width=True)
    else:
        st.warning("Coefficient figure not found.")

    st.divider()
    st.subheader("Key interpretation")

    interp_data = {
        "Variable":             ["NDVI anomaly", "Precipitation anomaly", "Temperature anomaly", "Flood fraction"],
        "Direction":            ["⬆ Positive", "⬆ Positive", "⬇ Negative", "⬇ Negative"],
        "Interpretation":       [
            "Higher crop health → higher yield",
            "More rain during Boro season → better yield",
            "Heat stress reduces grain filling",
            "Aman-season inundation reduces next Boro yield",
        ],
    }
    st.dataframe(pd.DataFrame(interp_data), use_container_width=True, hide_index=True)

    st.info(
        "The southwest HH-hotspot districts (Khulna, Barisal) show stronger flood "
        "coefficients than the national average, consistent with their structural "
        "flood risk classification by BARC."
    )


# ══════════════════════════════════════════════════════════════════
# PAGE 6 — ABOUT
# ══════════════════════════════════════════════════════════════════
elif page == "About":
    st.title("About this project")

    st.markdown("""
### Climate-Driven Vulnerability of Boro Rice — Bangladesh 64 Districts (2001–2022)

**Research question:**
To what extent do satellite-derived flood inundation extent and NDVI-based crop health,
combined with rainfall variability, explain district-level Boro rice yield disparities
across Bangladesh from 2001 to 2022, and which districts are most vulnerable to
compounding climate stress?
""")

    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Data sources")
        sources = {
            "Source": ["BBS Agricultural Yearbooks", "MODIS MOD13Q1 (GEE)",
                       "ERA5 (ECMWF Copernicus)", "JRC Surface Water (GEE)",
                       "BARC / HDX", "GADM v4.1", "FAO FAOSTAT"],
            "Variable": ["District Boro yield", "NDVI crop health",
                         "Temperature & precipitation", "Flood inundation fraction",
                         "Static flood risk zones", "District boundaries",
                         "National rice production"],
            "Period": ["2012–2022", "2001–2023", "2001–2023", "2001–2021",
                       "Static", "Static", "2001–2023"],
        }
        st.dataframe(pd.DataFrame(sources), use_container_width=True, hide_index=True)

    with c2:
        st.markdown("#### Key findings")
        st.markdown("""
- **Moran's I = 0.804** (p < 0.001) — strong geographic clustering of vulnerability
- **14 HH hotspot districts** in southwest Bangladesh (Khulna + Barisal)
- **10 LL coldspot districts** in northeast and Chattogram hill tracts
- NDVI anomaly and flood fraction are significant predictors of Boro yield
- Heat stress (temp anomaly) has a significant negative effect
""")
        st.markdown("#### Methodology")
        st.markdown("""
- Bronze → Silver → Gold medallion pipeline (Python · DuckDB)
- Spatial: Queen contiguity weights, Global & Local Moran's I (PySAL)
- Regression: Two-way FE panel (linearmodels), SE clustered by district
- Forecast: Facebook Prophet per district, 2023–2030
""")

    st.divider()
    st.markdown(
        "**GitHub:** [github.com/TasMumu](https://github.com/TasMumu?tab=repositories)  "
        "| **Contact:** tasnimmumu414@gmail.com"
    )
