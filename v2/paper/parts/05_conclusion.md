# 5. Conclusions

This paper presented an open Bronze–Silver–Gold data engineering framework, implemented in Python and DuckDB, that integrates official BBS district Boro statistics with satellite, flood and climate data for all 64 districts of Bangladesh. Every one of the {{ R['n_panel'] }} district-year yields is read from a printed BBS table, reconciled with the national total and with a second edition where one exists, and aligned to the Boro harvest year; no value is imputed.

Applied to Boro rice, the framework shows that documented integration changes conclusions. Because BBS yield is measured per harvested hectare, flood damage appears in harvested area and production rather than in yield: a 10-percentage-point increase in Sentinel-1 flash flood area is associated with about a {{ f(-100 * AP['Area M4']['coef']['s1_flash_10']['b'], 0) }} % reduction in harvested area, an effect dominated by large events such as the April 2017 haor flood. Within districts, reported yield shows no consistent association with weather or NDVI over 2011–2025. A demonstration vulnerability index identifies a spatially coherent cluster in the north-eastern haor districts that is robust to weighting choices.

All code, validated data, the analytical warehouse and the interactive dashboard are openly available, and the pipeline can be rerun with a single command as each new BBS yearbook is published.

# CRediT authorship contribution statement

Tasnim Ahmad Mumu: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Data curation, Writing – original draft, Writing – review & editing, Visualization.

# Declaration of competing interest

The author declares that she has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

# Declaration of generative AI use

[To be completed by the author according to the target journal's policy.]

# Data availability

All code, the validated BBS extraction with edition and page references, the Earth Engine district extracts, the DuckDB analytical database and the Streamlit dashboard are openly available at github.com/TasMumu/Bangladesh-Agri-Research (folder v2). BBS yearbooks are available from bbs.gov.bd; satellite and reanalysis data are available through Google Earth Engine.
