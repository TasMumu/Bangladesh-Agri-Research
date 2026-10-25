---
title: "An Open Multi-Source Data Engineering Framework for District-Level Agricultural Vulnerability Assessment in Bangladesh"
---

Tasnim Ahmad Mumu

Department of Agronomy and Agricultural Extension, University of Rajshahi, Bangladesh

tasnimmumu414@gmail.com · ORCID 0009-0006-8346-9622 · github.com/TasMumu/Bangladesh-Agri-Research

Keywords: data engineering; reproducibility; Boro rice; Bangladesh; agricultural statistics; Sentinel-1; flash flood; vulnerability index; spatial autocorrelation; DuckDB

# Highlights

- An open Python/DuckDB pipeline builds a 64-district Boro panel from official BBS tables.
- Every yield is checked against unit identities, national totals and a second edition.
- The panel contains {{ R['n_panel'] }} observed district-years (2011–2025) and no imputed values.
- Flash floods reduce harvested Boro area and production rather than reported yield.
- Vulnerability clusters in the north-eastern haor districts under varied index weights.

# Abstract

Background: District crop statistics, satellite observations and climate reanalysis are routinely combined for agricultural monitoring, but the steps that join them are rarely documented well enough to be checked, and errors at these steps propagate into every result.

Methods: We built an open Bronze–Silver–Gold pipeline in Python and DuckDB that extracts every district Boro rice table from 14 editions of the Bangladesh Bureau of Statistics (BBS) Yearbook of Agricultural Statistics, validates each value against unit identities, printed national totals and a second edition, and aligns it by harvest year with cropland NDVI (MODIS), ERA5-Land climate, and monsoon and flash flood fractions from JRC (Landsat) and Sentinel-1. The resulting panel of {{ R['n_panel'] }} observed district-years (64 districts, 2011–2025) is used for a demonstration vulnerability index, spatial cluster analysis and two-way fixed-effects models.

Results: District sums reproduce BBS national totals in every season, and the two flood sources agree closely (r = {{ f(R['flood_overlap_monsoon']['pearson_r'], 2) }} for monsoon flooding). Within districts, no weather, NDVI or flood variable is consistently associated with reported yield, but a 10-percentage-point increase in Sentinel-1 flash flood area is associated with {{ f(-100 * AP['Area M4']['coef']['s1_flash_10']['b'], 0) }} % lower harvested area and production, as in the April 2017 haor flood, when yield was unchanged. Vulnerability is spatially clustered (Moran's I = {{ f(R['vi']['moran_I'], 2) }}), with a high–high cluster in the north-eastern haor districts.

Conclusions: Documented, validated integration changes substantive conclusions: because BBS yield is measured per harvested hectare, flood impacts must be assessed on area and production. All code, data and an interactive dashboard are openly available.
