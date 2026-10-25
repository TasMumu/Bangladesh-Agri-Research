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
- The panel contains 960 observed district-years (2011–2025) and no imputed values.
- Flash floods reduce harvested Boro area and production rather than reported yield.
- Vulnerability clusters in the north-eastern haor districts under varied index weights.

# Abstract

Background: District crop statistics, satellite observations and climate reanalysis are routinely combined for agricultural monitoring, but the steps that join them are rarely documented well enough to be checked, and errors at these steps propagate into every result.

Methods: We built an open Bronze–Silver–Gold pipeline in Python and DuckDB that extracts every district Boro rice table from 14 editions of the Bangladesh Bureau of Statistics (BBS) Yearbook of Agricultural Statistics, validates each value against unit identities, printed national totals and a second edition, and aligns it by harvest year with cropland NDVI (MODIS), ERA5-Land climate, and monsoon and flash flood fractions from JRC (Landsat) and Sentinel-1. The resulting panel of 960 observed district-years (64 districts, 2011–2025) is used for a demonstration vulnerability index, spatial cluster analysis and two-way fixed-effects models.

Results: District sums reproduce BBS national totals in every season, and the two flood sources agree closely (r = 0.94 for monsoon flooding). Within districts, no weather, NDVI or flood variable is consistently associated with reported yield, but a 10-percentage-point increase in Sentinel-1 flash flood area is associated with 24 % lower harvested area and production, as in the April 2017 haor flood, when yield was unchanged. Vulnerability is spatially clustered (Moran's I = 0.43), with a high–high cluster in the north-eastern haor districts.

Conclusions: Documented, validated integration changes substantive conclusions: because BBS yield is measured per harvested hectare, flood impacts must be assessed on area and production. All code, data and an interactive dashboard are openly available.


# 1. Introduction

## 1.1 Why data engineering matters for agricultural monitoring

Agricultural monitoring increasingly depends on combining government crop statistics with satellite observations and climate reanalysis. These sources arrive on different schedules, in different formats and at different spatial resolutions, and the steps that join them (table extraction, name matching, temporal alignment, quality control) are rarely reported in enough detail to be audited or repeated. Errors introduced at these steps propagate silently into every downstream model. Reproducible, documented pipelines that make each step inspectable are therefore a precondition for trustworthy district-scale analysis, and the same principles that underpin open research data in general [1] apply directly to agricultural statistics.

Bangladesh is a demanding test case. Rice is the dominant staple, and the irrigated dry-season Boro crop supplies a little over half of national rice production; BBS estimates Boro output at 21.3 million tonnes of husked rice in 2024-25 [2]. District statistics are published each year in the Yearbook of Agricultural Statistics of the Bangladesh Bureau of Statistics (BBS) as PDF tables whose layout, district spellings and regional groupings change between editions [2,3]. Satellite and reanalysis products, by contrast, are distributed as gridded time series that must be aggregated to the same 64 districts and aligned to the Boro calendar, which spans two calendar years.

## 1.2 Related work

District-level studies of Boro rice in Bangladesh have used national time series [4], BBS district statistics for trend analysis [5], or satellite vegetation indices for crop monitoring and yield forecasting [6,7]. Multi-source pipelines for crop-yield prediction have recently been proposed [8], but they target field-scale machine learning rather than auditable integration of official statistics. Composite vulnerability indices are widely used for agricultural risk screening [9,10], yet their sensitivity to weighting choices is rarely tested [11]. Floods affect Boro through two distinct pathways: monsoon (Aman-season) inundation in the months before planting, and pre-harvest flash floods, which in April 2017 destroyed rice worth an estimated US$450 million in the north-eastern haor wetlands [12]. Optical flood records such as the JRC Global Surface Water dataset [13] are limited by monsoon cloud cover, whereas Sentinel-1 synthetic aperture radar observes through cloud and has been used operationally for flood mapping in Bangladesh [14].

## 1.3 Objective and contributions

This paper presents an open data engineering framework that integrates BBS district yields with satellite, flood and climate data for all 64 districts of Bangladesh, and validates it with an agricultural vulnerability case study of Boro rice. The emphasis is on the pipeline: its architecture, the checks that make each value traceable to its source, and its transferability. The contributions are:

- an open Bronze–Silver–Gold pipeline in Python and DuckDB that extracts and validates every BBS district Boro table published in the 2012–2025 yearbook editions, yielding a complete panel of 64 districts × 15 seasons (Boro harvest years 2011–2025) built only from observed values;
- a documented, harvest-year-aligned set of district covariates: peak-season NDVI over cropland, season climate from ERA5-Land, and separate monsoon and flash flood fractions from JRC (Landsat) and Sentinel-1;
- a demonstration vulnerability index with an explicit weight-sensitivity analysis, spatial cluster detection, and panel models that serve as a validation of the integrated data rather than as the paper's primary contribution;
- an interactive dashboard that reads directly from the analytical warehouse.

# 2. Materials and methods

## 2.1 Study area and crop calendar

Bangladesh (147,570 km²) is divided into 64 districts in eight divisions. Boro rice is transplanted from December to February and harvested from late April to May, and is irrigated mainly from groundwater. Throughout this paper a Boro season is identified by its harvest year t: the crop grown from November of year t−1 to May of year t, which BBS reports as crop year "(t−1)–t". All covariates are aligned to this definition (Section 2.5). District boundaries are taken from GADM v4.1; no district boundary changed during the study period.

## 2.2 Data sources

Table 1 lists the sources. All are public. No yield value is estimated, interpolated or modelled; a district-year enters the analysis only if BBS printed it.

Table 1. Data sources.

| Source | Variable(s) | Resolution | Period used | Access |
|---|---|---|---|---|
| BBS Yearbook of Agricultural Statistics, 2012–2025 editions [2,3] | District Boro area, yield and production (husked rice) | 64 districts | Crop years 2010-11 to 2024-25 | bbs.gov.bd (PDF) |
| MODIS MOD13Q1 v061 [15] | NDVI, 16-day composites | 250 m | 2011–2025 | Google Earth Engine [16] |
| ESA WorldCover v200 [17] | Cropland mask | 10 m | 2021 | Google Earth Engine |
| ERA5-Land daily aggregates [18] | 2 m temperature, daily maximum, precipitation | 0.1° | Nov 2010 – May 2025 | Google Earth Engine |
| JRC Global Surface Water v1.4, monthly history [13] | Monthly water presence | 30 m | 2010–2021 | Google Earth Engine |
| Sentinel-1 GRD, IW, VV [19] | Backscatter for water detection | 10 m (analysed at 60 m) | 2015–2025 | Google Earth Engine |
| SRTM v3 [20] | Slope mask for radar water detection | 30 m | Static | Google Earth Engine |
| GADM v4.1 | District boundaries | Vector | Static | gadm.org |

## 2.3 Pipeline architecture

The pipeline follows the Bronze–Silver–Gold (medallion) layering used in lakehouse systems [21] and stores analytical tables in DuckDB, an embedded analytical database [22] (Figure 1). Bronze holds sources exactly as received: the yearbook PDFs and the Earth Engine district extracts, cached per variable and year. Silver holds one validated table per source keyed on district and harvest year. Gold holds the integrated panel and the tables read by the analyses and the dashboard. Each step is a separate script, so any table can be regenerated from the layer below, and the full pipeline runs with a single command.

Figure 1. Pipeline architecture. Sources are stored unmodified (Bronze), validated and aligned to district and harvest year (Silver), and integrated into DuckDB tables (Gold) that feed the analyses and the dashboard.

![](figures/fig1_pipeline.png)

## 2.4 Extraction and validation of BBS yields

The district table "Estimates of Total Boro (Local + HYV + Hybrid)" was located in each of the 14 yearbook editions and read with camelot (lattice mode). Each edition prints two crop years, so every year from 2011-12 onward appears in two editions. District names were harmonised to a single gazetteer of 64 districts; across editions, BBS uses older spellings (for example Jessore, Comilla, Bogra) and transliteration variants. The 2012 and 2013 editions group districts under the former greater-district regions; five of these regions (Bandarban, Khagrachhari, Rangamati, Mymensingh and Tangail) contain a single present-day district and print no separate district row, so the region row is that district's estimate.

Three checks were applied to every row. First, each row reports area in acres and hectares, yield in maunds per acre and tonnes per hectare, and production in tonnes; a row is accepted only if the unit conversions agree (within 1–2 %) and area × yield reproduces production. Second, the sum of district production in each edition and year is compared with the national total printed in the same table. Third, values for years printed in two editions are compared, and the later edition is used. The outcome of these checks is reported in Section 3.1.

## 2.5 Covariates

All covariates are district means over the district polygon and are aligned to harvest year t (Table 2).

Table 2. Temporal alignment of variables to Boro harvest year t.

| Variable | Source | Window for harvest year t |
|--------------------------|------------------------|--------------------------|
| Boro yield | BBS crop year (t−1)–t | Harvest Apr–May t |
| Peak-season NDVI | MODIS composites | Jan–Apr t |
| Mean temperature, mean daily maximum, season precipitation | ERA5-Land daily | Nov t−1 – May t |
| Hot days (Tmax > 35 °C) | ERA5-Land daily | Mar–May t |
| Monsoon flood fraction | JRC monthly / Sentinel-1 | Jun–Oct t−1, net of Jan–Mar t−1 water |
| Flash flood fraction | JRC monthly / Sentinel-1 | Apr–May t, net of Jan–Mar t water |

Peak-season NDVI is the mean of MOD13Q1 16-day composites from January to April of year t, covering the vegetative to grain-filling stages of Boro. Only pixels with the SummaryQA flag at 0 or 1 are used, and only cells in which cropland (WorldCover class 40) covers more than half of the 250 m cell.

Mean temperature and mean daily maximum temperature are averaged over November t−1 to May t; season precipitation is the total over the same months. Hot days count the days from March to May of year t on which the daily maximum temperature exceeds 35 °C, the approximate threshold above which spikelet fertility in rice declines during flowering [23,24].

The monsoon flood fraction is the share of district area observed as water in any month from June to October of year t−1 but not as water in January–March of year t−1. Subtracting dry-season water excludes permanent rivers and water bodies, so the variable measures seasonal inundation before the Boro crop is planted. The flash flood fraction is the share of district area observed as water in April or May of year t but not in January–March of year t, which captures inundation during the Boro harvest window.

Both flood fractions are computed from two sources. From JRC monthly water history (Landsat, 30 m) they are available for harvest years 2011–2022 (monsoon) and 2011–2021 (flash), since the record ends in December 2021. From Sentinel-1 they are available for 2016–2025 (monsoon) and 2015–2025 (flash). For Sentinel-1, monthly median VV backscatter was smoothed with a 50 m median filter and classified as water below −18 dB, a threshold in the range used for Bangladesh floodplains [14,25], with slopes above 5° excluded. Because the two sensors differ in sensitivity and cloud limitation, the two series are kept as separate variables and are never spliced; their agreement is reported where they overlap.

## 2.6 Vulnerability index

The demonstration index combines five components, each min–max normalised across districts so that higher values mean greater vulnerability (Table 3). Two describe the sensitivity of Boro production (low mean yield and year-to-year production instability) and three describe exposure (monsoon flooding, flash flooding and heat). Instability is measured on production rather than yield because BBS yield is reported per harvested hectare: a crop destroyed before harvest reduces harvested area and production but not the reported yield (Section 3.4). Equal weights are used as the baseline because there is no agreed basis for preferring one component over another [26]. Weight sensitivity is assessed in two ways: by recomputing the index with each component omitted, and by drawing 10,000 weight vectors uniformly from the simplex (flat Dirichlet) and recording, for each district, the share of draws in which it ranks in the top ten [27]. Rankings rather than fixed tier thresholds are reported.

Table 3. Vulnerability index components (all computed from observed data).

| Component | Definition | Period |
|---|---|---|
| Low yield | Negative of mean BBS Boro yield | 2011–2025 |
| Production instability | Standard deviation of linearly detrended log BBS production | 2011–2025 |
| Monsoon flood exposure | Mean JRC monsoon flood fraction | 2011–2021 |
| Flash flood exposure | Mean JRC flash flood fraction | 2011–2021 |
| Heat exposure | Mean number of hot days (Tmax > 35 °C, March–May) | 2011–2025 |

## 2.7 Spatial autocorrelation

Spatial weights use fuzzy contiguity: districts are neighbours if their boundaries, buffered by 100 m, touch. This avoids spurious islands caused by slivers between GADM polygons and gives every district at least one neighbour. Weights are row-standardised. Global Moran's I [28] is tested with 9,999 random permutations, so the smallest attainable pseudo p-value is 0.0001. Local indicators of spatial association (LISA) [29] classify districts as high–high, low–low, high–low or low–high at pseudo p < 0.05; because 64 local tests are performed, clusters that survive a Benjamini–Hochberg false discovery rate (FDR) correction [30] are also reported. Spatial statistics were computed with the PySAL libraries libpysal and esda [31].

## 2.8 Panel models

The panel models test whether the integrated covariates relate to observed yields in the expected directions, which validates the alignment of the data. The specification is

yield(i,t) = β′X(i,t) + α(i) + γ(t) + ε(i,t),

where α(i) are district fixed effects, γ(t) are harvest-year fixed effects and X contains the covariates. District effects absorb time-invariant differences such as soils and irrigation infrastructure; year effects absorb shocks common to all districts, including national technology and price changes. Four models are estimated with yield as the outcome: weather only (M1); weather plus peak-season NDVI (M2); weather plus JRC flood fractions for 2011–2021 (M3); and weather plus Sentinel-1 flood fractions for 2016–2025 (M4). NDVI is reported in a separate model because it is itself an outcome of weather and management, so including it changes the interpretation of the weather coefficients [32]. Because BBS yield is measured on harvested area, models M1, M3 and M4 are also estimated with the natural logarithm of harvested area and of production as outcomes; their coefficients, multiplied by 100, approximate percentage changes.

Standard errors are clustered by district. Because neighbouring districts share weather, Driscoll–Kraay standard errors, which are robust to cross-sectional and serial correlation [33], are reported alongside. The R² reported is the within R² of the two-way demeaned model. Residual spatial dependence is tested with Moran's I on the M2 residuals for each harvest year. Coefficients are interpreted as within-district associations, not causal effects [32,34]. Estimation used linearmodels [35].

## 2.9 Trend analysis

Monotonic trends in national Boro yield (BBS national totals) and in area-weighted national means of the covariates were tested with the Mann–Kendall test [36,37] using the Hamed–Rao variance correction for serial correlation [38], with Sen's slope as the trend magnitude [39]. District-level yield trends were tested in the same way, with FDR correction across the 64 districts.


# 3. Results

## 3.1 Pipeline outputs and data quality

The pipeline parsed 1,726 district rows from the 14 yearbook editions (28 edition–crop-year tables). Of these, 4 failed the arithmetic identities, all in the 2012-13 columns of the 2013 edition; the same year is printed consistently in the 2014 edition, which is used. In 24 of the 28 edition–year tables all 64 district rows were parsed; in the remaining four (the 2015 and 2018 editions, where part of the table did not parse) the same crop years are complete in another edition. Wherever a complete table prints a national total (18 tables), the sum of district production equals it to within 0.001 %. For the two crop years whose tables print no national row, the district sums agree with the totals quoted in the yearbook text: 18,616,780 t against "186.17 lac metric tons" for 2010-11 (2012 edition), and 20,185,943 t against "201,85,945 metric tons" for 2021-22 (2022 edition). Of the 766 district-years printed in two editions, 6 differ, each by at most 1 ha of area, consistent with rounding. The result is a complete panel of 960 district-years with no missing yields (Table 4, Figure 2), and each row records the edition and page from which it was read.

Table 4. Extraction and validation of BBS district Boro estimates by crop year.

| Crop year | Harvest year | Editions | Districts | Rows failing checks | Gap to national total | Edition used |
|---------|---------|----------|---------|---------|------------------|---------|
| 2010-11 | 2011 | 2012 | 64 | 0 | matches text total | 2012 |
| 2011-12 | 2012 | 2012, 2013 | 64 | 0 | < 0.001 % | 2013 |
| 2012-13 | 2013 | 2013, 2014 | 64 | 4 | < 0.001 % | 2014 |
| 2013-14 | 2014 | 2014, 2015 | 64 | 0 | < 0.001 % | 2015 |
| 2014-15 | 2015 | 2015, 2016 | 64 | 0 | < 0.001 % | 2016 |
| 2015-16 | 2016 | 2016, 2017 | 64 | 0 | < 0.001 % | 2017 |
| 2016-17 | 2017 | 2017, 2018 | 64 | 0 | < 0.001 % | 2018 |
| 2017-18 | 2018 | 2018, 2019 | 64 | 0 | < 0.001 % | 2019 |
| 2018-19 | 2019 | 2019, 2020 | 64 | 0 | < 0.001 % | 2020 |
| 2019-20 | 2020 | 2020, 2021 | 64 | 0 | < 0.001 % | 2021 |
| 2020-21 | 2021 | 2021, 2022 | 64 | 0 | < 0.001 % | 2022 |
| 2021-22 | 2022 | 2022, 2023 | 64 | 0 | matches text total | 2023 |
| 2022-23 | 2023 | 2023, 2024 | 64 | 0 | < 0.001 % | 2024 |
| 2023-24 | 2024 | 2024, 2025 | 64 | 0 | < 0.001 % | 2025 |
| 2024-25 | 2025 | 2025 | 64 | 0 | < 0.001 % | 2025 |

Figure 2. Number of districts with observed data for each variable and Boro harvest year.

![](figures/fig2_coverage.png)

The two flood sources agree closely where they overlap (Figure 3). For harvest years 2016-2022, the district monsoon flood fractions from JRC and Sentinel-1 have a Pearson correlation of 0.94 (n = 448) and similar means (8.1 % and 8.5 % of district area). Flash flood fractions agree less closely (r = 0.87, n = 384), as expected for a short April–May window in which a single cloud-free Landsat scene can decide whether flooding is observed.

Figure 3. Agreement between JRC (Landsat) and Sentinel-1 flood fractions for the same districts and harvest years. Dashed line: 1:1.

![](figures/fig6_flood_agreement.png)

## 3.2 Descriptive statistics

Table 5 summarises the panel. District Boro yield averaged 4.014 t/ha of husked rice (SD 0.448), ranging from 2.083 t/ha (Patuakhali, 2016) to 5.375 t/ha (Gopalganj, 2024). National yield, computed from the district totals, rose from 3.903 t/ha in 2011 to 4.361 t/ha in 2025. Monsoon flooding covered on average 7.8 % (JRC) to 8.3 % (Sentinel-1) of district area, and flash flooding about 1.4 % in both sources, with long right tails driven by the north-eastern haor districts.

Table 5. Descriptive statistics (district-year observations).

| Variable | Harvest years | N | Mean | SD | Min | Max |
|--------------------------|---------|---------|---------|---------|---------|---------|
| Boro yield (t/ha, husked rice) | 2011-2025 | 960 | 4.014 | 0.448 | 2.083 | 5.375 |
| Boro area (ha) | 2011-2025 | 960 | 74,844 | 57,574 | 230.000 | 266,243 |
| Peak-season NDVI (Jan–Apr) | 2011-2025 | 960 | 0.534 | 0.047 | 0.342 | 0.631 |
| Mean temperature (°C) | 2011-2025 | 960 | 23.448 | 0.838 | 21.305 | 25.584 |
| Mean daily maximum temperature (°C) | 2011-2025 | 960 | 28.661 | 0.742 | 26.662 | 30.774 |
| Season precipitation (mm) | 2011-2025 | 960 | 539.002 | 253.119 | 118.955 | 2,165 |
| Hot days, Tmax > 35 °C (Mar–May) | 2011-2025 | 960 | 13.502 | 12.482 | 0.000 | 51.328 |
| Monsoon flood fraction, JRC | 2011-2022 | 768 | 0.078 | 0.101 | 0.000 | 0.646 |
| Flash flood fraction, JRC | 2011-2021 | 704 | 0.014 | 0.042 | 0.000 | 0.439 |
| Monsoon flood fraction, Sentinel-1 | 2016-2025 | 640 | 0.083 | 0.103 | 0.000 | 0.646 |
| Flash flood fraction, Sentinel-1 | 2016-2025 | 640 | 0.014 | 0.033 | 0.000 | 0.447 |

## 3.3 Vulnerability index and spatial clustering

The index ranges from 0.104 (Noakhali) to 0.578 (Sunamganj). The ten highest-ranked districts are listed in Table 6. They fall into three groups: the north-eastern haor districts (Sunamganj, Kishoreganj, Sylhet, Habiganj, Netrokona), where flood exposure dominates; the coastal districts Patuakhali and Barguna, where low and unstable yields on a small Boro area dominate; and western districts (Chapai Nawabganj, Meherpur), where heat exposure dominates. Brahmanbaria combines moderate flood exposure with moderate yield.

The ranking is moderately robust to weighting. Across 10,000 random weight vectors, the median Spearman correlation with the equal-weight ranking is 0.80 (5th percentile 0.51). Of the ten top-ranked districts, 9 remain in the top ten in at least half of the draws; the exception is Meherpur (47 %). Omitting one component at a time gives Spearman correlations of 0.60–0.97 with the baseline and retains 6–8 of the top ten; the heat component has the largest influence because it is negatively correlated with the flood components.

Table 6. The ten highest-ranked districts. Flood columns are mean JRC fractions (2011–2021); the top-10 share is the percentage of 10,000 random weightings in which the district ranks in the top ten.

| Rank | District | Index | Yield (t/ha) | Monsoon flood (%) | Flash flood (%) | Hot days | Top-10 share (%) | LISA |
|---------|----------------|---------|---------|---------|---------|---------|---------|---------|
| 1 | Sunamganj | 0.578 | 3.79 | 48.2 | 16.4 | 1.9 | 88 | HH |
| 2 | Patuakhali | 0.464 | 2.67 | 2.5 | 0.9 | 7.6 | 77 | ns |
| 3 | Kishoreganj | 0.460 | 4.23 | 46.6 | 12.7 | 6.7 | 77 | HH |
| 4 | Barguna | 0.368 | 3.06 | 1.0 | 0.5 | 7.0 | 61 | ns |
| 5 | Sylhet | 0.354 | 3.07 | 21.3 | 7.2 | 1.6 | 70 | HH |
| 6 | Brahmanbaria | 0.318 | 4.04 | 30.1 | 4.3 | 8.9 | 56 | ns |
| 7 | Chapai Nawabganj | 0.307 | 4.08 | 11.0 | 0.1 | 25.8 | 51 | ns |
| 8 | Habiganj | 0.306 | 3.66 | 18.7 | 6.2 | 6.2 | 59 | HH |
| 9 | Netrokona | 0.304 | 4.15 | 28.9 | 7.2 | 4.1 | 53 | HH |
| 10 | Meherpur | 0.303 | 4.00 | 0.6 | 0.0 | 29.9 | 47 | ns |

The index is spatially clustered (global Moran's I = 0.429, z = 5.54, pseudo p = 0.0001, the minimum attainable with 9,999 permutations). LISA identifies a high–high cluster of 5 north-eastern districts (Sunamganj, Kishoreganj, Sylhet, Habiganj, Netrokona) and low–low clusters in the north-west and the lower Meghna region (Chandpur, Feni, Thakurgaon, Lakshmipur, Dinajpur, Munshiganj, Lalmonirhat, Panchagarh, Nilphamari) (Figure 4). After FDR correction, Sunamganj and Habiganj remain significant high–high districts and Nilphamari a significant low–low district. Patuakhali and Barguna rank highly but do not form a significant cluster, because neighbouring coastal districts score lower.

Figure 4. (a) Vulnerability index; numbers mark the five highest-ranked districts (1 Sunamganj, 2 Patuakhali, 3 Kishoreganj, 4 Barguna, 5 Sylhet). (b) LISA clusters at pseudo p < 0.05 (9,999 permutations, fuzzy contiguity weights); outlined districts remain significant after FDR correction.

![](figures/fig3_vulnerability_lisa.png)

## 3.4 Panel models

Within districts, after removing district and year effects, none of the weather variables, NDVI or flood fractions has a consistent association with BBS yield (Table 7, Figure 5a). In the full period (M1, M2) no coefficient is significant, and the within R² is below 0.01. Peak-season NDVI has a small negative, non-significant coefficient: -0.071 t/ha (SE 0.089, p = 0.427; Driscoll–Kraay p = 0.307) per 0.1 NDVI. In the shorter JRC window (M3), hot days have a small positive coefficient (+0.0066 t/ha (SE 0.0019, p < 0.001; Driscoll–Kraay p < 0.001) per day), and mean temperature and precipitation small negative ones, but none of these associations appears in the full period (M1) or in the Sentinel-1 window (M4), so they are not robust to the choice of years.

Table 7. Two-way fixed-effects models of Boro yield (t/ha). Coefficient with significance from district-clustered standard errors; clustered SE in parentheses; Driscoll–Kraay p-value in brackets. *** p < 0.01, ** p < 0.05, * p < 0.10.

| Variable | M1 Weather | M2 Weather + NDVI | M3 Weather + flood (JRC) | M4 Weather + flood (Sentinel-1) |
|--------------------------|----------------|----------------|----------------|----------------|
| Mean temperature (°C) | 0.0100 | -0.0025 | -0.1146* | 0.0643 |
|  | (0.0701) [0.895] | (0.0719) [0.975] | (0.0635) [0.024] | (0.0934) [0.461] |
| Season precipitation (100 mm) | -0.0036 | -0.0036 | -0.0133* | 0.0019 |
|  | (0.0060) [0.538] | (0.0060) [0.559] | (0.0070) [0.031] | (0.0090) [0.804] |
| Hot days (Tmax > 35 °C) | 0.0027 | 0.0025 | 0.0066*** | -0.0005 |
|  | (0.0018) [0.438] | (0.0019) [0.458] | (0.0019) [0.000] | (0.0026) [0.911] |
| Peak-season NDVI (0.1 units) |  | -0.0712 |  |  |
|  |  | (0.0895) [0.307] |  |  |
| Monsoon flood, JRC (10 pp) |  |  | 0.0100 |  |
|  |  |  | (0.0367) [0.721] |  |
| Flash flood, JRC (10 pp) |  |  | 0.0394* |  |
|  |  |  | (0.0234) [0.026] |  |
| Monsoon flood, Sentinel-1 (10 pp) |  |  |  | 0.0328 |
|  |  |  |  | (0.0370) [0.190] |
| Flash flood, Sentinel-1 (10 pp) |  |  |  | -0.0049 |
|  |  |  |  | (0.0353) [0.900] |
| Harvest years | 2011-2025 | 2011-2025 | 2011-2021 | 2016-2025 |
| Districts | 64 | 64 | 64 | 64 |
| Observations | 960 | 960 | 704 | 640 |
| R-squared (within, two-way) | 0.005 | 0.007 | 0.035 | 0.003 |

Flood effects appear in harvested area and production instead (Table 8, Figure 5b). A 10-percentage-point increase in the Sentinel-1 flash flood fraction is associated with a change in harvested area of -24.3 % (SE 10.5, p = 0.021; Driscoll–Kraay p < 0.001) and in production of -24.5 % (SE 11.0, p = 0.027; Driscoll–Kraay p < 0.001). The JRC flash flood coefficient has the same sign but is smaller and not significant at 5 % (area -4.8 % (SE 2.8, p = 0.080; Driscoll–Kraay p = 0.140)). Monsoon flood fractions show no consistent association: the JRC coefficient on area is positive (+5.5 % (SE 3.1, p = 0.073; Driscoll–Kraay p = 0.098)) and the Sentinel-1 coefficient negative (-5.0 % (SE 5.4, p = 0.350; Driscoll–Kraay p = 0.169)).

Table 8. Two-way fixed-effects models of log harvested area (Area) and log production (Prod.). Coefficients and standard errors multiplied by 100 (approximate % change). Notation as in Table 7.

| Variable | Area M1 | Area M3 | Area M4 | Prod. M1 | Prod. M3 | Prod. M4 |
|--------------------------|--------------|--------------|---------------|--------------|--------------|---------------|
| Mean temperature (°C) | 0.73 | -3.10 | 4.59 | 1.17 | -6.23 | 6.88 |
|  | (6.25) [0.861] | (4.85) [0.530] | (6.23) [0.256] | (7.03) [0.844] | (5.39) [0.278] | (6.55) [0.218] |
| Season precipitation (100 mm) | -0.49 | -1.14* | 1.61 | -0.60 | -1.51** | 1.67 |
|  | (1.02) [0.672] | (0.67) [0.020] | (1.67) [0.131] | (1.07) [0.631] | (0.70) [0.005] | (1.70) [0.124] |
| Hot days (Tmax > 35 °C) | -0.06 | 0.14 | -0.29 | 0.02 | 0.32* | -0.31 |
|  | (0.19) [0.800] | (0.16) [0.020] | (0.26) [0.228] | (0.20) [0.955] | (0.18) [0.000] | (0.25) [0.335] |
| Monsoon flood, JRC (10 pp) |  | 5.52* |  |  | 5.89* |  |
|  |  | (3.07) [0.098] |  |  | (3.18) [0.103] |  |
| Flash flood, JRC (10 pp) |  | -4.83* |  |  | -3.76 |  |
|  |  | (2.75) [0.140] |  |  | (2.71) [0.215] |  |
| Monsoon flood, Sentinel-1 (10 pp) |  |  | -5.02 |  |  | -4.21 |
|  |  |  | (5.37) [0.169] |  |  | (5.68) [0.303] |
| Flash flood, Sentinel-1 (10 pp) |  |  | -24.29** |  |  | -24.47** |
|  |  |  | (10.47) [0.000] |  |  | (11.03) [0.000] |
| Harvest years | 2011-2025 | 2011-2021 | 2016-2025 | 2011-2025 | 2011-2021 | 2016-2025 |
| Districts | 64 | 64 | 64 | 64 | 64 | 64 |
| Observations | 960 | 704 | 640 | 960 | 704 | 640 |
| R-squared (within, two-way) | 0.001 | 0.023 | 0.061 | 0.001 | 0.027 | 0.056 |

Much of the flash flood signal comes from the April 2017 haor flood. Table 9 lists the districts with the largest Sentinel-1 flash flood fractions in 2017: in all six north-eastern districts harvested area fell by 15–72 % and production by 16–72 % relative to 2015–2016, while yield changed by no more than 3.8 %. Across all 64 districts the rank correlation between the 2017 flash flood fraction and the change in area is weak (ρ = -0.14), because flash flooding was negligible outside the north-east. Excluding 2017, the Sentinel-1 flash flood coefficient on harvested area is similar in size (-23.3 % (SE 20.6, p = 0.258; Driscoll–Kraay p = 0.004)), but it is no longer significant with district-clustered standard errors. The flash flood effect is therefore consistent in magnitude but rests on a small number of large events.

Table 9. The April 2017 flash flood: Sentinel-1 and JRC flash flood fractions and the change in BBS harvested area, yield and production relative to the 2015–2016 mean (eight districts with the largest Sentinel-1 fractions).

| District | Flash flood, S1 (%) | Flash flood, JRC (%) | Harvested area (%) | Yield (%) | Production (%) |
|------------|---------|---------|---------|---------|----------|
| Sunamganj | 44.7 | 37.2 | -71.5 | -0.1 | -71.5 |
| Kishoreganj | 27.0 | 30.0 | -31.4 | +3.8 | -28.7 |
| Netrokona | 17.4 | 16.2 | -21.2 | +0.3 | -21.0 |
| Sylhet | 12.7 | 26.7 | -18.8 | -0.3 | -19.1 |
| Habiganj | 10.2 | 14.1 | -14.8 | -1.6 | -16.2 |
| Moulvibazar | 8.4 | 9.5 | -21.3 | -0.2 | -21.5 |
| Lalmonirhat | 7.9 | 0.4 | -2.8 | +3.2 | +0.2 |
| Brahmanbaria | 5.8 | 5.7 | -4.9 | +1.2 | -3.8 |

Figure 5. Fixed-effects coefficients with 95 % confidence intervals (district-clustered standard errors). (a) Yield models M1–M4. (b) Flood coefficients in models of log harvested area and log production (%, per 10 percentage points of district area).

![](figures/fig4_coefficients.png)

Residuals of model M2 remain spatially correlated in some years: Moran's I is significant at p < 0.05 in 9 of 15 harvest years and in 7 after FDR correction (median I = 0.14; Appendix Table A1). This supports reporting Driscoll–Kraay standard errors alongside clustered ones. In this panel the Driscoll–Kraay errors are often smaller than the clustered errors, which makes several weak associations in the JRC window (M3) nominally significant (Tables 7 and 8). Because these associations do not recur in the other periods, we base our conclusions on the more conservative clustered errors and on consistency across windows.

## 3.5 Trends

National Boro yield increased by 0.0336 t/ha per year over 2011–2025 (Kendall's τ = 0.96, Hamed–Rao p < 0.001), and area-weighted peak-season NDVI increased by 0.0051 per year (p < 0.001) (Table 10, Figure 6). Mean temperature, season precipitation and hot days show no significant trend over the 15 seasons (p = 0.235, 0.276 and 0.428). At district level, yield increased significantly in 39 of 64 districts after FDR correction and decreased significantly in none (median Sen's slope 0.031 t/ha per year).

Table 10. Mann–Kendall trend tests with Hamed–Rao correction (national series, harvest years 2011–2025).

| Series | Harvest years | n | Trend | Kendall's tau | Sen's slope (per year) | p (Hamed–Rao) |
|--------------------------|---------|---------|----------|---------|---------|-----------|
| National Boro yield (t/ha, BBS) | 2011-2025 | 15 | increasing | 0.962 | +0.0336 | < 0.001 |
| Peak-season NDVI (area-weighted) | 2011-2025 | 15 | increasing | 0.733 | +0.0051 | < 0.001 |
| Mean temperature (°C, area-weighted) | 2011-2025 | 15 | no trend | 0.238 | +0.0391 | 0.235 |
| Season precipitation (mm, area-weighted) | 2011-2025 | 15 | no trend | -0.219 | -10.0820 | 0.276 |
| Hot days (area-weighted) | 2011-2025 | 15 | no trend | 0.162 | +0.4962 | 0.428 |

Figure 6. National Boro yield and area-weighted covariates, 2011–2025, with Sen's slope.

![](figures/fig5_trends.png)

## 3.6 Interactive dashboard

The Streamlit dashboard reads the Gold tables and analysis outputs directly, so its figures cannot diverge from those in the paper (Figure 7). It provides a national overview, a district explorer for every panel variable, the vulnerability index and LISA maps, the model tables, and a data-quality page that reproduces the BBS extraction checks.

Figure 7. Overview page of the dashboard.

![](figures/fig7_dashboard.png)


# 4. Discussion

## 4.1 What documented integration changes

The main lesson of this study concerns the integration steps rather than any single model. An earlier version of this pipeline, built with the same sources, contained three errors that no downstream statistic revealed. BBS crop year "(t−1)–t" had been keyed to calendar year t−1, so every yield was paired with satellite and climate data from the previous season. Two complete seasons (2010-11 and 2011-12) had been dropped because the 2012 and 2013 editions group districts under former regions. And several editions had been only partly extracted, so up to seven districts were missing in some years; those gaps were filled by interpolation, and all years before 2012 by yields predicted from NDVI. Each error was plausible on its own and produced a dataset of the expected shape. They were found only by reconciling each extracted table with the totals printed by BBS, comparing the two editions in which each year appears, and recording the edition and page of every value. These checks are cheap, and we suggest they should be standard whenever official statistics are digitised from PDF.

Correcting the errors changed the substantive results. Associations between NDVI and yield reported for the earlier panel do not appear in the corrected one, and the vulnerability hotspot moved from the south-west to the north-east once the index was rebuilt from observed yields and documented flood measures. Pipelines that make each step inspectable are therefore not only a matter of convenience: they determine which conclusions can be trusted.

## 4.2 What BBS yield measures

The panel results are best explained by how BBS defines yield. Yield is production divided by harvested area, estimated from crop-cutting surveys on harvested fields [2]. A crop destroyed before harvest therefore leaves the harvested area instead of lowering the yield. The April 2017 flash flood shows this clearly: in Sunamganj, BBS harvested area and production both fell by 72 %, while yield was unchanged (Table 9). Studies that relate weather or flood exposure to BBS district yield alone will understate damage from events that destroy whole fields, and flood impacts should be assessed on harvested area and production.

The absence of within-district yield associations with weather and NDVI should be read in the same light. After district and year effects are removed, the remaining year-to-year variation in BBS yield is small, and part of it reflects sampling in the crop-cut surveys. Shocks common to all districts, such as national weather anomalies, input prices or variety releases, are absorbed by the year effects. Over 15 seasons the data therefore have little power to detect modest weather effects on yield, and the null results here are not evidence that weather does not matter for Boro rice. Hot days were associated with higher yield in one window but not in the others; we do not interpret this as a real effect, since temperatures above 35 °C during flowering are known to reduce spikelet fertility [23,24]. National NDVI and national yield both rose steadily over the period, without a matching trend in temperature, precipitation or hot days. This is consistent with gains from improved varieties and management, although the trend analysis cannot separate these causes.

## 4.3 Geography of vulnerability

The rebuilt index identifies the north-eastern haor basin as the main cluster of Boro vulnerability. This agrees with what is known of the region: Boro is the main rice crop of the deeply flooded haor basin, and it is harvested in April–May, when pre-monsoon flash floods can arrive from the upstream hills [12]. Patuakhali and Barguna rank highly for a different reason: Boro there is grown on a small area with low and variable yields, which is consistent with salinity and fresh-water constraints in the coastal zone, although neither is measured in this index. The western districts of Chapai Nawabganj and Meherpur (and, just outside the top ten, Chuadanga) rank highly because of heat exposure in March–May. The weight-sensitivity analysis shows that these three groups are stable, but the exact order within the top ten depends on the weights, so rankings should guide where to look more closely rather than serve as allocation rules [11,27].

## 4.4 Flood measurement

Keeping the JRC and Sentinel-1 flood series separate made it possible to test them against each other. They agree closely for monsoon flooding, which supports both, but Sentinel-1 captures the 2017 flash flood more consistently and produces the clearer association with harvested area. This is expected: April–May is often cloudy, and an optical record can miss short-lived inundation that radar observes [14,25]. For harvest years after 2015, radar-based flood fractions are therefore the better choice for Boro flood studies in Bangladesh. The monsoon flood fraction, by contrast, shows no consistent association with Boro area or production. As defined here it measures the extent of seasonal inundation, much of which is normal on the floodplain and may even benefit the following crop. Separating damaging floods from normal inundation would require comparing each year with a longer flood climatology.

## 4.5 Spatial dependence

The vulnerability index is spatially clustered, and model residuals remain spatially correlated in several years. Rather than estimate a cross-sectional spatial lag model on district means, which answers a different question from the panel models and has little power with 64 districts, we report Driscoll–Kraay standard errors that allow for correlation between districts. These errors were often smaller than district-clustered ones, so we base inference on the clustered errors and on whether an association recurs across periods; no additional association met that standard. A spatial panel model with fixed effects [40] would represent the dependence directly and is a natural extension once a longer series is available.

## 4.6 Transferability

The framework is not specific to Bangladesh or to rice. Its components are a gazetteer that maps every source spelling to one district list, table extraction with arithmetic and total checks, an explicit crop-calendar alignment, and Earth Engine extraction cached per variable and year. These carry over to any country that publishes sub-national crop statistics as PDF tables. Adding a source requires one new Silver table keyed on district and harvest year; the Gold schema and the analyses read from it unchanged.

## 4.7 Limitations

Several limitations remain. First, BBS estimates are survey-based and subject to sampling and revision error; we use them as published and have not compared them with independent area estimates. Second, 15 seasons is a short panel for detecting weather effects on yield, and the flash flood effect rests largely on a few large events. Third, the Sentinel-1 water threshold (−18 dB) and the 50 % cropland rule are fixed choices; apart from the 2017 event and the agreement with JRC, the flood fractions have not been validated against field observations. Fourth, the cropland mask is static (2021) and not specific to Boro, so NDVI also reflects other dry-season crops. Fifth, the vulnerability index covers exposure and production sensitivity only; salinity [41], groundwater depletion [42], irrigation access and socio-economic capacity are not included. Finally, all associations are within-district correlations and do not establish causal effects [32].

## 4.8 Future work

Following the separation suggested for this work, the agricultural questions raised here are left for a companion study. It would extend the econometric analysis with flood anomalies relative to a long-term climatology, Boro-specific crop masks, salinity and groundwater data for the coastal and haor districts, and spatial panel models. The pipeline will be updated as each new BBS yearbook is published.


# 5. Conclusions

This paper presented an open Bronze–Silver–Gold data engineering framework, implemented in Python and DuckDB, that integrates official BBS district Boro statistics with satellite, flood and climate data for all 64 districts of Bangladesh. Every one of the 960 district-year yields is read from a printed BBS table, reconciled with the national total and with a second edition where one exists, and aligned to the Boro harvest year; no value is imputed.

Applied to Boro rice, the framework shows that documented integration changes conclusions. Because BBS yield is measured per harvested hectare, flood damage appears in harvested area and production rather than in yield: a 10-percentage-point increase in Sentinel-1 flash flood area is associated with about a 24 % reduction in harvested area, an effect dominated by large events such as the April 2017 haor flood. Within districts, reported yield shows no consistent association with weather or NDVI over 2011–2025. A demonstration vulnerability index identifies a spatially coherent cluster in the north-eastern haor districts that is robust to weighting choices.

All code, validated data, the analytical warehouse and the interactive dashboard are openly available, and the pipeline can be rerun with a single command as each new BBS yearbook is published.

# CRediT authorship contribution statement

Tasnim Ahmad Mumu: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Writing – original draft, Writing – review & editing, Visualization.

# Declaration of competing interest

The author declares that she has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

# Declaration of generative AI use

[To be completed by the author according to the target journal's policy.]

# Data availability

All code, the validated BBS extraction with edition and page references, the Earth Engine district extracts, the DuckDB analytical database and the Streamlit dashboard are openly available at github.com/TasMumu/Bangladesh-Agri-Research (folder v2). BBS yearbooks are available from bbs.gov.bd; satellite and reanalysis data are available through Google Earth Engine.


# References

[1] Wilkinson MD, Dumontier M, Aalbersberg IJ, et al. The FAIR Guiding Principles for scientific data management and stewardship. Scientific Data. 2016;3:160018. doi:10.1038/sdata.2016.18

[2] Bangladesh Bureau of Statistics. Yearbook of Agricultural Statistics-2025 (37th series). Dhaka: Statistics and Informatics Division, Ministry of Planning; June 2026.

[3] Bangladesh Bureau of Statistics. Yearbook of Agricultural Statistics of Bangladesh, 2012–2024 editions (24th–36th series). Dhaka: Statistics and Informatics Division, Ministry of Planning; 2013–2025.

[4] Shahrier R, Hasan MN, Ankita SY, Tasnim I, Rahman KT. Impact of climate change on Boro rice production in Bangladesh: evidence from time series modeling. PLOS ONE. 2025;20(7):e0328699. doi:10.1371/journal.pone.0328699

[5] Al Mamun MA, Nihad SAI, Sarker MR, Sarkar MAR, Hossain MI, Kabir MS. Spatiotemporal mapping of rice acreage and productivity growth in Bangladesh. PLOS ONE. 2024;19(3):e0300648. doi:10.1371/journal.pone.0300648

[6] Mkhabela MS, Bullock P, Raj S, Wang S, Yang Y. Crop yield forecasting on the Canadian Prairies using MODIS NDVI data. Agricultural and Forest Meteorology. 2011;151(3):385–393. doi:10.1016/j.agrformet.2010.11.012

[7] Sakamoto T, Van Nguyen N, Ohno H, Ishitsuka N, Yokozawa M. Spatio-temporal distribution of rice phenology and cropping systems in the Mekong Delta with special reference to the seasonal water flow of the Mekong and Bassac rivers. Remote Sensing of Environment. 2006;100(1):1–16. doi:10.1016/j.rse.2005.09.007

[8] Khidirova E, Karakuş O. UniCrop: a universal, multi-source data engineering pipeline for scalable crop yield prediction. arXiv preprint arXiv:2601.01655. 2026.

[9] Wiréhn L, Danielsson Å, Neset TSS. Assessment of composite index methods for agricultural vulnerability to climate change. Journal of Environmental Management. 2015;156:70–80. doi:10.1016/j.jenvman.2015.03.020

[10] Murthy CS, Laxman B, Sesha Sai MVR. Geospatial analysis of agricultural drought vulnerability using a composite index based on exposure, sensitivity and adaptive capacity. International Journal of Disaster Risk Reduction. 2015;12:163–171. doi:10.1016/j.ijdrr.2015.01.004

[11] Tate E. Social vulnerability indices: a comparative assessment using uncertainty and sensitivity analysis. Natural Hazards. 2012;63(2):325–347. doi:10.1007/s11069-012-0152-2

[12] Kamal ASMM, Shamsudduha M, Ahmed B, et al. Resilience to flash floods in wetland communities of northeastern Bangladesh. International Journal of Disaster Risk Reduction. 2018;31:478–488. doi:10.1016/j.ijdrr.2018.06.011

[13] Pekel JF, Cottam A, Gorelick N, Belward AS. High-resolution mapping of global surface water and its long-term changes. Nature. 2016;540(7633):418–422. doi:10.1038/nature20584

[14] Uddin K, Matin MA, Meyer FJ. Operational flood mapping using multi-temporal Sentinel-1 SAR images: a case study from Bangladesh. Remote Sensing. 2019;11(13):1581. doi:10.3390/rs11131581

[15] Didan K. MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061 [dataset]. NASA EOSDIS Land Processes DAAC; 2021. doi:10.5067/MODIS/MOD13Q1.061

[16] Gorelick N, Hancher M, Dixon M, Ilyushchenko S, Thau D, Moore R. Google Earth Engine: planetary-scale geospatial analysis for everyone. Remote Sensing of Environment. 2017;202:18–27. doi:10.1016/j.rse.2017.06.031

[17] Zanaga D, Van De Kerchove R, Daems D, et al. ESA WorldCover 10 m 2021 v200 [dataset]. Zenodo; 2022. doi:10.5281/zenodo.7254221

[18] Muñoz-Sabater J, Dutra E, Agustí-Panareda A, et al. ERA5-Land: a state-of-the-art global reanalysis dataset for land applications. Earth System Science Data. 2021;13(9):4349–4383. doi:10.5194/essd-13-4349-2021

[19] Torres R, Snoeij P, Geudtner D, et al. GMES Sentinel-1 mission. Remote Sensing of Environment. 2012;120:9–24. doi:10.1016/j.rse.2011.05.028

[20] Farr TG, Rosen PA, Caro E, et al. The Shuttle Radar Topography Mission. Reviews of Geophysics. 2007;45(2):RG2004. doi:10.1029/2005RG000183

[21] Armbrust M, Ghodsi A, Xin R, Zaharia M. Lakehouse: a new generation of open platforms that unify data warehousing and advanced analytics. In: Proceedings of the 11th Conference on Innovative Data Systems Research (CIDR); 2021.

[22] Raasveldt M, Mühleisen H. DuckDB: an embeddable analytical database. In: Proceedings of the 2019 International Conference on Management of Data (SIGMOD). ACM; 2019. p. 1981–1984. doi:10.1145/3299869.3320212

[23] Jagadish SVK, Craufurd PQ, Wheeler TR. High temperature stress and spikelet fertility in rice (Oryza sativa L.). Journal of Experimental Botany. 2007;58(7):1627–1635. doi:10.1093/jxb/erm003

[24] Prasad PVV, Boote KJ, Allen LH, Sheehy JE, Thomas JMG. Species, ecotype and cultivar differences in spikelet fertility and harvest index of rice in response to high temperature stress. Field Crops Research. 2006;95(2–3):398–411. doi:10.1016/j.fcr.2005.04.008

[25] Twele A, Cao W, Plank S, Martinis S. Sentinel-1-based flood mapping: a fully automated processing chain. International Journal of Remote Sensing. 2016;37(13):2990–3004. doi:10.1080/01431161.2016.1192304

[26] OECD, European Commission Joint Research Centre. Handbook on Constructing Composite Indicators: Methodology and User Guide. Paris: OECD Publishing; 2008. doi:10.1787/9789264043466-en

[27] Saisana M, Saltelli A, Tarantola S. Uncertainty and sensitivity analysis techniques as tools for the quality assessment of composite indicators. Journal of the Royal Statistical Society: Series A. 2005;168(2):307–323. doi:10.1111/j.1467-985X.2005.00350.x

[28] Moran PAP. Notes on continuous stochastic phenomena. Biometrika. 1950;37(1–2):17–23. doi:10.1093/biomet/37.1-2.17

[29] Anselin L. Local indicators of spatial association—LISA. Geographical Analysis. 1995;27(2):93–115. doi:10.1111/j.1538-4632.1995.tb00338.x

[30] Benjamini Y, Hochberg Y. Controlling the false discovery rate: a practical and powerful approach to multiple testing. Journal of the Royal Statistical Society: Series B. 1995;57(1):289–300. doi:10.1111/j.2517-6161.1995.tb02031.x

[31] Rey SJ, Anselin L. PySAL: a Python library of spatial analytical methods. Review of Regional Studies. 2007;37(1):5–27. doi:10.52324/001c.8285

[32] Dell M, Jones BF, Olken BA. What do we learn from the weather? The new climate–economy literature. Journal of Economic Literature. 2014;52(3):740–798. doi:10.1257/jel.52.3.740

[33] Driscoll JC, Kraay AC. Consistent covariance matrix estimation with spatially dependent panel data. Review of Economics and Statistics. 1998;80(4):549–560. doi:10.1162/003465398557825

[34] Wooldridge JM. Econometric Analysis of Cross Section and Panel Data. 2nd ed. Cambridge, MA: MIT Press; 2010.

[35] Sheppard K. linearmodels: linear (regression) models for Python, version 7.0 [software]. https://github.com/bashtage/linearmodels

[36] Mann HB. Nonparametric tests against trend. Econometrica. 1945;13(3):245–259. doi:10.2307/1907187

[37] Kendall MG. Rank Correlation Methods. 4th ed. London: Charles Griffin; 1975.

[38] Hamed KH, Rao AR. A modified Mann–Kendall trend test for autocorrelated data. Journal of Hydrology. 1998;204(1–4):182–196. doi:10.1016/S0022-1694(97)00125-X

[39] Sen PK. Estimates of the regression coefficient based on Kendall's tau. Journal of the American Statistical Association. 1968;63(324):1379–1389. doi:10.1080/01621459.1968.10480934

[40] Elhorst JP. Spatial Econometrics: From Cross-Sectional Data to Spatial Panels. Berlin: Springer; 2014.

[41] Sarkar SK, Rudra RR, Sohan AR, et al. Coupling of machine learning and remote sensing for soil salinity mapping in coastal area of Bangladesh. Scientific Reports. 2023;13:17056. doi:10.1038/s41598-023-44132-4

[42] Shamsudduha M, Taylor RG, Longuevergne L. Monitoring groundwater storage changes in the highly seasonal humid tropics: validation of GRACE measurements in the Bengal Basin. Water Resources Research. 2012;48(2):W02508. doi:10.1029/2011WR010993

# Appendix A. Residual spatial dependence

Table A1. Moran's I of model M2 residuals by harvest year (fuzzy contiguity weights, 9,999 permutations).

| Harvest year | Moran's I | Pseudo p | FDR-adjusted p |
|---------|---------|---------|------------|
| 2011 | 0.186 | 0.0097 | 0.0364 |
| 2012 | 0.234 | 0.0040 | 0.0200 |
| 2013 | 0.006 | 0.3737 | 0.4004 |
| 2014 | 0.064 | 0.1709 | 0.1972 |
| 2015 | 0.141 | 0.0337 | 0.0632 |
| 2016 | 0.07 | 0.1489 | 0.1861 |
| 2017 | -0.115 | 0.1069 | 0.1458 |
| 2018 | -0.034 | 0.4260 | 0.4260 |
| 2019 | 0.361 | 0.0001 | 0.0015 |
| 2020 | 0.256 | 0.0015 | 0.0112 |
| 2021 | 0.16 | 0.0227 | 0.0486 |
| 2022 | 0.131 | 0.0439 | 0.0732 |
| 2023 | 0.085 | 0.1045 | 0.1458 |
| 2024 | 0.155 | 0.0194 | 0.0486 |
| 2025 | 0.152 | 0.0203 | 0.0486 |

# Appendix B. Software

Table B1. Software and versions used to produce the results.

| Package | Version | Role |
|---------------|---------|--------------------------|
| Python | 3.13.7 | Language |
| duckdb | 1.5.2 | Analytical warehouse (Gold layer) |
| pandas | 2.3.3 | Data manipulation |
| numpy | 2.3.3 | Numerics |
| pyarrow | 24.0.0 | Parquet (Silver layer) |
| camelot-py | 1.0.9 | BBS PDF table extraction |
| earthengine-api | 1.7.22 | MODIS, ERA5-Land, JRC, Sentinel-1 extraction |
| geopandas | 1.1.3 | Boundaries and maps |
| libpysal | 4.14.1 | Spatial weights |
| esda | 2.9.0 | Moran's I, LISA |
| linearmodels | 7.0 | Fixed-effects panel models |
| statsmodels | 0.14.6 | FDR correction |
| pymannkendall | 1.4.3 | Mann–Kendall tests |
| scipy | 1.16.3 | Rank correlations |
| matplotlib | 3.10.7 | Figures |
| streamlit | 1.58.0 | Dashboard |
| plotly | 6.8.0 | Dashboard charts |
