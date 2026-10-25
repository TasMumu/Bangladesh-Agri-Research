# 3. Results

## 3.1 Pipeline outputs and data quality

The pipeline parsed {{ f"{BBS['n_rows']:,}" }} district rows from the 14 yearbook editions (28 edition–crop-year tables). Of these, {{ BBS['n_fail'] }} failed the arithmetic identities, all in the 2012-13 columns of the 2013 edition; the same year is printed consistently in the 2014 edition, which is used. In {{ BBS['n_complete'] }} of the 28 edition–year tables all 64 district rows were parsed; in the remaining four (the 2015 and 2018 editions, where part of the table did not parse) the same crop years are complete in another edition. Wherever a complete table prints a national total ({{ BBS['n_nat_complete'] }} tables), the sum of district production equals it to within {{ "0.001" if BBS['max_gap_pct'] < 0.001 else f(BBS['max_gap_pct'], 3) }} %. For the two crop years whose tables print no national row, the district sums agree with the totals quoted in the yearbook text: {{ f"{NATSUM['2010-11']:,.0f}" }} t against "186.17 lac metric tons" for 2010-11 (2012 edition), and {{ f"{NATSUM['2021-22']:,.0f}" }} t against "201,85,945 metric tons" for 2021-22 (2022 edition). Of the {{ BBS['n_two'] }} district-years printed in two editions, {{ BBS['n_diff'] }} differ, each by at most {{ int(BBS['max_area_diff']) }} ha of area, consistent with rounding. The result is a complete panel of {{ R['n_panel'] }} district-years with no missing yields (Table 4, Figure 2), and each row records the edition and page from which it was read.

Table 4. Extraction and validation of BBS district Boro estimates by crop year.

{{ table_bbs_checks }}

Figure 2. Number of districts with observed data for each variable and Boro harvest year.

![](figures/fig2_coverage.png)

The two flood sources agree closely where they overlap (Figure 3). For harvest years {{ R['flood_overlap_monsoon']['years'] }}, the district monsoon flood fractions from JRC and Sentinel-1 have a Pearson correlation of {{ f(R['flood_overlap_monsoon']['pearson_r'], 2) }} (n = {{ R['flood_overlap_monsoon']['n'] }}) and similar means ({{ f(100 * R['flood_overlap_monsoon']['mean_jrc'], 1) }} % and {{ f(100 * R['flood_overlap_monsoon']['mean_s1'], 1) }} % of district area). Flash flood fractions agree less closely (r = {{ f(R['flood_overlap_flash']['pearson_r'], 2) }}, n = {{ R['flood_overlap_flash']['n'] }}), as expected for a short April–May window in which a single cloud-free Landsat scene can decide whether flooding is observed.

Figure 3. Agreement between JRC (Landsat) and Sentinel-1 flood fractions for the same districts and harvest years. Dashed line: 1:1.

![](figures/fig6_flood_agreement.png)

## 3.2 Descriptive statistics

Table 5 summarises the panel. District Boro yield averaged {{ f(R['yield_mean']) }} t/ha of husked rice (SD {{ f(R['yield_sd']) }}), ranging from {{ f(R['yield_min']) }} t/ha ({{ R['yield_min_case'][0] }}, {{ int(R['yield_min_case'][1]) }}) to {{ f(R['yield_max']) }} t/ha ({{ R['yield_max_case'][0] }}, {{ int(R['yield_max_case'][1]) }}). National yield, computed from the district totals, rose from {{ f(R['national_yield']['2011']) }} t/ha in 2011 to {{ f(R['national_yield']['2025']) }} t/ha in 2025. Monsoon flooding covered on average {{ f(100 * DESC.loc['Monsoon flood fraction, JRC', 'mean'], 1) }} % (JRC) to {{ f(100 * DESC.loc['Monsoon flood fraction, Sentinel-1', 'mean'], 1) }} % (Sentinel-1) of district area, and flash flooding about {{ f(100 * DESC.loc['Flash flood fraction, Sentinel-1', 'mean'], 1) }} % in both sources, with long right tails driven by the north-eastern haor districts.

Table 5. Descriptive statistics (district-year observations).

{{ table_descriptives }}

## 3.3 Vulnerability index and spatial clustering

