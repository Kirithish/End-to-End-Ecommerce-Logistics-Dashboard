# End-to-End Ecommerce Logistics Dashboard

**Python + SQL Server + Power BI** | Author: Kirithish Kathiresan

An end-to-end analysis of last-mile ecommerce deliveries: data cleaning, feature engineering and statistical testing in Python, a star schema in SQL Server, and a 5-page Power BI dashboard that ends in a recommendation.

## Business question

Which conditions (traffic, time of day, distance, area type, weather and agent profile) make deliveries slow, how many minutes does each one add, and what would fixing the biggest ones save?

## Key findings

All figures come from 43,739 deliveries. A delivery is **late** when it takes more than **160 minutes** (the 75th percentile). Overall, 76.95% of deliveries are on time (10,084 late) and the average delivery takes 125 minutes.

| Finding | Evidence |
|---|---|
| **Agent rating and traffic are the biggest drivers** | Agents rated below 4.5 are late 63% of the time vs 13 to 15% for higher-rated agents (median +55 min). Jam traffic is late 41% of the time vs 6% in low traffic (median +50 min). |
| **Long trips are slower** | Trips of 10 km or more are late about 38% of the time, vs 7 to 10% under 6 km. Each extra km adds about 1.6 min. |
| **Agent age matters too** | Agents aged 31 and over are late about 32% of the time vs 14 to 17% for younger agents. |
| **Evenings are slowest, mostly because of mix** | Evening orders average about 140 min vs about 101 min in the morning, but after controlling for traffic, distance and agents, evening adds only about 6 min. Evenings have more heavy traffic and longer trips. |
| **Low traffic is the easy case; the rest are similar** | Medium, high and jam traffic add about 16, 35 and 32 min over low traffic once other factors are held fixed. High vs medium traffic is a negligible difference. |
| **City, weekday and weekend do not matter** | Average delivery time stays within about 123 to 129 min across 22 cities, and weekdays and weekends are identical. |

Jam traffic is 31% of deliveries but 56% of late orders. Jam traffic in the evening is 30.5% of deliveries and 54% of late orders.

### Recommendation

1. **Match agents to routes.** Agent rating has the largest effect. Pair coaching for agents rated below 4.5 with shorter, lower-traffic routes.
2. **Add capacity in heavy-traffic windows.** Stagger pickups or add agents in the evening (about 5 to 10 pm), where jam traffic and late orders are concentrated.
3. **Route long trips deliberately.** Assign trips of 10 km or more to the nearest available agent and avoid batching them.

**Estimated impact (illustrative):** jam traffic accounts for about ₹259K of the ₹435K illustrative cost of late deliveries (about 59%). A 20% reduction would save an estimated **₹52K** over the 44 days in this data, under the assumed rates below.

## Statistical tests

Run with `Python Code/eda_analysis.py`. Delivery time was compared with Mann-Whitney U tests. The effect size is the rank-biserial r (about 0.1 small, 0.3 medium, 0.5 large).

| Comparison | Median gap | Effect size r |
|---|---|---|
| Agents rated below 4.5 vs 4.5 and above | +55 min | 0.59 |
| Jam vs low traffic | +50 min | 0.51 |
| Evening vs morning | +40 min | 0.45 |
| Trips of 10 km or more vs under 6 km | +35 min | 0.39 |
| Agents aged 31+ vs 30 and under | +30 min | 0.34 |
| High vs medium traffic | +5 min | 0.03 |
| Weekend vs weekday | 0 min | 0.00 |
| 22 cities (Kruskal-Wallis) | n/a | epsilon-squared 0.0002 (p = 0.075) |

**Regression** (delivery minutes on traffic, distance, evening, agent rating, agent age and date group; n = 39,958; R-squared = 0.30). Compared with low traffic: medium +16 min, high +35 min, jam +32 min. Each km adds 1.6 min, each point of agent rating lowers delivery time by 40 min, and each year of agent age adds 2.1 min.

## Dashboard (Power BI, Import mode)

Five pages: Overview, Delivery Performance, City Performance, Cost Analysis, and Drivers and Actions. Import mode was chosen because the data is static and the report is shared as a file; DirectQuery would suit data that updates continuously.

![Overview](Visual/Overview%20Page.png)
![Delivery Performance](Visual/Delivery%20Peformance%20Page.png)
![City Performance](Visual/City%20Performance%20Page.png)
![Cost Analysis](Visual/Cost%20Analysis%20Page.png)
![Drivers and Actions](Visual/Drivers%20and%20Actions%20Page.png)

