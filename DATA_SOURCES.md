# Data Sources and Access Instructions

All data sources used in this project are free and publicly accessible.
This document provides the exact access instructions for each source.

---

## 1. BBS Agricultural Yearbooks
**Provider:** Bangladesh Bureau of Statistics  
**URL:** http://bbs.gov.bd/site/page/3e838eb6-30a2-4709-be85-40484b0c16c6  
**What to download:** "Yearbook of Agricultural Statistics of Bangladesh" — one PDF per year, 2012–2022  
**How to use:** Run `bbs_extractor_final.py` on each PDF (see script for instructions)

---

## 2. MODIS MOD13Q1 v061 (NDVI)
**Provider:** NASA via Google Earth Engine  
**Dataset ID:** `MODIS/061/MOD13Q1`  
**Access:** Free GEE account at earthengine.google.com  
**Authentication:** Run `earthengine authenticate` in terminal once  
**Script:** See Section 1c of `01_Data_Engineering_Pipeline.ipynb`

---

## 3. ERA5 Monthly Reanalysis
**Provider:** ECMWF via Copernicus Climate Data Store  
**Dataset:** `reanalysis-era5-single-levels-monthly-means`  
**Access:** Free account at cds.climate.copernicus.eu  
**Authentication:** Create `~/.cdsapirc` with UID and API key  
**Script:** See Section 1d of `01_Data_Engineering_Pipeline.ipynb`

---

## 4. JRC Global Surface Water
**Provider:** European Commission JRC via Google Earth Engine  
**Dataset ID:** `JRC/GSW1_4/MonthlyHistory`  
**Access:** Same GEE account as MODIS above  
**Script:** See Section 2 of `02_Spatial_Analysis_Flood_Exposure.ipynb`

---

## 5. BARC Flood Hazard Shapefile
**Provider:** Bangladesh Agricultural Research Council via HDX  
**Dataset ID:** `7362ef2d-7282-459f-bc1b-0347076fcc12`  
**URL:** https://data.humdata.org/dataset/bangladesh-hazards  
**Access:** Direct download, no account needed  
**Script:** Downloaded automatically in Section 1 of `02_Spatial_Analysis_Flood_Exposure.ipynb`

---

## 6. GADM v4.1 Bangladesh District Boundaries
**Provider:** UC Davis GADM project  
**URL:** https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_BGD_shp.zip  
**Access:** Direct download, no account needed  
**Script:** Downloaded automatically in Section 1e of `01_Data_Engineering_Pipeline.ipynb`

---

## 7. FAO FAOSTAT
**Provider:** Food and Agriculture Organisation of the United Nations  
**Dataset:** QCL (Crops and livestock products), Bangladesh, Rice paddy  
**URL:** https://www.fao.org/faostat/en/#data/QCL  
**Access:** Bulk ZIP download, no account needed  
**Script:** Downloaded automatically in Section 1a of `01_Data_Engineering_Pipeline.ipynb`

---

## 8. World Bank Development Indicators
**Provider:** World Bank  
**API endpoint:** https://api.worldbank.org/v2/country/BD/indicator/{indicator}  
**Access:** Free REST API, no account needed  
**Script:** Downloaded automatically in Section 1b of `01_Data_Engineering_Pipeline.ipynb`