The index ranges from {{ f(R['vi']['min'][1]) }} ({{ R['vi']['min'][0] }}) to {{ f(R['vi']['max'][1]) }} ({{ R['vi']['max'][0] }}). The ten highest-ranked districts are listed in Table 6. They fall into three groups: the north-eastern haor districts (Sunamganj, Kishoreganj, Sylhet, Habiganj, Netrokona), where flood exposure dominates; the coastal districts Patuakhali and Barguna, where low and unstable yields on a small Boro area dominate; and western districts (Chapai Nawabganj, Meherpur), where heat exposure dominates. Brahmanbaria combines moderate flood exposure with moderate yield.

The ranking is moderately robust to weighting. Across 10,000 random weight vectors, the median Spearman correlation with the equal-weight ranking is {{ f(R['vi']['random_weights']['spearman_median'], 2) }} (5th percentile {{ f(R['vi']['random_weights']['spearman_p05'], 2) }}). Of the ten top-ranked districts, {{ int((TOP.p_top10_random_weights >= 0.5).sum()) }} remain in the top ten in at least half of the draws; the exception is {{ ", ".join(f"{d} ({100 * s:.0f} %)" for d, s in TOP.p_top10_random_weights[TOP.p_top10_random_weights < 0.5].items()) }}. Omitting one component at a time gives Spearman correlations of {{ f(min(v['spearman'] for v in R['vi']['leave_one_out'].values()), 2) }}–{{ f(max(v['spearman'] for v in R['vi']['leave_one_out'].values()), 2) }} with the baseline and retains {{ min(v['top10_overlap'] for v in R['vi']['leave_one_out'].values()) }}–{{ max(v['top10_overlap'] for v in R['vi']['leave_one_out'].values()) }} of the top ten; the heat component has the largest influence because it is negatively correlated with the flood components.

Table 6. The ten highest-ranked districts. Flood columns are mean JRC fractions (2011–2021); the top-10 share is the percentage of 10,000 random weightings in which the district ranks in the top ten.

{{ table_vi_top }}

