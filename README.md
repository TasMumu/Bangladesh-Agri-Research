<div align="center">

<img src="https://upload.wikimedia.org/wikipedia/commons/f/f9/Flag_of_Bangladesh.svg" height="52" alt="Flag of Bangladesh"/>

# Climate-Driven Vulnerability of Boro Rice Yield
### Across Bangladesh's 64 Districts · 2001–2022

*A multi-source data engineering and spatial research project*

---

[![Live Dashboard](https://img.shields.io/badge/🌾_Live_Dashboard-Open_App-FF4B4B?style=for-the-badge)](https://your-app.streamlit.app)
&nbsp;
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
&nbsp;
[![DuckDB](https://img.shields.io/badge/DuckDB-0.10-FFF000?style=flat-square)](https://duckdb.org)
&nbsp;
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
&nbsp;
[![GEE](https://img.shields.io/badge/Google_Earth_Engine-4285F4?style=flat-square&logo=google&logoColor=white)](https://earthengine.google.com)
&nbsp;
[![License: MIT](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)](LICENSE)

**Author:** Tasnim Ahmad Mumu &nbsp;|&nbsp; **Last updated:** 2026

</div>

---

## Research Question

> *To what extent do satellite-derived flood inundation extent and NDVI-based crop health, combined with rainfall variability, explain district-level Boro rice yield disparities across Bangladesh from 2001 to 2022 — and which districts are most vulnerable to compounding climate stress?*

Bangladesh's Boro season — the country's most productive rice season, accounting for approximately **55% of annual output** — faces escalating climate stress from riverine flooding, rainfall variability, and rising temperatures. While national trends are documented, the spatial structure of district-level vulnerability and its climate determinants remained poorly understood, owing to fragmented data infrastructure and the absence of an integrated multi-source analytical pipeline.

This project addresses that gap by constructing the **first open, reproducible district-level agricultural vulnerability index** for all 64 districts of Bangladesh, integrating six public data sources through a transparent data engineering pipeline.

---

## Key Findings at a Glance

<table>
<tr>
<td width="50%" valign="top">

### 📍 Strong Spatial Clustering
**Global Moran's I = 0.804**  
z-statistic = 8.31 · p < 0.001

Agricultural vulnerability is **strongly geographically concentrated** — not randomly distributed. Vulnerable districts form a continuous southwest belt in the Ganges–Brahmaputra–Meghna delta zone, confirmed by both Global and Local Moran's I analysis.

</td>
<td width="50%" valign="top">

### 🔴 14 Hotspot Districts Identified
**LISA HH clusters · p < 0.05**

Patuakhali · Pabna · Chuadanga · Kushtia · Meherpur · Khulna · Magura · Rajbari · Jhenaidah · Narail · Natore · Bagerhat · Barisal · Gopalganj — all in the southwest delta, where river flooding and coastal tidal inundation converge.

</td>
</tr>
<tr>
<td valign="top">

### 📈 NDVI — Dominant Yield Predictor
**β = +1.83 MT/ha · p < 0.01**

Within-district NDVI anomaly is the single most significant predictor of Boro yield after controlling for district and year fixed effects. One unit of positive NDVI anomaly above a district's historical mean is associated with 1.83 MT/ha higher yield.

</td>
<td valign="top">

### 🌡️ Technology-Driven Yield Growth
**Sen's slope = +0.015 MT/ha/year · p < 0.001**

A significant 22-year upward trend in both yield (τ = +0.654) and NDVI (τ = +0.697) — with **no corresponding trend** in temperature or precipitation — is consistent with technology adoption (BRRI HYV varieties, irrigation expansion) rather than climate amelioration.

</td>
</tr>
</table>

---

## Project Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│  DATA SOURCES  (6 heterogeneous public sources)                          │
│  BBS PDFs · FAO FAOSTAT · MODIS GEE · ERA5 CDS · JRC GEE · GADM        │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │  Python ingestion scripts
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  BRONZE LAYER  raw files as received · CSV · JSON · NetCDF · PDF        │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │  Pandas · GeoPandas · Great Expectations
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  SILVER LAYER  cleaned · validated · Parquet                            │
│  silver_bbs_boro · silver_ndvi_districts · silver_climate_seasonal      │
│  silver_flood_fraction · silver_spatial_analysis · silver_dim_district  │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │  DuckDB SQL models
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  GOLD LAYER  DuckDB analytical database                                 │
│  fact_district_season_v2 · mart_vulnerability_index                     │
└──────────────┬──────────────────────────┬───────────────────────────────┘
               │                          │
               ▼                          ▼
  ┌────────────────────┐      ┌───────────────────────┐
  │  SPATIAL ANALYSIS  │      │  ECONOMETRIC MODEL    │
  │  Queen contiguity  │      │  Two-way FE panel     │
  │  Global Moran's I  │      │  Spatial Lag Model    │
  │  LISA clusters     │      │  Mann-Kendall trend   │
  │  Flood overlay     │      │  IPCC AR6 scenarios   │
  └──────────┬─────────┘      └──────────┬────────────┘
             └──────────┬────────────────┘
                        ▼
             ┌──────────────────────┐
             │  STREAMLIT DASHBOARD │
             │  6 interactive pages │
             │  Live public URL     │
             └──────────────────────┘
```

---

## Repository Structure

```
bangladesh-agri-research/
│
├── 📓  01_Data_Engineering_Pipeline.ipynb      # Bronze → Silver → Gold pipeline
├── 📓  02_Spatial_Analysis_Flood_Exposure.ipynb # Moran's I · LISA · flood overlay
├── 📓  03_Econometric_Modelling.ipynb           # Panel regression · SLM · MK · scenarios
│
├── 🖥️  dashboard.py                             # Streamlit dashboard (6 pages)
├── 🔧  bbs_extractor_final.py                   # BBS PDF → CSV (camelot-py)
│
├── 📄  requirements.txt
├── 📄  DATA_SOURCES.md                          # Data access instructions
├── 📄  CONTRIBUTING.md
├── 📄  LICENSE
│
├── ⚙️  .streamlit/
│   └── config.toml                              # Streamlit theme config
│
└── 📊  outputs/
    ├── maps/
    │   ├── fig1_vulnerability_flood_combined.png
    │   ├── map1_vulnerability_index.html
    │   ├── map2_flood_fraction.html
    │   └── map3_lisa_clusters.html
    └── analysis/
        ├── fig2_eda_overview.png
        ├── fig3_regression_coefficients.png
        ├── fig_mann_kendall_trends.png
        ├── fig_scenario_simulation.png
        ├── regression_results_table.csv
        ├── spatial_lag_model_results.csv
        └── regression_full_summary.txt
```

> **Note:** The `data/` directory (Bronze, Silver, Gold) is excluded from version control via `.gitignore` due to file size. The DuckDB analytical database is tracked via Git LFS.

---

## Data Sources

| # | Source | Variable | Resolution | Coverage | Access |
|---|--------|----------|-----------|---------|--------|
| 1 | **BBS Agricultural Yearbooks** | District Boro yield (area, production, MT/ha) | 64 districts | 2012–2022 | PDF extraction — `bbs_extractor_final.py` |
| 2 | **MODIS MOD13Q1 v061** | Seasonal mean NDVI | 250 m | 2001–2023 | Google Earth Engine |
| 3 | **ERA5 Monthly Means** | Temperature, precipitation | 0.25° grid | 2001–2023 | Copernicus CDS API |
| 4 | **JRC Global Surface Water** | Annual flood inundation fraction | 30 m | 2001–2021 | Google Earth Engine |
| 5 | **BARC / HDX** | Structural flood risk zones (FLOODCAT) | Vector | Static | data.humdata.org |
| 6 | **GADM v4.1** | District boundaries | Vector | Static | gadm.org |
| 7 | **FAO FAOSTAT** | National rice production (QCL) | National | 1961–2023 | Bulk ZIP download |
| 8 | **World Bank WDI** | Fertilizer, irrigation, rural population | National | 2001–2024 | REST API |

---

## Methodology

### Data Engineering

The pipeline follows the **medallion architecture** (Bronze → Silver → Gold):

- **Bronze:** Raw files stored exactly as received. No transformations — full auditability.
- **Silver:** Cleaned Parquet files. Key operations: district name canonicalisation across 6 sources (over 100 spelling variants resolved), NDVI quality filtering, seasonal ERA5 aggregation, range validation via Great Expectations.
- **Gold:** DuckDB analytical tables. `fact_district_season_v2` joins all sources into one row per district × season × year. `mart_vulnerability_index` materialises the composite vulnerability scores.

**Pre-2012 yield gap:** BBS district data is only available from 2012. For 2001–2011, yield is estimated via a per-district linear NDVI calibration (calibrated on 2012–2022). All rows carry a `yield_data_source` flag (`bbs_actual` / `ndvi_proxy` / `interpolated`) for full transparency.

### Vulnerability Index

Composite of four min-max normalised components:

| Component | Weight | Operationalisation |
|---|---|---|
| NDVI stress | **35%** | 1 − normalised mean Boro NDVI |
| Precipitation variability | **30%** | Coefficient of variation of seasonal precipitation |
| Frequency of poor years | **20%** | Fraction of years with NDVI anomaly < −0.05 |
| Heat stress | **15%** | Normalised mean seasonal temperature maximum |

Classification: **High** ≥ 0.70 · **Medium** 0.40–0.70 · **Low** < 0.40

### Spatial Autocorrelation

Queen contiguity spatial weights (row-standardised). **Global Moran's I** tests overall clustering. **Local Moran's I (LISA)** classifies each district as HH hotspot, LL coldspot, or spatial outlier (significance threshold: p < 0.05, 999 permutations).

### Econometric Model

Two-way fixed-effects panel regression:

```math
yield_{it}
=
\beta_1 \cdot \mathrm{NDVI\_anomaly}_{it}
+
\beta_2 \cdot \mathrm{Precip\_anomaly}_{it}
+
\beta_3 \cdot \mathrm{Temp\_anomaly}_{it}
+
\beta_4 \cdot \mathrm{Flood}_{it}
+
\alpha_i
+
\gamma_t
+
\varepsilon_{it}
```

where $\alpha_i$ = district fixed effects, $\gamma_t$ = year fixed effects. SE clustered by district.

A **Spatial Lag Model** (GM-Lag, `spreg`) is estimated to account for spatial dependence in residuals, with Lagrange Multiplier diagnostics guiding specification choice.

---

## Results

### Regression Results — Model 2 (preferred specification)

| Variable | Coefficient | 95% CI | p-value |
|---|---|---|---|
| **NDVI anomaly** | **+1.8281** | [0.600, 3.056] | **0.004 \*\*\*** |
| Precipitation anomaly (mm) | −0.0005 | [−0.002, 0.001] | 0.591 |
| **Temperature anomaly (°C)** | **+0.0967** | [0.009, 0.184] | **0.030 \*\*** |
| Flood fraction | −0.0486 | [−0.369, 0.271] | 0.766 |

*N = 1,115 · 56 districts · 20 years · R² (within) = 0.025 · F = 6.76 (p < 0.001)*  
*The low within-R² reflects that district + year FE absorb the large majority of total variance; the F-statistic confirms joint significance of climate regressors.*

### Mann-Kendall Trend Test (2001–2022, national annual means)

| Variable | Trend | Kendall's τ | Sen's slope | p-value |
|---|---|---|---|---|
| Boro yield (MT/ha) | **↑ Increasing** | +0.654 | **+0.0151/yr** | < 0.001 \*\*\* |
| NDVI | **↑ Increasing** | +0.697 | +0.0042/yr | < 0.001 \*\*\* |
| Mean temperature (°C) | No trend | −0.086 | −0.012/yr | 0.608 |
| Total precipitation (mm) | No trend | +0.010 | +0.020/yr | 0.976 |

### IPCC AR6 Illustrative Scenarios (linear model applied to climate deltas)

| Scenario | Projected yield (MT/ha) | vs baseline | % change |
|---|---|---|---|
| Baseline (2015–2022) | 4.029 | — | — |
| SSP2-4.5 (2030) | 4.069 | +0.040 | +1.01% |
| SSP2-4.5 (2050) | 4.131 | +0.102 | +2.56% |
| SSP5-8.5 (2050) | 4.205 | +0.176 | +4.40% |
| SSP5-8.5 (2080) | 4.342 | +0.313 | +7.86% |

> **Limitation note:** These are illustrative scenarios applying historical linear regression coefficients to projected climate deltas — not process-based crop model projections. Non-linear heat stress above spikelet sterility thresholds (~35°C) is not captured and represents the primary uncertainty under SSP5-8.5 (2080).

---

## Dashboard

The Streamlit dashboard (`dashboard.py`) provides an interactive interface for exploring all research outputs across **six pages**:

| Page | Content |
|---|---|
| **Overview** | Project KPIs, national yield trend, vulnerability tier distribution, filterable top-N table |
| **District Explorer** | Per-district 22-year yield + NDVI, climate, and flood time series with year-range slider |
| **Vulnerability Map** | Interactive choropleth of vulnerability index + LISA spatial cluster map |
| **Flood & Climate** | Flood fraction by division, major flood year timeline, NDVI anomaly heatmap |
| **Regression Findings** | Three-model comparison table, coefficient plot, Spatial Lag Model results, BBS robustness note |
| **About** | Data sources, methodology summary, key findings, contact |

**Live app:** [your-app.streamlit.app](https://your-app.streamlit.app)

---

## Reproducing This Project

### 1. Clone and install

```bash
git clone https://github.com/TasMumu/bangladesh-agri-research.git
cd bangladesh-agri-research
pip install -r requirements.txt
```

### 2. Authenticate external data services (one time each)

```bash
# Google Earth Engine
earthengine authenticate

# Copernicus CDS — create ~/.cdsapirc with your UID and API key
# Instructions: https://cds.climate.copernicus.eu/api-how-to
```

### 3. Run notebooks in order

| Step | Notebook | Approx. time | Notes |
|---|---|---|---|
| 1 | `01_Data_Engineering_Pipeline.ipynb` | 2–3 hours | GEE + ERA5 downloads cache locally |
| 2 | `02_Spatial_Analysis_Flood_Exposure.ipynb` | 30 min | Requires GEE for JRC flood extraction |
| 3 | `03_Econometric_Modelling.ipynb` | 20 min | Reads from DuckDB only |

Each notebook reads from `data/` and writes outputs back to `data/silver/`, `data/gold/`, and `outputs/`. No variables are passed between notebooks — everything communicates through disk.

### 4. Launch the dashboard

```bash
streamlit run dashboard.py
```

The dashboard connects to `data/gold/bangladesh_agri.duckdb` and `data/silver/*.parquet` relative to its own directory.

---

## Limitations

| # | Limitation | Impact |
|---|---|---|
| 1 | BBS district data available only from 2012; 2001–2011 uses NDVI calibration proxy | NDVI coefficient inflated in full-sample regression — addressed via BBS-only robustness check |
| 2 | JRC flood data excludes 2022 (incomplete in GEE at extraction time) | Flood time series covers 2001–2021 only |
| 3 | Linear regression framework | Non-linear heat stress above ~35°C not captured — relevant under SSP5-8.5 (2080) |
| 4 | Aman-season flood fraction as Boro proxy | Temporal mismatch attenuates flood coefficient — lagged specification tested in Model 3 |
| 5 | Seven districts excluded from spatial weights | No contiguous neighbours in projected CRS; reported in methodology |

---

## Citation

If you use this project or any of its outputs, please cite:

```bibtex
@misc{mumu2026bangladesh,
  author    = {Mumu, Tasnim Ahmad},
  title     = {Climate-Driven Vulnerability of Boro Rice Yield Across
               Bangladesh's 64 Districts (2001--2022)},
  year      = {2026},
  publisher = {GitHub},
  journal   = {GitHub Repository},
  url       = {https://github.com/TasMumu/bangladesh-agri-research}
}
```

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.  
All data sources are subject to their respective licences (FAO, BBS, ECMWF, NASA, GADM).

---

<div align="center">

Made with 🌾 in Bangladesh

**[Tasnim Ahmad Mumu](mailto:tasnimmumu414@gmail.com)** · [GitHub](https://github.com/TasMumu)

</div>
