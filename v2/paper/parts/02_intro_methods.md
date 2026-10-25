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

{{ table_alignment }}

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

Spatial weights use fuzzy contiguity: districts are neighbours if their boundaries, buffered by 100 m, touch. This avoids spurious islands caused by slivers between GADM polygons and gives every district at least one neighbour. Weights are row-standardised. Global Moran's I [28] is tested with 9,999 random permutations, so the smallest attainable pseudo p-value is 0.0001. Local indicators of spatial association (LISA) [29] classify districts as high–high, low–low, high–low or low–high at pseudo p < 0.05; because 64 local tests are performed, clusters that survive a Benjamini–Hochberg false discovery rate (FDR) correction [30] are also reported. Spatial statistics were computed with the PySAL libraries libpysal and esda [39].

## 2.8 Panel models

The panel models test whether the integrated covariates relate to observed yields in the expected directions, which validates the alignment of the data. The specification is

yield(i,t) = β′X(i,t) + α(i) + γ(t) + ε(i,t),

where α(i) are district fixed effects, γ(t) are harvest-year fixed effects and X contains the covariates. District effects absorb time-invariant differences such as soils and irrigation infrastructure; year effects absorb shocks common to all districts, including national technology and price changes. Four models are estimated with yield as the outcome: weather only (M1); weather plus peak-season NDVI (M2); weather plus JRC flood fractions for 2011–2021 (M3); and weather plus Sentinel-1 flood fractions for 2016–2025 (M4). NDVI is reported in a separate model because it is itself an outcome of weather and management, so including it changes the interpretation of the weather coefficients [31]. Because BBS yield is measured on harvested area, models M1, M3 and M4 are also estimated with the natural logarithm of harvested area and of production as outcomes; their coefficients, multiplied by 100, approximate percentage changes.

Standard errors are clustered by district. Because neighbouring districts share weather, Driscoll–Kraay standard errors, which are robust to cross-sectional and serial correlation [32], are reported alongside. The R² reported is the within R² of the two-way demeaned model. Residual spatial dependence is tested with Moran's I on the M2 residuals for each harvest year. Coefficients are interpreted as within-district associations, not causal effects [31,33]. Estimation used linearmodels [34].

## 2.9 Trend analysis

Monotonic trends in national Boro yield (BBS national totals) and in area-weighted national means of the covariates were tested with the Mann–Kendall test [35,36] using the Hamed–Rao variance correction for serial correlation [37], with Sen's slope as the trend magnitude [38]. District-level yield trends were tested in the same way, with FDR correction across the 64 districts.