## Architecture

```
Ecommerce Delivery Data.csv -> Python (clean, features, tests) -> SQL Server (star schema) -> Power BI
```

| Step | What I did |
|---|---|
| Clean and enrich | Fixed types and text, flagged invalid values, built distance (km, from coordinates), time-of-day, bands, late flag and an estimated city |
| Store | Staging table, then a star schema: `fact_deliveries`, lookup tables for weather, traffic, vehicle, area, category, city and date, a separate `delivery_costs` table, and one analysis view (`vw_delivery_analysis`). See `Data/SQL Server Brief.png`. |
| Analyse | EDA, Mann-Whitney tests with effect sizes, and a regression in `Python Code/eda_analysis.py` |
| Visualise | 5-page Power BI dashboard with DAX measures, in `Visual/End_to_End_Dashboard Pro.pbix` |

## Data

**Source:** Amazon Delivery Dataset (Kaggle), 43,739 deliveries from 11 Feb to 6 Apr 2022 in one flat table.

### Cleaning log

| Issue | Count | Handling |
|---|---|---|
| Zero or negative coordinates | 3,693 rows (8.4%) | Rows kept; distance blank and city set to Unknown |
| Agent ratings above 5 (6.0) | 53 | Set to blank |
| Agent ages under 18 (15) | 38 | Set to blank |
| Missing weather and traffic | 91 each | Labelled "Unknown" |
| Missing agent rating | 54 | Left blank |
| Text issues | n/a | Trimmed spaces, fixed "Metropolitian" typo |
| Pickup time crossing midnight | n/a | Moved to the next day |

### Limitations (please read)

- **Possibly simulated data.** Effects change in sharp steps at round numbers (rating 4.5, age 30, distance 10 km), and pickup wait is only ever 5, 10 or 15 minutes. Treat the findings as patterns in this dataset, not claims about real delivery operations.
- **Odd/even date pattern.** The late rate alternates between odd dates (about 16%) and even dates (about 32%) because the traffic, time-of-day and distance mix differs. The main effects hold within each group separately, and the regression adds about 5 min for even dates. I treat this as a data artifact and do not show a daily trend.
- **Only 44 days** inside a 55-day range (19 to 28 Feb and 22 Mar are missing), so there is no seasonality or month-over-month analysis.
- **No scheduled time, late flag, review scores, agent IDs or store IDs.** "Late" is my own threshold (over 160 minutes), and analysis is by group, not by individual agent.
- **City is estimated** from the nearest of 22 city centres to the store coordinates, so it is approximate.
- **Observational data:** findings show association, not proof of cause. Weather shows a large raw gap (sunny about 9% late vs cloudy and fog about 35%) but is not used for conclusions because of the dataset's other oddities.
- **Small groups** (Semi-Urban with 152 rows, bicycle with 15) are not used for conclusions.

### Illustrative cost assumptions

The cost page uses assumed rates and is **not measured cost**: 0.5 INR per agent minute, a fuel cost per km by vehicle (motorcycle 2.5, scooter 2.0, van 7.0, bicycle 0), and a 25 INR penalty per late order. They are used only to turn real minute gaps into rupees.

## Repository structure

```
README.md
Data/
  Ecommerce Delivery Data.csv
  SQL Server Brief.png
Python Code/
  eda_analysis.py
Visual/
  Overview Page.png
  Delivery Peformance Page.png
  City Performance Page.png
  Cost Analysis Page.png
  Drivers and Actions Page.png
  End_to_End_Dashboard Pro.pbix
```

## How to reproduce

1. Load the dataset into SQL Server as a staging table (SSMS, Import Flat File), then build the star schema and the `vw_delivery_analysis` view (see `Data/SQL Server Brief.png`).
2. Run the analysis: `pip install pandas numpy scipy`, then `python "Python Code/eda_analysis.py" "Data/Ecommerce Delivery Data.csv"`. The script expects the enriched columns, such as `late_flag`, `distance_km` and `traffic`.
3. Open the `.pbix` in Power BI Desktop and point the data source at your SQL Server instance and the `vw_delivery_analysis` view.

## Skills demonstrated

Python (pandas, feature engineering, Mann-Whitney tests, regression), SQL Server (star schema, keys, CTEs, window functions, views), Power BI (DAX, Import mode, sort-by-column, conditional formatting), data validation, and clear communication of limits.
