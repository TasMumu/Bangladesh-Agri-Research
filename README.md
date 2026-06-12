# Climate-Driven Vulnerability of Boro Rice Yield Across Bangladesh's 64 Districts (2001–2022)

**Author:** Tasnim Ahmad Mumu  
**Contact:** tasnimmumu414@gmail.com

---

## Research Question

To what extent do satellite-derived flood inundation extent and NDVI-based crop health, combined with rainfall variability, explain district-level Boro rice yield disparities across Bangladesh from 2001 to 2022, and which districts are most vulnerable to compounding climate stress?

---

## Project Structure

```
bangladesh_agri/
├── Bangladesh_Agriculture_Pipeline.ipynb   ← Data pipeline: Bronze → Silver → Gold
├── Phase_4_geospatial_data_analysis.ipynb  ← Spatial analysis and mapping
├── Phase 5 — Statistical Modelling.ipynb   ← Panel regression, forecasting, scenarios
├── Untitled.ipynb                           ← Dashboard development
├── dashboard/
│   └── app.py                              ← Streamlit web dashboard
├── data/
│   ├── bronze/                             ← Raw data (FAOSTAT, ERA5, MODIS, BBS, GADM)
│   ├── silver/                             ← Cleaned Parquet files
│   └── gold/
│       └── bangladesh_agri.duckdb          ← Analytical database
├── outputs/
│   ├── maps/                               ← HTML maps and publication figures
│   └── analysis/                           ← Regression tables, forecast files, figures
├── docs/                                   ← Research documentation
│   ├── 01_data_pipeline.md
│   ├── 02_geospatial_analysis.md
│   ├── 03_statistical_modelling.md
│   └── 04_dashboard.md
└── requirements.txt
```

---

## Data Sources

| Source | Variable | Years |
|--------|----------|-------|
| BBS Agricultural Yearbooks | District-level Boro rice yield | 2012–2022 |
| MODIS MOD13Q1 (Google Earth Engine) | NDVI crop health (250 m, 16-day) | 2001–2023 |
| ERA5 Reanalysis (Copernicus CDS) | Monthly temperature, precipitation | 2001–2023 |
| JRC Global Surface Water (GEE) | Annual flood inundation fraction | 2001–2021 |
| BARC / HDX | Static flood risk zones | Static |
| GADM v4.1 | District boundaries (64 districts) | Static |
| FAOSTAT | National rice production benchmark | 2001–2022 |

---

## Methodology

### Data Pipeline
A Bronze–Silver–Gold medallion architecture ingests and transforms six data sources into a unified DuckDB analytical database. Missing district-level yield data for 2001–2011 (BBS records begin 2012) are gap-filled using a linear NDVI calibration approach. All yield rows carry a `yield_data_source` provenance flag for downstream robustness checks.

### Spatial Analysis
Queen contiguity spatial weights and Local Moran's I (LISA) are used to test for and identify geographic clustering in the composite vulnerability index.

### Statistical Modelling
Two-way fixed-effects panel regression with standard errors clustered by district. Three model specifications are compared. Robustness checks use the BBS-actual subsample. Non-parametric Mann-Kendall tests assess monotonic trends in national annual series.

### Forecasting
Facebook Prophet is fitted per district on the 2001–2022 Boro yield series, producing 2023–2030 projections with 95% prediction intervals.

### Scenario Simulation
IPCC AR6 projected temperature and precipitation changes for Bangladesh (SSP2-4.5 and SSP5-8.5) are applied to Model 2 regression coefficients to estimate yield outcomes under five climate scenarios.

---

## Key Findings

- **Global Moran's I = 0.804 (p = 0.001):** Agricultural vulnerability is strongly spatially clustered — high-risk districts form a contiguous southwest corridor (Khulna and Barisal divisions).
- **15 HH hotspot districts** identified by LISA represent the primary targets for climate adaptation intervention.
- **NDVI anomaly is the dominant yield predictor** within the fixed-effects framework (coef = +1.83 MT/ha, p < 0.01).
- **Boro yield increased at +0.015 MT/ha per year** over 2001–2022 (Mann-Kendall, p < 0.001), consistent with technology-driven productivity growth.
- **Climate scenario projections** suggest modest positive yield effects (+1–8%) under warming scenarios due to the positive temperature coefficient in the Boro season, though non-linear heat stress above critical thresholds is not captured by the linear model.

---

## Running the Project

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Prerequisites
- Google Earth Engine account: run `earthengine authenticate` once
- Copernicus CDS API key: configure `~/.cdsapirc`
- BBS yield CSV: place in `data/bronze/bbs/`

### 3. Execute Notebooks in Order
1. `Bangladesh_Agriculture_Pipeline.ipynb` — builds Bronze, Silver, and Gold layers
2. `Phase_4_geospatial_data_analysis.ipynb` — GIS analysis and `fact_district_season_v2`
3. `Phase 5 — Statistical Modelling.ipynb` — all statistical outputs
4. `Untitled.ipynb` — dashboard application code

### 4. Launch Dashboard
```bash
streamlit run dashboard/app.py
```

---

## Documentation

Detailed methodology documentation for each notebook is in the [`docs/`](docs/) folder:

- [01 — Data Pipeline](docs/01_data_pipeline.md)
- [02 — Geospatial Analysis](docs/02_geospatial_analysis.md)
- [03 — Statistical Modelling](docs/03_statistical_modelling.md)
- [04 — Dashboard](docs/04_dashboard.md)
