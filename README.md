# dengue-analysis

Where dengue hits Bangladesh hardest, how that has changed over time, and who dies from it, covering 2000 to October 2026. The analysis compares division maps for 2025 and 2026 and looks for the districts that are hot zones year after year.

**➡ The full analysis is in the notebook: [notebooks/dengue_analysis.ipynb](notebooks/dengue_analysis.ipynb)** (it opens on GitHub with all charts and tables already rendered).

![Cases per 100,000 by division, 2025 vs 2026](figures/04_map_cases_2025_vs_2026.png)

## Key findings

- **2026 is running ahead of 2025.** By 21 Oct 2026 there were **116,990 cases and 364 deaths**, already more than the whole of 2025 (102,861 cases). For weeks 1–39, 2026 had about **twice as many cases** as the same weeks of 2025 (81,589 vs 41,089).
- **Barishal is the worst-hit division for its population.** It had 231 cases per 100,000 people in 2025, 3.8× the national rate, and 116 per 100,000 so far in 2026. It has been a hotspot in 6 of the last 7 years.
- **Khulna is the new hot zone in 2026.** Its cases are up from 5,473 to 13,081, and it now has the **highest dengue death rate in the country**: 2.6 deaths per million people.
- **Some districts are hot zones almost every year.** Dhaka, Barisal, Pirojpur, Barguna, Madaripur and Narail were in the national top 10 by cases per person in all 7 years with complete data (2016–2018 and 2020–2023). Manikganj and Cox's Bazar were in the top 10 in 6 of those years. In 2023 Manikganj had the highest rate (831 cases per 100,000).
- **Deaths are concentrated in Dhaka city, but this is changing.** In 2025, Dhaka North and South city corporations had 31% of the country's cases but **63% of its deaths**. That is partly because severely ill patients from elsewhere are referred to Dhaka hospitals. In 2026 the city's share of deaths has fallen to 40% as more people die outside Dhaka.
- **Women die at about twice the rate of men once hospitalised.** This holds every year, for example 0.76% vs 0.39% in 2023, even though men make up about 60% of patients. The death rate rises steeply with age and passes 1% over age 55.
- **Seasonal timing:** 82–95% of each year's cases come between July and November. Case numbers rise and fall in step with temperature two to three months earlier.

## Charts

| | |
|---|---|
| ![Deaths map](figures/05_map_deaths_2025_vs_2026.png) | ![District maps](figures/07_map_districts_2022_2023.png) |
| ![Persistent hot zones](figures/08_map_district_persistence.png) | ![Hotspot heatmap](figures/03_hotspot_heatmap_division_year.png) |
| ![Weekly 2026 vs 2025](figures/09_weekly_2026_vs_2025.png) | ![National trend](figures/01_national_trend_2000_2026.png) |
| ![Seasonality](figures/02_seasonality_month_year.png) | ![Dhaka city vs rest](figures/06_dhaka_city_vs_rest.png) |
| ![Deaths and CFR](figures/10_deaths_cfr_division_year.png) | ![Age and sex](figures/11_age_sex.png) |

## Data sources

| Dataset | Coverage | Source |
|---|---|---|
| National yearly cases & deaths | 2000 – 21 Oct 2026 | [Hossain et al. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10334535/) (2000–22); DGHS figures via [Dhaka Tribune](https://www.dhakatribune.com/bangladesh/health/420184/dengue-two-more-die-as-1-232-cases-recorded-in-24), [Xinhua](https://english.news.cn/20251228/e1aeeae58a6047e88e4f45e5e13cf4c8/c.html), [TBS](https://www.tbsnews.net/bangladesh/health/dengue-death-toll-reaches-364-7-more-die-1579376) |
| DGHS Dengue Dashboard snapshot: totals by division and city corporation, weekly division series, monthly series, age and sex | 2023 – 1 Oct 2026 | [dashboard.dghs.gov.bd](https://dashboard.dghs.gov.bd/pages/heoc_dengue_v1.php), captured by [Ashiq-r-khan/Bangladesh-Dengue-Forecasting-Analysis](https://github.com/Ashiq-r-khan/Bangladesh-Dengue-Forecasting-Analysis) |
| Monthly cases, deaths & climate by division | Jan 2020 – Oct 2025 | [Mendeley Data doi:10.17632/cgwjshkx5k.2](https://data.mendeley.com/datasets/cgwjshkx5k) |
| Monthly cases for each of the 64 districts | 2016 – Feb 2024 | DGHS daily reports, compiled by [Khalidsyfullah/Research-on-Bangladeshi-Dengue-Data](https://github.com/Khalidsyfullah/Research-on-Bangladeshi-Dengue-Data) |
| Population by division and district | Census 2022 | Bangladesh Bureau of Statistics |
| Boundaries | — | [geoBoundaries](https://www.geoboundaries.org) BGD ADM1 (CC0) / ADM2 (CC BY 3.0 IGO) |

## Project layout

```
notebooks/dengue_analysis.ipynb   the analysis (run top to bottom)
data/raw/                         downloaded source files, unchanged
data/external/                    small hand-built tables (national series, populations) with sources
data/processed/                   cleaned tables written by the notebook
reports/                          result tables written by the notebook
figures/                          charts and maps written by the notebook
```

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/jupyter lab notebooks/dengue_analysis.ipynb   # then Run All
```

## Caveats

- **Cases are hospitalised cases reported to DGHS.** Infections that were never reported or treated in hospital are not counted, so the true number of infections is higher.
- **Deaths are recorded where the patient dies.** Because severe cases are referred to Dhaka hospitals, Dhaka's death rate looks higher than it really is, and other areas' death rates look lower.
- **The 2026 figures stop at different dates.** Division and city-corporation figures run to 1 Oct 2026, the date the dashboard snapshot was taken. National totals run to 21 Oct 2026.
- **District data is older and has a gap.** The open district series ends in early 2024, and its 2019 data covers only about a quarter of that year's cases, so 2019 is left out of the district analysis. Dhaka district also includes patients treated in Dhaka city hospitals who came from other districts.
- **The Mendeley dataset seems to contain one copy error.** Dhaka has exactly 40,615 cases in both August and October 2023. Its yearly totals still match the DGHS figures to within 1%.
- **Some age labels in the dashboard were broken.** A spreadsheet had turned some age ranges into dates (e.g. "06-Oct" for 6–10), so these were repaired. A handful of unreadable labels with very small counts were dropped.
- **Population is held at the 2022 census figure for every year**, so rates for other years are approximate.