The index is spatially clustered (global Moran's I = {{ f(R['vi']['moran_I']) }}, z = {{ f(R['vi']['moran_z'], 2) }}, pseudo p = {{ f(R['vi']['moran_p'], 4) }}, the minimum attainable with 9,999 permutations). LISA identifies a high–high cluster of {{ len(R['vi']['hh_005']) }} north-eastern districts ({{ ", ".join(R['vi']['hh_005']) }}) and low–low clusters in the north-west and the lower Meghna region ({{ ", ".join(R['vi']['ll_005']) }}) (Figure 4). After FDR correction, {{ " and ".join(R['vi']['hh_fdr']) }} remain significant high–high districts and {{ " and ".join(R['vi']['ll_fdr']) }} a significant low–low district. Patuakhali and Barguna rank highly but do not form a significant cluster, because neighbouring coastal districts score lower.

Figure 4. (a) Vulnerability index; numbers mark the five highest-ranked districts (1 Sunamganj, 2 Patuakhali, 3 Kishoreganj, 4 Barguna, 5 Sylhet). (b) LISA clusters at pseudo p < 0.05 (9,999 permutations, fuzzy contiguity weights); outlined districts remain significant after FDR correction.

![](figures/fig3_vulnerability_lisa.png)

## 3.4 Panel models

Within districts, after removing district and year effects, none of the weather variables, NDVI or flood fractions has a consistent association with BBS yield (Table 7, Figure 5a). In the full period (M1, M2) no coefficient is significant, and the within R² is below 0.01. Peak-season NDVI has a small negative, non-significant coefficient: {{ coef('M2', 'ndvi_01') }} per 0.1 NDVI. In the shorter JRC window (M3), hot days have a small positive coefficient ({{ coef('M3', 'hot_days', 4) }} per day), and mean temperature and precipitation small negative ones, but none of these associations appears in the full period (M1) or in the Sentinel-1 window (M4), so they are not robust to the choice of years.

Table 7. Two-way fixed-effects models of Boro yield (t/ha). Coefficient with significance from district-clustered standard errors; clustered SE in parentheses; Driscoll–Kraay p-value in brackets. *** p < 0.01, ** p < 0.05, * p < 0.10.

{{ table_fe }}

Flood effects appear in harvested area and production instead (Table 8, Figure 5b). A 10-percentage-point increase in the Sentinel-1 flash flood fraction is associated with a change in harvested area of {{ pct('Area M4', 's1_flash_10') }} and in production of {{ pct('Production M4', 's1_flash_10') }}. The JRC flash flood coefficient has the same sign but is smaller and not significant at 5 % (area {{ pct('Area M3', 'jrc_flash_10') }}). Monsoon flood fractions show no consistent association: the JRC coefficient on area is positive ({{ pct('Area M3', 'jrc_monsoon_10') }}) and the Sentinel-1 coefficient negative ({{ pct('Area M4', 's1_monsoon_10') }}).

Table 8. Two-way fixed-effects models of log harvested area (Area) and log production (Prod.). Coefficients and standard errors multiplied by 100 (approximate % change). Notation as in Table 7.

{{ table_fe_ap }}

Much of the flash flood signal comes from the April 2017 haor flood. Table 9 lists the districts with the largest Sentinel-1 flash flood fractions in 2017: in all six north-eastern districts harvested area fell by {{ f(-EV.area_change_pct.max(), 0) }}–{{ f(-EV.area_change_pct.min(), 0) }} % and production by {{ f(-EV.production_change_pct.max(), 0) }}–{{ f(-EV.production_change_pct.min(), 0) }} % relative to 2015–2016, while yield changed by no more than {{ f(EV.yield_change_pct.abs().max(), 1) }} %. Across all 64 districts the rank correlation between the 2017 flash flood fraction and the change in area is weak (ρ = {{ f(R['event_2017']['spearman_s1_area'], 2) }}), because flash flooding was negligible outside the north-east. Excluding 2017, the Sentinel-1 flash flood coefficient on harvested area is similar in size ({{ pct('Area M4', 's1_flash_10', EX) }}), but it is no longer significant with district-clustered standard errors. The flash flood effect is therefore consistent in magnitude but rests on a small number of large events.

Table 9. The April 2017 flash flood: Sentinel-1 and JRC flash flood fractions and the change in BBS harvested area, yield and production relative to the 2015–2016 mean (eight districts with the largest Sentinel-1 fractions).

{{ table_event }}

Figure 5. Fixed-effects coefficients with 95 % confidence intervals (district-clustered standard errors). (a) Yield models M1–M4. (b) Flood coefficients in models of log harvested area and log production (%, per 10 percentage points of district area).

![](figures/fig4_coefficients.png)

Residuals of model M2 remain spatially correlated in some years: Moran's I is significant at p < 0.05 in {{ R['residual_moran']['n_sig_005'] }} of {{ R['residual_moran']['years'] }} harvest years and in {{ R['residual_moran']['n_sig_fdr'] }} after FDR correction (median I = {{ f(R['residual_moran']['median_I'], 2) }}; Appendix Table A1). This supports reporting Driscoll–Kraay standard errors alongside clustered ones. In this panel the Driscoll–Kraay errors are often smaller than the clustered errors, which makes several weak associations in the JRC window (M3) nominally significant (Tables 7 and 8). Because these associations do not recur in the other periods, we base our conclusions on the more conservative clustered errors and on consistency across windows.

## 3.5 Trends

National Boro yield increased by {{ f(R['trends'][0]['sen_slope'], 4) }} t/ha per year over 2011–2025 (Kendall's τ = {{ f(R['trends'][0]['tau'], 2) }}, Hamed–Rao p {{ fmt_p(R['trends'][0]['p']) }}), and area-weighted peak-season NDVI increased by {{ f(R['trends'][1]['sen_slope'], 4) }} per year (p {{ fmt_p(R['trends'][1]['p']) }}) (Table 10, Figure 6). Mean temperature, season precipitation and hot days show no significant trend over the 15 seasons (p = {{ f(R['trends'][2]['p']) }}, {{ f(R['trends'][3]['p']) }} and {{ f(R['trends'][4]['p']) }}). At district level, yield increased significantly in {{ R['district_trends']['n_up_fdr'] }} of 64 districts after FDR correction and decreased significantly in none (median Sen's slope {{ f(R['district_trends']['median_slope'], 3) }} t/ha per year).

Table 10. Mann–Kendall trend tests with Hamed–Rao correction (national series, harvest years 2011–2025).

{{ table_mk }}

Figure 6. National Boro yield and area-weighted covariates, 2011–2025, with Sen's slope.

![](figures/fig5_trends.png)

## 3.6 Interactive dashboard

The Streamlit dashboard reads the Gold tables and analysis outputs directly, so its figures cannot diverge from those in the paper (Figure 7). It provides a national overview, a district explorer for every panel variable, the vulnerability index and LISA maps, the model tables, and a data-quality page that reproduces the BBS extraction checks.

Figure 7. Overview page of the dashboard.

![](figures/fig7_dashboard.png)
